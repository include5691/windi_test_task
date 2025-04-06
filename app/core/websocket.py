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

    async def send_to_chat(self, message: dict, user_ids: list[int]):
        """
        Sends a message to all users in a chat. Send yourself as confirmation.
        """
        message = json.dumps(message)
        for user_id in user_ids:
            if user_id in self.active_connections:
                websockets = self.active_connections[user_id]
                for connection in list(websockets):
                    try:
                        await connection.send_text(message)
                    except Exception as e:
                        logging.error(f"Error sending message to user {user_id}: {e}. Removing connection.")
                        self.disconnect(connection, user_id)
    
    async def send_to_user(self, message: dict, user_id: int):
        """
        Sends a read notification to a specific user.
        """
        message = json.dumps(message)
        if user_id in self.active_connections:
            websockets = self.active_connections[user_id]
            for connection in list(websockets):
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logging.error(f"Error sending read notification to user {user_id}: {e}. Removing connection.")
                    self.disconnect(connection, user_id)

ws_manager = WebSocketManager()