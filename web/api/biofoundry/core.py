import datetime
from functools import partial
import json
import csv
import os
from xml.dom import INVALID_STATE_ERR
from marshmallow import ValidationError
from jwt import (ExpiredSignatureError, PyJWTError)
from sqlalchemy.exc import IntegrityError, DataError
from psycopg2.errors import StringDataRightTruncation
from web.database.models import SubmissionStatus
from web.extensions import db
from .genetic_part import GeneticPart
from .plasmid import Plasmid
from .strain import Strain
from .exceptions import (DataErrorException, FileErrorException,
                        InvalidUsage, DataLengthException, DBError,
                        DataSyntaxError, PlasmidNumberException)

def validate_and_extract_objects(schema, json_data, update=False):
    try:
        objects = schema(many=True).load(json_data, partial=update)
    except ValidationError as err:
        raise InvalidUsage.from_validation_error(err)
    return objects

def extract_update_info(update_info):
    ids_to_update = list()
    update_data = list()
    try:
        for obj in update_info:
            ids_to_update.append(obj['global_id'])
            update_data.append(obj['update_data'])
    except KeyError as err:
        raise DataSyntaxError
    return ids_to_update, update_data

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

def update_objects_in_db(obj_class: type, ids_to_update: list, update_data_list: list):
    try:
        for idx, global_id in enumerate(ids_to_update):
            update_data = update_data_list[idx]
            obj_class.get_by_id(global_id).update(**update_data)
    except IntegrityError as err:
        raise DBError(err)
    except AttributeError:
        raise InvalidUsage.resource_not_found()
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

def delete_objects(obj_class, object_ids):
    if type(object_ids) != list:
        raise DataSyntaxError
    try:
        for object_id in object_ids:
            object = obj_class.get_by_id(object_id)
            if object is None:
                raise InvalidUsage.resource_not_found()
            object.delete()
        db.session.commit()
    except DataError as err:
        raise DBError(err)
    return True

def validate_and_extract_construct(schema, json_data):
    try:
        data = schema(many=False).load(json_data)
        email = data.pop('email')
        #need to validate construct for GG MoClo
    except ValidationError as err:
        raise InvalidUsage.from_validation_error(err)
    return data, email

def build_plasmid_from_parts(plasmid_data, email):
    plasmid = Plasmid.create_from_parts(**plasmid_data, status='Submitted', submitter=email)
    return plasmid.id, plasmid.name

def build_protocol_from_plasmid():
    raise InvalidUsage.not_implemented()

def infer_transformation_data(strains):
    for strain in strains:
        if len(strain['plasmid_ids']) > 1:
            raise PlasmidNumberException
        plasmid_id = strain['plasmid_ids'][0]
        plasmid = Plasmid.get_by_id(plasmid_id)
        
        if 'global_id' not in strain:
            plasmid_prefix = 2 if plasmid_id[:2] == 'p_' else 0
            strain['global_id'] = f's_{plasmid_id[plasmid_prefix:]}'
        if 'name' not in strain:
            strain['name'] = plasmid.name
        if 'friendly_name' not in strain:
            strain['friendly_name'] = plasmid.friendly_name
        if 'description' not in strain:
            strain['description'] = f"""
                {strain['background_strain']} containing the following plasmid:\n
                {plasmid.description}"""
        
        strain['status'] = 'Processed'
    
    return strains, plasmid