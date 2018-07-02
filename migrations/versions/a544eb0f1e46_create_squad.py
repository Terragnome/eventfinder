"""create squad

Revision ID: a544eb0f1e46
Revises: b11e2c61a68a
Create Date: 2018-07-01 19:20:43.368809

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import ForeignKey

# revision identifiers, used by Alembic.
revision = 'a544eb0f1e46'
down_revision = 'b11e2c61a68a'
branch_labels = None
depends_on = None


def upgrade():
	op.create_table(
		'squads',
		sa.Column('squad_id', sa.Integer, primary_key=True, autoincrement=True),
		sa.Column('name', sa.String(255))
	)
	op.create_index('squads_by_name', 'squads', ['name'])

	op.create_table(
		'squad_users',
		sa.Column('squad_id', sa.Integer, ForeignKey('squads.squad_id'), primary_key=True),
		sa.Column('user_id', sa.Integer, ForeignKey('users.user_id'), primary_key=True)
	)

	op.create_table(
		'squad_invites',
		sa.Column('squad_id', sa.Integer, ForeignKey('squads.squad_id'), primary_key=True),
		sa.Column('email', sa.String, primary_key=True),
		sa.Column('user_id', sa.Integer, ForeignKey('users.user_id')),
	)
	op.create_index('squad_invites_by_user_id', 'squad_invites', ['user_id'])



def downgrade():
    op.drop_table('squad_invites')
    op.drop_table('squad_users')
    op.drop_table('squads')