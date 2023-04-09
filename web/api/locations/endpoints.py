from flask import (Blueprint, jsonify)
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