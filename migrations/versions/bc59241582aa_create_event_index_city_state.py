"""create_event_index_city_state

Revision ID: bc59241582aa
Revises: 7f1f69b874d1
Create Date: 2018-08-18 21:25:43.841262

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.sql import func

# revision identifiers, used by Alembic.
revision = 'bc59241582aa'
down_revision = '7f1f69b874d1'
branch_labels = None
depends_on = None

def upgrade():
  op.create_index('events_by_city_state', 'events', ['city', 'state'])

  op.create_table(
    'tags',
    sa.Column('tag_id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('tag_name', sa.String(255), nullable=False),
    sa.Column('tag_type', sa.String(255)),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now()),
    sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=func.now())
  )
  op.create_index('tags_by_name', 'tags', ['tag_name'])
  op.create_index('tags_by_type', 'tags', ['tag_type'])

  op.create_table(
    'event_tags',
    sa.Column('tag_id', sa.Integer, ForeignKey('tags.tag_id'), primary_key=True),
    sa.Column('event_id', sa.Integer, ForeignKey('events.event_id'), primary_key=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now()),
    sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=func.now())
  )

def downgrade():
  op.drop_table('event_tags')
  op.drop_table('tags')
  op.drop_index('events_by_city_state', 'events')