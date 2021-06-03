from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from .base import Base

class Tag(Base):
  FOOD_DRINK = "FOOD + DRINK"
  GEAR = "GEAR"
  TVM = "TV + MOVIES"

  __tablename__ = 'tags'
  tag_id = Column(Integer, primary_key=True, autoincrement=True)
  tag_name = Column(String, nullable=False)
  tag_type = Column(String, nullable=False)
  created_at = Column(DateTime)
  updated_at = Column(DateTime)

  events = relationship('Event', secondary='event_tags')

  @classmethod
  def types(klass):
    return [
      klass.TVM,
      klass.FOOD_DRINK,
      klass.GEAR,
    ]

  @property
  def count(self):
    return len(self.events)