"""add_canvas_size

Revision ID: b8ebf60a501c
Revises: 7a53942ec9af
Create Date: 2021-10-24 19:12:14.457769

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

from migrations.utils.session import session_scope

Base = declarative_base()

class ArtpieceModel(Base):
    __tablename__ = 'artpieces'

    id = sa.Column(sa.Integer, primary_key=True)
    canvas_size = sa.Column(sa.JSON(), nullable=False)

# revision identifiers, used by Alembic.
revision = 'b8ebf60a501c'
down_revision = '7a53942ec9af'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('artpieces', sa.Column('canvas_size', sa.JSON(), nullable=True))
    # ### end Alembic commands ###

    with session_scope() as session:
        artpieces = session.query(ArtpieceModel).all()
        for artpiece in artpieces:
            artpiece.canvas_size = {'x':39,'y':26}

    op.alter_column('artpieces', 'canvas_size', nullable=False)


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('artpieces', 'canvas_size')
    # ### end Alembic commands ###
