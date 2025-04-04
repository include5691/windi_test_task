import asyncio
from fastapi import FastAPI
from app.core import settings
from app.db import AsyncLocalSession, User

app = FastAPI(title=settings.PROJECT_NAME)
