import logging
from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError
from app.db.base import get_async_session
from app.db.models import Chat, UserChat, User, Message
from app.api.deps import get_current_user, get_current_user_from_token
from app.schemas import ChatRead, ChatCreate, MessageCreate, MessageResponse, MessageReadNotification, WebSocketCommand
from app.core.websocket import ws_manager

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


@chat_router.websocket("/ws/{token}")
async def websocket_endpoint(
    websocket: WebSocket, token: str, session: AsyncSession = Depends(get_async_session)
):
    """
    WebSocket endpoint for real-time chat communication
    """
    user_id: int | None = None
    logging.info(f"WebSocket connection attempt with token: {token}")
    try:
        current_user = await get_current_user_from_token(token=token, session=session)
        user_id = current_user.id
        await ws_manager.connect(websocket, user_id)
        logging.info(f"User {user_id} connected to WebSocket")
        while True:
            data = await websocket.receive_json()
            command = data.get("command")
            payload = data.get("payload")
            if command == WebSocketCommand.SEND_MESSAGE:
                try:
                    message_in = MessageCreate(**payload, sender_id=user_id)
                except ValidationError as e:
                    logging.error(f"Validation error: {e}")
                    raise WebSocketException(
                        code=status.WS_1007_INVALID_PAYLOAD,
                        reason="Invalid message format",
                    )
                double_stmt = select(Message).where(Message.client_message_id == message_in.client_message_id)
                result = await session.execute(double_stmt)
                existing_message = result.scalars().first()
                if existing_message:
                    raise WebSocketException(
                        code=status.WS_1008_POLICY_VIOLATION,
                        reason=f"Duplicate message detected (Client ID: {message_in.client_message_id}).",
                    )
                chat_stmt = select(Chat).where(Chat.id == message_in.chat_id)
                result = await session.execute(chat_stmt)
                chat = result.scalars().first()
                if not chat:
                    raise WebSocketException(
                        code=status.WS_1007_INVALID_PAYLOAD,
                        reason="Chat not found",
                    )
                message = Message(**message_in.model_dump())
                session.add(message)
                await session.commit()
                await session.refresh(message)
                message_out = MessageResponse.model_validate(message)
                get_users_stmt = select(UserChat).where(
                    UserChat.chat_id == message.chat_id
                )
                result = await session.execute(get_users_stmt)
                user_chats = result.scalars().all()
                user_ids = [user_chat.user_id for user_chat in user_chats]
                await ws_manager.send_to_chat(message_out.model_dump_json(), user_ids)
                logging.info(
                    f"Message sent from user {user_id} to chat {message.chat_id}: {message.text}"
                )
            elif command == WebSocketCommand.READ_MESSAGE:
                message_id = payload.get("id")
                if not message_id:
                    raise WebSocketException(
                        code=status.WS_1007_INVALID_PAYLOAD,
                        reason="Message ID is required",
                    )
                read_stmt = select(Message).where(Message.id == message_id)
                result = await session.execute(read_stmt)
                message = result.scalars().first()
                if not message:
                    raise WebSocketException(
                        code=status.WS_1008_POLICY_VIOLATION,
                        reason="Message not found",
                    )
                if not message.is_read:
                    message.is_read = True
                    await session.commit()
                    await ws_manager.send_to_user(message=MessageReadNotification.model_validate(message).model_dump_json(), user_id=message.sender_id)
                    logging.info(
                        f"Message {message.id} marked as read by user {user_id} and notified sender {message.sender_id}"
                    )
    except WebSocketDisconnect:
        logging.info(f"WebSocket disconnected for user {user_id}.")
        if user_id:
            ws_manager.disconnect(websocket, user_id)
