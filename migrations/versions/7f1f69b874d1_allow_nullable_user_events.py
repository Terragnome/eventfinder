"""Allow nullable user events

Revision ID: 7f1f69b874d1
Revises: f2bf7f9f0b5c
Create Date: 2018-07-17 22:36:09.846751

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7f1f69b874d1'
down_revision = 'f2bf7f9f0b5c'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('user_events', 'interested', nullable=True)

def downgrade():
    op.alter_column('user_events', 'interested', nullable=False)