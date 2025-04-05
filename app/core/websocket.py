import logging
import json
from fastapi import WebSocket

class WebSocketManager:
    
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            user_connections = self.active_connections[user_id]
            if websocket in user_connections:
                user_connections.remove(websocket)
                if not user_connections:
                    del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: int):
        "Sends a message to a specific user"
        if user_id in self.active_connections:
            websockets = self.active_connections[user_id]
            message_json = json.dumps(message) # Сериализуем один раз
            for connection in list(websockets):
                try:
                    await connection.send_text(message_json)
                except Exception as e:
                    logging.error(f"Error sending message to user {user_id}: {e}. Removing connection.")
                    self.disconnect(connection, user_id)

    async def broadcast_to_chat(self, message: dict, chat_id: int, sender_id: int, user_ids: list[int]):
        "Sends a message to all users in a group chat"
        message_json = json.dumps(message)
        for user_id in user_ids:
            if user_id == sender_id:
                continue
            if user_id in self.active_connections:
                websockets = self.active_connections[user_id]
                for connection in list(websockets):
                    try:
                        await connection.send_text(message_json)
                    except Exception as e:
                        logging.error(f"Error broadcasting to user {user_id} in chat {chat_id}: {e}. Removing connection.")
                        self.disconnect(connection, user_id)

ws_manager = WebSocketManager()