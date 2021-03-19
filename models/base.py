from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

import os
db_url = os.getenv('DATABASE_URL', 'postgresql://root:root@postgres/eventfinder')

engine = create_engine(db_url, convert_unicode = True)
db_session = scoped_session(sessionmaker(bind=engine))

class Base:
  @property
  def json(self):
    return self.to_json()

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
from .event_tag import EventTag
from .follow import Follow
from .squad import Squad
from .squad_invite import SquadInvite
from .squad_user import SquadUser
from .tag import Tag
from .user import User
from .user_auth import UserAuth
from .user_event import UserEvent