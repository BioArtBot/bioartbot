from marshmallow import (fields, Schema, post_load, EXCLUDE)
from .genetic_part import GeneticPart
from .plasmid import Plasmid
from .strain import Strain

class GeneticPartSchema(Schema):
    global_id = fields.Str(required=True)
    name = fields.Str(required=True)
    friendly_name = fields.Str(required=False)
    description = fields.Str(required=True)
    sequence = fields.Str(required=True)
    part_type = fields.Str(required=True)
    cloning_prefix = fields.Str(required=True)
    cloning_suffix = fields.Str(required=True)

    def __init__(self, many=False, **kwargs):
        only = kwargs['only'] if 'only' in kwargs else None
        Schema.__init__(self, many=many, only=only)

    class meta:
        strict=True

    @post_load
    def make_part(self, data, **kwargs):
        return GeneticPart.create(**data)

class PlasmidSchema(Schema):
    global_id = fields.Str(required=True)
    name = fields.Str(required=True)
    friendly_name = fields.Str(required=True)
    description = fields.Str(required=True)
    sequence = fields.Str(required=True)
    sequence_of_interest = fields.Str(required=True)
    antibiotic_resistance = fields.Str(required=True) #TODO: Make enum?
    source = fields.Str(required=False)
    inserts = fields.List(fields.Nested(GeneticPartSchema))

    def __init__(self, many=False, **kwargs):
        only = kwargs['only'] if 'only' in kwargs else None
        Schema.__init__(self, many=many, only=only)

    class meta:
        strict=True

    @post_load
    def make_plasmid(self, data, **kwargs):
        return Plasmid.create(**data)

class StrainSchema(Schema):
    global_id = fields.Str(required=True)
    name = fields.Str(required=True)
    friendly_name = fields.Str(required=True)
    description = fields.Str(required=True)
    background_strain = fields.Str(required=True)
    plasmids = fields.List(fields.Nested(PlasmidSchema))

    def __init__(self, many=False, **kwargs):
        only = kwargs['only'] if 'only' in kwargs else None
        Schema.__init__(self, many=many, only=only)

    class meta:
        strict=True

    @post_load
    def make_strain(self, data, **kwargs):
        return Strain.create(**data)