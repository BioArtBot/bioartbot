"""seed palette lab_objects

Revision ID: d9a41f7c3b2e
Revises: 89e56a30bc94
Create Date: 2026-11-08 19:05:12.412873

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from migrations.utils.session import session_scope

# revision identifiers, used by Alembic.
revision = 'd9a41f7c3b2e'
down_revision = '89e56a30bc94'
branch_labels = None
depends_on = None


Base = declarative_base()

class LabObjectsModel(Base):
    __tablename__ = 'lab_objects'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(50), nullable=False, unique=True, index=True)
    obj_class = sa.Column(sa.String(50), nullable=False)

    def __repr__(self):
        return '<%r: %r>' % (self.obj_class, self.name)


_Model = LabObjectsModel

PALETTE_CLASS = 'palette'

PALETTE_NAMES = [
    'cryo_35_tuberack_2000ul',
    'greiner_96_wellplate_323ul',
    'corning_6_wellplate_16.8ml_flat',
    'usascientific_96_wellplate_2.4ml_deep',
    'axygen_1_reservoir_90ml',
]

def upgrade():
    with session_scope() as session:
        already_stored = {name for (name,) in session.query(_Model.name)
                                       .filter(_Model.name.in_(PALETTE_NAMES))
                                       .all()}
        for name in PALETTE_NAMES:
            if name in already_stored: #Don't clobber a palette that already exists
                continue
            session.add(_Model(name=name, obj_class=PALETTE_CLASS))


def downgrade():
    with session_scope() as session:
        (session.query(_Model)
                .filter(_Model.obj_class == PALETTE_CLASS,
                        _Model.name.in_(PALETTE_NAMES))
                .delete(synchronize_session=False))
