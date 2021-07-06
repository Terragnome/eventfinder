from flask import current_app, session
from sqlalchemy import Column, ForeignKey, JSON, String
from sqlalchemy.orm import relationship
from sqlalchemy_json import NestedMutableJson

from .base import Base
from models.base import db_session
from models.event import Event
from models.event_tag import EventTag
from models.user_event import UserEvent
from models.tag import Tag

class ConnectorEvent(Base):
  TYPE = None

  __tablename__ = 'connector_events'
  connector_event_id = Column(String, primary_key=True)
  connector_type = Column(String, primary_key=True)
  data = Column(NestedMutableJson)

  event_id = Column(String, ForeignKey('events.event_id'))
  event = relationship('Event', uselist=False)

  @classmethod
  def create_key(self, name, city, *args):
    key_components = [name, city]
    key_components.extend(args or [])
    return " | ".join(key_components)

  @property
  def type(self):
    return self.TYPE

  @classmethod
  def all(klass):
    if klass.TYPE is None:
      current_app.logger.error("TYPE has not been set")
    return ConnectorEvent.query.filter(ConnectorEvent.connector_type == klass.TYPE)

  @classmethod
  def purge_events(klass):
    if klass.TYPE is None:
      current_app.logger.error("TYPE has not been set")
      return

    all_events = klass.all()
    if all_events:
      event_ids = [int(e.event_id) for e in all_events if e.event_id is not None ]

    EventTag.query.filter(EventTag.event_id.in_(event_ids)).delete(synchronize_session='fetch')
    UserEvent.query.filter(UserEvent.event_id.in_(event_ids)).delete(synchronize_session='fetch')
    ConnectorEvent.query.filter(ConnectorEvent.event_id.in_(event_ids)).delete(synchronize_session='fetch')
    Event.query.filter(Event.event_id.in_(event_ids)).delete(synchronize_session='fetch')
    db_session.commit()

  def sync(self, args):
    if 'purge' in args:
      if args['purge']:
        self.purge_events()
      del args['purge']

    events = self.extract(**args)
    if events:
      for i, entry in enumerate(events):
        event, debug_output = entry
        print(i, debug_output, "\n")

  def extract(self):
    return None