import datetime
import json
import csv
import os
from marshmallow import ValidationError
from jwt import (ExpiredSignatureError, PyJWTError)
from sqlalchemy.exc import IntegrityError, DataError
from psycopg2.errors import StringDataRightTruncation
from web.extensions import db
from .genetic_part import GeneticPart
from .plasmid import Plasmid
from .strain import Strain
from .exceptions import (DataErrorException, FileErrorException,
                        InvalidUsage, DataLengthException, DBError)

def validate_and_extract_objects(schema, json_data):
    try:
        objects = schema(many=True).load(json_data)
        print(objects[-1]._model)
    except ValidationError as err:
        raise InvalidUsage.from_validation_error(err)
    return objects

def save_objects_in_db(objects: list):
    try:
        [object.save() for object in objects]
    except IntegrityError as err:
        raise DataErrorException
    except DataError as err:
        if type(err.orig) == StringDataRightTruncation:
            raise DataLengthException
        raise DBError(err)

    db.session.commit()
    return True

def extract_json_from_csv(csv_file):
    try:
        filename = 'temp.csv'
        csv_file.save(filename)
        with open(filename) as saved_file:
            reader = csv.DictReader(saved_file)
            json_data = [line for line in reader]
        os.remove(filename)
    except:
        try:
            os.remove(filename)
        except:
            pass
        raise FileErrorException
    return json_data

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