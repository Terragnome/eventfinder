"""add event details

Revision ID: 2d71e2b103b0
Revises: 4744a7798ee0
Create Date: 2021-06-26 14:53:09.240128

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2d71e2b103b0'
down_revision = '4744a7798ee0'
branch_labels = None
depends_on = None


def upgrade():
  op.add_column("events", sa.Column("details", sa.JSON))

def downgrade():
  op.drop_column("events", "details")