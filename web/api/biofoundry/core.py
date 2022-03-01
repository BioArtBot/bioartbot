import datetime
import json
from marshmallow import ValidationError
from jwt import (ExpiredSignatureError, PyJWTError)
from sqlalchemy.exc import IntegrityError
from web.extensions import db
from .genetic_part import GeneticPart
from .plasmid import Plasmid
from .strain import Strain
from .exceptions import DataErrorException, InvalidUsage

def validate_and_extract_objects(schema, json_data):
    try:
        objects = schema(many=True).load(json_data)
    except ValidationError as err:
        raise InvalidUsage.from_validation_error(err)
    return objects

def save_objects_in_db(objects: list):
    try:
        [object.save() for object in objects]
    except IntegrityError as err: #Consider getting more specific
        raise DataErrorException

    db.session.commit()
    return True

def validate_and_extract_construct(schema, json_data):
    try:
        data = schema(many=False).load(json_data)
        email = data.pop('email')
        #need to validate construct for GG MoClo
    except ValidationError as err:
        raise InvalidUsage.from_validation_error(err)
    return data, email

def build_plasmid_from_submission(plasmid_data, email):
    plasmid = Plasmid.create_from_parts(**plasmid_data, status='Submitted', submitter=email)
    return plasmid.id, plasmid.name