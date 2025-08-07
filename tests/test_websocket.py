#!/usr/bin/env python3
"""
WebSocket endpoint tesztek

Ez a modul teszteli a WebSocket funkcionalitást:
- Kapcsolat létrehozása
- Üzenet küldése és fogadása
- Session kezelés
- Hibakezelés
"""

import pytest
import json
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect

from src.main import app
from src.integrations.websocket_manager import websocket_manager, chat_handler


class TestWebSocketEndpoints:
    """WebSocket endpoint tesztek"""
    
    @pytest.fixture
    def client(self):
        """Test client létrehozása"""
        return TestClient(app)
    
    @pytest.fixture
    def session_id(self):
        """Teszt session ID"""
        return str(uuid.uuid4())
    
    @pytest.fixture
    def user_id(self):
        """Teszt user ID"""
        return "test_user_123"
    
    def test_websocket_connection_establishment(self, client, session_id):
        """WebSocket kapcsolat létrehozásának tesztje"""
        with client.websocket_connect(f"/ws/chat/{session_id}") as websocket:
            # Kapcsolat visszajelzés ellenőrzése
            response = websocket.receive_json()
            
            assert response["type"] == "connection_established"
            assert response["data"]["session_id"] == session_id
            assert "connection_id" in response["data"]
            assert "timestamp" in response["data"]
    
    def test_websocket_connection_with_user_id(self, client, session_id, user_id):
        """WebSocket kapcsolat létrehozása user ID-val"""
        with client.websocket_connect(f"/ws/chat/{session_id}?user_id={user_id}") as websocket:
            response = websocket.receive_json()
            
            assert response["type"] == "connection_established"
            assert response["data"]["session_id"] == session_id
            assert response["data"]["user_id"] == user_id
    
    def test_websocket_ping_pong(self, client, session_id):
        """Ping-pong teszt"""
        with client.websocket_connect(f"/ws/chat/{session_id}") as websocket:
            # Kapcsolat visszajelzés fogadása
            websocket.receive_json()
            
            # Ping üzenet küldése
            ping_message = {
                "type": "ping",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            websocket.send_json(ping_message)
            
            # Pong válasz ellenőrzése
            response = websocket.receive_json()
            assert response["type"] == "pong"
            assert "timestamp" in response["data"]
    
    def test_websocket_session_info_request(self, client, session_id):
        """Session információk lekérésének tesztje"""
        with client.websocket_connect(f"/ws/chat/{session_id}") as websocket:
            # Kapcsolat visszajelzés fogadása
            websocket.receive_json()
            
            # Session info kérés küldése
            session_info_request = {
                "type": "session_info",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            websocket.send_json(session_info_request)
            
            # Válasz ellenőrzése
            response = websocket.receive_json()
            assert response["type"] == "session_info"
            assert response["data"]["session_id"] == session_id
            assert "connected_at" in response["data"]
            assert "last_activity" in response["data"]
            assert "message_count" in response["data"]
    
    def test_websocket_chat_message_processing(self, client, session_id):
        """Chat üzenet feldolgozásának tesztje"""
        with client.websocket_connect(f"/ws/chat/{session_id}") as websocket:
            # Kapcsolat visszajelzés fogadása
            websocket.receive_json()
            
            # Chat üzenet küldése
            chat_message = {
                "type": "chat_message",
                "content": "Szia! Szeretnék információt kapni a termékekről.",
                "session_id": session_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            websocket.send_json(chat_message)
            
            # Válasz ellenőrzése (streaming format)
            # First, we may receive multiple chunk messages
            final_response = None
            max_attempts = 5  # Maximum attempts to find final response
            
            for _ in range(max_attempts):
                response = websocket.receive_json()
                if response["type"] == "chat_response":
                    final_response = response
                    break
                elif response["type"] == "chat_response_chunk":
                    # Continue to next message
                    continue
                else:
                    # Unexpected message type
                    break
            
            # Check we got a final chat_response
            assert final_response is not None, f"Did not receive chat_response, last response was: {response}"
            assert final_response["type"] == "chat_response"
            assert "content" in final_response["data"]
            assert "agent_type" in final_response["data"]
            assert "confidence" in final_response["data"]
            assert "timestamp" in final_response["data"]
    
    def test_websocket_empty_message_error(self, client, session_id):
        """Üres üzenet hibakezelésének tesztje"""
        with client.websocket_connect(f"/ws/chat/{session_id}") as websocket:
            # Kapcsolat visszajelzés fogadása
            websocket.receive_json()
            
            # Üres üzenet küldése
            empty_message = {
                "type": "chat_message",
                "content": "",
                "session_id": session_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            websocket.send_json(empty_message)
            
            # Hiba válasz ellenőrzése
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert response["data"]["error_type"] == "empty_message"
    
    def test_websocket_missing_session_error(self, client, session_id):
        """Hiányzó session ID hibakezelésének tesztje"""
        with client.websocket_connect(f"/ws/chat/{session_id}") as websocket:
            # Kapcsolat visszajelzés fogadása
            websocket.receive_json()
            
            # Üzenet hiányzó session ID-val
            message_without_session = {
                "type": "chat_message",
                "content": "Teszt üzenet",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            websocket.send_json(message_without_session)
            
            # Hiba válasz ellenőrzése
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert response["data"]["error_type"] == "missing_session"
    
    def test_websocket_unknown_message_type(self, client, session_id):
        """Ismeretlen üzenet típus hibakezelésének tesztje"""
        with client.websocket_connect(f"/ws/chat/{session_id}") as websocket:
            # Kapcsolat visszajelzés fogadása
            websocket.receive_json()
            
            # Ismeretlen típusú üzenet
            unknown_message = {
                "type": "unknown_type",
                "content": "Teszt üzenet",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            websocket.send_json(unknown_message)
            
            # Hiba válasz ellenőrzése
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert response["data"]["error_type"] == "unknown_type"
    
    def test_websocket_missing_message_type(self, client, session_id):
        """Hiányzó üzenet típus hibakezelésének tesztje"""
        with client.websocket_connect(f"/ws/chat/{session_id}") as websocket:
            # Kapcsolat visszajelzés fogadása
            websocket.receive_json()
            
            # Üzenet típus nélkül
            message_without_type = {
                "content": "Teszt üzenet",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            websocket.send_json(message_without_type)
            
            # Hiba válasz ellenőrzése
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert response["data"]["error_type"] == "missing_type"
    
    def test_websocket_stats_endpoint(self, client):
        """WebSocket statisztikák endpoint tesztje"""
        response = client.get("/api/v1/websocket/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "websocket_stats" in data
        assert "timestamp" in data
        assert "total_connections" in data["websocket_stats"]
        assert "total_sessions" in data["websocket_stats"]
        assert "total_users" in data["websocket_stats"]


class TestWebSocketManager:
    """WebSocket manager tesztek"""
    
    def test_websocket_manager_initialization(self):
        """WebSocket manager inicializálásának tesztje"""
        assert websocket_manager is not None
        assert hasattr(websocket_manager, 'active_connections')
        assert hasattr(websocket_manager, 'session_connections')
        assert hasattr(websocket_manager, 'user_connections')
    
    def test_websocket_manager_stats(self):
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


class TestChatWebSocketHandler:
    """Chat WebSocket handler tesztek"""
    
    def test_chat_handler_initialization(self):
        """Chat handler inicializálásának tesztje"""
        assert chat_handler is not None
        assert hasattr(chat_handler, 'websocket_manager')
        assert hasattr(chat_handler, 'redis_cache_service')
    
    def test_error_response_creation(self):
        """Hiba válasz létrehozásának tesztje"""
        error_response = chat_handler._create_error_response("test_error", "Teszt hiba üzenet")
        
        assert error_response["type"] == "error"
        assert error_response["data"]["error_type"] == "test_error"
        assert error_response["data"]["error_message"] == "Teszt hiba üzenet"
        assert "timestamp" in error_response["data"]
    
    def test_pong_response_creation(self):
        """Pong válasz létrehozásának tesztje"""
        pong_response = chat_handler._create_pong_response()
        
        assert pong_response["type"] == "pong"
        assert "timestamp" in pong_response["data"]


if __name__ == "__main__":
    pytest.main([__file__]) 