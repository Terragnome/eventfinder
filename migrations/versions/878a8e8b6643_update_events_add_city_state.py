"""update_events_add_city_state

Revision ID: 878a8e8b6643
Revises: a544eb0f1e46
Create Date: 2018-07-01 20:40:02.338180

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '878a8e8b6643'
down_revision = 'a544eb0f1e46'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column(
    	"events",
    	sa.Column("city", sa.String)
    )
    op.add_column(
    	"events",
    	sa.Column("state", sa.String)
    )

def downgrade():
    op.drop_column("events", "city")
    op.drop_column("events", "state")