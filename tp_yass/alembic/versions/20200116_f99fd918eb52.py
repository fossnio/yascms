"""rename user status

Revision ID: f99fd918eb52
Revises: 57854f910565
Create Date: 2020-01-16 10:57:21.838332

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'f99fd918eb52'
down_revision = '57854f910565'
branch_labels = None
depends_on = None

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('status', sa.Integer(), server_default='0', nullable=False))
    op.drop_column('users', 'password_status')
    # ### end Alembic commands ###

def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('password_status', mysql.INTEGER(display_width=11), server_default=sa.text('0'), autoincrement=False, nullable=False))
    op.drop_column('users', 'status')
    # ### end Alembic commands ###
