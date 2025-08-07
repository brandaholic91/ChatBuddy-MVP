import asyncio
import json
from typing import AsyncGenerator, Dict, Any

class WebSocketHandler:
    """
    Handles WebSocket connections and streaming responses to connected clients.
    """
    def __init__(self):
        self.active_connections: Dict[str, Any] = {} # Stores active WebSocket connections

    async def connect(self, websocket, client_id: str):
        """
        Establishes a new WebSocket connection and adds it to active connections.
        """
        self.active_connections[client_id] = websocket
        try:
            # Keep the connection open
            while True:
                await websocket.receive_text()
        except Exception as e:
            print(f"WebSocket connection closed for client {client_id}: {e}")
        finally:
            await self.disconnect(client_id)

    async def disconnect(self, client_id: str):
        """
        Removes a WebSocket connection from active connections.
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            print(f"Client {client_id} disconnected.")

    async def stream_response(self, client_id: str, response_generator: AsyncGenerator[str, None]):
        """
        Streams a response from an async generator to a specific client.
        Each chunk from the generator is sent as a WebSocket message.
        """
        websocket = self.active_connections.get(client_id)
        if not websocket:
            print(f"No active WebSocket connection found for client {client_id}.")
            return

        try:
            async for chunk in response_generator:
                await websocket.send_text(json.dumps({"type": "stream_chunk", "data": chunk}))
            await websocket.send_text(json.dumps({"type": "stream_end"}))
        except Exception as e:
            print(f"Error streaming response to client {client_id}: {e}")
            await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
        finally:
            # Consider if connection should be closed or kept open for subsequent messages
            pass

    async def send_message(self, client_id: str, message: Dict[str, Any]):
        """
        Sends a single JSON message to a specific client.
        """
        websocket = self.active_connections.get(client_id)
        if not websocket:
            print(f"No active WebSocket connection found for client {client_id}.")
            return
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            print(f"Error sending message to client {client_id}: {e}")

websocket_handler = WebSocketHandler()
