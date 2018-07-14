from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from .base import Base

class Auth(Base):
  __tablename__ = 'auths'
  auth_key = Column(String, primary_key=True)
  auth_name = Column(String)

  GOOGLE = "google"