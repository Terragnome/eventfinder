"""add_event_accolades

Revision ID: 8ed7f1e75b5c
Revises: 4d512a32a29e
Create Date: 2021-06-21 15:42:53.752272

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8ed7f1e75b5c'
down_revision = '4d512a32a29e'
branch_labels = None
depends_on = None

def upgrade():
  op.add_column("events", sa.Column("accolades", sa.JSON))
  # op.create_index('events_by_accolades', 'events', ['accolades'])

def downgrade():
  # op.drop_index('events_by_accolades', 'events')
  op.drop_column("events", "accolades")
