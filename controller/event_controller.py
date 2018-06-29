from data.connector_eb import ConnectorEB, EBEventType

from model.base import session
from model.connector_event import ConnectorEvent
from model.event import Event

class EventController:
	def get_events(self):
		# ConnectorEB().get_events(
		# 	address='13960 Lynde Ave, Saratoga, CA 95070',
		# 	distance='100mi',
		# 	categories=EBEventType.FOOD_DRINK,
		# 	next_week=True
		# )
		events = session.query(Event).all()
		return events