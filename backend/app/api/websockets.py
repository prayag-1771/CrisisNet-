import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json

logger = structlog.get_logger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for real-time dashboard updates."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("websocket_connected", total=len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("websocket_disconnected", total=len(self.active_connections))

    async def broadcast(self, event_type: str, data: dict):
        """Broadcast a typed event to all connected dashboard clients."""
        message = json.dumps({"type": event_type, "data": data})
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
        # Clean up dead connections
        for conn in disconnected:
            self.active_connections.remove(conn)
            logger.warning("removed_dead_websocket")

    async def send_personal(self, websocket: WebSocket, event_type: str, data: dict):
        """Send a message to a specific client."""
        await websocket.send_text(json.dumps({"type": event_type, "data": data}))


manager = ConnectionManager()


@router.websocket("/ws/feed")
async def websocket_feed(websocket: WebSocket):
    """
    WebSocket endpoint for real-time dashboard updates.
    Clients connect here to receive:
      - new_message: a new case entered the pipeline
      - classification_update: severity classification completed
      - queue_update: human review queue changed
      - resolution: a case was fully resolved
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive. The dashboard mostly listens.
            # We can also receive heartbeat pings from the client.
            data = await websocket.receive_text()
            if data == "ping":
                await manager.send_personal(websocket, "pong", {})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error("websocket_error", error=str(e))
        manager.disconnect(websocket)
