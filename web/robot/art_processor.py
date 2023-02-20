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

#Finds the closest point from the given point
def min_dist_point(start, remaininglist, cache = None, required_gap = 0):

    def point_close_to_cache(point):
        if cache:
            for cached_point in cache:
                if round(euclidean_distance(cached_point, point),5) < required_gap:
                    return True
        return False

    # Initialize minimum distance to max val and null for minimal point
    min_dist = sys.maxsize
    min_point = None

    # Search for nearest point if distance is smaller than previous
    #then keep that point
    for v in remaininglist:
        dist = euclidean_distance(start, v)
        if dist < min_dist and round(dist,5) >= required_gap:
            if not point_close_to_cache(v):
                min_dist = dist
                min_point = v

    if min_point is None: #If no point that is far enough away is found, just use the closest point
        print('no point found, using closest')
        min_point = min_dist_point(start, remaininglist, required_gap = 0)

    return min_point

#Finds Euclidean Distance Given Two Points
def euclidean_distance(start, end):
    return math.sqrt((start[0] - end[0])**2 +(start[1] - end[1])**2)

def create_segments(full_list):
    #create a grid from a list of tuples and return a list of lists

    #There is no reason to make segments of very small lists
    if len(full_list) < 60:
        return [full_list]

    segments = []
    num_segments = 20

    x_num_segments = int(math.sqrt(num_segments))
    x_segment_length = int(len(full_list) / x_num_segments)
    full_list.sort(key=lambda x: x[0])
    x_segments = [full_list[i:i+x_segment_length] for i in range(0, len(full_list), x_segment_length)]

    y_num_segments = int(math.ceil(num_segments / x_num_segments))
    for x_segment in x_segments:
        x_segment.sort(key=lambda x: x[1])
        y_segment_length = int(math.ceil(len(x_segment) / y_num_segments))
        y_segments = [x_segment[i:i+y_segment_length] for i in range(0, len(x_segment), y_segment_length)]
        segments.extend(y_segments)

    return segments

def optimize_print_order(list, units_per_mm):
    """
    Accepts an aribitrary list of points and returns that list in an
    order that minimizes the total distance traveled by the pipette.
    For very small distances between points (<2mm), the travel distance
    is optimized as much as possible, while not allowing points that are
    next to each other to be placed one after another. This is to ensure
    that the points have some time to dry.
    """

    #Starts with first item in list.
    
    ordered_list = []

    segments = create_segments(list)

    minimum_sequential_distance = 2 * units_per_mm #Assume 2mm required between subsequent points to give time to dry
    
    for segment in segments:
        current = segment[0]
        ordered_list.append(current)
        cache = []
        segment.remove(current)

        #Once added to the ordered list, it removes from previous list
        while len(segment) != 0:
            closest = min_dist_point(current, segment, cache, required_gap=minimum_sequential_distance)
            cache.append(closest)
            if len(cache) > 10:
                cache.pop(0)
            segment.remove(closest)
            ordered_list.append(closest)
            current = closest
    
    return ordered_list


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
