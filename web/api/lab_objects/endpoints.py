from flask import (Blueprint, jsonify)
from flask_jwt_extended import jwt_required
from .lab_objects import LabObject
from .serializers import LabObjectSchema
from ..user.utilities import access_level_required #TODO bad dependency
from web.database.models import SuperUserRole


lab_object_blueprint = Blueprint('lab_object', __name__)

@lab_object_blueprint.route('/available_labware', methods=('GET', ))
@jwt_required()
@access_level_required(SuperUserRole.printer)
def get_available_labware():
    available_labware = LabObject.stored_object_types(obj_class='labware')
    schema = LabObjectSchema(many=True)
    serialized = schema.dumps(available_labware)

    return jsonify({'data': serialized})