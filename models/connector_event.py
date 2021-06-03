from flask import current_app, session
from sqlalchemy import Column, ForeignKey, JSON, String
from sqlalchemy.orm import relationship

from .base import Base
from models.base import db_session
from models.event import Event
from models.event_tag import EventTag
from models.user_event import UserEvent
from models.tag import Tag

class ConnectorEvent(Base):
  CONNECTOR_TYPE = None

  __tablename__ = 'connector_events'
  connector_event_id = Column(String, primary_key=True)
  connector_type = Column(String, primary_key=True)
  data = Column(JSON)
  event_id = Column(String, ForeignKey('events.event_id'))

  event = relationship('Event', uselist=False)

  @classmethod
  def all(klass):
    return ConnectorEvent.query.filter(ConnectorEvent.connector_type == klass.CONNECTOR_TYPE)

  @classmethod
  def purge_events(klass):
    if klass.CONNECTOR_TYPE is None:
      current_app.logger.error("Must define CONNECTOR_TYPE")
      return

    event_ids = [int(e.event_id) for e in klass.all()]

    EventTag.query.filter(EventTag.event_id.in_(event_ids)).delete(synchronize_session='fetch')
    UserEvent.query.filter(UserEvent.event_id.in_(event_ids)).delete(synchronize_session='fetch')
    ConnectorEvent.query.filter(ConnectorEvent.event_id.in_(event_ids)).delete(synchronize_session='fetch')
    Event.query.filter(Event.event_id.in_(event_ids)).delete(synchronize_session='fetch')
    db_session.commit()