from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .base import Base

class Event(Base):
	__tablename__ = 'events'
	event_id = Column(Integer, primary_key=True)
	name = Column(Integer, primary_key=True)
	description = Column(String)
	short_name = Column(String)
	img_url = Column(String)
	start_time = Column(DateTime)
	end_time = Column(DateTime)
	cost = Column(Integer)
	currency = Column(String)