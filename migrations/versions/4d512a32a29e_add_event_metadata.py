"""add_event_metadata

Revision ID: 4d512a32a29e
Revises: eb2fe2c4897d
Create Date: 2021-06-19 18:56:27.838033

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4d512a32a29e'
down_revision = 'eb2fe2c4897d'
branch_labels = None
depends_on = None

def upgrade():
  op.add_column("events", sa.Column("primary_type", sa.String))
  op.add_column("events", sa.Column("alias", sa.String))
  op.add_column("events", sa.Column("meta", sa.JSON))
  op.create_index('events_by_primary_type', 'events', ['primary_type', 'alias'])
  op.create_index('events_by_alias', 'events', ['alias'])

def downgrade():
  op.drop_index('events_by_alias', 'events')
  op.drop_index('events_by_primary_type', 'events')
  op.drop_column("events", "primary_type")
  op.drop_column("events", "alias")
  op.drop_column("events", "meta")