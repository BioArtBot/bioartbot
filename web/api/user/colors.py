from flask import g
from marshmallow import fields, Schema, post_dump
from sqlalchemy.exc import DataError
from web.extensions import db
from web.database.models import BacterialColorModel, ApplicationModel
from web.api.biofoundry.strain import Strain
from .exceptions import InvalidUsage
from ..biofoundry.exceptions import (DataSyntaxError, DBError)

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
    strain.application = ApplicationModel.get_by_id(1) #assume 1 is bioart
    
    return BacterialColor(name=name, red=red, blue=blue, green=green, opacity=opacity, strain=strain, in_use=in_use).save(commit=True)

def get_color_id_by_name(name):
    return BacterialColor.query.filter(BacterialColor.name==name).one_or_none().id

def delete_colors(color_names):
    if type(color_names) != list:
        raise DataSyntaxError
    try:
        for color_name in color_names:
            color = BacterialColor.query.filter(BacterialColor.name==color_name).one_or_none()
            if color is None:
                raise InvalidUsage.resource_not_found()

            strain = color.strain
            strain.application = None
            strain.save()

            color.delete()
        db.session.commit()
    except DataError as err:
        raise DBError(err)
    return True