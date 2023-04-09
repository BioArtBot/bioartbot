from marshmallow import (fields, Schema, post_load, EXCLUDE)


class LocationSchema(Schema):
    name = fields.Str(required=True)
    description = fields.Str(required=False)

    def __init__(self, many=False, **kwargs):
        only = kwargs['only'] if 'only' in kwargs else None
        Schema.__init__(self, many=many, only=only)

    class meta:
        strict=True