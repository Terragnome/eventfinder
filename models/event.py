from sqlalchemy import and_

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON
from sqlalchemy import orm
from sqlalchemy import String
from sqlalchemy.orm import relationship

from .base import Base
from .base import db_session
from .event_tag import EventTag
from .tag import Tag
from .user_event import UserEvent

class Event(Base):
  __tablename__ = 'events'
  event_id = Column(Integer, primary_key=True, autoincrement=True)
  name = Column(Integer, primary_key=True)
  description = Column(String)
  short_name = Column(String)
  img_url = Column(String)
  backdrop_url = Column(String)
  start_time = Column(DateTime)
  end_time = Column(DateTime)
  cost = Column(Integer)
  currency = Column(String)

  venue_name = Column(String)
  address = Column(JSON)
  city = Column(String)
  state = Column(String)
  latitude = Column(Float)
  longitude = Column(Float)

  link = Column(String)

  connector_events = relationship('ConnectorEvent', cascade="all,delete-orphan")
  tags = relationship('Tag', single_parent=True, secondary='event_tags', lazy='dynamic', cascade= "all,delete-orphan")
  user_events = relationship('UserEvent', cascade= "all,delete-orphan")
  users = relationship('User', secondary='user_events', lazy='dynamic')

  @orm.reconstructor
  def init_on_load(self):
    pass

  def chip_names(self):
    return self.category_names() | self.tag_names()

  def category_names(self):
    return set(t.tag_type for t in self.tags)

  def tag_names(self):
    return set(t.tag_name for t in self.tags)

  def add_tag(self, tag_name, tag_type):
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

    row_event_tag = self.tags.filter(Tag.tag_id == row_tag.tag_id).first()
    if not row_event_tag:
      row_event_tag = EventTag(
        event_id = self.event_id,
        tag_id = row_tag.tag_id
      )
      db_session.add(row_event_tag)
      db_session.commit()

  def remove_tag(self, tag_name):
    row_tag = Tag.query.filter(Tag.tag_name == tag_name).first()

    if row_tag:
      row_event_tag = self.tags.filter(Tag.tag_id == row_tag.tag_id).first()

      if row_event_tag:
        db_session.delete(row_event_tag)
        db_session.commit()

  def remove_all_tags(self):
    EventTag.query.filter(EventTag.event_id == self.event_id).delete()
    db_session.commit()

  @property
  def current_user_event(self):
    return self._current_user_event
  @current_user_event.setter
  def current_user_event(self, value):
    self._current_user_event = value

  @property
  def current_user_interested(self):
    return (
      self.current_user_event
      and self.current_user_event.interest != None
      and self.current_user_event.interest>0
    )

  @property
  def display_city(self):
    response = ""
    if self.city and self.state:
      return ", ".join([self.city, self.state])
    elif self.city:
      return self.city
    elif self.state:
      return self.state
    return response

  @property
  def display_end_date_day(self):
    return self.end_time.day

  @property
  def display_end_date_month(self):
    return self.end_time.strftime("%b")

  @property
  def display_start_date_day(self):
    return self.start_time.day

  @property
  def display_start_date_month(self):
    return self.start_time.strftime("%b")

  @property
  def display_name(self):
    return self.name

  @property
  def display_time(self):
    def format_date(t):
      return t.strftime("%a, %b %-d")

    def format_time(t):
      return t.strftime("%-I:%M%p").replace(":00", "")

    if self.start_time.isocalendar() == self.end_time.isocalendar():
      return " ".join([
        format_date(self.start_time),
        "@ {} - {}".format(
          format_time(self.start_time),
          format_time(self.end_time)
        )
      ])

    return " - ".join([
      "{} @ {}".format(
        format_date(self.start_time),
        format_time(self.start_time)
      ),
      "{} @ {}".format(
        format_date(self.end_time),
        format_time(self.end_time)
      )   
    ])

  @property
  def display_venue_name(self):
    return "" if self.venue_name in self.display_title else self.venue_name

  @property
  def start_date(self):
    return self.start_time.date()

  @property
  def end_date(self):
    return self.end_time.date()

  @property
  def interested_follows(self):
    return self._interested_follows
  @interested_follows.setter
  def interested_follows(self, value):
    self._interested_follows = value

  @property
  def interested_users(self):
    return self.users.filter(UserEvent.interest>0)

  @property
  def interested_user_count(self):
    return self._interested_user_count
  @interested_user_count.setter
  def interested_user_count(self, value):
    self._interested_user_count = value

  @property
  def is_free(self):
    return self.cost == 0