"""empty message

Revision ID: b51e0d9c6f26
Revises: 88f313fe1de5
Create Date: 2018-08-22 22:27:35.934751

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b51e0d9c6f26'
down_revision = '88f313fe1de5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('dataset', sa.Column('active', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('dataset', 'active')
    # ### end Alembic commands ###