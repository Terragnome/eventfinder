from sqlalchemy import Boolean, Column, ForeignKey, Integer
from sqlalchemy.orm import relationship, validates

from .base import Base

class UserEvent(Base):
  DONE = "done"
  GO = "go"
  MAYBE = "maybe"
  SKIP = "skip"

  INTERESTED = "interested" # Go and Maybe

  INTEREST_KEYS = {
    DONE: 3,
    GO: 2,
    MAYBE: 1,
    SKIP: 0
  }

  __tablename__ = 'user_events'
  event_id = Column(Integer, ForeignKey('events.event_id'), primary_key=True)
  user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
  interest = Column(Integer, nullable=True)

  event = relationship('Event', uselist=False)
  user = relationship('User', uselist=False)

  @classmethod
  def interest_keys(klass):
    return [
      klass.DONE,
      klass.GO,
      klass.MAYBE,
      klass.SKIP
    ]

  @classmethod
  def interest_chip_names(klass):
    return [
      klass.DONE,
      klass.INTERESTED,
      klass.SKIP
    ]

  @classmethod
  def interest_level(klass, key):
    for interest_key, interest_level in klass.INTEREST_KEYS.items():
      if interest_key == key: return interest_level
    return None

  @property
  def interest_key(self):
    if self.interest is not None:
      for interest_key, interest_level in self.INTEREST_KEYS.items():
        if self.interest >= interest_level: return interest_key
    return None

  @validates('interest')
  def validate_interest(self, key, val):
    assert (val is None or (val >=0 and val <=4))
    return val

  @property
  def is_done(self):
    return self.interest_key == self.DONE

  @property
  def is_go(self):
    return self.interest_key == self.GO

  @property
  def is_maybe(self):
    return self.interest_key == self.MAYBE

  @property
  def is_skip(self):
    return self.interest_key == self.SKIP

  @property
  def is_selected(self):
    return self.interest_key is not None