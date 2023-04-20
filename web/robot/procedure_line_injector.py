import sys
import math

class ProcedureLineInjector:

    # Lists slots that should typically be available
    def canvas_slot_generator(self):
        for slot in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            yield str(slot)


    def get_spacing(self, plate, grid_size):
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


    def plate_location_map(self, coord, plate, well_radius, wellspacing, x_max_mm, y_max_mm):
        #Note coordinates stored as [y,x]
        x = (wellspacing * coord[1] - x_max_mm) / well_radius
        y = (wellspacing * -coord[0] + y_max_mm) / well_radius

        z = plate.z_touch_position_frac

        return x, y, z

    #Finds the closest point from the given point
    def min_dist_point(self, start, remaininglist, cache = None, required_gap = 0):

        def point_close_to_cache(point):
            if cache:
                for cached_point in cache:
                    if round(self.euclidean_distance(cached_point, point),5) < required_gap:
                        return True
            return False

        # Initialize minimum distance to max val and null for minimal point
        min_dist = sys.maxsize
        min_point = None

        # Search for nearest point if distance is smaller than previous
        #then keep that point
        for v in remaininglist:
            dist = self.euclidean_distance(start, v)
            if dist < min_dist and round(dist,5) >= required_gap:
                if not point_close_to_cache(v):
                    min_dist = dist
                    min_point = v

        if min_point is None: #If no point that is far enough away is found, just use the closest point
            #print('no point found, using closest')
            min_point = self.min_dist_point(start, remaininglist, required_gap = 0)

        return min_point

    #Finds Euclidean Distance Given Two Points
    def euclidean_distance(self, start, end):
        return math.sqrt((start[0] - end[0])**2 +(start[1] - end[1])**2)

    def create_segments(self, full_list):
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

    def optimize_print_order(self, list, units_per_mm):
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

        segments = self.create_segments(list)

        minimum_sequential_distance = 2 * units_per_mm #Assume 2mm required between subsequent points to give time to dry
        
        for segment in segments:
            current = segment[0]
            ordered_list.append(current)
            cache = []
            segment.remove(current)

            #Once added to the ordered list, it removes from previous list
            while len(segment) != 0:
                closest = self.min_dist_point(current, segment, cache, required_gap=minimum_sequential_distance)
                cache.append(closest)
                if len(cache) > 10:
                    cache.pop(0)
                segment.remove(closest)
                ordered_list.append(closest)
                current = closest
        
        return ordered_list

    def add_labware(self, template_string, labware):
        # replace labware placeholders with the proper Opentrons labware name, as specified in the arguments
        labware['tiprack'] = 'opentrons_96_tiprack_300ul' if 'p300' in labware['pipette'] else 'opentrons_96_tiprack_20ul'
        
        procedure = template_string.replace('%%PALETTE GOES HERE%%', labware['palette'])
        procedure = procedure.replace('%%CANVAS GOES HERE%%', labware['canvas'])
        procedure = procedure.replace('%%PIPETTE GOES HERE%%', labware['pipette'])
        procedure = procedure.replace('%%TIPRACK GOES HERE%%', labware['tiprack'])
        return procedure

    def add_canvas_locations(self, template_string, artpieces):
        # write where canvas plates are to be placed into code
        get_canvas_slot = self.canvas_slot_generator()
        canvas_locations = dict(zip([artpiece.slug for artpiece in artpieces], get_canvas_slot))
        procedure = template_string.replace('%%CANVAS LOCATIONS GO HERE%%', str(canvas_locations))
        return procedure, canvas_locations

    def add_pixel_locations(self, template_string, artpieces, canvas):
        # write where to draw pixels on each plate into code. Listed by color to reduce contamination
        pixels_by_color = dict()
        for artpiece in artpieces:
            grid_size = artpiece.canvas_size
            well_radius, wellspacing, x_max_mm, y_max_mm = self.get_spacing(canvas, grid_size)
            for color in artpiece.art:
                pixel_list = self.optimize_print_order(
                    [self.plate_location_map(pixel, canvas, well_radius, wellspacing, x_max_mm, y_max_mm) for pixel in artpiece.art[color]],
                    units_per_mm = 1 / well_radius
                )
                if color not in pixels_by_color:
                    pixels_by_color[color] = dict()
                pixels_by_color[color][artpiece.slug] = pixel_list
        procedure = template_string.replace('%%PIXELS GO HERE%%', str(pixels_by_color))
        return procedure

    def add_color_map(self, template_string, colors):
        color_map = {str(color.id): color.name for color in colors}
        procedure = template_string.replace('%%COLORS GO HERE%%', str(color_map))
        return procedure