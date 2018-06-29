from model.base import session
from model.connector_event import ConnectorEvent
from model.event import Event
from model.event_connector_event import EventConnectorEvent

def run():
	session.query(EventConnectorEvent).delete()
	session.query(ConnectorEvent).delete()
	session.query(Event).delete()
	session.commit()

if __name__ == "__main__":
	run()