from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from .base import Base

class Tag(Base):
  FOOD_DRINK = "Food + Drink"
  TVM = "TV + MOVIES"

  __tablename__ = 'tags'
  tag_id = Column(Integer, primary_key=True, autoincrement=True)
  tag_name = Column(String, nullable=False)
  tag_type = Column(String, nullable=False)
  created_at = Column(DateTime)
  updated_at = Column(DateTime)

  events = relationship('Event', secondary='event_tags')

  @property
  def count(self):
    return len(self.events)
  