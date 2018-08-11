"""create_users

Revision ID: b11e2c61a68a
Revises: a6e624c45eda
Create Date: 2018-06-30 14:14:19.330123

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.sql import func

# revision identifiers, used by Alembic.
revision = 'b11e2c61a68a'
down_revision = 'a6e624c45eda'
branch_labels = None
depends_on = None

def upgrade():
	auth_table = op.create_table(
		'auths',
		sa.Column('auth_key', sa.String(255), primary_key=True),
		sa.Column('auth_name', sa.String(255), nullable=False),
		sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now()),
		sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=func.now())
	)
	op.bulk_insert(
		auth_table,
	    [
	    	{
	        	'auth_key': 'google',
	        	'auth_name': 'Google'
	        }
	    ]
	)

	op.create_table(
		'users',
		sa.Column('user_id', sa.Integer, primary_key=True, autoincrement=True),
		sa.Column('username', sa.String(255), nullable=False),
		sa.Column('email', sa.String(255), nullable=False),
		sa.Column('display_name', sa.String(255)),
		sa.Column('first_name', sa.String(255)),
		sa.Column('last_name', sa.String(255)),
		sa.Column('image_url', sa.String(255)),
		sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now()),
		sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=func.now())
	)
	op.create_index('users_by_username', 'users', ['username'])
	op.create_index('users_by_email', 'users', ['email'])

	op.create_table(
		'user_auths',
		sa.Column('user_id', sa.Integer, ForeignKey('users.user_id'), primary_key=True, unique=True),
		sa.Column('auth_key', sa.String(255), ForeignKey('auths.auth_key'), primary_key=True),
		sa.Column('auth_id', sa.String(255), primary_key=True),
		sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now()),
		sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=func.now())
	)

	op.create_table(
		'user_events',
		sa.Column('event_id', sa.Integer, ForeignKey('events.event_id'), primary_key=True),
		sa.Column('user_id', sa.Integer, ForeignKey('users.user_id'), primary_key=True),
		sa.Column('interest', sa.Integer, nullable=False),
		sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now()),
		sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=func.now()),
	)
	op.create_index('user_events_by_interest', 'user_events', ['event_id', 'user_id', 'interest'])

def downgrade():
	op.drop_table('user_auths')
	op.drop_table('user_events')
	op.drop_table('auths')
	op.drop_table('users')