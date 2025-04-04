from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    PROJECT_NAME: str = "WinDi messages test task app"

    SECRET_KEY: str
    DATABASE_URL: str

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"


settings = Settings()