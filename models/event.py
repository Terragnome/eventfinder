from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import JSON
from sqlalchemy import orm
from sqlalchemy import String
from sqlalchemy.orm import relationship

from .base import Base
from .user_event import UserEvent

class Event(Base):
  __tablename__ = 'events'
  event_id = Column(Integer, primary_key=True, autoincrement=True)
  name = Column(Integer, primary_key=True)
  description = Column(String)
  short_name = Column(String)
  img_url = Column(String)
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

  connector_events = relationship('ConnectorEvent')
  user_events = relationship('UserEvent')
  users = relationship(
    'User',
    secondary='user_events',
    lazy='dynamic'
  )

  @orm.reconstructor
  def init_on_load(self):
    pass

  @property
  def current_user_event(self):
    return self._current_user_event
  @current_user_event.setter
  def current_user_event(self, value):
    self._current_user_event = value

  @property
  def current_user_interested(self):
    return self.current_user_event and self.current_user_event.interested

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
    return self.venue_name if self.venue_name and len(self.venue_name)<=45 else self.display_city or ""  

  @property
  def interested_follows(self):
    return self._interested_follows
  @interested_follows.setter
  def interested_follows(self, value):
    self._interested_follows = value

  @property
  def interested_users(self):
    return self.users.filter(UserEvent.interested)

  @property
  def interested_user_count(self):
    return self._interested_user_count
  @interested_user_count.setter
  def interested_user_count(self, value):
    self._interested_user_count = value

  @property
  def is_free(self):
    return self.cost == 0