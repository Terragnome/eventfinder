"""create_event

Revision ID: a6e624c45eda
Revises: 
Create Date: 2018-06-24 21:27:12.883136

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import ForeignKey

# revision identifiers, used by Alembic.
revision = 'a6e624c45eda'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
	# type_latlon = sa.Float(precision=13)

	op.create_table(
		'events',
		sa.Column('event_id', sa.Integer, primary_key=True, unique=True, autoincrement=True),
		sa.Column('name', sa.String(255), nullable=False),
		sa.Column('description', sa.Text),
		sa.Column('short_name', sa.String(255)),
		sa.Column('img_url', sa.String(255)),
		sa.Column('start_time', sa.DateTime),
		sa.Column('end_time', sa.DateTime),
		sa.Column('cost', sa.Integer),
		sa.Column('currency', sa.String(255)),
		sa.Column('venue_name', sa.String(255)),
		sa.Column('address', sa.JSON),
		sa.Column('latitude', sa.Float(precision=15)),
		sa.Column('longitude', sa.Float(precision=15)),
		sa.Column('link', sa.String(255))
	)
	op.create_index('events_by_name', 'events', ['name'])
	op.create_index('events_by_cost_and_start_time', 'events', ['cost', 'start_time'])

	op.create_table(
		'connector_events',
		sa.Column('connector_event_id', sa.String(255), primary_key=True, unique=True),
		sa.Column('connector_type', sa.String(255)),
		sa.Column('data', sa.JSON, nullable=False),
	)
	op.create_index('connector_events_by_connector_type', 'connector_events', ['connector_type'])

	op.create_table(
		'event_connector_events',
		sa.Column('connector_event_id', sa.String(255), ForeignKey('connector_events.connector_event_id'), primary_key=True),
		sa.Column('event_id', sa.Integer, ForeignKey('events.event_id'), primary_key=True),
	)

def downgrade():
    op.drop_table('event_connector_events')
    op.drop_table('connector_events')
    op.drop_table('events')
    