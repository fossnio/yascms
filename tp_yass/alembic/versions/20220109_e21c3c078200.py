"""init

Revision ID: e21c3c078200
Revises:
Create Date: 2022-01-09 12:31:49.455396

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e21c3c078200'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('global_config',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('value', sa.Text(), nullable=False),
    sa.Column('type', sa.String(length=5), nullable=False),
    sa.Column('description', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('groups',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('type', sa.Integer(), server_default='1', nullable=False),
    sa.Column('order', sa.Integer(), server_default='0', nullable=False),
    sa.Column('ancestor_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['ancestor_id'], ['groups.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('link_categories',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('order', sa.Integer(), server_default='0', nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('news_categories',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('order', sa.Integer(), server_default='0', nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('pages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=100), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tags',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('telext',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=50), nullable=False),
    sa.Column('ext', sa.String(length=50), nullable=False),
    sa.Column('order', sa.Integer(), server_default='0', nullable=False),
    sa.Column('is_pinned', sa.Integer(), server_default='0', nullable=False),
    sa.Column('publication_datetime', sa.DateTime(), nullable=False),
    sa.Column('last_updated_datetime', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_telext_title'), 'telext', ['title'], unique=False)
    op.create_table('theme_config',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('value', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('first_name', sa.String(length=20), nullable=False),
    sa.Column('last_name', sa.String(length=20), nullable=False),
    sa.Column('account', sa.String(length=50), nullable=False),
    sa.Column('password', sa.String(length=77), server_default='*', nullable=False),
    sa.Column('status', sa.Integer(), server_default='0', nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('account')
    )
    op.create_table('auth_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('datetime', sa.DateTime(), nullable=False),
    sa.Column('client_addr', sa.String(length=48), nullable=False),
    sa.Column('type', sa.Integer(), nullable=False),
    sa.Column('source', sa.String(length=20), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('email',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('address', sa.String(length=100), nullable=False),
    sa.Column('type', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('group_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('address')
    )
    op.create_table('groups_pages_association',
    sa.Column('group_id', sa.Integer(), nullable=True),
    sa.Column('page_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ),
    sa.ForeignKeyConstraint(['page_id'], ['pages.id'], )
    )
    op.create_table('links',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=100), nullable=False),
    sa.Column('url', sa.Text(), nullable=False),
    sa.Column('icon', sa.String(length=100), nullable=False),
    sa.Column('is_pinned', sa.Integer(), server_default='0', nullable=False),
    sa.Column('pinned_order', sa.Integer(), server_default='0', nullable=False),
    sa.Column('categorized_order', sa.Integer(), server_default='0', nullable=False),
    sa.Column('publication_datetime', sa.DateTime(), nullable=False),
    sa.Column('last_updated_datetime', sa.DateTime(), nullable=False),
    sa.Column('group_id', sa.Integer(), nullable=True),
    sa.Column('category_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['category_id'], ['link_categories.id'], ),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_links_title'), 'links', ['title'], unique=False)
    op.create_table('navbar',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), server_default='', nullable=False),
    sa.Column('aria_name', sa.String(length=50), nullable=True),
    sa.Column('url', sa.Text(), nullable=True),
    sa.Column('page_id', sa.Integer(), nullable=True),
    sa.Column('is_href_blank', sa.Integer(), server_default='0', nullable=False),
    sa.Column('icon', sa.String(length=50), server_default='', nullable=False),
    sa.Column('type', sa.Integer(), nullable=False),
    sa.Column('module_name', sa.String(length=50), nullable=True),
    sa.Column('order', sa.Integer(), server_default='0', nullable=False),
    sa.Column('is_visible', sa.Integer(), server_default='1', nullable=False),
    sa.Column('ancestor_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['ancestor_id'], ['navbar.id'], ),
    sa.ForeignKeyConstraint(['page_id'], ['pages.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('news',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=100), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('is_pinned', sa.Integer(), server_default='0', nullable=False),
    sa.Column('pinned_start_datetime', sa.Date(), nullable=True),
    sa.Column('pinned_end_datetime', sa.Date(), nullable=True),
    sa.Column('visible_start_datetime', sa.DateTime(), nullable=True),
    sa.Column('visible_end_datetime', sa.DateTime(), nullable=True),
    sa.Column('publication_datetime', sa.DateTime(), nullable=False),
    sa.Column('last_updated_datetime', sa.DateTime(), nullable=False),
    sa.Column('group_id', sa.Integer(), nullable=True),
    sa.Column('category_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['category_id'], ['news_categories.id'], ),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_news_title'), 'news', ['title'], unique=False)
    op.create_table('page_attachments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('original_name', sa.String(length=100), nullable=False),
    sa.Column('real_name', sa.String(length=100), nullable=False),
    sa.Column('page_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['page_id'], ['pages.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('pages_tags_association',
    sa.Column('page_id', sa.Integer(), nullable=True),
    sa.Column('tag_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['page_id'], ['pages.id'], ),
    sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], )
    )
    op.create_table('users_groups_association',
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('group_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )
    op.create_table('news_attachments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('original_name', sa.String(length=100), nullable=False),
    sa.Column('real_name', sa.String(length=100), nullable=False),
    sa.Column('news_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['news_id'], ['news.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('news_tags_association',
    sa.Column('news_id', sa.Integer(), nullable=True),
    sa.Column('tag_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['news_id'], ['news.id'], ),
    sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], )
    )
    # ### end Alembic commands ###

def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('news_tags_association')
    op.drop_table('news_attachments')
    op.drop_table('users_groups_association')
    op.drop_table('pages_tags_association')
    op.drop_table('page_attachments')
    op.drop_index(op.f('ix_news_title'), table_name='news')
    op.drop_table('news')
    op.drop_table('navbar')
    op.drop_index(op.f('ix_links_title'), table_name='links')
    op.drop_table('links')
    op.drop_table('groups_pages_association')
    op.drop_table('email')
    op.drop_table('auth_logs')
    op.drop_table('users')
    op.drop_table('theme_config')
    op.drop_index(op.f('ix_telext_title'), table_name='telext')
    op.drop_table('telext')
    op.drop_table('tags')
    op.drop_table('pages')
    op.drop_table('news_categories')
    op.drop_table('link_categories')
    op.drop_table('groups')
    op.drop_table('global_config')
    # ### end Alembic commands ###