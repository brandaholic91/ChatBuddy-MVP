#!/usr/bin/env python3
"""
Egyszerű WebSocket tesztek

Ez a modul teszteli a WebSocket funkcionalitást a FastAPI alkalmazás nélkül:
- WebSocket manager működése
- Chat handler működése
- Üzenet feldolgozás
"""

import pytest
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from src.integrations.websocket_manager import WebSocketManager, ChatWebSocketHandler, WebSocketConnection
from src.models.chat import ChatMessage, ChatSession, MessageType


class TestWebSocketManagerSimple:
    """Egyszerű WebSocket manager tesztek"""
    
    @pytest.fixture
    def websocket_manager(self):
        """WebSocket manager létrehozása"""
        return WebSocketManager()
    
    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket objektum"""
        websocket = MagicMock()
        websocket.client.host = "127.0.0.1"
        websocket.headers.get.return_value = "test-user-agent"
        return websocket
    
    @pytest.fixture
    def session_id(self):
        """Teszt session ID"""
        return str(uuid.uuid4())
    
    @pytest.fixture
    def user_id(self):
        """Teszt user ID"""
        return "test_user_123"
    
    def test_websocket_manager_initialization(self, websocket_manager):
        """WebSocket manager inicializálásának tesztje"""
        assert websocket_manager is not None
        assert hasattr(websocket_manager, 'active_connections')
        assert hasattr(websocket_manager, 'session_connections')
        assert hasattr(websocket_manager, 'user_connections')
        assert len(websocket_manager.active_connections) == 0
    
    def test_websocket_manager_stats(self, websocket_manager):
        """WebSocket manager statisztikák tesztje"""
        stats = websocket_manager.get_stats()
        
        assert "total_connections" in stats
        assert "total_sessions" in stats
        assert "total_users" in stats
        assert "sessions" in stats
        assert "users" in stats
        
        assert isinstance(stats["total_connections"], int)
        assert isinstance(stats["total_sessions"], int)
        assert isinstance(stats["total_users"], int)
        assert isinstance(stats["sessions"], dict)
        assert isinstance(stats["users"], dict)
        
        assert stats["total_connections"] == 0
        assert stats["total_sessions"] == 0
        assert stats["total_users"] == 0
    
    @pytest.mark.asyncio
    async def test_websocket_connection_creation(self, websocket_manager, mock_websocket, session_id, user_id):
        """WebSocket kapcsolat létrehozásának tesztje"""
        connection_id = await websocket_manager.connect(mock_websocket, session_id, user_id)
        
        assert connection_id is not None
        assert len(connection_id) > 0
        assert connection_id in websocket_manager.active_connections
        
        connection = websocket_manager.active_connections[connection_id]
        assert connection.session_id == session_id
        assert connection.user_id == user_id
        assert connection.websocket == mock_websocket
    
    @pytest.mark.asyncio
    async def test_websocket_connection_disconnect(self, websocket_manager, mock_websocket, session_id, user_id):
        """WebSocket kapcsolat lezárásának tesztje"""
        connection_id = await websocket_manager.connect(mock_websocket, session_id, user_id)
        
        # Kapcsolat eltávolítása
        await websocket_manager.disconnect(connection_id)
        
        assert connection_id not in websocket_manager.active_connections
        assert session_id not in websocket_manager.session_connections
        assert user_id not in websocket_manager.user_connections
    
    @pytest.mark.asyncio
    async def test_websocket_session_connections(self, websocket_manager, mock_websocket, session_id):
        """Session kapcsolatok tesztje"""
        connection_id = await websocket_manager.connect(mock_websocket, session_id)
        
        assert session_id in websocket_manager.session_connections
        assert connection_id in websocket_manager.session_connections[session_id]
        
        session_connections = websocket_manager.get_session_connections(session_id)
        assert len(session_connections) == 1
        assert session_connections[0]["connection_id"] == connection_id
        assert session_connections[0]["session_id"] == session_id
    
    @pytest.mark.asyncio
    async def test_websocket_user_connections(self, websocket_manager, mock_websocket, session_id, user_id):
        """User kapcsolatok tesztje"""
        connection_id = await websocket_manager.connect(mock_websocket, session_id, user_id)
        
        assert user_id in websocket_manager.user_connections
        assert connection_id in websocket_manager.user_connections[user_id]
        
        user_connections = websocket_manager.get_user_connections(user_id)
        assert len(user_connections) == 1
        assert user_connections[0]["connection_id"] == connection_id
        assert user_connections[0]["user_id"] == user_id
    
    @pytest.mark.asyncio
    async def test_websocket_connection_info(self, websocket_manager, mock_websocket, session_id, user_id):
        """Kapcsolat információk tesztje"""
        connection_id = await websocket_manager.connect(mock_websocket, session_id, user_id)
        
        info = websocket_manager.get_connection_info(connection_id)
        assert info is not None
        assert info["connection_id"] == connection_id
        assert info["session_id"] == session_id
        assert info["user_id"] == user_id
        assert "connected_at" in info
        assert "last_activity" in info
        assert "client_info" in info


class TestChatWebSocketHandlerSimple:
    """Egyszerű Chat WebSocket handler tesztek"""
    
    @pytest.fixture
    def websocket_manager(self):
        """WebSocket manager létrehozása"""
        return WebSocketManager()
    
    @pytest.fixture
    def chat_handler(self, websocket_manager):
        """Chat handler létrehozása"""
        return ChatWebSocketHandler(websocket_manager)
    
    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket objektum"""
        websocket = MagicMock()
        websocket.client.host = "127.0.0.1"
        websocket.headers.get.return_value = "test-user-agent"
        return websocket
    
    def test_chat_handler_initialization(self, chat_handler):
        """Chat handler inicializálásának tesztje"""
        assert chat_handler is not None
        assert hasattr(chat_handler, 'websocket_manager')
        assert hasattr(chat_handler, 'redis_cache_service')
    
    def test_error_response_creation(self, chat_handler):
        """Hiba válasz létrehozásának tesztje"""
        error_response = chat_handler._create_error_response("test_error", "Teszt hiba üzenet")
        
        assert error_response["type"] == "error"
        assert error_response["data"]["error_type"] == "test_error"
        assert error_response["data"]["error_message"] == "Teszt hiba üzenet"
        assert "timestamp" in error_response["data"]
    
    def test_pong_response_creation(self, chat_handler):
        """Pong válasz létrehozásának tesztje"""
        pong_response = chat_handler._create_pong_response()
        
        assert pong_response["type"] == "pong"
        assert "timestamp" in pong_response["data"]
    
    @pytest.mark.asyncio
    async def test_chat_message_validation(self, chat_handler, mock_websocket):
        """Chat üzenet validálásának tesztje"""
        # Üres üzenet
        empty_message = {
            "type": "chat_message",
            "content": "",
            "session_id": "test_session"
        }
        
        response = await chat_handler.handle_message(mock_websocket, "test_connection", empty_message)
        assert response["type"] == "error"
        assert response["data"]["error_type"] == "empty_message"
        
        # Hiányzó session ID
        message_without_session = {
            "type": "chat_message",
            "content": "Teszt üzenet"
        }
        
        response = await chat_handler.handle_message(mock_websocket, "test_connection", message_without_session)
        assert response["type"] == "error"
        assert response["data"]["error_type"] == "missing_session"
        
        # Hiányzó üzenet típus
        message_without_type = {
            "content": "Teszt üzenet",
            "session_id": "test_session"
        }
        
        response = await chat_handler.handle_message(mock_websocket, "test_connection", message_without_type)
        assert response["type"] == "error"
        assert response["data"]["error_type"] == "missing_type"
        
        # Ismeretlen üzenet típus
        unknown_message = {
            "type": "unknown_type",
            "content": "Teszt üzenet",
            "session_id": "test_session"
        }
        
        response = await chat_handler.handle_message(mock_websocket, "test_connection", unknown_message)
        assert response["type"] == "error"
        assert response["data"]["error_type"] == "unknown_type"
    
    @pytest.mark.asyncio
    async def test_ping_message_handling(self, chat_handler, mock_websocket):
        """Ping üzenet kezelésének tesztje"""
        ping_message = {
            "type": "ping",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        response = await chat_handler.handle_message(mock_websocket, "test_connection", ping_message)
        assert response["type"] == "pong"
        assert "timestamp" in response["data"]


class TestWebSocketConnection:
    """WebSocket kapcsolat tesztek"""
    
    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket objektum"""
        websocket = MagicMock()
        websocket.client.host = "127.0.0.1"
        websocket.headers.get.return_value = "test-user-agent"
        return websocket
    
    def test_websocket_connection_creation(self, mock_websocket):
        """WebSocket kapcsolat létrehozásának tesztje"""
        connection = WebSocketConnection(
            websocket=mock_websocket,
            session_id="test_session",
            user_id="test_user"
        )
        
        assert connection.websocket == mock_websocket
        assert connection.session_id == "test_session"
        assert connection.user_id == "test_user"
        assert connection.connected_at is not None
        assert connection.last_activity is not None
        assert connection.client_info is not None
        assert connection.is_active is True
    
    def test_websocket_connection_client_info(self, mock_websocket):
        """WebSocket kapcsolat kliens információk tesztje"""
        # Mock a client_info inicializálását
        mock_websocket.client.host = "127.0.0.1"
        mock_websocket.headers.get.return_value = "test-user-agent"
        
        connection = WebSocketConnection(
            websocket=mock_websocket,
            session_id="test_session",
            user_id="test_user"
        )
        
        # A client_info alapértelmezetten üres dict, mert a connect metódusban van inicializálva
        assert isinstance(connection.client_info, dict)


if __name__ == "__main__":
    pytest.main([__file__]) 