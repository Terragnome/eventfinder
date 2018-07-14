from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from .base import Base

class SquadUser(Base):
  __tablename__ = 'squad_users'
  squad_id = Column(Integer, ForeignKey('squads.squad_id'), primary_key=True)
  user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)

  squad = relationship('Squad', uselist=False)
  user = relationship('User', uselist=False)