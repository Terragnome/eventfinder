from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

alembic_cfg = Config("./alembic.ini")
engine = create_engine(alembic_cfg.get_main_option("sqlalchemy.url"))
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()

from .connector_event import ConnectorEvent
from .event import Event
from .event_connector_event import EventConnectorEvent