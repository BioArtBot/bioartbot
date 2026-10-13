#required to use get_current_user()
def user_lookup_callback(_jwt_header, jwt_data):
    # the "sub" claim is a string (PyJWT >= 2.10 enforces this), so cast back to int
    user_id = int(jwt_data['sub'])
    from web.api.user.user import SuperUser
    return SuperUser.get_by_id(user_id)