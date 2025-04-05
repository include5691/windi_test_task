from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import User
from app.api.deps import get_async_session
from app.schemas import UserCreate, UserRead, Token
from app.core.security import hash_password, verify_password, create_access_token
from app.exceptions import UnauthorizedException

auth_router = APIRouter()

@auth_router.post("/register/", response_model=UserRead, status_code=status.HTTP_201_CREATED, summary="Register a new user")
async def register_user(
    user_in: UserCreate,
    session: AsyncSession = Depends(get_async_session)
):
    stmt = select(User).where(User.email == user_in.email)
    result = await session.execute(stmt)
    user = result.scalars().first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    user = User(
        email=user_in.email,
        name=user_in.name,
        hashed_password=hash_password(user_in.password)
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

@auth_router.post("/token/", response_model=Token, summary="Generate access token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_async_session)
):
    stmt = select(User).where(User.email == form_data.username)
    result = await session.execute(stmt)
    user = result.scalars().first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise UnauthorizedException(detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}