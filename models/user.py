from sqlalchemy import Column, Integer, String
from sqlalchemy import and_
from sqlalchemy.orm import relationship

from .base import Base
from .block import Block
from .follow import Follow
from .user_event import UserEvent

class User(Base):
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
  squad_users = relationship('SquadUser', cascade="all, delete-orphan")

  _user_events = relationship(
    'UserEvent',
    cascade="all, delete-orphan",
    lazy='dynamic'
  )

  blocked_users = relationship(
    'User',
    secondary='blocks',
    primaryjoin='User.user_id==Block.user_id',
    secondaryjoin='User.user_id==Block.block_id',
    lazy='dynamic'
  )

  followed_users = relationship(
    'User',
    secondary='follows',
    primaryjoin='User.user_id==Follow.user_id',
    secondaryjoin='User.user_id==Follow.follow_id',
    lazy='dynamic'
  )
  
  @property
  def interested_events(self):
    return self.events.filter(UserEvent.interested)

  @property
  def user_events(self):
    return self._user_events.filter(UserEvent.interested != None)

  @property
  def is_blocked(self):
    return self._is_blocked
  @is_blocked.setter
  def is_blocked(self, value):
    self._is_blocked = value

  def is_blocks_user(self, user):
    return self.blocked_users.filter(
      and_(
        Block.block_id==user.user_id,
        Block.active
      )
    ).first()

  @property
  def is_followed(self):
    return self._is_followed
  @is_followed.setter
  def is_followed(self, value):
    self._is_followed = value

  def is_follows_user(self, user):
    return self.followed_users.filter(
      and_(
        Follow.follow_id==user.user_id,
        Follow.active
      )
    ).first()