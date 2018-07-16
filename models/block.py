from sqlalchemy import Boolean, Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from .base import Base

class Block(Base):
  __tablename__ = 'blocks'
  user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
  block_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
  active = Column(Boolean)