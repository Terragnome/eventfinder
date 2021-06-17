import datetime

from flask import current_app
from sqlalchemy import Column, Integer, String
from sqlalchemy import alias
from sqlalchemy import and_, or_
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import db_session
from .base import Base
from .block import Block
from .event import Event
from .follow import Follow
from .user_event import UserEvent

class User(Base):
  FOLLOWER = "followers"
  FOLLOWING = "following"
  SUGGESTED = "suggested"
  BLOCKED = "blocked"

  @classmethod
  def relationship_types(klass):
    return [
      klass.FOLLOWER,
      klass.FOLLOWING,
      klass.BLOCKED
    ]

  __tablename__ = 'users'
  user_id = Column(Integer, primary_key=True, autoincrement=True)
  username = Column(String, nullable=False)
  email = Column(String, nullable=False)
  display_name = Column(String)
  first_name = Column(String)
  last_name = Column(String)
  image_url = Column(String)

  auth = relationship('Auth', secondary='user_auths')
  events = relationship('Event', secondary='user_events', lazy='dynamic')
  squads = relationship('Squad', secondary='squad_users')
  squad_users = relationship('SquadUser', cascade="all,delete-orphan")

  _user_events = relationship('UserEvent', cascade="all,delete-orphan", lazy='dynamic')

  def user_events(self):
    return self._user_events.filter(UserEvent.interest != None)

  def user_events_count(self):
    return self.user_events().count()

  def active_user_events(self):
    return self.user_events().join(
      Event
    ).filter(
      and_(
        # or_(
        #   Event.end_time is None,
        #   Event.end_time >= datetime.datetime.now()
        # ),
        UserEvent.interest.in_(UserEvent.INTERESTED_LEVELS)
      )
    )

  def active_user_events_count(self):
    return self.active_user_events().count()

  _blocked_users = relationship(
    'User',
    secondary='blocks',
    primaryjoin='User.user_id==Block.user_id',
    secondaryjoin='User.user_id==Block.block_id',
    lazy='dynamic'
  )

  def blocked_users(self):
    return self._blocked_users.filter(Block.active == True)

  def blocked_users_count(self):
    return self.blocked_users().count() or 0

  _following_users = relationship(
    'User',
    secondary='follows',
    primaryjoin='User.user_id==Follow.user_id',
    secondaryjoin='User.user_id==Follow.follow_id',
    lazy='dynamic'
  )

  def all_blocks_table(self):
    blocking = db_session.query(
      Block.block_id.label('block_id')
    ).filter(
      Block.user_id == self.user_id,
      Block.active == True
    )

    blocked_by = db_session.query(
      Block.user_id.label('block_id')
    ).filter(
      Block.block_id == self.user_id,
      Block.active == True
    )

    return blocking.union(blocked_by).subquery()

  def following_users(self):
    all_blocks_table = self.all_blocks_table()
    return self._following_users.outerjoin(
      all_blocks_table,
      Follow.follow_id == all_blocks_table.c.block_id
    ).filter(
      and_(
        Follow.follow_id != None,
        all_blocks_table.c.block_id == None,
        Follow.active == True
      )
    )

  def following_users_count(self):
    return self.following_users().count() or 0
  
  _follower_users = relationship(
    'User',
    secondary='follows',
    primaryjoin='User.user_id==Follow.follow_id',
    secondaryjoin='User.user_id==Follow.user_id',
    lazy='dynamic'
  )

  def follower_users(self):
    all_blocks_table = self.all_blocks_table()
    return self._follower_users.outerjoin(
      all_blocks_table,
      Follow.user_id == all_blocks_table.c.block_id
    ).filter(
      and_(
        Follow.user_id != None,
        all_blocks_table.c.block_id == None,
        Follow.active == True
      )
    )

    return self._follower_users.filter(
      Follow.active == True
    ).join(
      Block,
      Follow.follow_id == Block.user_id
    ).filter(
      or_(
        and_(
          Follow.follow_id != None,
          Block.user_id == None
        ),
        Block.active != True
      )
    )

  def follower_users_count(self):
    return self.follower_users().count() or 0

  def interested_events(self):
    return self.events.filter(UserEvent.interest>0)

  def is_blocks_user(self, user):
    return self.blocked_users().filter(
      and_(
        Block.block_id==user.user_id,
        Block.active
      )
    ).first() != None

  def is_follows_user(self, user):
    return self.following_users().filter(
      and_(
        Follow.follow_id==user.user_id,
        Follow.active
      )
    ).first() != None

  @property
  def card_relationship_type(self):
    return self._card_relationship_type
  @card_relationship_type.setter
  def card_relationship_type(self, value):
    self._card_relationship_type = value

  @property
  def card_follower_count(self):
    return self._card_follower_count
  @card_follower_count.setter
  def card_follower_count(self, value):
    self._card_follower_count = value

  @property
  def card_event_count(self):
    return self._card_event_count
  @card_event_count.setter
  def card_event_count(self, value):
    self._card_event_count = value

  @property
  def card_is_following(self):
    return self._card_is_following
  @card_is_following.setter
  def card_is_following(self, value):
    self._card_is_following = value

  @property
  def card_is_blocked(self):
    return self._card_is_blocked
  @card_is_blocked.setter
  def card_is_blocked(self, value):
    self._card_is_blocked = value

  @property
  def card_is_suggested(self):
    return self._card_is_suggested
  @card_is_suggested.setter
  def card_is_suggested(self, value):
    self._card_is_suggested = value