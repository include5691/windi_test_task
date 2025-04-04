from ..base import Base
from sqlalchemy import Column, Integer, String, ForeignKey, ARRAY

class Group(Base):
    "It wasn't obvious in the terms of reference, so we consider groups to be channels"
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    members = Column(ARRAY(Integer))