#!/usr/bin/env python3
"""
WebSocket Manager Implementation

Ez a modul implementálja a WebSocket kapcsolatok kezelését:
- Connection management
- Session tracking
- Message routing
- Redis session cache integráció
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict

from fastapi import WebSocket, WebSocketDisconnect
from src.config.logging import get_logger
from src.integrations.cache.redis_cache import get_redis_cache_service
from src.models.chat import ChatMessage, ChatSession, WebSocketMessage, ChatError, MessageType
from src.workflows.coordinator import process_coordinator_message
from src.models.user import User

logger = get_logger(__name__)


@dataclass
class WebSocketConnection:
    """WebSocket kapcsolat adatai"""
    websocket: WebSocket
    session_id: str
    user_id: Optional[str] = None
    connected_at: datetime = None
    last_activity: datetime = None
    client_info: Dict[str, Any] = None
    is_active: bool = True
    
    def __post_init__(self):
        if self.connected_at is None:
            self.connected_at = datetime.now(timezone.utc)
        if self.last_activity is None:
            self.last_activity = datetime.now(timezone.utc)
        if self.client_info is None:
            self.client_info = {}


class WebSocketManager:
    """WebSocket kapcsolatok kezelője"""
    
    def __init__(self):
        """Inicializálja a WebSocket manager-t"""
        self.active_connections: Dict[str, WebSocketConnection] = {}
        self.session_connections: Dict[str, Set[str]] = {}  # session_id -> connection_ids
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self._lock = asyncio.Lock()
        
    async def connect(self, websocket: WebSocket, session_id: str, user_id: Optional[str] = None) -> str:
        """
        Új WebSocket kapcsolat hozzáadása
        
        Args:
            websocket: WebSocket objektum
            session_id: Session azonosító
            user_id: Felhasználó azonosító (opcionális)
            
        Returns:
            Connection ID
        """
        connection_id = str(uuid.uuid4())
        
        # Client információk összegyűjtése
        client_info = {
            "ip_address": websocket.client.host if websocket.client else None,
            "user_agent": websocket.headers.get("user-agent"),
            "accept_language": websocket.headers.get("accept-language"),
            "connection_id": connection_id
        }
        
        connection = WebSocketConnection(
            websocket=websocket,
            session_id=session_id,
            user_id=user_id,
            client_info=client_info
        )
        
        async with self._lock:
            # Kapcsolat hozzáadása
            self.active_connections[connection_id] = connection
            
            # Session kapcsolatok frissítése
            if session_id not in self.session_connections:
                self.session_connections[session_id] = set()
            self.session_connections[session_id].add(connection_id)
            
            # User kapcsolatok frissítése (ha van user_id)
            if user_id:
                if user_id not in self.user_connections:
                    self.user_connections[user_id] = set()
                self.user_connections[user_id].add(connection_id)
        
        logger.info(f"WebSocket kapcsolat létrehozva: {connection_id} (session: {session_id}, user: {user_id})")
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """
        WebSocket kapcsolat eltávolítása
        
        Args:
            connection_id: Kapcsolat azonosító
        """
        async with self._lock:
            if connection_id in self.active_connections:
                connection = self.active_connections[connection_id]
                
                # Session kapcsolatok frissítése
                if connection.session_id in self.session_connections:
                    self.session_connections[connection.session_id].discard(connection_id)
                    if not self.session_connections[connection.session_id]:
                        del self.session_connections[connection.session_id]
                
                # User kapcsolatok frissítése
                if connection.user_id and connection.user_id in self.user_connections:
                    self.user_connections[connection.user_id].discard(connection_id)
                    if not self.user_connections[connection.user_id]:
                        del self.user_connections[connection.user_id]
                
                # Kapcsolat eltávolítása
                del self.active_connections[connection_id]
                
                logger.info(f"WebSocket kapcsolat lezárva: {connection_id}")
    
    async def send_personal_message(self, message: Dict[str, Any], connection_id: str) -> bool:
        """
        Üzenet küldése egy adott kapcsolatnak
        
        Args:
            message: Küldendő üzenet
            connection_id: Kapcsolat azonosító
            
        Returns:
            Sikeres küldés esetén True
        """
        if connection_id not in self.active_connections:
            logger.warning(f"Kapcsolat nem található: {connection_id}")
            return False
        
        try:
            connection = self.active_connections[connection_id]
            await connection.websocket.send_json(message)
            connection.last_activity = datetime.now(timezone.utc)
            return True
        except Exception as e:
            logger.error(f"Hiba az üzenet küldésekor {connection_id}: {e}")
            await self.disconnect(connection_id)
            return False
    
    async def send_to_session(self, message: Dict[str, Any], session_id: str) -> int:
        """
        Üzenet küldése egy session összes kapcsolatának
        
        Args:
            message: Küldendő üzenet
            session_id: Session azonosító
            
        Returns:
            Sikeresen elküldött üzenetek száma
        """
        if session_id not in self.session_connections:
            return 0
        
        sent_count = 0
        connection_ids = list(self.session_connections[session_id])
        
        for connection_id in connection_ids:
            if await self.send_personal_message(message, connection_id):
                sent_count += 1
        
        return sent_count
    
    async def send_to_user(self, message: Dict[str, Any], user_id: str) -> int:
        """
        Üzenet küldése egy felhasználó összes kapcsolatának
        
        Args:
            message: Küldendő üzenet
            user_id: Felhasználó azonosító
            
        Returns:
            Sikeresen elküldött üzenetek száma
        """
        if user_id not in self.user_connections:
            return 0
        
        sent_count = 0
        connection_ids = list(self.user_connections[user_id])
        
        for connection_id in connection_ids:
            if await self.send_personal_message(message, connection_id):
                sent_count += 1
        
        return sent_count
    
    async def broadcast(self, message: Dict[str, Any]) -> int:
        """
        Üzenet küldése minden aktív kapcsolatnak
        
        Args:
            message: Küldendő üzenet
            
        Returns:
            Sikeresen elküldött üzenetek száma
        """
        sent_count = 0
        connection_ids = list(self.active_connections.keys())
        
        for connection_id in connection_ids:
            if await self.send_personal_message(message, connection_id):
                sent_count += 1
        
        return sent_count
    
    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """
        Kapcsolat információk lekérése
        
        Args:
            connection_id: Kapcsolat azonosító
            
        Returns:
            Kapcsolat információk vagy None
        """
        if connection_id not in self.active_connections:
            return None
        
        connection = self.active_connections[connection_id]
        return {
            "connection_id": connection_id,
            "session_id": connection.session_id,
            "user_id": connection.user_id,
            "connected_at": connection.connected_at.isoformat(),
            "last_activity": connection.last_activity.isoformat(),
            "client_info": connection.client_info
        }
    
    def get_session_connections(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Session kapcsolatok lekérése
        
        Args:
            session_id: Session azonosító
            
        Returns:
            Kapcsolat információk listája
        """
        if session_id not in self.session_connections:
            return []
        
        connections = []
        for connection_id in self.session_connections[session_id]:
            info = self.get_connection_info(connection_id)
            if info:
                connections.append(info)
        
        return connections
    
    def get_user_connections(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Felhasználó kapcsolatok lekérése
        
        Args:
            user_id: Felhasználó azonosító
            
        Returns:
            Kapcsolat információk listája
        """
        if user_id not in self.user_connections:
            return []
        
        connections = []
        for connection_id in self.user_connections[user_id]:
            info = self.get_connection_info(connection_id)
            if info:
                connections.append(info)
        
        return connections
    
    def get_stats(self) -> Dict[str, Any]:
        """
        WebSocket manager statisztikák
        
        Returns:
            Statisztikai információk
        """
        return {
            "total_connections": len(self.active_connections),
            "total_sessions": len(self.session_connections),
            "total_users": len(self.user_connections),
            "sessions": {
                session_id: len(connections) 
                for session_id, connections in self.session_connections.items()
            },
            "users": {
                user_id: len(connections) 
                for user_id, connections in self.user_connections.items()
            }
        }


class ChatWebSocketHandler:
    """Chat WebSocket üzenetek kezelője"""
    
    def __init__(self, websocket_manager: WebSocketManager):
        """Inicializálja a chat WebSocket handler-t"""
        self.websocket_manager = websocket_manager
        self.redis_cache_service = None
    
    async def initialize(self):
        """Handler inicializálása"""
        self.redis_cache_service = await get_redis_cache_service()
    
    async def handle_message(self, websocket: WebSocket, connection_id: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Chat üzenet feldolgozása
        
        Args:
            websocket: WebSocket objektum
            connection_id: Kapcsolat azonosító
            message_data: Üzenet adatok
            
        Returns:
            Válasz üzenet
        """
        try:
            # Üzenet validálása
            if "type" not in message_data:
                return self._create_error_response("missing_type", "Üzenet típusa hiányzik")
            
            message_type = message_data.get("type")
            
            if message_type == "chat_message":
                return await self._handle_chat_message(websocket, connection_id, message_data)
            elif message_type == "ping":
                return self._create_pong_response()
            elif message_type == "session_info":
                return await self._handle_session_info_request(connection_id, message_data)
            else:
                return self._create_error_response("unknown_type", f"Ismeretlen üzenet típus: {message_type}")
                
        except Exception as e:
            logger.error(f"Hiba az üzenet feldolgozásakor: {e}")
            return self._create_error_response("processing_error", "Üzenet feldolgozási hiba")
    
    async def _handle_chat_message(self, websocket: WebSocket, connection_id: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Chat üzenet feldolgozása"""
        try:
            # Üzenet adatok kinyerése
            content = message_data.get("content", "").strip()
            session_id = message_data.get("session_id")
            user_id = message_data.get("user_id")
            
            if not content:
                return self._create_error_response("empty_message", "Üzenet tartalma nem lehet üres")
            
            if not session_id:
                return self._create_error_response("missing_session", "Session azonosító hiányzik")
            
            # Session validálása/cache-ből betöltése
            session = await self._get_or_create_session(session_id, user_id, websocket)
            
            # Chat üzenet létrehozása
            chat_message = ChatMessage(
                id=str(uuid.uuid4()),
                session_id=session_id,
                type=MessageType.USER,
                content=content,
                metadata={
                    "connection_id": connection_id,
                    "client_info": self.websocket_manager.get_connection_info(connection_id)
                }
            )
            
            # Üzenet mentése a session-be
            session.messages.append(chat_message)
            session.last_activity = datetime.now(timezone.utc)
            
            # Session cache frissítése
            await self._update_session_cache(session)
            
            # Koordinátor agent hívása (streaming)
            try:
                user = None
                if user_id:
                    user = User(id=user_id, email="user@example.com")  # Placeholder
                
                full_response_content = ""
                async for agent_response_chunk in process_coordinator_message(
                    message=content,
                    user=user,
                    session_id=session_id
                ):
                    # Válasz üzenet létrehozása (JSON-serializable metadata-val)
                    safe_metadata = {}
                    if agent_response_chunk.metadata:
                        for key, value in agent_response_chunk.metadata.items():
                            # Filter out non-serializable objects
                            if isinstance(value, (str, int, float, bool, type(None), list, dict)):
                                safe_metadata[key] = value
                            else:
                                safe_metadata[key] = str(value)  # Convert to string for serialization
                    
                    # Send each chunk as a streaming response
                    await websocket.send_json({
                        "type": "chat_response_chunk",
                        "data": {
                            "content_chunk": agent_response_chunk.response_text,
                            "agent_type": str(agent_response_chunk.agent_type.value) if agent_response_chunk.agent_type else "unknown",
                            "confidence": float(agent_response_chunk.confidence) if agent_response_chunk.confidence else 0.0,
                            "metadata": safe_metadata
                        },
                        "session_id": session_id,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    full_response_content += agent_response_chunk.response_text

                # After streaming, save the full response to session
                response_message = ChatMessage(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    type=MessageType.ASSISTANT,
                    content=full_response_content,
                    metadata={
                        "agent_type": str(agent_response_chunk.agent_type.value) if agent_response_chunk.agent_type else "unknown",
                        "confidence": float(agent_response_chunk.confidence) if agent_response_chunk.confidence else 0.0,
                        "processing_time": float(agent_response_chunk.processing_time) if agent_response_chunk.processing_time else 0.0,
                        **safe_metadata
                    }
                )
                session.messages.append(response_message)
                await self._update_session_cache(session)

                # Send a final backward-compatible message for tests and legacy clients
                final_response = {
                    "type": "chat_response",
                    "data": {
                        "content": full_response_content,
                        "agent_type": str(agent_response_chunk.agent_type.value) if agent_response_chunk.agent_type else "unknown",
                        "confidence": float(agent_response_chunk.confidence) if agent_response_chunk.confidence else 0.0,
                        "metadata": safe_metadata,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    },
                    "session_id": session_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                # Send both the final response and the completion message
                await websocket.send_json(final_response)
                return {"type": "chat_response_complete", "session_id": session_id, "timestamp": datetime.now(timezone.utc).isoformat() }

            except Exception as e:
                logger.error(f"Hiba a coordinator agent hívásakor: {e}")
                return self._create_error_response("agent_error", "Agent feldolgozási hiba")
            
        except Exception as e:
            logger.error(f"Hiba a chat üzenet feldolgozásakor: {e}")
            return self._create_error_response("chat_error", "Chat feldolgozási hiba")
    
    async def _handle_session_info_request(self, connection_id: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Session információk lekérése"""
        connection_info = self.websocket_manager.get_connection_info(connection_id)
        if not connection_info:
            return self._create_error_response("connection_not_found", "Kapcsolat nem található")
        
        session_id = connection_info["session_id"]
        session = await self._get_session_from_cache(session_id)
        
        return {
            "type": "session_info",
            "data": {
                "session_id": session_id,
                "user_id": connection_info["user_id"],
                "connected_at": connection_info["connected_at"],
                "last_activity": connection_info["last_activity"],
                "message_count": len(session.messages) if session else 0,
                "client_info": connection_info["client_info"]
            },
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _create_pong_response(self) -> Dict[str, Any]:
        """Pong válasz létrehozása"""
        return {
            "type": "pong",
            "data": {
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _create_error_response(self, error_type: str, error_message: str) -> Dict[str, Any]:
        """Hiba válasz létrehozása"""
        return {
            "type": "error",
            "data": {
                "error_type": error_type,
                "error_message": error_message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def _get_or_create_session(self, session_id: str, user_id: Optional[str], websocket: WebSocket) -> ChatSession:
        """Session lekérése vagy létrehozása"""
        # Először cache-ből próbáljuk betölteni
        session = await self._get_session_from_cache(session_id)
        
        if not session:
            # Új session létrehozása
            session = ChatSession(
                session_id=session_id,
                user_id=user_id,
                context={
                    "client_info": {
                        "ip_address": websocket.client.host if websocket.client else None,
                        "user_agent": websocket.headers.get("user-agent")
                    }
                }
            )
        
        return session
    
    async def _get_session_from_cache(self, session_id: str) -> Optional[ChatSession]:
        """Session lekérése cache-ből"""
        if not self.redis_cache_service:
            return None
        
        try:
            session_data = await self.redis_cache_service.session_cache.get_session(session_id)
            if session_data and isinstance(session_data, dict):  # Ellenőrizzük a típust
                # Biztonságos deserializáció dict-ből
                return ChatSession(
                    session_id=session_data.get("session_id"),
                    user_id=session_data.get("user_id"),
                    started_at=session_data.get("started_at"),
                    last_activity=session_data.get("last_activity"),
                    context=session_data.get("context", {}),
                    is_active=session_data.get("is_active", True),
                    messages=[]  # TODO: Messages cache-ből betöltése
                )
            elif session_data and hasattr(session_data, 'session_id'):
                # Ha SessionData objektum
                return ChatSession(
                    session_id=session_data.session_id,
                    user_id=session_data.user_id,
                    started_at=session_data.started_at,
                    last_activity=session_data.last_activity,
                    context=session_data.context,
                    is_active=session_data.is_active,
                    messages=[]  # TODO: Messages cache-ből betöltése
                )
        except Exception as e:
            logger.error(f"Hiba a session cache-ből való betöltésekor: {e}")
        
        return None
    
    async def _update_session_cache(self, session: ChatSession):
        """Session cache frissítése"""
        if not self.redis_cache_service:
            return
        
        try:
            # SessionData létrehozása
            from src.integrations.cache.redis_cache import SessionData
            session_data = SessionData(
                session_id=session.session_id,
                user_id=session.user_id or "anonymous",
                started_at=session.started_at,
                last_activity=session.last_activity,
                context=session.context,
                is_active=session.is_active
            )
            
            await self.redis_cache_service.session_cache.update_session(session.session_id, session_data)
        except Exception as e:
            logger.error(f"Hiba a session cache frissítésekor: {e}")


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
chat_handler = ChatWebSocketHandler(websocket_manager) 