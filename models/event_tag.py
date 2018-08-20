from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .base import Base

class EventTag(Base):
  __tablename__ = 'event_tags'
  event_id = Column(Integer, ForeignKey('events.event_id'), primary_key=True)
  tag_id = Column(Integer, ForeignKey('tags.tag_id'), primary_key=True)
  created_at = Column(DateTime)
  updated_at = Column(DateTime)

  event = relationship('Event', uselist=False)
  tag = relationship('Tag', uselist=False)