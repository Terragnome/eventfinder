from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .base import Base

class UserAuth(Base):
	__tablename__ = 'user_auths'
	user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True, unique=True)
	auth_key = Column(String, ForeignKey('auths.auth_key'), primary_key=True)
	auth_id = Column(String, primary_key=True)

	auth = relationship('Auth', uselist=False)
	user = relationship('User', uselist=False)