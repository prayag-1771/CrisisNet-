from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        # Sends a JSON message to all connected clients
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                pass # Handle disconnected clients gracefully

manager = ConnectionManager()

@router.websocket("/ws/feed")
async def websocket_feed(websocket: WebSocket):
    """
    WebSocket endpoint for real-time dashboard updates.
    The frontend will connect here to receive updates about new messages,
    classifications, and queue changes.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection open. Dashboard mostly listens.
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
