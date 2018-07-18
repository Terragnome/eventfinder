from sqlalchemy import Boolean, Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from .base import Base

class UserEvent(Base):
  __tablename__ = 'user_events'
  event_id = Column(Integer, ForeignKey('events.event_id'), primary_key=True)
  user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
  interested = Column(Boolean, nullable=True)

  event = relationship('Event', uselist=False)
  user = relationship('User', uselist=False)