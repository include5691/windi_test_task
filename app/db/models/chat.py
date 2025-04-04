from ..base import Base
from sqlalchemy import Column, Integer, String, Boolean

class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    is_group = Column(Boolean)