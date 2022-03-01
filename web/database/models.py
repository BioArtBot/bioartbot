#models.py - Defines the database tables used in the website.
import datetime as dt
from collections import namedtuple
from enum import Enum

from sqlalchemy.orm import relation
from .database import (Model, SurrogatePK, db, Column, Table, Base,
                              reference_col, relationship, deferred, composite,
                              OrderedEnum)

class SubmissionStatus(Enum):
    submitted = 'Submitted'
    processing = 'Processing'
    processed = 'Processed'

#Stores all submitted art and allows it to be referenced later by the robot interface
class ArtpieceModel(SurrogatePK, Model):
    __tablename__ = 'artpieces'

    slug = Column(db.String(60), nullable=False, unique=True, index=True)
    title = Column(db.String(50), nullable=False)
    user_id = Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    submit_date = Column(db.DateTime(), nullable=False)
    art = Column(db.JSON(), nullable=False, name='art_encoding')
    canvas_size = Column(db.JSON(), nullable=False)
    status = Column(
            db.Enum(SubmissionStatus, values_callable=lambda x: [e.value for e in x])
            , nullable=False, name='submission_status')
    confirmed = Column(db.Boolean, nullable=False)
    image_uri = Column(db.String(128), nullable=False)

    def __repr__(self):
        return '<%r: %r>' % (self.id, self.title)

class UserRole(OrderedEnum):
    artist = 'Artist'

class UserModel(SurrogatePK, Model):
    __tablename__ = 'users'

    email = Column(db.String(50), nullable=False, index=True, unique=True)
    created_at = Column(db.DateTime(), nullable=False)
    role = Column(
            db.Enum(UserRole, values_callable=lambda x: [e.value for e in x])
            , nullable=False, name='role', default='Artist')
    artpieces = relationship('ArtpieceModel', backref='user', lazy='dynamic')
    password_hash = Column(db.String(128), nullable=True)

    def __repr__(self):
        return '<%r: %r>' % (self.id, self.email)

class SuperUserRole(OrderedEnum):
    printer = 'Printer'
    admin = 'Admin'

class SuperUserModel(SurrogatePK, Model):
    __tablename__ = 'super_users'

    email = Column(db.String(50), nullable=False, index=True, unique=True)
    created_at = Column(db.DateTime(), nullable=False)
    role = Column(
            db.Enum(SuperUserRole, values_callable=lambda x: [e.value for e in x])
            , nullable=False, name='role', default='Printer')
    password_hash = Column(db.String(128), nullable=True)

    def __repr__(self):
        return '<%r: %r>' % (self.id, self.email)

class ApplicationModel(SurrogatePK, Model):
    __tablename__ = 'applications'

    name = Column(db.String(30), nullable=False)
    

RGBA = namedtuple('RGBA', ['r','g','b','a'])

class BacterialColorModel(SurrogatePK, Model):
    __tablename__ = 'bacterial_colors'

    name = Column(db.String(20), unique=True, nullable=False)
    red = Column(db.SmallInteger(), nullable=False)
    green = Column(db.SmallInteger(), nullable=False)
    blue = Column(db.SmallInteger(), nullable=False)
    opacity = Column(db.SmallInteger(), nullable=False)
    strain_id = Column(db.Integer, db.ForeignKey('strains.id', ondelete="CASCADE"), nullable=False)
    strain = relationship("StrainModel",
                    primaryjoin="and_(BacterialColorModel.strain_id==StrainModel.id, "
                        "StrainModel.application_id==1)", #assume 1 == 'bioart'
                    cascade="all, delete")
    in_use = Column(db.Boolean(), nullable=False)

    rgba = composite(RGBA, red, green, blue, opacity)

    def __repr__(self):
        return '<%r: (%r,%r,%r,%r)>' % (self.name, self.red, self.green, self.blue, self.opacity)


strain_plasmid_association = Table('strain_plasmid_association', Model.metadata,
    Column('strain_id', db.ForeignKey('strains.id'), primary_key=True),
    Column('plasmid_id', db.ForeignKey('plasmids.id'), primary_key=True)
)

plasmid_part_association = Table('plasmid_part_association', Model.metadata,
    Column('plasmid_id', db.ForeignKey('plasmids.id'), primary_key=True),
    Column('part_id', db.ForeignKey('genetic_parts.id'), primary_key=True)
)

class PlasmidModel(SurrogatePK, Model):
    """
    A plasmid is a physical piece of DNA that exists somewhere,
    possibly inside of a strain, or possibly as pure DNA.
    It may comprise several genetic parts, and/or DNA that is
    not formalized in this system (i.e. just ACTGs).
    """
    __tablename__ = 'plasmids'

    global_id = Column(db.String(30), unique=True, nullable=False)
    name = Column(db.String(20), unique=True, nullable=False)
    friendly_name = Column(db.String(20), nullable=False)
    description = Column(db.String(500), nullable=False)
    sequence = Column(db.Text())
    sequence_of_interest = Column(db.Text())
    antibiotic_resistance = Column(db.String(25), nullable=False)
    status = Column(
            db.Enum(SubmissionStatus, values_callable=lambda x: [e.value for e in x])
            , nullable=False, name='build_status')
    application_id = Column(db.Integer, db.ForeignKey('applications.id'))
    application = relationship('ApplicationModel')
    source = Column(db.String(50))
    inserts = relationship('GeneticPartsModel', 
                            secondary=plasmid_part_association,
                            backref="in_plasmids",
                            lazy="dynamic")

    def __repr__(self):
        return '<%r: %r>' % (self.global_id, self.friendly_name)


class GeneticPartsModel(SurrogatePK, Model):
    """
    A genetic part is a sequence of DNA with at least the following:
      - Sequences enabling it's assembly into a larger construct via
        one or more specific assembly methods
      - An intended use in a biomolecular context (e.g. "promoter")
    """
    __tablename__ = 'genetic_parts'

    global_id = Column(db.String(30), unique=True, nullable=False)
    name = Column(db.String(20), unique=True, nullable=False)
    friendly_name = Column(db.String(20), nullable=False)
    description = Column(db.String(500), nullable=False)
    sequence = Column(db.Text(), nullable=False)
    part_type = Column(db.String(20))
    assembly_method = Column(db.String(50), nullable=False)
    cloning_prefix = Column(db.String(10), nullable=False)
    cloning_suffix = Column(db.String(10), nullable=False)

    def __repr__(self):
        return '<%r %r: %r>' % (self.part_type, self.global_id, self.friendly_name)

class StrainModel(SurrogatePK, Model):
    """
    A strain is a microbe (probably GMO) that is preserved somewhere
    in such a way that we can expect the same genotype every time 
    we do something with it. It may contain a plasmid as its GM
    component. It is derived from a background strain. It has one
    or more intended applications.
    """
    __tablename__ = 'strains'

    global_id = Column(db.String(30), unique=True, nullable=False)
    name = Column(db.String(20), unique=True, nullable=False)
    friendly_name = Column(db.String(20), nullable=False)
    description = Column(db.String(500), nullable=False)
    background_strain = Column(db.String(30), nullable=False)
    status = Column(
            db.Enum(SubmissionStatus, values_callable=lambda x: [e.value for e in x])
            , nullable=False, name='build_status')
    application_id = Column(db.Integer, db.ForeignKey('applications.id'))
    application = relationship('ApplicationModel')
    plasmids = relationship('PlasmidModel', 
                            secondary=strain_plasmid_association,
                            backref="in_strains")

    def __repr__(self):
        return '<%r: %r>' % (self.global_id, self.friendly_name)


class EmailFailureState(Enum):
    submission_confirmation = 's_confirmation'
    bioart_completion = 'bioart_completion'

class EmailFailureModel(SurrogatePK, Model):
    __tablename__ = 'emailfailures'

    artpiece_id = Column(db.Integer, db.ForeignKey('artpieces.id'), nullable=False)
    state = Column(db.Enum(EmailFailureState, values_callable=lambda x: [e.value for e in x])
            , nullable=False, name='failure_state')
    error_msg = Column(db.String(150), nullable=False)

class LabObjectsModel(SurrogatePK, Model):
    __tablename__ = 'lab_objects'

    name = Column(db.String(50), nullable=False, unique=True, index=True)
    obj_class = Column(db.String(50), nullable=False)
    properties = relationship('LabObjectPropertyModel', backref='object', lazy='dynamic')

    def __repr__(self):
        return '<%r: %r>' % (self.obj_class, self.name)

class LabObjectPropertyModel(SurrogatePK, Model):
    __tablename__ = 'lab_object_properties'

    object_id = Column(db.Integer, db.ForeignKey('lab_objects.id'))
    obj_property = Column(db.String(50), nullable=False)
    obj_property_units = Column(db.String(20), nullable=True)
    property_value_num = Column(db.Float, nullable = True)
    property_value_str = Column(db.String(255), nullable=True)
    

    def __repr__(self):
        return '<%r: %r>' % (self.obj_property,
                            self.property_value_num or self.property_value_str)