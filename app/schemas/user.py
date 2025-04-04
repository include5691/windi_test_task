from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="Name of the user")
    email: EmailStr = Field(..., description="Email address of the user")

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=128, description="Password for the user account")

class UserRead(UserBase):
    id: int = Field(..., description="Unique identifier for the user")
    
    class Config:
        from_attributes = True