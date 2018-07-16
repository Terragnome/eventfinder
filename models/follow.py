from sqlalchemy import Boolean, Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from .base import Base

class Follow(Base):
  __tablename__ = 'follows'
  user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
  follow_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
  active = Column(Boolean)