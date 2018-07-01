from sqlalchemy import Boolean, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from .base import Base

class UserEvent(Base):
	__tablename__ = 'user_events'
	event_id = Column(String, ForeignKey('events.event_id'), primary_key=True)
	user_id = Column(String, ForeignKey('users.user_id'), primary_key=True)
	interested = Column(Boolean, nullable=False)

	event = relationship('Event', uselist=False)
	user = relationship('User', uselist=False)