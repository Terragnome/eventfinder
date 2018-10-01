"""Add backdrops to events

Revision ID: a6d01d6eef29
Revises: bc59241582aa
Create Date: 2018-10-01 15:08:53.497122

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a6d01d6eef29'
down_revision = 'bc59241582aa'
branch_labels = None
depends_on = None

def upgrade():
  op.add_column("events", sa.Column("backdrop_url", sa.String))

def downgrade():
  op.drop_column("events", "backdrop_url")