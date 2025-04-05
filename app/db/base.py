import logging
from typing import AsyncGenerator
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

Base = declarative_base()

async_engine = create_async_engine(settings.DATABASE_URL)

AsyncLocalSession = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a new async session."""
    async with AsyncLocalSession() as session:
        try:
            yield session
        except Exception as e:
            logging.error(f"Error in session generator: {e}")
            await session.rollback()
            raise