import asyncio
from fastapi import FastAPI
from app.core import settings
from app.api.endpoints import auth_router

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(auth_router, tags=["Authorization"])