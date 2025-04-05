from pydantic import BaseModel, Field

class MessageBase(BaseModel):
    chat_id: int = Field(..., description="Unique identifier for the chat")
    sender_id: int = Field(..., description="Unique identifier for the sender")
    text: str = Field(..., min_length=1, max_length=500, description="Content of the message")

class MessageCreate(MessageBase):
    pass

class MessageRead(MessageBase):
    id: int = Field(..., description="Unique identifier for the message")
    timestamp: int = Field(..., description="Timestamp of when the message was sent")
    is_read: bool = Field(..., description="Read status of the message")

    class Config:
        from_attributes = True