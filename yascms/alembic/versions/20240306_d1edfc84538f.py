"""change_text_column_to_longtext

Revision ID: d1edfc84538f
Revises: 7f9bd8a119d1
Create Date: 2024-03-06 14:45:59.112485

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'd1edfc84538f'
down_revision = '7f9bd8a119d1'
branch_labels = None
depends_on = None

def upgrade():
    if op.get_bind().engine.dialect.name in ('mysql', 'mariadb'):
        op.alter_column('news', 'content',
                   existing_type=mysql.TEXT(),
                   type_=mysql.LONGTEXT(),
                   existing_nullable=False)
        op.alter_column('pages', 'content',
                   existing_type=mysql.TEXT(),
                   type_=mysql.LONGTEXT(),
                   existing_nullable=False)

def downgrade():
    if op.get_bind().engine.dialect.name in ('mysql', 'mariadb'):
        op.alter_column('pages', 'content',
                   existing_type=mysql.LONGTEXT(),
                   type_=mysql.TEXT(),
                   existing_nullable=False)
        op.alter_column('news', 'content',
                   existing_type=mysql.LONGTEXT(),
                   type_=mysql.TEXT(),
                   existing_nullable=False)
