import logging
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_async_session
from app.db.models import Chat, UserChat, User
from app.api.deps import get_current_user
from app.schemas import ChatRead, ChatCreate

chat_router = APIRouter(prefix="/chats", tags=["Chat"])


@chat_router.get(
    "/",
    response_model=list[ChatRead],
    status_code=status.HTTP_200_OK,
    summary="Get all chats",
)
async def get_chats(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get all chats for the current user.
    """
    stmt = select(Chat).join(UserChat).where(UserChat.user_id == current_user.id)
    result = await session.execute(stmt)
    chats = result.scalars().all()
    return [ChatRead.model_validate(chat) for chat in chats]


@chat_router.post(
    "/",
    response_model=ChatRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new chat",
)
async def create_chat(
    chat_in: ChatCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Create a new chat.
    """
    if chat_in.recipient_id:
        if current_user.id == chat_in.recipient_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot create a chat with yourself",
            )
        stmt = select(User).where(User.id == chat_in.recipient_id)
        result = await session.execute(stmt)
        recipient = result.scalars().first()
        if not recipient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found"
            )

        # check for existing chat between current user and recipient
        uc1 = aliased(UserChat, name="user_chat_1")
        uc2 = aliased(UserChat, name="user_chat_2")
        stmt_find_existing = (
            select(Chat)
            .join(uc1, Chat.id == uc1.chat_id)
            .join(uc2, Chat.id == uc2.chat_id)
            .where(
                uc1.user_id == current_user.id,
                uc2.user_id == recipient.id,
                Chat.is_group == False,
            )
        )
        result_existing = await session.execute(stmt_find_existing)
        existing_chat = result_existing.scalars().first()
        if existing_chat:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A chat between you and user {recipient.id} already exists (ID: {existing_chat.id}).",
            )

        # create new chat
        chat = Chat(name=chat_in.name, is_group=False)
        session.add(chat)
        await session.commit()
        await session.refresh(chat)
        relation_1 = UserChat(user_id=current_user.id, chat_id=chat.id)
        relation_2 = UserChat(user_id=recipient.id, chat_id=chat.id)
        session.add(relation_1)
        session.add(relation_2)
        await session.commit()
        return chat
    elif chat_in.is_group:
        # check for existing group chat with the same name
        stmt = (
            select(Chat)
            .where(Chat.name == chat_in.name, Chat.is_group == True)
            .join(UserChat)
            .where(UserChat.user_id == current_user.id)
        )
        result = await session.execute(stmt)
        existing_chat = result.scalars().first()
        if existing_chat:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A group chat with the name '{chat_in.name}' already exists (ID: {existing_chat.id}).",
            )

        # create new group chat
        chat = Chat(name=chat_in.name, is_group=True)
        session.add(chat)
        await session.commit()
        await session.refresh(chat)

        # add current user to the group chat
        relation = UserChat(user_id=current_user.id, chat_id=chat.id)
        session.add(relation)
        await session.commit()
        return chat
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must specify either a recipient ID or group chat name.",
        )


@chat_router.post(
    "/{chat_id}/add-user",
    status_code=status.HTTP_200_OK,
    summary="Add user to chat",
)
async def add_user_to_chat(
    chat_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Add a user to a chat.
    """
    # Check if the chat exists
    stmt = select(Chat).where(Chat.id == chat_id)
    result = await session.execute(stmt)
    chat = result.scalars().first()
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
        )
    if chat.is_group is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot add users to a private chat",
        )

    # Check if the user exists
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Check if the current user is a member of the chat
    stmt = (
        select(UserChat)
        .where(UserChat.chat_id == chat_id, UserChat.user_id == current_user.id)
    )
    result = await session.execute(stmt)
    is_member = result.scalar_one_or_none()
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this chat",
        )

    # Check if the user is already a member of the chat
    stmt = (
        select(UserChat)
        .where(UserChat.chat_id == chat_id, UserChat.user_id == user.id)
    )
    result = await session.execute(stmt)
    is_member = result.scalar_one_or_none()
    if is_member:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this chat",
        )

    # Add the user to the chat
    relation = UserChat(user_id=user.id, chat_id=chat.id)
    session.add(relation)
    await session.commit()
    await session.refresh(chat)
    return {"detail": "User added to chat successfully"}


@chat_router.delete(
    "/{chat_id}/exit",
    status_code=status.HTTP_200_OK,
    summary="Exit a chat",
)
async def exit_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Exit a chat.
    """
    # Check if the chat exists
    stmt = select(Chat).where(Chat.id == chat_id)
    result = await session.execute(stmt)
    chat = result.scalars().first()
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
        )

    # Check if the user is a member of the chat
    stmt = (
        select(UserChat)
        .where(UserChat.chat_id == chat_id, UserChat.user_id == current_user.id)
    )
    result = await session.execute(stmt)
    is_member = result.scalar_one_or_none()
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this chat",
        )

    # Remove the user from the chat
    await session.delete(is_member)
    await session.commit()
    await session.refresh(chat)
    return {"detail": "User removed from chat successfully"}