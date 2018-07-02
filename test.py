from model.base import session
from model.connector_event import ConnectorEvent
from model.event import Event

def run():
	session.query(ConnectorEvent).delete()
	session.query(Event).delete()
	session.commit()

if __name__ == "__main__":
	run()