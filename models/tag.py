from flask import current_app

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy import distinct
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import db_session
from .base import Base
from .event_tag import EventTag

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
  def types_with_counts(klass):
    types_with_counts = db_session.query(
      Tag.tag_type.label('chip_name'),
      func.count(distinct(EventTag.event_id)).label('ct')
    ).join(
      EventTag,
      EventTag.tag_id == Tag.tag_id
    ).group_by(
      Tag.tag_type
    )

    return [
      {
        'chip_name': tag_type,
        'ct': ct
      } for tag_type, ct in types_with_counts
    ]

  @property
  def count(self):
    return len(self.events)