"""empty message

Revision ID: fc2bbd3e5824
Revises: 9d511bb80efc
Create Date: 2020-10-28 00:34:25.795253

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fc2bbd3e5824'
down_revision = '9d511bb80efc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('analysis', 'name',
               existing_type=sa.TEXT(),
               nullable=True)
    op.add_column('neurovault_collection', sa.Column('cli_version', sa.Text(), nullable=True))
    op.add_column('neurovault_collection', sa.Column('fmriprep_version', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('neurovault_collection', 'fmriprep_version')
    op.drop_column('neurovault_collection', 'cli_version')
    op.alter_column('analysis', 'name',
               existing_type=sa.TEXT(),
               nullable=False)
    # ### end Alembic commands ###
