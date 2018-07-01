from sqlalchemy import Column, ForeignKey, JSON, String
from sqlalchemy.orm import relationship

from .base import Base

class ConnectorEvent(Base):
	__tablename__ = 'connector_events'
	connector_event_id = Column(String, primary_key=True)
	connector_type = Column(String, primary_key=True)
	data = Column(JSON)

	event = relationship('Event', secondary='event_connector_events', uselist=False)