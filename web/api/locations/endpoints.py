from flask import (Blueprint, jsonify, request)
from flask_jwt_extended import jwt_required
from .location import Location
from .serializers import LocationSchema
from ..user.utilities import access_level_required #TODO bad dependency
from web.database.models import SuperUserRole


location_blueprint = Blueprint('location', __name__)

@location_blueprint.route('/locations', methods=('GET', ))
@jwt_required()
@access_level_required(SuperUserRole.printer)
def get_locations():
    locations = Location.get_all()
    schema = LocationSchema(many=True)
    serialized = schema.dumps(locations)

    return jsonify({'data': serialized})


@location_blueprint.route('/locations/add', methods=('POST', ))
@jwt_required()
@access_level_required(SuperUserRole.admin)
def add_location():
    json_object = request.get_json()
    schema = LocationSchema()
    location_data = schema.load(json_object)
    location = Location.create(location_data['name'], location_data['description'])

    return jsonify({'success': True, 'msg': f'Successfully added location {location.name}'}), 201


@location_blueprint.route('/locations/update', methods=('POST', ))
@jwt_required()
@access_level_required(SuperUserRole.admin)
def update_location():
    json_object = request.get_json()
    schema = LocationSchema()
    location_data = schema.load(json_object)
    location = Location.get_by_name(location_data['name'])
    location.update(description=location_data.description)

    return jsonify({'success': True, 'msg': f'Updated description for {location.name}'}), 201

@location_blueprint.route('/locations/delete', methods=('PUT', ))
@jwt_required()
@access_level_required(SuperUserRole.admin)
def delete_location():
    json_object = request.get_json()
    schema = LocationSchema()
    location_data = schema.load(json_object)
    location = Location.get_by_name(location_data['name'])
    location.delete()

    return jsonify({'success': True, 'msg': f'Deleted {location.name}'}), 201