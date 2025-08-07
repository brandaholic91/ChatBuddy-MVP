"""
Test module for BaseAgent functionality.

Tests the common base agent functionality and error handling.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from src.agents.base.base_agent import BaseAgent, BaseDependencies, BaseResponse
from src.models.agent import AgentType


class TestAgent(BaseAgent):
    """Test implementation of BaseAgent."""
    
    @property
    def agent_type(self) -> AgentType:
        return AgentType.GENERAL
    
    @property
    def system_prompt(self) -> str:
        return "Test agent system prompt"
    
    @property
    def dependencies_type(self) -> type:
        return BaseDependencies
    
    @property
    def response_type(self) -> type:
        return BaseResponse
    
    def _register_tools(self, agent) -> None:
        """Register test tools."""
        @agent.tool
        async def test_tool(ctx) -> str:
            return "test_result"


@pytest.fixture
def base_dependencies():
    """Create test dependencies."""
    return BaseDependencies(
        user_context={"user_id": "test_user"},
        supabase_client=None,
        webshop_api=None,
        security_context=None,
        audit_logger=None
    )


@pytest.fixture
def test_agent():
    """Create test agent instance."""
    return TestAgent()


@pytest.mark.unit
@pytest.mark.agents
class TestBaseAgent:
    """Test BaseAgent functionality."""
    
    def test_agent_initialization(self, test_agent):
        """Test agent initialization."""
        assert test_agent.model == 'openai:gpt-4o'
        assert test_agent.agent_type == AgentType.GENERAL
        assert test_agent.system_prompt == "Test agent system prompt"
        assert test_agent._agent is None
    
    def test_agent_initialization_with_custom_model(self):
        """Test agent initialization with custom model."""
        custom_agent = TestAgent(model='openai:gpt-3.5-turbo')
        assert custom_agent.model == 'openai:gpt-3.5-turbo'
    
    @patch('src.agents.base.base_agent.Agent')
    def test_create_agent(self, mock_agent_class, test_agent):
        """Test agent creation."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        result = test_agent.create_agent()
        
        assert result == mock_agent
        assert test_agent._agent == mock_agent
        mock_agent_class.assert_called_once_with(
            test_agent.model,
            deps_type=BaseDependencies,
            result_type=BaseResponse,
            system_prompt=test_agent.system_prompt
        )
    
    @patch('src.agents.base.base_agent.Agent')
    def test_create_agent_caching(self, mock_agent_class, test_agent):
        """Test that agent instance is cached."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        # First call
        result1 = test_agent.create_agent()
        # Second call
        result2 = test_agent.create_agent()
        
        assert result1 == result2
        assert mock_agent_class.call_count == 1
    
    @pytest.mark.asyncio
    async def test_run_success(self, test_agent, base_dependencies):
        """Test successful agent run."""
        mock_agent = AsyncMock()
        mock_result = MagicMock()
        mock_result.data = BaseResponse(
            response_text="Test response",
            confidence=0.9
        )
        mock_agent.run.return_value = mock_result
        
        with patch.object(test_agent, 'create_agent', return_value=mock_agent):
            result = await test_agent.run("test message", base_dependencies)
        
        assert isinstance(result, BaseResponse)
        assert result.response_text == "Test response"
        assert result.confidence == 0.9
        mock_agent.run.assert_called_once_with("test message", deps=base_dependencies)
    
    @pytest.mark.asyncio
    async def test_run_error_handling(self, test_agent, base_dependencies):
        """Test error handling in agent run."""
        mock_agent = AsyncMock()
        mock_agent.run.side_effect = Exception("Test error")
        
        with patch.object(test_agent, 'create_agent', return_value=mock_agent):
            result = await test_agent.run("test message", base_dependencies)
        
        assert isinstance(result, BaseResponse)
        assert "hiba történt" in result.response_text.lower()
        assert result.confidence == 0.0
        assert "error_type" in result.metadata
        assert "original_message" in result.metadata
    
    @pytest.mark.asyncio
    async def test_handle_error_with_audit_logger(self, test_agent, base_dependencies):
        """Test error handling with audit logger."""
        mock_audit_logger = AsyncMock()
        base_dependencies.audit_logger = mock_audit_logger
        
        error = Exception("Test error")
        result = await test_agent._handle_error(error, "test message", base_dependencies)
        
        assert isinstance(result, BaseResponse)
        assert "Test error" in result.response_text
        mock_audit_logger.log_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_log_data_access(self, test_agent, base_dependencies):
        """Test data access logging."""
        mock_audit_logger = AsyncMock()
        base_dependencies.audit_logger = mock_audit_logger
        
        await test_agent._log_data_access(
            base_dependencies, 
            "test_operation", 
            True, 
            {"key": "value"}
        )
        
        mock_audit_logger.log_data_access.assert_called_once_with(
            user_id="test_user",
            data_type="general",
            operation="test_operation",
            success=True,
            details={"key": "value"}
        )
    
    @pytest.mark.asyncio
    async def test_log_data_access_without_logger(self, test_agent, base_dependencies):
        """Test data access logging without audit logger."""
        # Should not raise an error
        await test_agent._log_data_access(
            base_dependencies, 
            "test_operation", 
            True, 
            {"key": "value"}
        )
    
    def test_get_user_id(self, test_agent, base_dependencies):
        """Test user ID extraction."""
        user_id = test_agent._get_user_id(base_dependencies)
        assert user_id == "test_user"
    
    def test_get_user_id_anonymous(self, test_agent):
        """Test user ID extraction with no user context."""
        deps = BaseDependencies(user_context={})
        user_id = test_agent._get_user_id(deps)
        assert user_id == "anonymous"


@pytest.mark.unit
class TestBaseDependencies:
    """Test BaseDependencies functionality."""
    
    def test_dependencies_creation(self):
        """Test dependencies creation."""
        deps = BaseDependencies(
            user_context={"user_id": "test"},
            supabase_client="mock_client",
            webshop_api="mock_api",
            security_context="mock_security",
            audit_logger="mock_logger"
        )
        
        assert deps.user_context == {"user_id": "test"}
        assert deps.supabase_client == "mock_client"
        assert deps.webshop_api == "mock_api"
        assert deps.security_context == "mock_security"
        assert deps.audit_logger == "mock_logger"
    
    def test_dependencies_defaults(self):
        """Test dependencies with default values."""
        deps = BaseDependencies(user_context={"user_id": "test"})
        
        assert deps.user_context == {"user_id": "test"}
        assert deps.supabase_client is None
        assert deps.webshop_api is None
        assert deps.security_context is None
        assert deps.audit_logger is None


@pytest.mark.unit
class TestBaseResponse:
    """Test BaseResponse functionality."""
    
    def test_response_creation(self):
        """Test response creation."""
        response = BaseResponse(
            response_text="Test response",
            confidence=0.8,
            metadata={"key": "value"}
        )
        
        assert response.response_text == "Test response"
        assert response.confidence == 0.8
        assert response.metadata == {"key": "value"}
    
    def test_response_defaults(self):
        """Test response with default values."""
        response = BaseResponse(
            response_text="Test response",
            confidence=0.8
        )
        
        assert response.response_text == "Test response"
        assert response.confidence == 0.8
        assert response.metadata == {}
    
    def test_confidence_validation(self):
        """Test confidence value validation."""
        # Valid confidence values
        BaseResponse(response_text="test", confidence=0.0)
        BaseResponse(response_text="test", confidence=1.0)
        BaseResponse(response_text="test", confidence=0.5)
        
        # Invalid confidence values should be handled by Pydantic
        with pytest.raises(Exception):  # Pydantic validation error
            BaseResponse(response_text="test", confidence=-0.1)
        
        with pytest.raises(Exception):  # Pydantic validation error
            BaseResponse(response_text="test", confidence=1.1)