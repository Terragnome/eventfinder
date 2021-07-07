"""event description objects

Revision ID: 60ac900e6dcc
Revises: 2d71e2b103b0
Create Date: 2021-07-07 06:27:48.255669

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '60ac900e6dcc'
down_revision = '2d71e2b103b0'
branch_labels = None
depends_on = None


def upgrade():
  op.drop_column("events", "description")
  op.add_column("events", sa.Column("description", sa.JSON))

def downgrade():
  op.drop_column("events", "description")
  op.add_column("events", sa.Column("description", sa.Text))
