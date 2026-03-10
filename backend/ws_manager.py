"""
Global WebSocket ConnectionManager for SideloadOS.

Singleton `manager` instance is imported wherever broadcast is needed.
"""

import json
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict) -> None:
        """Serialize dict to JSON and send to all connected clients."""
        data = json.dumps(message)
        for connection in list(self.active_connections):
            try:
                await connection.send_text(data)
            except Exception:
                self.active_connections.remove(connection)


manager = ConnectionManager()
