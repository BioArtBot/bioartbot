from xml.sax.handler import property_declaration_handler
from marshmallow import (fields, Schema, post_load, pre_load, pre_dump, validates)
from web.database.models import SubmissionStatus
from .genetic_part import GeneticPart
from .plasmid import Plasmid
from .strain import Strain
from .validators import validate_antibiotic_resistance, validate_status, validate_object_ids_exist

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
    antibiotic_resistance = fields.Str(required=True)
    source = fields.Str(required=False)
    status = fields.Str(required=False)
    inserts = fields.List(fields.Nested(GeneticPartSchema), dump_only=True)
    insert_ids = fields.List(fields.Str(), load_only=True)

    def __init__(self, many=False, **kwargs):
        only = kwargs['only'] if 'only' in kwargs else None
        Schema.__init__(self, many=many, only=only)

    class meta:
        strict=True

    @validates('antibiotic_resistance')
    def _validate_antibiotic_resistance_field(self, antibiotic_resistance):
        validate_antibiotic_resistance(antibiotic_resistance)

    @validates('status')
    def _validate_status_field(self, status):
        validate_status(status)

    @validates('insert_ids')
    def _validate_insert_ids_field(self, insert_ids):
        validate_object_ids_exist(GeneticPart, insert_ids)
 
    @post_load
    def make_plasmid(self, data, **kwargs):
        if 'insert_ids' in data:
            data['inserts'] = [GeneticPart.get_by_id(insert) for insert in data['insert_ids']]
            data.pop('insert_ids')
        return Plasmid.create(**data)


class StrainSchema(Schema):
    global_id = fields.Str(required=True)
    name = fields.Str(required=True)
    friendly_name = fields.Str(required=True)
    description = fields.Str(required=True)
    background_strain = fields.Str(required=True)
    status = fields.Str(required=False)
    plasmids = fields.List(fields.Nested(PlasmidSchema), dump_only=True)
    plasmid_ids = fields.List(fields.Str(), load_only=True)

    def __init__(self, many=False, **kwargs):
        only = kwargs['only'] if 'only' in kwargs else None
        Schema.__init__(self, many=many, only=only)

    class meta:
        strict=True

    @validates('status')
    def _validate_status_field(self, status):
        validate_status(status)

    @validates('plasmid_ids')
    def _validate_plasmid_ids_field(self, plasmid_ids):
        validate_object_ids_exist(Plasmid, plasmid_ids)
    
    @post_load
    def make_strain(self, data, **kwargs):
        if 'plasmid_ids' in data:
            data['plasmids'] = [Plasmid.get_by_id(plasmid) for plasmid in data['plasmid_ids']]
            data.pop('plasmid_ids')
        return Strain.create(**data)


class ConstructSubmissionSchema(Schema):
    email = fields.Email(required=True, load_only=True)
    name = fields.Str(required=True)
    description = fields.Str(required=True)
    inserts= fields.List(fields.Str(), required=True)

    def __init__(self, many=False, **kwargs):
        only = kwargs['only'] if 'only' in kwargs else None
        Schema.__init__(self, many=many, only=only)

    class meta:
        strict=True
