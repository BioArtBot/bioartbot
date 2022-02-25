from flask import (Blueprint, jsonify, request)
from flask_jwt_extended import jwt_required
from .core import validate_and_extract_objects, save_objects_in_db
from .genetic_part import GeneticPart
from .strain import Strain
from .serializers import GeneticPartSchema, StrainSchema
from ..user.utilities import access_level_required #TODO bad dependency
from web.database.models import SuperUserRole


biofoundry_blueprint = Blueprint('biofoundry', __name__, url_prefix='/biofoundry')

@biofoundry_blueprint.route('/available_parts', methods=('GET', ))
@jwt_required()
@access_level_required(SuperUserRole.printer)
def get_available_parts():
    available_parts = GeneticPart.get_available_parts()
    schema = GeneticPartSchema(many=True)
    serialized = schema.dumps(available_parts)

    return jsonify({'data': serialized}), 200

@biofoundry_blueprint.route('/available_strains', methods=('GET', ))
@jwt_required()
@access_level_required(SuperUserRole.printer)
def get_available_strains():
    available_strains = Strain.get_available()
    schema = StrainSchema(many=True)
    serialized = schema.dumps(available_strains)

    return jsonify({'data': serialized}), 200

@biofoundry_blueprint.route('/upload_part', methods=('POST', ))
@jwt_required()
@access_level_required(SuperUserRole.admin)
def load_new_part():
    genetic_parts = validate_and_extract_objects(GeneticPartSchema, request.get_json())
    save_objects_in_db(genetic_parts)

    return jsonify({'data': None}), 201

def receive_construct():
    pass

def build_protocol():
    pass

def update_strain_status():
    pass