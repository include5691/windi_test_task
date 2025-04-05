from pydantic import BaseModel, Field

class ChatBase(BaseModel):
    
    name: str = Field(..., title="Name of the chat")
    is_group: bool = Field(False, title="Is the chat a group chat")

class ChatCreate(ChatBase):

    recipient_id: int = Field(..., title="ID of the recipient user")

class ChatRead(ChatBase):
    id: int = Field(..., title="ID of the chat")
    
    class Config:
        from_attributes = True