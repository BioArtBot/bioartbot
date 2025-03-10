"""add strain.short_description

Revision ID: 89e56a30bc94
Revises: 2580b1c0f9f0
Create Date: 2025-03-09 23:38:59.538345

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '89e56a30bc94'
down_revision = '2580b1c0f9f0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('strains', sa.Column('short_description', sa.String(length=280), nullable=True))


def downgrade():
    op.drop_column('strains', 'short_description')
