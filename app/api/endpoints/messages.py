import logging
from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
    Depends,
    status,
    HTTPException,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError
from app.db.base import get_async_session
from app.db.models import Chat, User, UserChat, Message
from app.api.deps import get_current_user_from_token, get_current_user
from app.schemas import (
    MessageCreate,
    MessageResponse,
    MessageReadNotification,
    WebSocketCommand,
)
from app.core.websocket import ws_manager

message_router = APIRouter(tags=["Message"])


@message_router.get(
    "/history/{chat_id}",
    response_model=list[MessageResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all messages in a chat",
)
async def get_messages(
    chat_id: int,
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    Get all messages in a chat.
    """
    chat_user_stmt = select(UserChat).where(
        UserChat.chat_id == chat_id,
        UserChat.user_id == current_user.id,
    )
    result = await session.execute(chat_user_stmt)
    chat_user = result.scalars().first()
    if not chat_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this chat",
        )
    message_stmt = (
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.timestamp.asc())
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(message_stmt)
    messages = result.scalars().all()
    return [MessageResponse.model_validate(message) for message in messages]


@message_router.websocket("/ws/{token}")
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
                double_stmt = select(Message).where(
                    Message.client_message_id == message_in.client_message_id
                )
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
                    await ws_manager.send_to_user(
                        message=MessageReadNotification.model_validate(
                            message
                        ).model_dump_json(),
                        user_id=message.sender_id,
                    )
                    logging.info(
                        f"Message {message.id} marked as read by user {user_id} and notified sender {message.sender_id}"
                    )
    except WebSocketDisconnect:
        logging.info(f"WebSocket disconnected for user {user_id}.")
        if user_id:
            ws_manager.disconnect(websocket, user_id)
