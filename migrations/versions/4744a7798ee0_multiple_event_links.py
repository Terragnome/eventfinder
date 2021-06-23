"""multiple_event_links

Revision ID: 4744a7798ee0
Revises: 8ed7f1e75b5c
Create Date: 2021-06-23 00:03:38.854441

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4744a7798ee0'
down_revision = '8ed7f1e75b5c'
branch_labels = None
depends_on = None


def upgrade():
  op.drop_column("events", "link")
  op.add_column("events", sa.Column('urls', sa.JSON))

def downgrade():
  op.drop_column("events", "urls")
  op.add_column("events", sa.Column('link', sa.String(255)))
