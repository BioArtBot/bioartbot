import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
import string
from datetime import datetime
import os
import sys
import math
import numpy as np
import pandas as pd
from contextlib import contextmanager

from web.api.lab_objects.lab_objects import LabObject, LabObjectPropertyCollection #Uncomfortable with this dependency
from web.database.models import (ArtpieceModel, SubmissionStatus, BacterialColorModel, LabObjectsModel)

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

# Lists slots that should typically be available
def canvas_slot_generator():
    for slot in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
        yield str(slot)


def get_spacing(plate, grid_size):
    max_grid_postion = {'x':grid_size['x']-1, 'y':grid_size['y']-1}
    if plate.shape == 'round': #inscribe in circle
        aspect_ratio = max_grid_postion['x'] / max_grid_postion['y']

        angle = math.atan(aspect_ratio)
        x_max_mm = math.sin(angle) * plate.x_radius_mm
        y_max_mm = math.cos(angle) * plate.y_radius_mm

        wellspacing = x_max_mm * 2 / max_grid_postion['x'] #x and y are identical
    else:
        x_wellspacing = plate.x_radius_mm * 2 / grid_size['x']
        y_wellspacing = plate.y_radius_mm * 2 / grid_size['y']
        wellspacing = min(x_wellspacing, y_wellspacing)

        x_max_mm = wellspacing * max_grid_postion['x'] / 2
        y_max_mm = wellspacing * max_grid_postion['y'] / 2
    well_radius = min(plate.x_radius_mm, plate.y_radius_mm)

    return well_radius, wellspacing, x_max_mm, y_max_mm


def plate_location_map(coord, plate, well_radius, wellspacing, x_max_mm, y_max_mm):
    #Note coordinates stored as [y,x]
    x = (wellspacing * coord[1] - x_max_mm) / well_radius
    y = (wellspacing * -coord[0] + y_max_mm) / well_radius

    z = plate.z_touch_position_frac

    return x, y, z

def module_to_last(p1,p2):
    module = np.sqrt((p1["x"] - p2[0])**2 + (p1["y"] - p2[1])**2)
    return module

def register_pixels_too_close(pixels_too_close, new_pixels):
    #reduce all existing time-to-live counters by 1
    pixels_too_close.ttl = pixels_too_close.ttl - 1

    #format new pixels and add them to existing list
    new_pixels_with_ttl = pd.DataFrame(columns = ["pixel_index", "ttl"])
    new_pixels_with_ttl["pixel_index"] = new_pixels.index
    new_pixels_with_ttl["ttl"] = 10

    final_pixels = pd.concat([pixels_too_close, new_pixels_with_ttl], axis=0)

    #if a pixel was already in the list, drop the old one so that we use the new one with ttl=10
    final_pixels = final_pixels.drop_duplicates(subset=["pixel_index"], keep='last')

    #Drop anything where the time-to-live = 0
    final_pixels = final_pixels.loc[final_pixels.ttl > 0]

    return final_pixels

def optimize_print_order(unoptimized_list, units_per_mm, minimum_module_mm=2):

    minimum_module_unit = minimum_module_mm * units_per_mm
    # add the first pixel to optimized_list
    optimized_list = [unoptimized_list[0]]

    #calculate the module for the rest of pixels
    # dataframe from columns x and y
    df = pd.DataFrame(unoptimized_list[1:], columns=["x","y"])

    pixels_too_close = pd.DataFrame(columns=["pixel_index", "ttl"])

    while len(df) > 0:
        df["module"] = df.apply(module_to_last, args=(optimized_list[-1:]),axis=1)
        pixels_too_close = register_pixels_too_close(pixels_too_close, df[df["module"] <= minimum_module_unit])
        pixels_far_enough = df.loc[~df.index.isin(pixels_too_close.pixel_index)]
        # If there are pixels far enough, add the nearer one to optimized_list
        if len(pixels_far_enough) > 0:
            # add the nearest pixel to optimized_list
            next_pixel = pixels_far_enough.loc[pixels_far_enough["module"].idxmin()][["x","y"]]
        else:
            # if there are no pixels far enough, add the fardest pixel to optimized_list
            next_pixel = df.loc[df["module"].idxmax()][["x","y"]]

        optimized_list = optimized_list + [next_pixel.tolist()]
        # remove it from the df
        df = df[df.index != next_pixel.name]

    return optimized_list


def add_labware(template_string, labware):
    # replace labware placeholders with the proper Opentrons labware name, as specified in the arguments
    labware['tiprack'] = 'opentrons_96_tiprack_300ul' if 'p300' in labware['pipette'] else 'opentrons_96_tiprack_20ul'
    
    procedure = template_string.replace('%%PALETTE GOES HERE%%', labware['palette'])
    procedure = procedure.replace('%%CANVAS GOES HERE%%', labware['canvas'])
    procedure = procedure.replace('%%PIPETTE GOES HERE%%', labware['pipette'])
    procedure = procedure.replace('%%TIPRACK GOES HERE%%', labware['tiprack'])
    return procedure

def add_canvas_locations(template_string, artpieces):
    # write where canvas plates are to be placed into code
    get_canvas_slot = canvas_slot_generator()
    canvas_locations = dict(zip([artpiece.slug for artpiece in artpieces], get_canvas_slot))
    procedure = template_string.replace('%%CANVAS LOCATIONS GO HERE%%', str(canvas_locations))
    return procedure, canvas_locations

def add_pixel_locations(template_string, artpieces, canvas):
    # write where to draw pixels on each plate into code. Listed by color to reduce contamination
    pixels_by_color = dict()
    for artpiece in artpieces:
        grid_size = artpiece.canvas_size
        well_radius, wellspacing, x_max_mm, y_max_mm = get_spacing(canvas, grid_size)
        for color in artpiece.art:
            pixel_list = optimize_print_order(
                [plate_location_map(pixel, canvas, well_radius, wellspacing, x_max_mm, y_max_mm) for pixel in artpiece.art[color]],
                units_per_mm = 1 / well_radius
            )
            if color not in pixels_by_color:
                pixels_by_color[color] = dict()
            pixels_by_color[color][artpiece.slug] = pixel_list
    procedure = template_string.replace('%%PIXELS GO HERE%%', str(pixels_by_color))
    return procedure

def add_color_map(template_string, colors):
    color_map = {str(color.id): color.name for color in colors}
    procedure = template_string.replace('%%COLORS GO HERE%%', str(color_map))
    return procedure

def make_procedure(artpiece_ids, SQLALCHEMY_DATABASE_URI = None, APP_DIR = None, num_pieces = 9, option_args = None): 
    NOTEBOOK, LABWARE = read_args(option_args)
    APP_DIR, SQLALCHEMY_DATABASE_URI = initiate_environment(SQLALCHEMY_DATABASE_URI, APP_DIR)
    Session = initiate_sql(SQLALCHEMY_DATABASE_URI)

    with session_scope(Session) as session:
        output_msg = []
        
        query_filter = (ArtpieceModel.status == SubmissionStatus.submitted
                       ,ArtpieceModel.confirmed == True
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
        else:
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

            #Get Python art procedure template
            file_extension = 'ipynb' if NOTEBOOK == True else 'py' #Use Jupyter notbook template or .py template
            with open(os.path.join(APP_DIR,f'ART_TEMPLATE.{file_extension}')) as template_file:
                template_string = template_file.read()

            procedure = add_labware(template_string, LABWARE)
            procedure, canvas_locations = add_canvas_locations(procedure, artpieces)
            procedure = add_pixel_locations(procedure, artpieces, canvas)
            procedure = add_color_map(procedure, colors)

            now = datetime.now().strftime("%Y%m%d-%H%M%S")
            unique_file_name = f'ARTISTIC_PROCEDURE_{now}.{file_extension}'
            with open(os.path.join(APP_DIR,'procedures',unique_file_name),'w') as output_file:
                output_file.write(procedure)

            for artpiece in artpieces:
                artpiece.status = SubmissionStatus.processed

            output_msg.append('Successfully generated artistic procedure')
            output_msg.append('The following slots will be used:')
            output_msg.append('\n'.join([f'Slot {str(canvas_locations[key])}: "{key}"' for key in canvas_locations]))
    return output_msg, [os.path.join(APP_DIR,'procedures'),unique_file_name]
