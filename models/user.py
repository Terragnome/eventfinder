from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from .base import Base

class User(Base):
	__tablename__ = 'users'
	user_id = Column(Integer, primary_key=True, autoincrement=True)
	username = Column(String, nullable=False)
	email = Column(String, nullable=False)
	first_name = Column(String)
	last_name = Column(String)
	image_url = Column(String)

	auth = relationship('Auth', secondary='user_auths')
	events = relationship('Event', secondary='user_events')
	user_events = relationship('UserEvent', cascade="all, delete-orphan")