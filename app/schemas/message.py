from pydantic import BaseModel, Field
from enum import StrEnum

class WebSocketCommand(StrEnum):
    SEND_MESSAGE = "SEND_MESSAGE"
    READ_MESSAGE = "READ_MESSAGE"


class MessageBase(BaseModel):
    chat_id: int = Field(..., description="Unique identifier for the chat")
    sender_id: int = Field(..., description="Unique identifier for the sender")
    text: str = Field(
        ..., min_length=1, max_length=500, description="Content of the message"
    )


class MessageCreate(MessageBase):
    pass


class MessageResponse(MessageBase):
    id: int = Field(..., description="Unique identifier for the message")
    timestamp: int = Field(..., description="Timestamp of when the message was sent")
    is_read: bool = Field(False, description="Read status of the message")

    class Config:
        from_attributes = True


class MessageReadNotification(BaseModel):
    id: int = Field(..., description="Unique identifier for the message")
    chat_id: int = Field(..., description="Unique identifier for the chat")
    command: str = Field(
        WebSocketCommand.READ_MESSAGE, description="Command to indicate read status"
    )

    class Config:
        from_attributes = True