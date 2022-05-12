from datetime import datetime
from flask_jwt_extended import jwt_required
from flask import (Blueprint, request, current_app, jsonify, send_file)
from flask_jwt_extended import (
        create_access_token, create_refresh_token
        , set_access_cookies, set_refresh_cookies
    )
from .core import (create_superuser, delete_superuser, validate_and_extract_user_data,
                   update_superuser_role, update_superuser_password, read_superusers
                  )
from .exceptions import InvalidUsage, error_template
from .user import SuperUser
from .utilities import access_level_required
from web.extensions.jwt_config import user_lookup_callback
from web.database.models import SuperUserRole

import base64


user_blueprint = Blueprint('user', __name__, url_prefix='/user')

@user_blueprint.route('/login', methods=('POST', ))
def login():
    username = request.json.get("username", None)
    password = request.json.get("password", None)

    user = SuperUser.get_by_email(username)
    
    if user is None or user.password_hash is None or not user.is_password_valid(password):
        raise InvalidUsage.bad_login()

    if user.password_needs_rehash():
        user.set_password(password)

    # Create the tokens we will be sending back to the user
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    # Set the JWTs and the CSRF double submit protection cookies
    # in this response
    resp = jsonify({'login': True, 'user':user.email, 'role':user.role.value})
    set_access_cookies(resp, access_token)
    set_refresh_cookies(resp, refresh_token)

    return resp, 200


@user_blueprint.route('/get', methods=('GET', ))
@jwt_required()
@access_level_required(SuperUserRole.admin)
def get_all():
    """
    Reads all superusers from the database.

    Parameters:
        none

    Returns:
        json:
            users <JSON>: A list of all superusers, with the following schema
                {user_id: <int>, email: <str>, role: <int>, created_at: <timestamp>}
            count <int>: The number of users returned from the database.
    """
    users = read_superusers()
    resp = jsonify({'users': users, 'count': len(users)})
    return resp, 200


@user_blueprint.route('/remove/<id>/<created_at_timestamp>', methods=('PUT', ))
@jwt_required()
@access_level_required(SuperUserRole.admin)
def remove(id, created_at_timestamp):
    """
    Removes the superuser with the given id. Request must also send the superuser's 
    created_at_timestamp, as a check to prevent accidental deletion.
    Parameters are part of the URL, not a JSON object.

    Parameters:
        id (int): The id of the superuser to be removed.
        created_at_timestamp (timestamp): The created_at_timestamp of the superuser to be removed.

    Returns:
        json: A json object confirming the superuser's email, and a success boolean.
    """
    email, success = delete_superuser(id, created_at_timestamp)
    resp = jsonify({'user': email, 'deleted': success})
    return resp, 200


@user_blueprint.route('/create', methods=('POST', ))
@jwt_required()
@access_level_required(SuperUserRole.admin)
def create():
    """
    Creates a new superuser from data provided in a JSON object.

    Parameters:
        json:
            email (str): The email of the superuser to be created.
            password (str): The password of the superuser to be created.
            role (str): The role of the superuser to be created (admin or printer).

    Returns:
        json: A json object giving the superuser's assigned id, and a success boolean.
    """
    data = validate_and_extract_user_data(request.json, new_user=True)
    email, password, role = data['email'], data['password'], data['role']

    id, success = create_superuser(email, password, role)

    resp = jsonify({'user_id': id, 'created': success})
    return resp, 200


@user_blueprint.route('/change_role', methods=('POST', ))
@jwt_required()
@access_level_required(SuperUserRole.admin)
def update_role():
    """
    Updates a superuser's role from data provided in a JSON object.

    Parameters:
        json:
            email (str): The email of the superuser to be updated.
            role (str): The new role of the superuser (admin or printer).

    Returns:
        json: A json object confirming the superuser's email,
              the old and new roles, and a success boolean.
    """
    data = validate_and_extract_user_data(request.json, skipped_fields=('password',))
    email, requested_role = data['email'], data['role']

    email, old_role, new_role = update_superuser_role(email, requested_role)
    resp = jsonify({'user': email, 'old_role': old_role, 'new_role': new_role})
    return resp, 200

@user_blueprint.route('/reset_password/', methods=('POST', ))
@jwt_required()
@access_level_required(SuperUserRole.admin)
def reset_password():
    """
    Updates a superuser's password from data provided in a JSON object.
    Must send the current password in addition to the requested new password.
    This endpoint is intended to be reached by a password reset screen accessed by
    the superuser themselves.

    Parameters:
        json:
            email (str): The email of the superuser to be updated.
            old_password (str): The current password of the superuser.
            new_password (str): The new password of the superuser.

    Returns:
        json: A json object confirming the superuser's email, and a success boolean.
    """
    """
    data = validate_and_extract_user_data(request.json, skipped_fields=('role',))
    email, old_password, requested_password = data['email'], data['old_password'], data['password']

    email, success = update_superuser_password(email, old_password, requested_password)
    resp = jsonify({'user': email, 'success': success})
    return resp, 200
    """
    #TODO implement this as a full password reset flow
    raise InvalidUsage.not_implemented()