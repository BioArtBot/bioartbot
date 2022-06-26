from flask import (Blueprint, jsonify, request)
from flask_jwt_extended import jwt_required
from flask_cors import cross_origin
from .core import (validate_and_extract_objects, validate_and_extract_construct,
                    save_objects_in_db, build_plasmid_from_parts, extract_json_from_csv,
                    delete_objects, update_objects_in_db, extract_update_info,
                    build_protocol_from_plasmid, infer_transformation_data)
from .genetic_part import GeneticPart
from .strain import Strain
from .plasmid import Plasmid
from .serializers import (GeneticPartSchema, PlasmidSchema, StrainSchema,
                          ConstructSubmissionSchema)
from ..user.utilities import access_level_required #TODO bad dependency
from web.database.models import SubmissionStatus, SuperUserRole


biofoundry_blueprint = Blueprint('biofoundry', __name__, url_prefix='/biofoundry')

@biofoundry_blueprint.route('/available_parts', methods=('GET', ))
@jwt_required()
@access_level_required(SuperUserRole.printer)
def get_available_parts():
    """
    Reads all available genetic parts from the database.

    Parameters: none

    Returns:
        json:
            assembly_standard <str>: The assembly standard the genetic
                parts are meant to be used with. Only Golden Gate MoClo
                currently supported
            inserts <JSON>: A dict of all genetic parts, with global_id
                as key, each containing the following fields:
                {
                 gloabl_id: <str>,
                 name: <str>,
                 friendly_name: <str>,
                 description: <str>,
                 sequence: <str>,
                 part_type: <str>,
                 cloning_prefix: <str>,
                 cloning_suffix: <str>
                 }
    """
    available_parts = GeneticPart.get_available_parts()
    schema = GeneticPartSchema(many=True)
    serialized = schema.dump(available_parts)

    insert_dict = {insert['global_id']: insert for insert in serialized}

    return jsonify({'assembly_standard': 'golden_gate_moclo', 'inserts': insert_dict}), 200

@biofoundry_blueprint.route('/available_strains', methods=('GET', ))
@jwt_required()
@access_level_required(SuperUserRole.printer)
def get_available_strains():
    """
    Reads all available strains from the database.

    Parameters: none

    Returns:
        json:
            data <JSON>: A list of all strains, each containing the
                following fields:
                    {
                    gloabl_id: <str>,
                    name: <str>,
                    friendly_name: <str>,
                    description: <str>,
                    background_strain: <str>,
                    plasmids: <list>: A list of plasmids <PlasmidSchema>
                    }
    """
    available_strains = Strain.get_available()
    schema = StrainSchema(many=True)
    serialized = schema.dumps(available_strains)

    return jsonify({'data': serialized}), 200

@biofoundry_blueprint.route('/available_plasmids', methods=('GET', ))
@jwt_required()
@access_level_required(SuperUserRole.printer)
def get_available_plasmids():
    """
    Reads all available plasmids from the database.

    Parameters: none

    Returns:
        json:
            data <JSON>: A list of all plasmids, each containing the
                following fields:
                    {
                    gloabl_id: <str>,
                    name: <str>,
                    friendly_name: <str>,
                    description: <str>,
                    sequence: <str>,
                    sequence_of_interest: <str>,
                    antibiotic_resistance: <str>,
                    source: <str>,
                    inserts: <list>: A list of genetic_parts <GeneticPartSchema>
                    }
    """
    available_plasmids = Plasmid.get_available()
    schema = PlasmidSchema(many=True)
    serialized = schema.dumps(available_plasmids)

    return jsonify({'data': serialized}), 200

@biofoundry_blueprint.route('/upload/<object>', methods=('POST', ))
@jwt_required()
@access_level_required(SuperUserRole.admin)
def load_new_object(object):
    """
    Upload a new part, plasmid, or strain to the database.
    Object type is supplied in URL, not in JSON.
    Data may be sent as CSV instead of JSON by using the argument
    'format=csv' in the request. If a CSV is sent, the json will
    be ignored.

    Parameters:
        object <str>: The type of object to upload. Must be one of
            'part', 'plasmid', or 'strain'
        json:
            an object or list of objects, following the schema documented
            in the respective object's 'get' endpoint.
            Parts inside of Plasmids should be sent with the key
                "insert_ids", a list of global_ids of GeneticParts.
            Plasmids inside of Strains should be sent with the key
                "plasmid_ids", a list of global_ids of Plasmids.
        files (optional):
            A CSV file containing the data to upload. If supplied,
            it should be called 'csvfile' and be of type 'text/csv'
            The CSV schema should follow the json schema above.

    Returns:
        json:
            success <bool>: True if the upload was successful, False
                otherwise
            msg <str>: A message describing the success or failure
                of the upload
    """
    try:
        schema = {'part': GeneticPartSchema,
                  'strain': StrainSchema,
                  'plasmid': PlasmidSchema
                  }[object]
    except KeyError:
        return 404
    args = request.args
    if args.get('format') == 'csv':
        json_object = extract_json_from_csv(request.files['csvfile'])
    else:
        json_object = request.get_json()
    objects = validate_and_extract_objects(schema, json_object)
    save_objects_in_db(objects)

    return jsonify({'success': True, 'msg': f'Successfully loaded {object}s'}), 201


@biofoundry_blueprint.route('/delete/<object>', methods=('POST', ))
@jwt_required()
@access_level_required(SuperUserRole.admin)
def delete_object(object):
    """
    Delete an object from the database.
    Object type is supplied in URL, not in JSON

    Parameters:
        object <str>: The type of object to delete. Must be one of
            'part', 'plasmid', or 'strain'
        json:
            global_ids <list>: List of global_ids <int> of the objects
                               to delete

    Returns:
        json:
            success <bool>: True if the upload was successful, False
                otherwise
            msg <str>: A message describing the success or failure
                of the upload
    """
    try:
        obj_class = {'part': GeneticPart,
                  'strain': Strain,
                  'plasmid': Plasmid
                  }[object]
    except KeyError:
        return 404
    ids_to_delete = request.get_json()
    success = delete_objects(obj_class, ids_to_delete)

    return jsonify({'success': success, 'msg': f'Successfully deleted {object}s'}), 201

@biofoundry_blueprint.route('/update/<object>', methods=('POST', ))
@jwt_required()
@access_level_required(SuperUserRole.admin)
def update_object(object):
    """
    Update an object in the database.
    Object type is supplied in URL, not in JSON.
    Objects are updated by their global_id. Beyond this, only the fields
    that need to be updated need to be supplied.

    Parameters:
        object <str>: The type of object to update. Must be one of
            'part', 'plasmid', or 'strain'
        json:
            to_update <list>: A list of objects, following the schema:
                global_id <str>: The global_id of the object to update
                update_data <JSON>: The new data to update the object with.
                    Should follow the schema documented in the object type's
                    'get' endpoint. Only data to update needs to be supplied.
                    Parts inside of Plasmids should be sent with the key
                        "insert_ids", a list of global_ids of GeneticParts.
                    Plasmids inside of Strains should be sent with the key
                        "plasmid_ids", a list of global_ids of Plasmids.

    Returns:
        json:
            success <bool>: True if the update was successful, False
                otherwise
            msg <str>: A message describing the success or failure
                of the update
    """
    try:
        obj_class, schema = {'part': (GeneticPart, GeneticPartSchema),
                  'strain': (Strain, StrainSchema),
                  'plasmid': (Plasmid, PlasmidSchema)
                  }[object]
    except KeyError:
        return 404
    update_info = request.get_json()
    ids_to_update, update_data = extract_update_info(update_info)
    #We don't use the returned objects, but we do need to make sure the data is valid
    objects = validate_and_extract_objects(schema, update_data, update=True)
    success = update_objects_in_db(obj_class, ids_to_update, update_data)

    return jsonify({'success': success, 'msg': f'Successfully updated {object}'}), 201


@biofoundry_blueprint.route('/submit_construct', methods=('POST', ))
@jwt_required()
@access_level_required(SuperUserRole.admin)
def receive_construct():
    """
    Endpoint for building a plasmid from inserts.
    Here, "plasmids" and "constructs" are the same thing.

    Parameters:
        json:
            email <str>: The email address of the user submitting
            name <str>: The name of the construct the user gave it
            description <str>: The description of the construct
            inserts <list>: A list of genetic_part global_ids <str>

    Returns:
        json:
            success <bool>: True if the upload was successful, False
            msg <str>: A message describing the success or failure
            data <JSON>: name and id of the newly created plasmid
    """
    plasmid_data, email = validate_and_extract_construct(ConstructSubmissionSchema, request.get_json())
    id, name = build_plasmid_from_parts(plasmid_data, email)

    msg = f'Successfully created plasmid {id}, named {name}. Ready for build process'

    return jsonify({'status':'success', 'msg': msg, 'data': {'plasmid_id':id,'name':name}}), 201


@biofoundry_blueprint.route('/get_assembly_protocol', methods=('POST', ))
@jwt_required()
@access_level_required(SuperUserRole.admin)
def build_protocol():
    """
    Endpoint to build an assembly protocol for a plasmid.
    Marks plasmid as "Processing" if it is currently "Submitted"

    Not implemented.
    """
    return build_protocol_from_plasmid() 


@biofoundry_blueprint.route('/transform_from_plasmid', methods=('POST', ))
@jwt_required()
@access_level_required(SuperUserRole.admin)
def transform_from_plasmid():
    """
    Creates a new strain from a given plasmid and associates the two, then
    marks both as "Processed". Intended to be used a convenience method for
    when a plasmid was constructued and then immediately transformed for
    amplification in the lab.

    Parameters:
        json:
            background_strain <str>: The background strain the plasmid was transformed into
            plasmid_ids <str>: ID of the plasmid that was transformed into the strain
            global_id <str> (optional): ID to use for the new strain.
                If not provided, will create one based on the plasmid ID
            name <str> (optional): Name of the strain.
                If not provided, will create one based on the plasmid name
            friendly_name <str> (optional): Human-friendly name for the strain.
                If not provided, will create one based on the plasmid name
            description <str> (optional): Description for the strain.
                If not provided, will create one based on the plasmid description
            
    Returns:
        json:
            success <bool>: True if the upload was successful, False
            msg <str>: A message describing the success or failure
            data <JSON>: name and id of the newly created strain

    """

    transformation_info = request.get_json()

    StrainSchema(only=['background_strain','plasmid_ids']).validate(transformation_info)
    strains_info, plasmid = infer_transformation_data(transformation_info)

    strains = validate_and_extract_objects(StrainSchema, strains_info)
    
    plasmid_success = update_objects_in_db(Plasmid,
                                           [plasmid.global_id],
                                           [{'status':SubmissionStatus.processed}]
                                          )
    strain_success = save_objects_in_db(strains)
    success = plasmid_success and strain_success

    return jsonify({'success': success, 'msg': f'Successfully added strain and updated plasmid'}), 201