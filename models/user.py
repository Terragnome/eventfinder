import datetime

from sqlalchemy import Column, Integer, String
from sqlalchemy import and_, or_
from sqlalchemy.orm import relationship

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
    return self._blocked_users.filter(Block.active)

  def blocked_users_count(self):
    return self.blocked_users().count() or 0

  _following_users = relationship(
    'User',
    secondary='follows',
    primaryjoin='User.user_id==Follow.user_id',
    secondaryjoin='User.user_id==Follow.follow_id',
    lazy='dynamic'
  )

  def following_users(self):
    return self._following_users.filter(Follow.active)

  def following_users_count(self):
    return self.following_users().count() or 0
  
  _follower_users = relationship(
    'User',
    secondary='follows',
    primaryjoin='User.user_id==Follow.follow_id',
    secondaryjoin='Follow.user_id==User.user_id',
    lazy='dynamic'
  )

  def follower_users(self):
    return self._follower_users.filter(Follow.active)

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
  def card_is_followed(self):
    return self._card_is_followed
  @card_is_followed.setter
  def card_is_followed(self, value):
    self._card_is_followed = value

  @property
  def card_is_blocked(self):
    return self._card_is_blocked
  @card_is_blocked.setter
  def card_is_blocked(self, value):
    self._card_is_blocked = value