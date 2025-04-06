from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)

from fastapi import FastAPI, status
from app.core import settings
from app.api.endpoints import auth_router, chat_router, message_router

API_DESCRIPTION = """
API for a simple chat application featuring authentication, chat management, and real-time messaging via WebSockets.
"""
API_VERSION = "0.1.0"

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=API_DESCRIPTION,
    version=API_VERSION,
)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(message_router)
