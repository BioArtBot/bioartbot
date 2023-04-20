import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
import string
from datetime import datetime
import os
import sys
import math
from contextlib import contextmanager

from web.api.lab_objects.lab_objects import LabObject, LabObjectPropertyCollection #Uncomfortable with this dependency
from web.database.models import (ArtpieceModel, JobModel, SuperUserModel, SuperUserRole, SubmissionStatus, BacterialColorModel, LabObjectsModel)
from web.robot.procedure_line_injector import ProcedureLineInjector

def read_args(args):
    if not args: args = {'notebook':False
                        ,'palette':'cryo_35_tuberack_2000ul'
                        ,'pipette':'p20_single_gen2'
                        ,'canvas': 'bioartbot_petriplate_90mm_round'
                        }
    NOTEBOOK = args.pop('notebook')
    LABWARE = args #assume unused args are all labware
    return NOTEBOOK, LABWARE

def initiate_environment(SQLALCHEMY_DATABASE_URI = None, APP_DIR = None):
    if not APP_DIR:
        APP_DIR = os.path.abspath(os.path.dirname(__file__))
    if not SQLALCHEMY_DATABASE_URI:
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
        if not SQLALCHEMY_DATABASE_URI:
            raise Exception('Database URI expected in env vars or passed explcitly')
    return APP_DIR, SQLALCHEMY_DATABASE_URI

def initiate_sql(SQLALCHEMY_DATABASE_URI):
    SQL_ENGINE = sa.create_engine(SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=SQL_ENGINE)
    return Session

@contextmanager
def session_scope(Session):
    """Provide transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

def make_procedure(artpiece_ids, requestor = None, SQLALCHEMY_DATABASE_URI = None, APP_DIR = None, num_pieces = 9, option_args = None): 
    NOTEBOOK, LABWARE = read_args(option_args)
    APP_DIR, SQLALCHEMY_DATABASE_URI = initiate_environment(SQLALCHEMY_DATABASE_URI, APP_DIR)
    Session = initiate_sql(SQLALCHEMY_DATABASE_URI)

    with session_scope(Session) as session:

        output_msg = []
        
        query_filter = (ArtpieceModel.confirmed == True,
                       )
        if artpiece_ids: query_filter += (ArtpieceModel.id.in_(artpiece_ids),)

        artpieces = (session.query(ArtpieceModel)
                .filter(*query_filter)
                .order_by(ArtpieceModel.submit_date.asc())
                .limit(num_pieces)
                .all())

        if not artpieces:
            output_msg.append('No new art found. All done.')
            return output_msg, None

        output_msg.append(f'Loaded {len(artpieces)} pieces of art')
        for artpiece in artpieces:
            output_msg.append(f"{artpiece.id}: {artpiece.title}, {artpiece.submit_date}")

        # Get all colors
        colors = session.query(BacterialColorModel).all()

        # Get canvas plate dimensions
        try:
            canvas = LabObject.load_from_name(LABWARE['canvas'])
        except: #kludgy fix to handle when CLI is used instead of web interface
            canvas_model = session.query(LabObjectsModel).filter(LabObjectsModel.name==LABWARE['canvas']).one_or_none()
            property_model = canvas_model.properties.all()
            canvas = LabObject(canvas_model.name, canvas_model.obj_class, LabObjectPropertyCollection._from_model(property_model))
        
        procedure_line_injector = ProcedureLineInjector()

        if LABWARE["pipette"] == "p10_multi":
            with open(os.path.join(APP_DIR,f'ART_TEMPLATE_8_TO_1.py')) as template_file:
                template_string = template_file.read()
            
            file_extension = "py"
        else:
            #Get Python art procedure template
            file_extension = 'ipynb' if NOTEBOOK == True else 'py' #Use Jupyter notbook template or .py template
            with open(os.path.join(APP_DIR,f'ART_TEMPLATE.{file_extension}')) as template_file:
                template_string = template_file.read()
        

        procedure = procedure_line_injector.add_labware(template_string, LABWARE)
        procedure, canvas_locations = procedure_line_injector.add_canvas_locations(procedure, artpieces)
        procedure = procedure_line_injector.add_pixel_locations(procedure, artpieces, canvas)
        procedure = procedure_line_injector.add_color_map(procedure, colors)

        now = datetime.now().strftime("%Y%m%d-%H%M%S")
        unique_file_name = f'ARTISTIC_PROCEDURE_{now}.{file_extension}'
        with open(os.path.join(APP_DIR,'procedures',unique_file_name),'w') as output_file:
            output_file.write(procedure)

        for artpiece in artpieces:
            artpiece.status = SubmissionStatus.processed

        #Job creation should probably be the responsibility of a different function
        #This is too messy
        if requestor is None:
            requestor = session.query(SuperUserModel).filter(SuperUserModel.email=='null').one_or_none()
            if requestor is None:
                requestor = SuperUserModel(email='null', created_at=datetime.now())
        else:
            requestor = requestor._model
        job = JobModel(request_date=datetime.now(),
                        file_name=unique_file_name,
                        requestor=session.merge(requestor),
                        options = LABWARE,
                        artpieces = artpieces
                        )
        session.add(job)

    output_msg.append('Successfully generated artistic procedure')
    output_msg.append('The following slots will be used:')
    output_msg.append('\n'.join([f'Slot {str(canvas_locations[key])}: "{key}"' for key in canvas_locations]))
    
    return output_msg, [os.path.join(APP_DIR,'procedures'),unique_file_name]
