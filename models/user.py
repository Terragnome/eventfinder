from sqlalchemy import Column, Integer, String
from sqlalchemy import and_
from sqlalchemy.orm import relationship

from .base import Base
from .block import Block
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

  user_events = relationship(
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

  def blocks_user_id(self, user_id):
    if self.blocked_users.filter(
      and_(
        Block.user_id == self.user_id,
        Block.block_id == user_id,
        Block.active
      )
    ):
      return True
    return False