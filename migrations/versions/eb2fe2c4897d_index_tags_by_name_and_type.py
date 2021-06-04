"""Index Tags by name and type

Revision ID: eb2fe2c4897d
Revises: a6d01d6eef29
Create Date: 2021-06-04 16:48:09.665707

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eb2fe2c4897d'
down_revision = 'a6d01d6eef29'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index('tags_by_name')
    op.create_index('tags_by_name', 'tags', ['tag_name', 'tag_type'])
    op.create_index('tags_by_all', 'tags', ['tag_id', 'tag_name', 'tag_type'])

def downgrade():
    op.drop_index('tags_by_all')
    op.drop_index('tags_by_name')
    op.create_index('tags_by_name', 'tags', ['tag_name'])
