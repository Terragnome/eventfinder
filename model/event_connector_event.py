from sqlalchemy import Column, ForeignKey, JSON, String
from sqlalchemy.orm import relationship

from .base import Base

class EventConnectorEvent(Base):
	__tablename__ = 'event_connector_events'
	event_id = Column(String, ForeignKey('events.event_id'), primary_key=True)
	connector_event_id = Column(String, ForeignKey('connector_events.connector_event_id'), primary_key=True)