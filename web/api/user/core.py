from functools import partial
from marshmallow import ValidationError
from web.extensions import db
from .validators import validate_user_token
from .serializers import SuperUserSchema
from .exceptions import InvalidUsage, InvalidPasswordException
from .user import SuperUser, SuperUserRole


def validate_and_extract_user_data(json_data, requesting_user, skipped_fields: tuple= (), new_user: bool=False):
    if requesting_user.role == SuperUserRole.admin:
            skipped_fields += ('password',)
    try:
        data = SuperUserSchema(new_user).load(json_data, partial=skipped_fields)
    except ValidationError as err:
        raise InvalidUsage.from_validation_error(err)
    return data

def read_superusers():
    """
    Read all superusers from the database and return the email, created_at, and role
    """
    superusers = SuperUser.get_all()
    return [{'id': s_user.id,
             'email': s_user.email,
             'created_at': s_user.created_at,
             'role': s_user.role.value}
            for s_user in superusers]

def create_superuser(email, password, role = SuperUser.default_role()):
    s_user = SuperUser.from_email(email, role=role)
    s_user.set_password(password)

    db.session.commit()
    return s_user.id, True

def update_superuser_role(email, new_role, requesting_user):
    s_user = SuperUser.get_by_email(email)
    if s_user.email == requesting_user.email:
        raise InvalidUsage.cannot_change_own_role()
    old_role = s_user.role
    s_user.set_role(new_role)

    db.session.commit()
    return s_user.email, old_role.value, s_user.role.value

def update_superuser_password(email, old_password, new_password, requesting_user):
    s_user = SuperUser.get_by_email(email)
    if not s_user.is_password_valid(old_password) and requesting_user.role != SuperUserRole.admin:
        raise InvalidUsage.bad_login()
    if len(new_password) < 8:
        raise InvalidPasswordException
    s_user.set_password(new_password)

    db.session.commit()
    return s_user.email, True

def delete_superuser(id, created_at_timestamp):
    """
    Delete a user record from the SuperUser table
    For added security, must provide exact creation datetime
    of the user, in timestamp format
    """
    s_user = SuperUser.get_by_id(id)
    validate_user_token(s_user, created_at_timestamp)
    s_user.delete()

    db.session.commit()
    return s_user.email, True