"""Create blocks and follows

Revision ID: f2bf7f9f0b5c
Revises: a544eb0f1e46
Create Date: 2018-07-15 00:01:11.883249

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.sql import func

# revision identifiers, used by Alembic.
revision = 'f2bf7f9f0b5c'
down_revision = 'a544eb0f1e46'
branch_labels = None
depends_on = None

def upgrade():
  op.create_table(
    'follows',
    sa.Column('user_id', sa.Integer, ForeignKey('users.user_id'), primary_key=True),
    sa.Column('follow_id', sa.Integer, ForeignKey('users.user_id'), primary_key=True),
    sa.Column('active', sa.Boolean),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now()),
    sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=func.now())
  )
  op.create_index('follows_by_user_id_and_active', 'follows', ['user_id', 'active'])  

  op.create_table(
    'blocks',
    sa.Column('user_id', sa.Integer, ForeignKey('users.user_id'), primary_key=True),
    sa.Column('block_id', sa.Integer, ForeignKey('users.user_id'), primary_key=True),
    sa.Column('active', sa.Boolean),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now()),
    sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=func.now())
  )
  op.create_index('blocks_by_user_id_and_active', 'blocks', ['user_id', 'active'])  

def downgrade():
  op.drop_table('blocks')
  op.drop_table('follows')