import logging
from datetime import datetime, timedelta, timezone
from jose import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import settings
from app.db.models import User

ph = PasswordHasher()

def hash_password(password: str) -> str:
    """
    Hash a password using Argon2.
    """
    return ph.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hashed password.
    """
    try:
        ph.verify(hashed_password, password)
        return True
    except VerifyMismatchError:
        return False
    except Exception as e:
        logging.error(f"An error occurred during password verification: {e}")
        return False

def create_access_token(data: dict) -> str:
    """
    Create access token
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

async def authenticate_user(session: AsyncSession, email: str, password: str) -> User | None:
    """
    Authenticate a user by email and password.
    """
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    user = result.scalars().first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user