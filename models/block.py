from sqlalchemy import Boolean, Column, ForeignKey, Integer
from sqlalchemy import and_, or_
from sqlalchemy.orm import relationship

from .base import Base
from .base import db_session

class Block(Base):
  __tablename__ = 'blocks'
  user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
  block_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
  active = Column(Boolean)

  @classmethod
  def blocks(klass, user_id_a, user_id_b):
    return db_session.query(Block).filter(
      and_(
        Block.active,
        or_(
          and_(
            Block.user_id == user_id_a,
            Block.block_id == user_id_b
          ),
          and_(
            Block.user_id == user_id_b,
            Block.block_id == user_id_a
          )
        )
      )
    ).first()