"""empty message

Revision ID: 138ff2662c51
Revises: 834b1a697901
Create Date: 2023-03-15 23:11:45.610797

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '138ff2662c51'
down_revision = '834b1a697901'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('FA_token', sa.String(length=16), nullable=True))
    op.create_unique_constraint(None, 'user', ['token_expiration'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'user', type_='unique')
    op.drop_column('user', 'FA_token')
    # ### end Alembic commands ###
