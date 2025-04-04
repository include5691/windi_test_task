import logging
logging.basicConfig(level=logging.INFO)

import asyncio
from fastapi import FastAPI
from app.core import settings
from app.api.endpoints import auth_router, chat_router

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(auth_router, tags=["Authorization"])
app.include_router(chat_router, tags=["Chat"])