from flask import g
from marshmallow import fields, Schema, post_dump
from web.database.models import BacterialColorModel
from web.api.biofoundry.strain import Strain

BacterialColor = BacterialColorModel

def get_available_colors():
    return BacterialColor.query.filter(BacterialColor.in_use == True).all()

def get_available_colors_as_dicts():
    return [{'id': color.id, 'name': color.name, 'rgba': color.rgba} for color in
            get_available_colors()]

def get_all_colors():
    return BacterialColor.query.all()

def get_available_color_mapping():
    if not hasattr(g, 'color_mapping'):
        g.color_mapping = {str(color.id): color.rgba for color in get_available_colors()}
    return g.color_mapping

def set_color_strain(name, red, green, blue, opacity, in_use = True, strain = None, strain_global_id = None):
    if not opacity: opacity = 1.0
    if not strain:
        if not strain_global_id:
            raise ValueError('Must specify either strain or strain_id')
        else:
            strain = Strain.get_by_id(strain_global_id)
    # strain.application = 1 TODO properly set application
    
    return BacterialColor(name=name, red=red, blue=blue, green=green, opacity=opacity, strain=strain, in_use=in_use).save()