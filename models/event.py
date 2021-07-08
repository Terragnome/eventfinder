from flask import current_app

from sqlalchemy import and_
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON
from sqlalchemy import orm
from sqlalchemy import String
from sqlalchemy.orm import relationship
from sqlalchemy_json import NestedMutableJson

from .base import Base
from .base import db_session
from .event_tag import EventTag
from .tag import Tag
from .user_event import UserEvent

from utils.get_from import get_from

class Event(Base):
  DETAILS_COST = "cost"
  DETAILS_PHONE = "phone"
  DETAILS_RATING = "rating"
  DETAILS_REVIEW_COUNT = "review_count"
  DETAILS_URL = "url"
  DETAILS_SPECIALTIES = "specialties"

  __tablename__ = 'events'
  event_id = Column(Integer, primary_key=True, autoincrement=True)
  alias = Column(String)

  name = Column(String)
  primary_type = Column(String)

  description = Column(JSON)
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

  urls = Column(NestedMutableJson)

  accolades = Column(NestedMutableJson)
  details = Column(NestedMutableJson)
  meta = Column(NestedMutableJson)

  connector_events = relationship('ConnectorEvent', cascade="all,delete-orphan")
  tags = relationship('Tag', single_parent=True, secondary='event_tags', lazy='dynamic', cascade= "all,delete-orphan")
  user_events = relationship('UserEvent', cascade= "all,delete-orphan")
  users = relationship('User', secondary='user_events', lazy='dynamic')

  @orm.reconstructor
  def init_on_load(self):
    pass

  def update_meta(self, meta_type, meta_data):
    if self.meta is None: self.meta = {}
    self.meta[meta_type] = meta_data

  def chip_names(self):
    return self.category_names() | self.tag_names()

  def category_names(self):
    return set(t.tag_type for t in self.tags)

  def tag_names(self):
    return set(t.tag_name for t in self.tags)

  def has_tag(self, tag_name=None, tag_type=None):
    row_tag = Tag.get_tag(tag_name, tag_type)
    if not row_tag:
      return False

    return self.tags.filter(Tag.id == row_tag.id).first() is not None

  def add_tag(self, tag_name, tag_type=None):
    if tag_name is None:
      return

    row_tag = Tag.create_tag(tag_name, tag_type)

    row_event_tag = self.tags.filter(Tag.tag_id == row_tag.tag_id).first()
    if not row_event_tag:
      row_event_tag = EventTag(
        event_id = self.event_id,
        tag_id = row_tag.tag_id
      )
      db_session.add(row_event_tag)
      db_session.commit()

  def remove_tag(self, tag_name, tag_type=None):
    row_tag = Tag.get_tag(tag_name, tag_type)

    if row_tag:
      row_event_tag = self.tags.filter(Tag.tag_id == row_tag.tag_id).first()

      if row_event_tag:
        db_session.delete(row_event_tag)
        db_session.commit()

  def remove_all_tags(self):
    EventTag.query.filter(EventTag.event_id == self.event_id).delete()
    db_session.commit()

  def add_url(self, url_type, url):
    if self.urls is None:
      self.urls = {}
    self.urls[url_type] = url
    db_session.merge(self)
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
  def website(self):
    return get_from(self.details, [Event.DETAILS_URL])
  
  @property
  def phone(self):
    from models.data.connect_google import ConnectGoogle
    from models.data.connect_yelp import ConnectYelp
    phone = None
    if not phone:
      phone = get_from(self.details, [ConnectGoogle.TYPE, Event.DETAILS_PHONE])
    if not phone:
      phone = get_from(self.details, [ConnectYelp.TYPE, Event.DETAILS_PHONE])
    return phone

  @property
  def display_address(self):
    addr_components = [x for x in [self.address, self.city, self.state] if x is not None and x != ""]
    return ", ".join(addr_components)


  @property
  def short_description(self):
    return [
      (
        reviewer,
        url,
        ". ".join([x.strip() for x in desc.split(".")[:3]]),
        ". ".join([x.strip() for x in desc.split(".")[:3]]) != desc
      ) for reviewer, url, desc in self.description
    ]

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
  def is_free(self):
    return self.cost == 0

  @property
  def card_interested_follows(self):
    return self._card_interested_follows
  @card_interested_follows.setter
  def card_interested_follows(self, value):
    self._card_interested_follows = value

  @property
  def card_user_count(self):
    return self._card_user_count
  @card_user_count.setter
  def card_user_count(self, value):
    self._card_user_count = value

  @property
  def card_event_users(self):
    return self._card_event_users
  @card_event_users.setter
  def card_event_users(self, value):
    self._card_event_users = value