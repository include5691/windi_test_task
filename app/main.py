from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)

import asyncio
from fastapi import FastAPI
from app.core import settings
from app.api.endpoints import auth_router, chat_router, message_router

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(message_router)