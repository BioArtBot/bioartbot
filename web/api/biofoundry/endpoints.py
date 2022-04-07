from flask import (Blueprint, jsonify, request)
from flask_jwt_extended import jwt_required
from flask_cors import cross_origin
from .core import (validate_and_extract_objects, validate_and_extract_construct,
                    save_objects_in_db, build_plasmid_from_submission)
from .genetic_part import GeneticPart
from .strain import Strain
from .plasmid import Plasmid
from .serializers import GeneticPartSchema, PlasmidSchema, StrainSchema, ConstructSubmissionSchema
from ..user.utilities import access_level_required #TODO bad dependency
from web.database.models import SuperUserRole


biofoundry_blueprint = Blueprint('biofoundry', __name__, url_prefix='/biofoundry')

@biofoundry_blueprint.route('/available_parts', methods=('GET', ))
@jwt_required()
@access_level_required(SuperUserRole.printer)
def get_available_parts():
    available_parts = GeneticPart.get_available_parts()
    schema = GeneticPartSchema(many=True)
    serialized = schema.dump(available_parts)

    insert_dict = {insert['id']: insert for insert in serialized}

    return jsonify({'assembly_standard': 'golden_gate_moclo', 'inserts': insert_dict}), 200

@biofoundry_blueprint.route('/available_strains', methods=('GET', ))
@jwt_required()
@access_level_required(SuperUserRole.printer)
def get_available_strains():
    available_strains = Strain.get_available()
    schema = StrainSchema(many=True)
    serialized = schema.dumps(available_strains)

    return jsonify({'data': serialized}), 200

@biofoundry_blueprint.route('/available_plasmids', methods=('GET', ))
@jwt_required()
@access_level_required(SuperUserRole.printer)
def get_available_plasmids():
    available_plasmids = Plasmid.get_available()
    schema = PlasmidSchema(many=True)
    serialized = schema.dumps(available_plasmids)

    return jsonify({'data': serialized}), 200

@biofoundry_blueprint.route('/upload_part', methods=('POST', ))
@jwt_required()
@access_level_required(SuperUserRole.admin)
def load_new_part():
    genetic_parts = validate_and_extract_objects(GeneticPartSchema, request.get_json())
    save_objects_in_db(genetic_parts)

    return jsonify({'data': None}), 201

@biofoundry_blueprint.route('/submit_construct', methods=('POST', ))
@jwt_required()
@access_level_required(SuperUserRole.admin)
def receive_construct():
    plasmid_data, email = validate_and_extract_construct(ConstructSubmissionSchema, request.get_json())
    id, name = build_plasmid_from_submission(plasmid_data, email)

    msg = f'Successfully created plasmid {id}, named {name}. Ready for build process'

    return jsonify({'status':'success', 'msg': msg, 'data': {'plasmid_id':id,'name':name}}), 201

def build_protocol():
    pass

def update_strain_status():
    pass