from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

alembic_cfg = Config("./alembic.ini")
engine = create_engine(alembic_cfg.get_main_option("sqlalchemy.url"))
Session = sessionmaker(bind=engine)
db_session = Session()

class Base:
	def to_json(self):
		return {
			col.name: getattr(self, col.name) for col in self.__table__.columns
		}

Base = declarative_base(cls=Base)

from .auth import Auth
from .connector_event import ConnectorEvent
from .event import Event
from .squad import Squad
from .squad_invite import SquadInvite
from .squad_user import SquadUser
from .user import User
from .user_auth import UserAuth
from .user_event import UserEvent