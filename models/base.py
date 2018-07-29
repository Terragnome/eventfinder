from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

alembic_cfg = Config("./alembic.ini")
engine = create_engine(
  alembic_cfg.get_main_option("sqlalchemy.url"),
  convert_unicode = True
)
db_session = scoped_session(sessionmaker(bind=engine))

class Base:
  def to_json(self):
    return {
      col.name: getattr(self, col.name) for col in self.__table__.columns
    }

Base = declarative_base(cls=Base)
Base.query = db_session.query_property()

from .auth import Auth
from .block import Block
from .connector_event import ConnectorEvent
from .event import Event
from .follow import Follow
from .squad import Squad
from .squad_invite import SquadInvite
from .squad_user import SquadUser
from .user import User
from .user_auth import UserAuth
from .user_event import UserEvent