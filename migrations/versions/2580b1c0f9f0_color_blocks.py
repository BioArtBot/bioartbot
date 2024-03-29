"""color_blocks

Revision ID: 2580b1c0f9f0
Revises: e9475d315bf6
Create Date: 2023-04-27 06:05:27.006210

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from migrations.utils.session import session_scope

Base = declarative_base()

# revision identifiers, used by Alembic.
revision = '2580b1c0f9f0'
down_revision = 'e9475d315bf6'
branch_labels = None
depends_on = None

class ArtpieceModel(Base):
    __tablename__ = 'artpieces'

    id = sa.Column(sa.Integer, primary_key=True)
    art = sa.Column(sa.JSON(), nullable=False, name='art_encoding')


class ColorBlockModel(Base):
    __tablename__ = 'color_blocks'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    artpiece = relationship('ArtpieceModel', backref='color_blocks', lazy="joined")
    artpiece_id = sa.Column('artpiece_id', sa.ForeignKey('artpieces.id'), primary_key=True, autoincrement='ignore_fk')
    color = relationship('BacterialColorModel')
    color_id = sa.Column('color_id', sa.ForeignKey('bacterial_colors.id'), primary_key=True, autoincrement='ignore_fk')
    coordinates = sa.Column(sa.JSON(), nullable=False)


class BacterialColorModel(Base):
    __tablename__ = 'bacterial_colors'

    id = sa.Column(sa.Integer, primary_key=True)


def make_color_blocks(session, artpiece):
    """
    Breaks art in JSON format into individual ColorBlock objects,
    which can each be stored in the database
    """
    for color in artpiece.art:
        color_block = ColorBlockModel(artpiece=artpiece,
                                      color_id=color, 
                                      coordinates=artpiece.art[color]
        )
        session.add(color_block)


def make_art_dict(artpiece):
    art_dict = {}
    for color_block in artpiece.color_blocks:
        art_dict[color_block.color.id] = color_block.coordinates
    return art_dict


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('color_blocks',
    sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
    sa.Column('artpiece_id', sa.Integer(), nullable=False),
    sa.Column('color_id', sa.Integer(), nullable=False),
    sa.Column('coordinates', sa.JSON(), nullable=False),
    sa.ForeignKeyConstraint(['artpiece_id'], ['artpieces.id'], ),
    sa.ForeignKeyConstraint(['color_id'], ['bacterial_colors.id'], ),
    sa.PrimaryKeyConstraint('id', 'artpiece_id', 'color_id')
    )

    #move all data from art_encoding to color_block
    with session_scope() as session:
        artpieces = session.query(ArtpieceModel).all()
        for artpiece in artpieces:
            make_color_blocks(session, artpiece)
        session.commit()

    op.drop_column('artpieces', 'art_encoding')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('artpieces', sa.Column('art_encoding', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True))

    #move all data from color_blocks
    with session_scope() as session:
        artpieces = session.query(ArtpieceModel).all()
        for artpiece in artpieces:
            art_dict = make_art_dict(artpiece)
            artpiece.art = art_dict
        session.commit()
    op.alter_column('artpieces', 'art_encoding', nullable=False)

    op.drop_table('color_blocks')
    # ### end Alembic commands ###
