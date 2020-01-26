"""empty message

Revision ID: fca4d39d6f19
Revises: 8386df60ac9f
Create Date: 2019-10-31 13:06:26.681806

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fca4d39d6f19'
down_revision = '8386df60ac9f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('site_vars')
    # ### end Alembic commands ###
    op.alter_column('artpieces', 'art', new_column_name='art_encoding', type_=sa.JSON(),
            postgresql_using='art::json', nullable=False)
    op.alter_column('artpieces', 'picture', new_column_name='raw_image', nullable=True)
    op.alter_column('artpieces', 'status', new_column_name='submission_status', nullable=False)
    op.alter_column('artpieces', 'title', nullable=False)
    op.alter_column('artpieces', 'submit_date', nullable=False)

def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('site_vars',
    sa.Column('var', sa.VARCHAR(), nullable=False),
    sa.Column('val', sa.INTEGER(), nullable=True),
    sa.PrimaryKeyConstraint('var')
    )
    # ### end Alembic commands ###
    op.alter_column('artpieces', 'art_encoding', new_column_name='art', type_=sa.String()
            , nullable=True)
    op.alter_column('artpieces', 'raw_image', new_column_name='picture', nullable=True)
    op.alter_column('artpieces', 'submission_status', new_column_name='status', nullable=True)
    op.alter_column('artpieces', 'title', nullable=True)
    op.alter_column('artpieces', 'submit_date', nullable=True)
