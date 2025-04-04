from ..base import Base
from sqlalchemy import Column, Integer, ForeignKey

class UserChat(Base):
    "Represents the association table between users and chats."
    __tablename__ = "user_chats"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)