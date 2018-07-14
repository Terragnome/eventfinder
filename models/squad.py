from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from .base import Base

class Squad(Base):
  __tablename__ = 'squads'
  squad_id = Column(Integer, primary_key=True, autoincrement=True)
  name = Column(String, nullable=False)

  squad_invites = relationship('SquadInvite', cascade="all, delete-orphan")
  squad_users = relationship('SquadUser', cascade="all, delete-orphan")
  users = relationship('User', secondary='squad_users')