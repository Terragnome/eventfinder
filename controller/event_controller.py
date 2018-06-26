from data.connector_eb import ConnectorEB, EBEventType

class EventController:
	def get_events(self):
		events = ConnectorEB().get_events(
			address='13960 Lynde Ave, Saratoga, CA 95070',
			distance='100mi',
			categories=EBEventType.FOOD_DRINK
		)
		return events