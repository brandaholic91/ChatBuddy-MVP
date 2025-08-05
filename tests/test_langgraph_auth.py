"""
LangGraph Authentication Tests

Teszteli a LangGraph SDK authentikáció funkcionalitását.
"""

import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
from src.config.langgraph_auth import (
    LangGraphAuthManager, 
    langgraph_auth_manager,
    get_langgraph_client,
    initialize_langgraph_auth,
    shutdown_langgraph_auth
)


class TestLangGraphAuthManager:
    """LangGraph Auth Manager tesztek"""
    
    def test_init(self):
        """Auth manager inicializálás tesztelése"""
        manager = LangGraphAuthManager()
        assert manager.client is None
        assert manager.is_authenticated is False
        assert "api_key" in manager.auth_config
        assert "project_id" in manager.auth_config
    
    @patch.dict(os.environ, {
        "LANGGRAPH_API_KEY": "test-api-key",
        "LANGGRAPH_PROJECT_ID": "test-project-id",
        "LANGGRAPH_ENVIRONMENT": "test",
        "LANGGRAPH_TIMEOUT": "60"
    })
    def test_load_auth_config(self):
        """Auth konfiguráció betöltés tesztelése"""
        manager = LangGraphAuthManager()
        config = manager.auth_config
        
        assert config["api_key"] == "test-api-key"
        assert config["project_id"] == "test-project-id"
        assert config["environment"] == "test"
        assert config["timeout"] == 60
    
    @patch.dict(os.environ, {}, clear=True)
    def test_load_auth_config_defaults(self):
        """Auth konfiguráció alapértelmezett értékek tesztelése"""
        manager = LangGraphAuthManager()
        config = manager.auth_config
        
        assert config["api_key"] is None
        assert config["project_id"] is None
        assert config["environment"] == "development"
        assert config["timeout"] == 30
    
    @patch('src.config.langgraph_auth.get_client')
    @patch.dict(os.environ, {
        "LANGGRAPH_API_KEY": "test-api-key",
        "LANGGRAPH_PROJECT_ID": "test-project-id"
    })
    async def test_authenticate_success(self, mock_get_client):
        """Sikeres authentikáció tesztelése"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        manager = LangGraphAuthManager()
        
        # Mock a _test_connection metódust
        manager._test_connection = AsyncMock()
        
        result = await manager.authenticate()
        
        assert result is True
        assert manager.is_authenticated is True
        assert manager.client is not None
        mock_get_client.assert_called_once()
    
    @patch.dict(os.environ, {}, clear=True)
    async def test_authenticate_no_api_key(self):
        """Authentikáció API kulcs nélkül tesztelése"""
        manager = LangGraphAuthManager()
        
        result = await manager.authenticate()
        
        assert result is False
        assert manager.is_authenticated is False
        assert manager.client is None
    
    @patch('src.config.langgraph_auth.get_client')
    @patch.dict(os.environ, {
        "LANGGRAPH_API_KEY": "test-api-key",
        "LANGGRAPH_PROJECT_ID": "test-project-id"
    })
    async def test_authenticate_client_error(self, mock_get_client):
        """Authentikáció kliens hibával tesztelése"""
        mock_get_client.side_effect = Exception("Connection failed")
        manager = LangGraphAuthManager()
        
        result = await manager.authenticate()
        
        assert result is False
        assert manager.is_authenticated is False
    
    def test_get_client_not_authenticated(self):
        """Kliens lekérése nem authentikált állapotban"""
        manager = LangGraphAuthManager()
        client = manager.get_client()
        
        assert client is None
    
    def test_get_client_authenticated(self):
        """Kliens lekérése authentikált állapotban"""
        manager = LangGraphAuthManager()
        manager.client = Mock()
        manager.is_authenticated = True
        
        client = manager.get_client()
        
        assert client is not None
    
    async def test_disconnect(self):
        """Kapcsolat lezárás tesztelése"""
        manager = LangGraphAuthManager()
        manager.client = Mock()
        manager.is_authenticated = True
        
        await manager.disconnect()
        
        assert manager.client is None
        assert manager.is_authenticated is False


class TestLangGraphAuthFunctions:
    """LangGraph auth függvények tesztek"""
    
    @patch('src.config.langgraph_auth.langgraph_auth_manager')
    async def test_get_langgraph_client_not_authenticated(self, mock_manager):
        """LangGraph kliens lekérése nem authentikált állapotban"""
        mock_manager.is_authenticated = False
        mock_manager.authenticate = AsyncMock(return_value=False)
        mock_manager.get_client.return_value = None
        
        client = await get_langgraph_client()
        
        assert client is None
        mock_manager.authenticate.assert_called_once()
    
    @patch('src.config.langgraph_auth.langgraph_auth_manager')
    async def test_get_langgraph_client_authenticated(self, mock_manager):
        """LangGraph kliens lekérése authentikált állapotban"""
        mock_client = Mock()
        mock_manager.is_authenticated = True
        mock_manager.get_client.return_value = mock_client
        
        client = await get_langgraph_client()
        
        assert client is mock_client
        mock_manager.get_client.assert_called_once()
    
    @patch('src.config.langgraph_auth.langgraph_auth_manager')
    async def test_initialize_langgraph_auth_success(self, mock_manager):
        """LangGraph auth inicializálás sikeres eset"""
        mock_manager.authenticate = AsyncMock(return_value=True)
        
        result = await initialize_langgraph_auth()
        
        assert result is True
        mock_manager.authenticate.assert_called_once()
    
    @patch('src.config.langgraph_auth.langgraph_auth_manager')
    async def test_initialize_langgraph_auth_failure(self, mock_manager):
        """LangGraph auth inicializálás sikertelen eset"""
        mock_manager.authenticate = AsyncMock(return_value=False)
        
        result = await initialize_langgraph_auth()
        
        assert result is False
        mock_manager.authenticate.assert_called_once()
    
    @patch('src.config.langgraph_auth.langgraph_auth_manager')
    async def test_shutdown_langgraph_auth(self, mock_manager):
        """LangGraph auth leállítás tesztelése"""
        mock_manager.disconnect = AsyncMock()
        
        await shutdown_langgraph_auth()
        
        mock_manager.disconnect.assert_called_once()


@pytest.fixture
def mock_langgraph_env():
    """LangGraph környezeti változók mock-olása"""
    with patch.dict(os.environ, {
        "LANGGRAPH_API_KEY": "test-api-key",
        "LANGGRAPH_PROJECT_ID": "test-project-id",
        "LANGGRAPH_ENVIRONMENT": "test",
        "LANGGRAPH_TIMEOUT": "30"
    }):
        yield


class TestLangGraphAuthIntegration:
    """LangGraph auth integrációs tesztek"""
    
    @patch('src.config.langgraph_auth.get_client')
    async def test_full_auth_flow(self, mock_get_client, mock_langgraph_env):
        """Teljes authentikációs folyamat tesztelése"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Auth manager létrehozása
        manager = LangGraphAuthManager()
        
        # Authentikáció
        manager._test_connection = AsyncMock()
        result = await manager.authenticate()
        
        assert result is True
        assert manager.is_authenticated is True
        assert manager.client is not None
        
        # Kliens lekérése
        client = manager.get_client()
        assert client is not None
        
        # Kapcsolat lezárása
        await manager.disconnect()
        assert manager.client is None
        assert manager.is_authenticated is False 