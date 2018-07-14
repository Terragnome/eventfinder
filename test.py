from models.base import db_session
from models.connector_event import ConnectorEvent
from models.event import Event
from models.user import User

def run():
    row_user = db_session.query(User).first()

if __name__ == "__main__":
    run()