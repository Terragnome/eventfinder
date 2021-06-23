from flask import current_app

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy import distinct
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import db_session
from .base import Base
from .event_tag import EventTag

class Tag(Base):
  # Chip modes
  EXCLUSIVE = "exclusive"
  BOOLEAN = "boolean"

  TVM = "watch"
  FOOD_DRINK = "eat"
  GEAR = "acquire"
  ACTIVITY = "go"
  SERVICES = "services"

  TYPES = [
    TVM,
    FOOD_DRINK,
    GEAR,
    ACTIVITY,
    SERVICES
  ]

  ACCOLADES = "accolades"
  NEARBY = "nearby"
  OPEN_NOW = "open"
  FLAGS = [
    ACCOLADES,
    NEARBY,
    OPEN_NOW
  ]

  __tablename__ = 'tags'
  tag_id = Column(Integer, primary_key=True, autoincrement=True)
  tag_name = Column(String, nullable=False)
  tag_type = Column(String, nullable=False)
  created_at = Column(DateTime)
  updated_at = Column(DateTime)

  events = relationship('Event', secondary='event_tags')

  @classmethod
  def types(klass):
    return klass.TYPES

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

  @classmethod
  def get_tag(klass, tag_name, tag_type=None):
    tag_name = tag_name.lower()
    tag_type = tag_type.lower()
    
    tag_query = Tag.query.filter(Tag.tag_name == tag_name)
    if tag_type is not None:
      tag_query = row_tag.filter(Tag.tag_type == tag_type)
    return tag_query.first()

  @classmethod
  def create_tag(klass, tag_name, tag_type):
    tag_name = tag_name.lower()
    tag_type = tag_type.lower()

    row_tag = Tag.query.filter(
      Tag.tag_name == tag_name,
      Tag.tag_type == tag_type
    ).first()

    if not row_tag:
      row_tag = Tag(
        tag_name = tag_name,
        tag_type = tag_type
      )
      db_session.add(row_tag)
      db_session.commit()
    return row_tag