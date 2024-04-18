import os
from flask import (Blueprint, request, current_app, jsonify, send_file, render_template_string)
from flask_jwt_extended import jwt_required, get_current_user
from .core import (validate_and_extract_artpiece_data, create_artpiece,
        has_reached_monthly_submission_limit, guarantee_monthly_submission_limit_not_reached,
        validate_and_extract_status_update, validate_and_extract_color_data)
from .core import confirm_artpiece as core_confirm_artpiece
from ..email import send_confirmation_email_async
from ..exceptions import InvalidUsage
from ..colors import (get_available_color_mapping, get_available_colors,
                      get_available_colors_as_dicts, get_color_id_by_name, set_color_strain,
                      delete_colors, BacterialColor)
from ..utilities import access_level_required
from .artpiece import Artpiece
from .serializers import ArtpieceSchema, PrintableSchema, StatusSchema, ColorSchema
from ...biofoundry.core import (extract_update_info, update_objects_in_db) #should probably move this generic function to a parent module
from web.extensions import db
from web.database.models import SuperUserRole
from web.robot.art_processor import make_procedure

import base64

from web.database.models import ArtpieceModel


artpiece_blueprint = Blueprint('artpiece', __name__)

@artpiece_blueprint.route('/artpieces', methods=('GET', ))
def get_artpieces_meta():
    monthly_limit = current_app.config['MONTLY_SUBMISSION_LIMIT']
    location = location = request.args.get('location', None)
    return jsonify(
            {
                'meta':
                {
                    'submission_limit_exceeded': has_reached_monthly_submission_limit(
                        monthly_limit)
                    , 'bacterial_colors': get_available_colors_as_dicts(location)
                }
                , 'data': None
            }), 200


@artpiece_blueprint.route('/artpieces', methods=('POST', ))
def receive_art():
    monthly_limit = current_app.config['MONTLY_SUBMISSION_LIMIT']
    guarantee_monthly_submission_limit_not_reached(monthly_limit)

    email, title, art, canvas_size = validate_and_extract_artpiece_data(request.get_json()
            , get_available_color_mapping().keys())

    artpiece = create_artpiece(email, title, art, canvas_size)
    db.session.commit()

    send_confirmation_email_async(artpiece)

    return jsonify({'data': None}), 201


@artpiece_blueprint.route('/artpieces/<int:id>/confirmation/<token>', methods=('PUT', ))
def confirm_artpiece(id, token):
    artpiece = Artpiece.get_by_id(id)
    confirmation_status = core_confirm_artpiece(artpiece, token)
    if confirmation_status == 'confirmed':
        db.session.commit()

    return jsonify({'data': {'confirmation': {'status': confirmation_status}}}), 200


@artpiece_blueprint.route('/artpieces/<int:artpiece_id>/update_status', methods=('POST', ))
@jwt_required()
@access_level_required(SuperUserRole.printer)
def update_artpiece_status(artpiece_id):
    """
    Updates the status of the artpiece to the requested value.
    Values must be 'Submitted', 'Processsing', or 'Processed'

    Parameters:
        artpiece_id <int>: The id of the artpiece to update, in the url
        status <str>: The new status of the artpiece as as json, in the request body

    Return: An empty json response
    """
    new_status, artpiece = validate_and_extract_status_update(request.get_json(), artpiece_id)
    new_object = artpiece.update_status(new_status)
    serialized_artpiece = StatusSchema().dump(new_object)

    return jsonify({'success': True, 'update_artpiece': serialized_artpiece}), 200


@artpiece_blueprint.route('/artpieces/<int:artpiece_id>/delete', methods=('PUT', ))
@jwt_required()
@access_level_required(SuperUserRole.admin)
def delete_artpiece(artpiece_id):
    """
    Deletes the requested artpiece

    Parameters:
        artpiece_id <int>: The id of the artpiece to delete, in the url

    Return: An empty json response
    """
    artpiece = Artpiece.get_by_id(artpiece_id)
    if not artpiece: raise InvalidUsage.resource_not_found()
    success = artpiece.delete()

    return jsonify({'success': success}), 200


@artpiece_blueprint.route('/print_jobs', methods=('GET', ))
@jwt_required()
@access_level_required(SuperUserRole.printer)
def get_print_jobs():
    """
    Gets all artpieces. By default will return only artpieces that have been
    confirmed. This behavior can be changed by passing a query parameter.

    Parameters:
        unprinted_only (bool): If true, will only return artpieces that have not been printed.
        confirmed_only (bool): If true, will only return artpieces that have been confirmed.

    Return: JSON object containing all artpiece information.
    """
    args = request.args
    unprinted_only = args.get('unprinted_only', 'False').lower() == 'true'
    confirmed_only = args.get('confirmed_only', 'True').lower() == 'true'
    location = args.get('location', None)

    print_jobs = Artpiece.get_printable(unprinted_only=unprinted_only, confirmed_only=confirmed_only, location=location)
    schema = PrintableSchema(many=True)
    serialized = schema.dumps(print_jobs)

    return jsonify({'data': serialized})


@artpiece_blueprint.route('/procedures/<string:id>', methods=('GET', ))
@jwt_required()
@access_level_required(SuperUserRole.printer)
def get_procedure_file(id):
    
    procedure_file = f'{os.getcwd()}/web/robot/procedures/ARTISTIC_PROCEDURE_{id}'

    return send_file(procedure_file, mimetype='text/plain', as_attachment=True)


@artpiece_blueprint.route('/procedure_request', methods=('POST', ))
@jwt_required()
@access_level_required(SuperUserRole.printer)
def receive_print_request():

    artpiece_ids = request.get_json()['ids']
    labware = request.get_json()['labware']
    pipette = request.get_json()['pipette']

    option_args = {'notebook':False
                    ,'palette': 'cryo_35_tuberack_2000ul'
                    ,'pipette': pipette
                    ,'canvas': labware['canvas']
                    }
    
    try:
        option_args['location'] = request.get_json()['location']
    except KeyError:
        pass

    if option_args['pipette'][-5:] == 'multi' and len(artpiece_ids) > 1:
        raise InvalidUsage.invalid_pipette()
    
    requestor = get_current_user()
    msg, procedure_loc = make_procedure(artpiece_ids, requestor=requestor, option_args=option_args)

    if procedure_loc:
        unique_id = procedure_loc[1].split('_')[-1]
        procedure_uri = f'/procedures/{unique_id}'
    else:
        procedure_uri = None
        raise InvalidUsage.resource_not_found()
    
    return jsonify({'msg':msg, 'procedure_uri':procedure_uri}), 201


@artpiece_blueprint.route('/colors/get_all', methods=('GET', ))
@jwt_required()
@access_level_required(SuperUserRole.printer)
def get_all_colors():
    """
    Gets all available colors, including the RGBA values and
    associated strains. If a location is provided, will only
    return colors available at that location.

    Return: JSON object containing all available colors.
    """
    args = request.args
    location = args.get('location', None)

    colors = get_available_colors(location)
    schema = ColorSchema(many=True)
    serialized = schema.dumps(colors)

    return jsonify({'data': serialized})

@artpiece_blueprint.route('/colors/create', methods=('POST', ))
@jwt_required()
@access_level_required(SuperUserRole.printer)
def create_color():
    """
    Create and save a new color object in the database. Link the color
    to the strain that makes that color. Colors must be supplied in a
    JSON list of dictionaries, even if there is only one color.

    Parameters <list>:
        name <str>: The name of the color
        strain_global_id <str>: The global_id of the strain that makes the color
        red <int>: The red value of the color (0,255)
        green <int>: The green value of the color (0,255)
        blue <int>: The blue value of the color (0,255)
        opacity <float>: The opacity value of the color (0,1)
        in_use <bool>: Whether or not the color is in use and should be displayed on the website

    Return: Success boolean as JSON
    """
    json_object = request.get_json()
    color_data_list = validate_and_extract_color_data(json_object)
    colors = [set_color_strain(**color_data) for color_data in color_data_list]
    #TODO Handle duplicate data errors

    return jsonify({'success': True, 'colors_added':ColorSchema(many=True).dumps(colors)}), 201

@artpiece_blueprint.route('/colors/update', methods=('POST', ))
@jwt_required()
@access_level_required(SuperUserRole.printer)
def update_color():
    """
    Update an existing color object in the database.

    Colors are updated by their name, which functions as a global_id.
    Beyond this, only the fields that need to be updated need to be
    supplied.

    Parameters:
        json:
            to_update <list>: A list of objects, following the schema:
                global_id <str>: The name of the color to update
                update_data <JSON>: The new data to update the color with.
                    Should follow the schema documented in the object type's
                    'create' endpoint. Only data to update needs to be supplied.

    Returns:
        json:
            success <bool>: True if the update was successful, False
                otherwise
            msg <str>: A message describing the success or failure
                of the update
    """
    update_info = request.get_json()['to_update']
    names_to_update, update_data = extract_update_info(update_info)
    #We don't use the returned objects, but we do need to make sure the data is valid
    colors = validate_and_extract_color_data(update_data, update=True)
    ids_to_update = [get_color_id_by_name(name) for name in names_to_update]
    success = update_objects_in_db(BacterialColor, ids_to_update, update_data)
    #BUG: Strains don't update when strain_global_id is submitted

    return jsonify({'success': success, 'msg': f'Successfully updated color'}), 201

@artpiece_blueprint.route('/colors/delete', methods=('PUT', ))
@jwt_required()
@access_level_required(SuperUserRole.printer)
def delete_color():
    """
    Delete color from the database. WARNING: Deleting a color will also delete
    it's associated strain.
    
    Because unique names are required for colors,
    colors are referenced by their names only. Colors must be supplied in a JSON
    list of strings, even if there is only one color.

    Parameters <list>:
        name <str>: The name of the color to delete

    Return: Success boolean as JSON
    """
    json_object = request.get_json()
    success = delete_colors(json_object)

    return jsonify({'success': success}), 201