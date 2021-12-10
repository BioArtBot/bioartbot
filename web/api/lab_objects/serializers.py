from marshmallow import (fields, Schema, post_load, EXCLUDE)
from numbers import Number


class LabObjectPropertySchema(Schema):
    name = fields.Str(required=True)
    value = fields.Field(required=True)
    units = fields.Str(required=False)

    def __init__(self, many=False, **kwargs):
        only = kwargs['only'] if 'only' in kwargs else None
        Schema.__init__(self, many=many, only=only)

    class meta:
        strict=True

class LabObjectSchema(Schema):
    name = fields.Str(required=True)
    obj_class = fields.Str(required=True)
    serial_props = fields.List(fields.Nested(LabObjectPropertySchema))

    def __init__(self, many=False):
        Schema.__init__(self, many=many)

    class meta:
        strict=True