from sys import int_info
from marshmallow import (fields, Schema, pre_load, pre_dump, post_load, validates, validates_schema, validate)
from marshmallow.validate import (Length, Regexp, Range)
from .validators import (validate_art_content_length, validate_color_keys, validate_pixels,
        validate_title, validate_canvas_size)
from .exceptions import InvalidUsage
from ...biofoundry.strain import Strain
from ...file_manager import file_manager

_fm = file_manager()

class ArtpieceSchema(Schema):
    title = fields.Str(missing=None)
    email = fields.Email(required=True, load_only=True)
    art = fields.Dict(
            missing=None
            , keys=fields.Str()
            , values=fields.List(fields.Tuple((fields.Int(), fields.Int())))
            )
    canvas_size = fields.Dict(missing=None, keys=fields.Str(), values=fields.Int())

    def __init__(self, valid_color_keys, many=False):
        Schema.__init__(self, many=many)
        self._valid_color_keys = valid_color_keys

    @validates('title')
    def _validate_title_field(self, title):
        validate_title(title)

    @validates('art')
    def _validate_art_field(self, art):
        validate_art_content_length(art)
        validate_color_keys(art, self._valid_color_keys)

    @validates('canvas_size')
    def _validate_canvas_size(self, canvas_size):
        validate_canvas_size(canvas_size)

    @validates_schema()
    def _validate_canvas_size_and_art_combo(self, data, **kwargs):
        validate_pixels(data['art'], data['canvas_size'])

    @pre_load
    def strip_title(self, in_data, **kwargs):
        title = in_data['title'] if in_data else None
        if title is not None:
            in_data['title'] = title.strip()
        return in_data

    class meta:
        strict=True

class PrintableSchema(Schema):
    id = fields.Int()
    title = fields.Str(missing=None)
    user_id = fields.Int()
    submit_date = fields.DateTime()
    status = fields.Str()
    art = fields.Dict(
            missing=None
            , keys=fields.Str()
            , values=fields.List(fields.Tuple((fields.Int(), fields.Int())))
            )
    img_uri = fields.Function(lambda obj: _fm.get_file_url(f'{obj.slug}_{int(obj.submit_date.timestamp()*1000)}.jpg'))

    class Meta:
        ordered = True


class ColorSchema(Schema):
    @pre_dump
    def strain_to_global_id(self, obj, **kwargs):
        if hasattr(obj, 'strain'):
            obj.strain_global_id = obj.strain.global_id
        return obj

    name = fields.Str(required=True)
    red = fields.Int(required=True, validate=Range(min=0, max=255))
    blue = fields.Int(required=True, validate=Range(min=0, max=255))
    green = fields.Int(required=True, validate=Range(min=0, max=255))
    opacity = fields.Float(validate=Range(min=0, max=1.0))
    strain_global_id = fields.Str(required=True)
    in_use = fields.Bool()

    def __init__(self, many=False, **kwargs):
        only = kwargs['only'] if 'only' in kwargs else None
        Schema.__init__(self, many=many, only=only)

    class meta:
        strict=True

    @post_load
    def global_id_to_strain(self, in_data, **kwargs):
        try:
            if 'strain_global_id' in in_data:
                in_data['strain'] = Strain.get_by_id(in_data['strain_global_id'])
                assert in_data['strain'] is not None
                in_data.pop('strain_global_id')        
            return in_data
        except AssertionError:
            raise InvalidUsage.bad_reference(f'Strain {in_data["strain_global_id"]}')


class StatusSchema(Schema):
    status = fields.Str(validate=validate.OneOf(["submitted", "processing", "processed"]))

    class meta:
        strict=True