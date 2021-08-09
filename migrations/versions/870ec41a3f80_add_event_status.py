"""Add event status

Revision ID: 870ec41a3f80
Revises: 60ac900e6dcc
Create Date: 2021-08-05 03:47:06.868284

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '870ec41a3f80'
down_revision = '60ac900e6dcc'
branch_labels = None
depends_on = None

def upgrade():
  op.add_column("events", sa.Column("status", sa.String))
  op.create_index('events_by_status', 'events', ['status'])

def downgrade():
  op.drop_index('events_by_status', 'events')
  op.drop_column("events", "status")
