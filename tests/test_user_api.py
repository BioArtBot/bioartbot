import pytest
import json
import math
from flask import current_app
from web.api.user import exceptions as user_exceptions, core as user_core
from web.api.user.user import User, SuperUser
from web.api.user.artpiece import (core, exceptions as art_exceptions)
from web.api.user.exceptions import InvalidUsage
from web.database.models import ArtpieceModel, SuperUserRole

from .conftest import (VALID_EMAIL, VALID_TITLE, VALID_ART, VALID_PASSWORD,
                       INITIAL_ROLE, INITIAL_SUPERUSER_ROLE,
                       INITIAL_PASSWORD_HASH, VALID_CANVAS_SIZE,
                       INITIAL_ADMIN_EMAIL
                      )


def create_artpiece_data(email=VALID_EMAIL, title=VALID_TITLE, art=VALID_ART, canvas_size=VALID_CANVAS_SIZE):
    return {'email': email, 'title': title, 'art': art, 'canvas_size': canvas_size}

def create_artpiece(email=VALID_EMAIL, title=VALID_TITLE, art=VALID_ART, canvas_size=VALID_CANVAS_SIZE):
    return User.from_email(email).create_artpiece(title, art, canvas_size)

@pytest.mark.usefixtures("setup_app")
def test_create_artpiece_by_new_user():
    artpiece = core.create_artpiece(VALID_EMAIL, VALID_TITLE, VALID_ART, VALID_CANVAS_SIZE)
    assert artpiece.title == VALID_TITLE
    assert artpiece.creator.email == VALID_EMAIL
    assert artpiece.creator.role.value == INITIAL_ROLE
    assert artpiece.creator.password_hash is INITIAL_PASSWORD_HASH

@pytest.mark.usefixtures("setup_app")
@pytest.mark.parametrize('password', ['testpass', 'test password', 'rH79ffS3iNbY', 'I2E#$D1l0Sr#'])
def test_add_user_password(password):
    artpiece = core.create_artpiece(VALID_EMAIL, VALID_TITLE, VALID_ART, VALID_CANVAS_SIZE)
    user = User.get_by_email(VALID_EMAIL)
    user.set_password(password)
    assert user.is_password_valid(password)

@pytest.mark.usefixtures("setup_app")
@pytest.mark.parametrize('password', ['short', ''])
def test_user_password_length_requirement(password):
    s_user = SuperUser.from_email(VALID_EMAIL)
    s_user.set_password('')
    requesting_user = SuperUser.get_by_email(INITIAL_ADMIN_EMAIL)
    with pytest.raises(user_exceptions.InvalidPasswordException):
        user_core.update_superuser_password(VALID_EMAIL, '', password, requesting_user)

@pytest.mark.usefixtures("setup_app")
def test_monthly_submission_limit_exceeded():
    limit = 0
    with pytest.raises(art_exceptions.MonthlySubmissionLimitException):
        core.guarantee_monthly_submission_limit_not_reached(limit)
    create_artpiece()
    with pytest.raises(art_exceptions.MonthlySubmissionLimitException):
        core.guarantee_monthly_submission_limit_not_reached(limit)

@pytest.mark.usefixtures("setup_app")
def test_create_artpieces_with_same_email():
    with pytest.raises(art_exceptions.UserSubmissionLimitException):
        core.create_artpiece(VALID_EMAIL, VALID_TITLE, VALID_ART, VALID_CANVAS_SIZE)
        core.create_artpiece(VALID_EMAIL, VALID_TITLE, VALID_ART, VALID_CANVAS_SIZE)

@pytest.mark.usefixtures("setup_app")
@pytest.mark.parametrize('invalid_email', ['malformed@malformation', '@deadbeef', 'evil.universe'])
def test_create_artpiece_malformed_email(invalid_email):
    in_data = create_artpiece_data(email=invalid_email)
    with pytest.raises(InvalidUsage):
        core.validate_and_extract_artpiece_data(in_data, VALID_ART.keys())

@pytest.mark.usefixtures("setup_app")
@pytest.mark.parametrize('invalid_title', '`,~,!,@,#,$,%,^,&,*,/,\\,, ,  '.split(','))
def test_create_artpiece_non_alphanumeric_title(invalid_title):
    in_data = create_artpiece_data(title=invalid_title)
    with pytest.raises(art_exceptions.InvalidTitleException):
        core.validate_and_extract_artpiece_data(in_data, VALID_ART.keys())

@pytest.mark.usefixtures("setup_app")
@pytest.mark.parametrize('invalid_art', [{'art':{'1': [[100, 0]]},'size':{'x':26,'y':26}},
                                         {'art':{'2': [[5, 101]]},'size':{'x':26,'y':99}}
                                        ])
def test_create_artpiece_pixel_outofbounds(invalid_art):
    in_data = create_artpiece_data(art=invalid_art['art'], canvas_size=invalid_art['size'])
    with pytest.raises(art_exceptions.PixelOutOfBoundsException):
        core.validate_and_extract_artpiece_data(in_data, invalid_art['art'].keys())

@pytest.mark.usefixtures("setup_app")
def test_create_artpiece_unavailable_color():
    art_with_invalid_color = {'10': [[5, 5]]}
    in_data = create_artpiece_data(art=art_with_invalid_color)
    with pytest.raises(art_exceptions.ColorSchemeException):
        core.validate_and_extract_artpiece_data(in_data, VALID_ART.keys())

@pytest.mark.usefixtures("setup_app")
@pytest.mark.parametrize('invalid_art', [{}, {'1': []}])
def test_create_artpiece_with_empty_canvas(invalid_art):
    in_data = create_artpiece_data(art=invalid_art)
    with pytest.raises(art_exceptions.BlankCanvasException):
        core.validate_and_extract_artpiece_data(in_data, VALID_ART.keys())

@pytest.mark.usefixtures("setup_app")
@pytest.mark.parametrize('invalid_canvas', [{'x':26}, {'x':1000,'y':25}])
def test_create_artpiece_with_invalid_canvas(invalid_canvas):
    in_data = create_artpiece_data(canvas_size=invalid_canvas)
    with pytest.raises(art_exceptions.InvalidCanvasException):
        core.validate_and_extract_artpiece_data(in_data, VALID_ART.keys())

@pytest.mark.usefixtures("setup_app")
def test_confirm_artpiece():
    artpiece = create_artpiece()
    token = artpiece.get_confirmation_token()
    status = core.confirm_artpiece(artpiece, token)
    assert status == 'confirmed'

@pytest.mark.usefixtures("setup_app")
def test_confirmed_artpiece():
    artpiece = create_artpiece()
    artpiece.confirm()
    token = artpiece.get_confirmation_token()
    status = core.confirm_artpiece(artpiece, token)
    assert status == 'already_confirmed'

@pytest.mark.usefixtures("setup_app")
def test_expired_token_confirm_artpiece():
    artpiece = create_artpiece()
    token = artpiece.get_confirmation_token(expires_in=-1)

    with pytest.raises(art_exceptions.ExpiredConfirmationTokenException):
        core.confirm_artpiece(artpiece, token)

@pytest.mark.usefixtures("setup_app")
def test_token_id_mismatch_confirm_artpiece():
    artpiece_1 = create_artpiece()
    artpiece_2 = create_artpiece(email='other@mail.com')
    token_1 = artpiece_1.get_confirmation_token()

    with pytest.raises(art_exceptions.InvalidConfirmationTokenException):
        core.confirm_artpiece(artpiece_2, token_1)

@pytest.mark.usefixtures("setup_app")
def test_invalid_token_confirm_artpiece():
    artpiece = create_artpiece()
    with pytest.raises(art_exceptions.InvalidConfirmationTokenException):
        core.confirm_artpiece(artpiece, 'random_invalid_token')

@pytest.mark.usefixtures("setup_app")
def test_create_new_superuser():
    id, success = user_core.create_superuser(VALID_EMAIL, VALID_PASSWORD, INITIAL_SUPERUSER_ROLE)
    assert SuperUser.get_by_email(VALID_EMAIL) is not None

@pytest.mark.usefixtures("setup_app")
def test_update_superuser_role():
    id, success = user_core.create_superuser(VALID_EMAIL, VALID_PASSWORD, INITIAL_SUPERUSER_ROLE)
    requesting_user = SuperUser.get_by_email(INITIAL_ADMIN_EMAIL)
    user_core.update_superuser_role(VALID_EMAIL, 'Admin', requesting_user)
    assert SuperUser.get_by_id(id).role == SuperUserRole.admin

@pytest.mark.usefixtures("setup_app")
def test_update_superuser_password():
    id, success = user_core.create_superuser(VALID_EMAIL, VALID_PASSWORD, INITIAL_SUPERUSER_ROLE)
    s_user = SuperUser.get_by_id(id)
    requesting_user = SuperUser.get_by_email(INITIAL_ADMIN_EMAIL)
    user_core.update_superuser_password(VALID_EMAIL, VALID_PASSWORD, 'ThisIsANewValidPassword', requesting_user)
    SuperUser.get_by_id(id).is_password_valid('ThisIsANewValidPassword')

@pytest.mark.usefixtures("setup_app")
def test_delete_superuser():
    id, success = user_core.create_superuser(VALID_EMAIL, VALID_PASSWORD, INITIAL_SUPERUSER_ROLE)
    s_user = SuperUser.get_by_id(id)
    #API will receive timestamp in UTC String format, which is rounded down, so we recreate that here
    created_at_timestamp = math.floor(s_user.created_at.timestamp())
    user_core.delete_superuser(id, created_at_timestamp)
    assert SuperUser.get_by_email(VALID_EMAIL) is None

