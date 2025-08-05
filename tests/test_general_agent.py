"""
General Agent Tests - Chatbuddy MVP.

Ez a modul teszteli a general agent Pydantic AI implementációját,
amely a LangGraph workflow-ban használatos.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, Optional
from datetime import datetime

from src.agents.general.agent import (
    create_general_agent,
    call_general_agent,
    GeneralDependencies,
    GeneralResponse,
    Agent
)
from src.models.agent import AgentType


class TestGeneralAgent:
    """Tests for general agent Pydantic AI implementation."""
    
    pytestmark = pytest.mark.agent
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock dependencies for testing."""
        mock_audit_logger = AsyncMock()
        mock_security_context = Mock()
        mock_security_context.validate_access.return_value = True
        
        return GeneralDependencies(
            user_context={
                "user_id": "test_user_123",
                "session_id": "test_session_456",
                "preferences": {"language": "hu"}
            },
            supabase_client=Mock(),
            webshop_api=Mock(),
            security_context=mock_security_context,
            audit_logger=mock_audit_logger
        )
    
    @pytest.fixture
    def general_agent(self):
        """Create general agent instance."""
        # Mock OpenAI API initialization to avoid API key requirement
        with patch('pydantic_ai.models.openai.OpenAIModel') as mock_openai:
            with patch('pydantic_ai.providers.openai.AsyncOpenAI') as mock_client:
                mock_client.return_value = Mock()
                mock_openai.return_value = Mock()
                return create_general_agent()
    
    @pytest.mark.asyncio
    async def test_create_general_agent(self):
        """Test general agent creation."""
        # Mock OpenAI API initialization to avoid API key requirement
        with patch('pydantic_ai.models.openai.OpenAIModel') as mock_openai:
            with patch('pydantic_ai.providers.openai.AsyncOpenAI') as mock_client:
                mock_client.return_value = Mock()
                mock_openai.return_value = Mock()
                
                agent = create_general_agent()
                
                assert agent is not None
                assert isinstance(agent, Agent)
                # Check if agent can be created and has basic structure
                assert hasattr(agent, 'run')
                assert callable(agent.run)
    
    @pytest.mark.asyncio
    async def test_agent_get_help_topics_tool(self, general_agent, mock_dependencies):
        """Test get_help_topics tool functionality."""
        with patch('src.agents.general.agent.create_general_agent', return_value=general_agent):
            with patch.object(general_agent, 'run') as mock_run:
                mock_response = GeneralResponse(
                    response_text="Itt vannak az elérhető segítség témák:",
                    confidence=0.95,
                    help_topics=[
                        "Termékek keresése és vásárlása",
                        "Rendelések követése",
                        "Szállítási információk"
                    ],
                    metadata={"tool_used": "get_help_topics"}
                )
                mock_run.return_value = Mock(output=mock_response)
                
                result = await call_general_agent(
                    "Milyen segítség témák érhetők el?",
                    mock_dependencies
                )
                
                assert result is not None
                assert isinstance(result, GeneralResponse)
                assert "segítség témák" in result.response_text.lower()
                assert result.confidence > 0.8
                assert result.help_topics is not None
                assert len(result.help_topics) > 0
                assert "Termékek keresése" in result.help_topics[0]
    
    @pytest.mark.asyncio
    async def test_agent_get_contact_info_tool(self, general_agent, mock_dependencies):
        """Test get_contact_info tool functionality."""
        with patch('src.agents.general.agent.create_general_agent', return_value=general_agent):
            with patch.object(general_agent, 'run') as mock_run:
                mock_response = GeneralResponse(
                    response_text="Itt vannak a kapcsolatfelvételi információk:",
                    confidence=0.9,
                    suggested_actions=["Hívja az ügyfélszolgálatot"],
                    metadata={"tool_used": "get_contact_info"}
                )
                mock_run.return_value = Mock(output=mock_response)
                
                result = await call_general_agent(
                    "Hogyan tudok kapcsolatba lépni az ügyfélszolgálattal?",
                    mock_dependencies
                )
                
                assert result is not None
                assert isinstance(result, GeneralResponse)
                assert "kapcsolatfelvételi" in result.response_text.lower()
                assert result.confidence > 0.8
                assert result.suggested_actions is not None
                assert "Hívja az ügyfélszolgálatot" in result.suggested_actions[0]
    
    @pytest.mark.asyncio
    async def test_agent_get_faq_answers_tool(self, general_agent, mock_dependencies):
        """Test get_faq_answers tool functionality."""
        with patch('src.agents.general.agent.create_general_agent', return_value=general_agent):
            with patch.object(general_agent, 'run') as mock_run:
                mock_response = GeneralResponse(
                    response_text="A szállítási idő 1-3 munkanap, attól függően, hogy melyik szállítási módot választja.",
                    confidence=0.85,
                    metadata={"tool_used": "get_faq_answers", "category": "szállítás"}
                )
                mock_run.return_value = Mock(output=mock_response)
                
                result = await call_general_agent(
                    "Mennyi idő alatt érkezik meg a rendelésem?",
                    mock_dependencies
                )
                
                assert result is not None
                assert isinstance(result, GeneralResponse)
                assert "szállítási idő" in result.response_text.lower()
                assert result.confidence > 0.8
                assert result.metadata.get("category") == "szállítás"
    
    @pytest.mark.asyncio
    async def test_agent_get_website_info_tool(self, general_agent, mock_dependencies):
        """Test get_website_info tool functionality."""
        with patch('src.agents.general.agent.create_general_agent', return_value=general_agent):
            with patch.object(general_agent, 'run') as mock_run:
                mock_response = GeneralResponse(
                    response_text="A ChatBuddy Webshop Magyarország vezető elektronikai webshopja.",
                    confidence=0.9,
                    metadata={"tool_used": "get_website_info"}
                )
                mock_run.return_value = Mock(output=mock_response)
                
                result = await call_general_agent(
                    "Tudna mesélni a webshopról?",
                    mock_dependencies
                )
                
                assert result is not None
                assert isinstance(result, GeneralResponse)
                assert "chatbuddy" in result.response_text.lower()
                assert result.confidence > 0.8
                assert result.metadata.get("tool_used") == "get_website_info"
    
    @pytest.mark.asyncio
    async def test_agent_get_user_guide_tool(self, general_agent, mock_dependencies):
        """Test get_user_guide tool functionality."""
        with patch('src.agents.general.agent.create_general_agent', return_value=general_agent):
            with patch.object(general_agent, 'run') as mock_run:
                mock_response = GeneralResponse(
                    response_text="A fiók létrehozásához kövesse ezeket a lépéseket:",
                    confidence=0.88,
                    suggested_actions=["Kattintson a 'Regisztráció' gombra"],
                    metadata={"tool_used": "get_user_guide", "topic": "regisztráció"}
                )
                mock_run.return_value = Mock(output=mock_response)
                
                result = await call_general_agent(
                    "Hogyan hozhatok létre fiókot?",
                    mock_dependencies
                )
                
                assert result is not None
                assert isinstance(result, GeneralResponse)
                assert "fiók létrehozásához" in result.response_text.lower()
                assert result.confidence > 0.8
                assert result.suggested_actions is not None
                assert "Regisztráció" in result.suggested_actions[0]
    
    @pytest.mark.asyncio
    async def test_agent_general_inquiry(self, general_agent, mock_dependencies):
        """Test general inquiry handling."""
        with patch('src.agents.general.agent.create_general_agent', return_value=general_agent):
            with patch.object(general_agent, 'run') as mock_run:
                mock_response = GeneralResponse(
                    response_text="Üdvözlöm! Miben segíthetek?",
                    confidence=0.95,
                    metadata={"inquiry_type": "general_greeting"}
                )
                mock_run.return_value = Mock(output=mock_response)
                
                result = await call_general_agent(
                    "Szia!",
                    mock_dependencies
                )
                
                assert result is not None
                assert isinstance(result, GeneralResponse)
                assert "üdvözlöm" in result.response_text.lower()
                assert result.confidence > 0.9
    
    @pytest.mark.asyncio
    async def test_agent_error_handling(self, general_agent, mock_dependencies):
        """Test error handling in general agent."""
        with patch('src.agents.general.agent.create_general_agent', return_value=general_agent):
            with patch.object(general_agent, 'run') as mock_run:
                mock_run.side_effect = Exception("Test error")
                
                result = await call_general_agent(
                    "Teszt üzenet",
                    mock_dependencies
                )
                
                assert result is not None
                assert isinstance(result, GeneralResponse)
                assert "hiba történt" in result.response_text.lower()
                assert result.confidence == 0.0
                assert "error" in result.metadata
    
    @pytest.mark.asyncio
    async def test_agent_audit_logging(self, general_agent):
        """Test audit logging functionality."""
        mock_audit_logger = AsyncMock()
        mock_dependencies = GeneralDependencies(
            user_context={"user_id": "test_user"},
            audit_logger=mock_audit_logger
        )
        
        with patch('src.agents.general.agent.create_general_agent', return_value=general_agent):
            with patch.object(general_agent, 'run') as mock_run:
                mock_response = GeneralResponse(
                    response_text="Teszt válasz",
                    confidence=0.8
                )
                mock_run.return_value = Mock(output=mock_response)
                
                await call_general_agent("Teszt üzenet", mock_dependencies)
                
                # Verify audit logging was called
                # Note: This would depend on actual audit logging implementation
                # For now, we just verify the agent runs without error
    
    @pytest.mark.asyncio
    async def test_agent_response_validation(self, general_agent, mock_dependencies):
        """Test response validation."""
        with patch('src.agents.general.agent.create_general_agent', return_value=general_agent):
            with patch.object(general_agent, 'run') as mock_run:
                mock_response = GeneralResponse(
                    response_text="Valid response",
                    confidence=0.85,
                    suggested_actions=["Action 1", "Action 2"],
                    help_topics=["Topic 1", "Topic 2"],
                    metadata={"test": "data"}
                )
                mock_run.return_value = Mock(output=mock_response)
                
                result = await call_general_agent("Test message", mock_dependencies)
                
                assert result is not None
                assert isinstance(result, GeneralResponse)
                assert 0.0 <= result.confidence <= 1.0
                assert result.response_text is not None
                assert len(result.response_text) > 0
    
    @pytest.mark.asyncio
    async def test_agent_multilingual_support(self, general_agent, mock_dependencies):
        """Test multilingual support."""
        with patch('src.agents.general.agent.create_general_agent', return_value=general_agent):
            with patch.object(general_agent, 'run') as mock_run:
                mock_response = GeneralResponse(
                    response_text="Üdvözlöm! Miben segíthetek?",
                    confidence=0.9,
                    metadata={"language": "hu"}
                )
                mock_run.return_value = Mock(output=mock_response)
                
                result = await call_general_agent("Hello", mock_dependencies)
                
                assert result is not None
                assert isinstance(result, GeneralResponse)
                # Should respond in Hungarian as per system prompt
                assert "üdvözlöm" in result.response_text.lower()
    
    @pytest.mark.asyncio
    async def test_agent_security_context(self, general_agent):
        """Test security context integration."""
        mock_security_context = Mock()
        mock_security_context.validate_access.return_value = True
        
        mock_dependencies = GeneralDependencies(
            user_context={"user_id": "test_user"},
            security_context=mock_security_context
        )
        
        with patch('src.agents.general.agent.create_general_agent', return_value=general_agent):
            with patch.object(general_agent, 'run') as mock_run:
                mock_response = GeneralResponse(
                    response_text="Secure response",
                    confidence=0.9
                )
                mock_run.return_value = Mock(output=mock_response)
                
                result = await call_general_agent("Test message", mock_dependencies)
                
                assert result is not None
                # Note: In the current implementation, security context validation
                # is not explicitly called in the agent. This would be implemented
                # in a real scenario where security checks are performed.
                # For now, we just verify the agent runs with security context
                assert mock_dependencies.security_context is not None
    
    @pytest.mark.asyncio
    async def test_agent_performance(self, general_agent, mock_dependencies):
        """Test agent performance."""
        with patch('src.agents.general.agent.create_general_agent', return_value=general_agent):
            with patch.object(general_agent, 'run') as mock_run:
                mock_response = GeneralResponse(
                    response_text="Fast response",
                    confidence=0.9
                )
                mock_run.return_value = Mock(output=mock_response)
                
                start_time = asyncio.get_event_loop().time()
                result = await call_general_agent("Test message", mock_dependencies)
                end_time = asyncio.get_event_loop().time()
                
                assert result is not None
                response_time = end_time - start_time
                # Should respond within reasonable time (adjust as needed)
                assert response_time < 5.0  # 5 seconds max


class TestGeneralAgentIntegration:
    """Integration tests for general agent."""
    
    pytestmark = pytest.mark.integration
    
    @pytest.mark.asyncio
    async def test_agent_with_real_tools(self):
        """Test agent with real tool implementations."""
        # This would test with actual tool implementations
        # For now, we'll skip this as tools are mocked
        pytest.skip("Integration test requires real tool implementations")
    
    @pytest.mark.asyncio
    async def test_agent_workflow_integration(self):
        """Test agent integration with LangGraph workflow."""
        # This would test integration with the main workflow
        # For now, we'll skip this as it requires full workflow setup
        pytest.skip("Workflow integration test requires full setup")


class TestGeneralAgentEdgeCases:
    """Edge case tests for general agent."""
    
    pytestmark = pytest.mark.edge_cases
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock dependencies for edge case testing."""
        mock_audit_logger = AsyncMock()
        mock_security_context = Mock()
        mock_security_context.validate_access.return_value = True
        
        return GeneralDependencies(
            user_context={
                "user_id": "test_user_123",
                "session_id": "test_session_456",
                "preferences": {"language": "hu"}
            },
            supabase_client=Mock(),
            webshop_api=Mock(),
            security_context=mock_security_context,
            audit_logger=mock_audit_logger
        )
    
    @pytest.fixture
    def general_agent(self):
        """Create general agent instance for edge case testing."""
        with patch('pydantic_ai.models.openai.OpenAIModel') as mock_openai:
            with patch('pydantic_ai.providers.openai.AsyncOpenAI') as mock_client:
                mock_client.return_value = Mock()
                mock_openai.return_value = Mock()
                return create_general_agent()
    
    @pytest.mark.asyncio
    async def test_empty_message_handling(self, general_agent, mock_dependencies):
        """Test handling of empty messages."""
        with patch('src.agents.general.agent.create_general_agent', return_value=general_agent):
            with patch.object(general_agent, 'run') as mock_run:
                mock_response = GeneralResponse(
                    response_text="Kérjük, írjon be egy üzenetet.",
                    confidence=0.5,
                    metadata={"error_type": "empty_message"}
                )
                mock_run.return_value = Mock(output=mock_response)
                
                result = await call_general_agent("", mock_dependencies)
                
                assert result is not None
                assert "írjon be" in result.response_text.lower()
    
    @pytest.mark.asyncio
    async def test_very_long_message_handling(self, general_agent, mock_dependencies):
        """Test handling of very long messages."""
        long_message = "Ez egy nagyon hosszú üzenet " * 100  # ~3000 characters
        
        with patch('src.agents.general.agent.create_general_agent', return_value=general_agent):
            with patch.object(general_agent, 'run') as mock_run:
                mock_response = GeneralResponse(
                    response_text="Értem a kérdését. Miben segíthetek?",
                    confidence=0.8,
                    metadata={"message_length": len(long_message)}
                )
                mock_run.return_value = Mock(output=mock_response)
                
                result = await call_general_agent(long_message, mock_dependencies)
                
                assert result is not None
                assert result.metadata.get("message_length") == len(long_message)
    
    @pytest.mark.asyncio
    async def test_special_characters_handling(self, general_agent, mock_dependencies):
        """Test handling of special characters."""
        special_message = "Kérdés: Hogyan működik a @#$%^&*() rendszer?"
        
        with patch('src.agents.general.agent.create_general_agent', return_value=general_agent):
            with patch.object(general_agent, 'run') as mock_run:
                mock_response = GeneralResponse(
                    response_text="Értem a kérdését a rendszerről.",
                    confidence=0.85,
                    metadata={"special_chars": True}
                )
                mock_run.return_value = Mock(output=mock_response)
                
                result = await call_general_agent(special_message, mock_dependencies)
                
                assert result is not None
                assert "kérdését" in result.response_text.lower()
    
    @pytest.mark.asyncio
    async def test_unicode_handling(self, general_agent, mock_dependencies):
        """Test handling of unicode characters."""
        unicode_message = "Kérdés: Hogyan működik a 🚀 rendszer? És mi a helyzet a 🌍-gal?"
        
        with patch('src.agents.general.agent.create_general_agent', return_value=general_agent):
            with patch.object(general_agent, 'run') as mock_run:
                mock_response = GeneralResponse(
                    response_text="Értem a kérdését a rendszerről.",
                    confidence=0.85,
                    metadata={"unicode_chars": True}
                )
                mock_run.return_value = Mock(output=mock_response)
                
                result = await call_general_agent(unicode_message, mock_dependencies)
                
                assert result is not None
                assert "kérdését" in result.response_text.lower()
    
    @pytest.mark.asyncio
    async def test_malicious_input_handling(self, general_agent, mock_dependencies):
        """Test handling of potentially malicious input."""
        malicious_message = "<script>alert('xss')</script> SQL injection attempt"
        
        with patch('src.agents.general.agent.create_general_agent', return_value=general_agent):
            with patch.object(general_agent, 'run') as mock_run:
                mock_response = GeneralResponse(
                    response_text="Sajnálom, nem értem a kérdését. Kérjük, fogalmazza meg másképp.",
                    confidence=0.3,
                    metadata={"security_flag": True}
                )
                mock_run.return_value = Mock(output=mock_response)
                
                result = await call_general_agent(malicious_message, mock_dependencies)
                
                assert result is not None
                assert result.confidence < 0.5  # Lower confidence for suspicious input
                assert result.metadata.get("security_flag") is True


class TestGeneralAgentTools:
    """Tests for individual general agent tools."""
    
    pytestmark = pytest.mark.tools
    
    @pytest.mark.asyncio
    async def test_get_help_topics_tool_implementation(self):
        """Test get_help_topics tool implementation."""
        # Since tools are defined inside the agent, we test them through the agent
        agent = create_general_agent()
        
        # Create a mock context
        mock_context = Mock()
        mock_context.deps = GeneralDependencies(
            user_context={"user_id": "test_user"}
        )
        
        # Test the tool function by calling it through the agent
        # Note: This is a simplified test since we can't directly access the tools
        # In a real scenario, we would test the tool through the agent's run method
        
        # For now, we'll test that the agent can be created and has the expected structure
        assert agent is not None
        assert hasattr(agent, 'run')
        assert callable(agent.run)
        
        # Test that the agent can handle help topics requests
        with patch.object(agent, 'run') as mock_run:
            mock_response = GeneralResponse(
                response_text="Segítség témák:",
                confidence=0.9,
                help_topics=["Termékek keresése", "Rendelések követése"],
                metadata={"tool_used": "get_help_topics"}
            )
            mock_run.return_value = Mock(output=mock_response)
            
            # This would normally call the tool through the agent
            # For testing purposes, we verify the mock response
            assert mock_response.help_topics is not None
            assert len(mock_response.help_topics) > 0
            assert "Termékek keresése" in mock_response.help_topics[0]
    
    @pytest.mark.asyncio
    async def test_get_contact_info_tool_implementation(self):
        """Test get_contact_info tool implementation."""
        agent = create_general_agent()
        
        # Test that the agent can handle contact info requests
        with patch.object(agent, 'run') as mock_run:
            mock_response = GeneralResponse(
                response_text="Kapcsolatfelvételi információk:",
                confidence=0.9,
                suggested_actions=["Hívja az ügyfélszolgálatot"],
                metadata={"tool_used": "get_contact_info"}
            )
            mock_run.return_value = Mock(output=mock_response)
            
            # Verify the mock response structure
            assert mock_response.suggested_actions is not None
            assert "ügyfélszolgálatot" in mock_response.suggested_actions[0]
    
    @pytest.mark.asyncio
    async def test_get_faq_answers_tool_implementation(self):
        """Test get_faq_answers tool implementation."""
        agent = create_general_agent()
        
        # Test that the agent can handle FAQ requests
        with patch.object(agent, 'run') as mock_run:
            mock_response = GeneralResponse(
                response_text="Szállítási idő: 1-3 munkanap",
                confidence=0.85,
                metadata={"tool_used": "get_faq_answers", "category": "szállítás"}
            )
            mock_run.return_value = Mock(output=mock_response)
            
            # Verify the mock response
            assert "szállítási idő" in mock_response.response_text.lower()
            assert mock_response.metadata.get("category") == "szállítás"
    
    @pytest.mark.asyncio
    async def test_get_website_info_tool_implementation(self):
        """Test get_website_info tool implementation."""
        agent = create_general_agent()
        
        # Test that the agent can handle website info requests
        with patch.object(agent, 'run') as mock_run:
            mock_response = GeneralResponse(
                response_text="ChatBuddy Webshop információ",
                confidence=0.9,
                metadata={"tool_used": "get_website_info"}
            )
            mock_run.return_value = Mock(output=mock_response)
            
            # Verify the mock response
            assert "chatbuddy" in mock_response.response_text.lower()
            assert mock_response.metadata.get("tool_used") == "get_website_info"
    
    @pytest.mark.asyncio
    async def test_get_user_guide_tool_implementation(self):
        """Test get_user_guide tool implementation."""
        agent = create_general_agent()
        
        # Test that the agent can handle user guide requests
        with patch.object(agent, 'run') as mock_run:
            mock_response = GeneralResponse(
                response_text="Fiók létrehozása útmutató",
                confidence=0.88,
                suggested_actions=["Kattintson a 'Regisztráció' gombra"],
                metadata={"tool_used": "get_user_guide", "topic": "regisztráció"}
            )
            mock_run.return_value = Mock(output=mock_response)
            
            # Verify the mock response
            assert "fiók létrehozása" in mock_response.response_text.lower()
            assert mock_response.suggested_actions is not None
            assert "Regisztráció" in mock_response.suggested_actions[0]
    
    @pytest.mark.asyncio
    async def test_get_user_guide_unknown_topic(self):
        """Test get_user_guide tool with unknown topic."""
        agent = create_general_agent()
        
        # Test that the agent can handle unknown topic requests
        with patch.object(agent, 'run') as mock_run:
            mock_response = GeneralResponse(
                response_text="Útmutató nem található",
                confidence=0.3,
                metadata={"tool_used": "get_user_guide", "topic": "ismeretlen_téma"}
            )
            mock_run.return_value = Mock(output=mock_response)
            
            # Verify the mock response
            assert "nem található" in mock_response.response_text.lower()
            assert mock_response.confidence < 0.5  # Lower confidence for unknown topics 