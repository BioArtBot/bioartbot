"""biofoundry build status

Revision ID: c09016b87517
Revises: f37246b206a0
Create Date: 2022-02-26 15:39:29.968155

"""
from alembic import op
import sqlalchemy as sa
from migrations.utils.session import session_scope


# revision identifiers, used by Alembic.
revision = 'c09016b87517'
down_revision = 'f37246b206a0'
branch_labels = None
depends_on = None


def upgrade():

    submission_enum = sa.Enum('Submitted', 'Processing', 'Processed', name='submissionstatus')
    submission_enum.create(op.get_bind())

    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('plasmids', sa.Column('build_status', submission_enum, nullable=True))
    op.add_column('strains', sa.Column('build_status', submission_enum, nullable=True))
    # ### end Alembic commands ###

    op.execute("""UPDATE strains SET build_status = 'Processed'""")
    op.execute("""UPDATE plasmids SET build_status = 'Processed'""")

    op.alter_column('plasmids', 'build_status', nullable=False)
    op.alter_column('strains', 'build_status', nullable=False)

    # artpieces was never set to use enum. This corrects that
    op.execute("""ALTER TABLE artpieces
                  ALTER COLUMN submission_status
                  TYPE submissionstatus
                  USING submission_status::submissionstatus
               """)


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('strains', 'build_status')
    op.drop_column('plasmids', 'build_status')
    # ### end Alembic commands ###

    op.execute("""ALTER TABLE artpieces
                  ALTER COLUMN submission_status
                  TYPE VARCHAR
               """)

    submission_enum = sa.Enum('Submitted', 'Processing', 'Processed', name='submissionstatus')
    submission_enum.drop(op.get_bind())
