from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .base import Base

class SquadInvite(Base):
  __tablename__ = 'squad_invites'
  squad_id = Column(Integer, ForeignKey('squads.squad_id'), primary_key=True)
  email = Column(String, primary_key=True)
  user_id = Column(Integer, ForeignKey('users.user_id'))

  squad = relationship('Squad', uselist=False)
  user = relationship('User', uselist=False)

  @property
  def accepted(self):
    return self.user_id is not None
    