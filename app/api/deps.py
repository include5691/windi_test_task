import logging
from fastapi.security import OAuth2PasswordBearer
from fastapi import status, WebSocketException
from fastapi import Depends
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_async_session
from app.db.models import User
from app.exceptions import UnauthorizedException
from app.core import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


async def get_current_user(
    session: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme),
) -> User:
    """
    Get current user from token"
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email = payload.get("sub")
        if email is None:
            raise UnauthorizedException(detail="Invalid credentials")
    except JWTError:
        logging.error("JWTError: Invalid token")
        raise UnauthorizedException
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    user = result.scalars().first()
    if not user:
        logging.error("User not found")
        raise UnauthorizedException
    return user


async def get_current_user_from_token(token: str, session: AsyncSession) -> User:
    """
    Get current user from token for WebSocket connection.
    """
    credentials_exception = WebSocketException(
        code=status.WS_1008_POLICY_VIOLATION,
        reason="Invalid authentication credentials",
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email = payload.get("sub")
        if not email:
            logging.error(
                "JWTError: 'sub' (email) missing in WebSocket token payload."
            )
            raise credentials_exception
    except JWTError as e:
        logging.error(f"JWTError decoding WebSocket token: {e}")
        raise credentials_exception from e 
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    user = result.scalars().first()
    if not user:
        logging.warning(f"WebSocket Auth: User not found for email from token: {email}")
        raise credentials_exception
    return user
