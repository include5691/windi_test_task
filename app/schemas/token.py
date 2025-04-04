from pydantic import BaseModel

class Token(BaseModel):
    "Token for OAuth2 token response"
    access_token: str
    token_type: str