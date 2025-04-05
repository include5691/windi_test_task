from ..base import Base
import time
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(String, nullable=False)
    timestamp = Column(Integer, nullable=False, default=time.time)
    is_read = Column(Boolean, default=False)