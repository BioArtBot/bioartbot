"""longer_names

Revision ID: e10e80392138
Revises: c09016b87517
Create Date: 2022-04-11 21:18:49.369976

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e10e80392138'
down_revision = 'c09016b87517'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('artpieces', 'title',
               existing_type=sa.VARCHAR(),
               type_=sa.String(length=50),
               existing_nullable=False)
    op.alter_column('genetic_parts', 'friendly_name',
               existing_type=sa.VARCHAR(length=20),
               type_=sa.String(length=50),
               existing_nullable=False)
    op.alter_column('genetic_parts', 'name',
               existing_type=sa.VARCHAR(length=20),
               type_=sa.String(length=50),
               existing_nullable=False)
    op.alter_column('plasmids', 'friendly_name',
               existing_type=sa.VARCHAR(length=20),
               type_=sa.String(length=50),
               existing_nullable=False)
    op.alter_column('plasmids', 'name',
               existing_type=sa.VARCHAR(length=20),
               type_=sa.String(length=50),
               existing_nullable=False)
    op.alter_column('strains', 'friendly_name',
               existing_type=sa.VARCHAR(length=20),
               type_=sa.String(length=50),
               existing_nullable=False)
    op.alter_column('strains', 'name',
               existing_type=sa.VARCHAR(length=20),
               type_=sa.String(length=50),
               existing_nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('strains', 'name',
               existing_type=sa.String(length=50),
               type_=sa.VARCHAR(length=20),
               existing_nullable=False)
    op.alter_column('strains', 'friendly_name',
               existing_type=sa.String(length=50),
               type_=sa.VARCHAR(length=20),
               existing_nullable=False)
    op.alter_column('plasmids', 'name',
               existing_type=sa.String(length=50),
               type_=sa.VARCHAR(length=20),
               existing_nullable=False)
    op.alter_column('plasmids', 'friendly_name',
               existing_type=sa.String(length=50),
               type_=sa.VARCHAR(length=20),
               existing_nullable=False)
    op.alter_column('genetic_parts', 'name',
               existing_type=sa.String(length=50),
               type_=sa.VARCHAR(length=20),
               existing_nullable=False)
    op.alter_column('genetic_parts', 'friendly_name',
               existing_type=sa.String(length=50),
               type_=sa.VARCHAR(length=20),
               existing_nullable=False)
    op.alter_column('artpieces', 'title',
               existing_type=sa.String(length=50),
               type_=sa.VARCHAR(),
               existing_nullable=False)
    # ### end Alembic commands ###
