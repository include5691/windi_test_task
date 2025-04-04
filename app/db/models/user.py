from ..base import Base
from sqlalchemy import Column, Integer, String

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    name = Column(String, index=True)
    hashed_password = Column(String, nullable=False)