"""
Comprehensive integration tests for all components.
"""

import pytest
import pytest_asyncio
import os
from unittest.mock import Mock, AsyncMock, patch
from src.workflows.coordinator import get_coordinator_agent
from src.workflows.langgraph_workflow import get_workflow_manager
from src.agents.general.agent import call_general_agent, GeneralDependencies
from src.agents.marketing.agent import call_marketing_agent, MarketingDependencies
from src.integrations.database import SupabaseClient, VectorOperations


@pytest.fixture(autouse=True)
def setup_environment():
    """Set up environment variables for testing."""
    # Set required environment variables for testing
    os.environ["SECRET_KEY"] = "test_secret_key_for_testing_only"
    os.environ["OPENAI_API_KEY"] = "test_openai_key_for_testing_only"
    os.environ["SUPABASE_URL"] = "https://test.supabase.co"
    os.environ["SUPABASE_ANON_KEY"] = "test_anon_key"
    os.environ["SUPABASE_SERVICE_KEY"] = "test_service_key"
    yield
    # Clean up environment variables after tests
    for key in ["SECRET_KEY", "OPENAI_API_KEY", "SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_KEY"]:
        os.environ.pop(key, None)


class TestFullWorkflowIntegration:
    """Integration tests for complete workflow."""
    
    @pytest.mark.integration
    @pytest.mark.workflow
    @pytest.mark.asyncio
    @patch('src.workflows.coordinator.ChatOpenAI')
    async def test_complete_conversation_flow(self, 
                                            mock_chat_openai,
                                            mock_workflow_config, 
                                            mock_agent_state, 
                                            test_model):
        """Test complete conversation flow from message to response."""
        # Mock the ChatOpenAI
        mock_chat_openai.return_value = Mock()
        
        # Initialize components
        coordinator = get_coordinator_agent()
        workflow_manager = get_workflow_manager()
        
        # Process conversation through coordinator with string message
        response = await coordinator.process_message(
            message="Üdvözöllek! Miben segíthetek?",
            user=None,
            session_id="test_session"
        )
        assert response is not None
        assert hasattr(response, 'response_text')
        assert hasattr(response, 'confidence')
    
    @pytest.mark.integration
    @pytest.mark.workflow
    @pytest.mark.asyncio
    @patch('src.workflows.coordinator.ChatOpenAI')
    async def test_agent_coordination(self, 
                                    mock_chat_openai,
                                    mock_workflow_config, 
                                    test_model):
        """Test coordination between multiple agents."""
        # Mock the ChatOpenAI
        mock_chat_openai.return_value = Mock()
        
        # Initialize coordinator
        coordinator = get_coordinator_agent()
        
        # Test message processing with string message
        response = await coordinator.process_message(
            message="Szeretnék kapni a legújabb akciókat",
            user=None,
            session_id="test_session"
        )
        
        assert response is not None
        assert hasattr(response, 'response_text')
        assert hasattr(response, 'confidence')
        assert hasattr(response, 'metadata')


class TestDatabaseIntegration:
    """Integration tests for database operations."""
    
    @pytest.mark.integration
    @pytest.mark.database
    @pytest.mark.asyncio
    @patch('src.integrations.database.supabase_client.create_client')
    async def test_database_operations_flow(self, 
                                          mock_create_client,
                                          mock_supabase_client, 
                                          sample_user_data,
                                          sample_product_data):
        """Test complete database operations flow."""
        # Mock the Supabase client creation
        mock_create_client.return_value = mock_supabase_client
        
        # Initialize database client
        db_client = SupabaseClient()
        
        # Test connection
        connection_result = db_client.test_connection()
        assert connection_result is True
        
        # Test getting client
        client = db_client.get_client()
        assert client is not None
        
        # Test table info
        mock_supabase_client.table.return_value.select.return_value.execute.return_value.data = [sample_user_data]
        table_info = db_client.get_table_info("users")
        assert table_info is not None
    
    @pytest.mark.integration
    @pytest.mark.database
    @pytest.mark.asyncio
    @patch('src.integrations.database.supabase_client.create_client')
    async def test_vector_operations_integration(self, 
                                               mock_create_client,
                                               mock_supabase_client):
        """Test vector operations integration."""
        # Mock the Supabase client creation
        mock_create_client.return_value = mock_supabase_client
        
        # Initialize vector operations
        supabase_client = SupabaseClient()
        vector_ops = VectorOperations(supabase_client, os.environ["OPENAI_API_KEY"])
        
        # Mock the search method
        mock_supabase_client.rpc.return_value.execute.return_value.data = []
        
        # Test vector search
        search_result = await vector_ops.search_similar_products(
            query_text="smartphone",
            limit=5
        )
        assert search_result is not None
        assert isinstance(search_result, list)


class TestAgentIntegration:
    """Integration tests for agent operations."""
    
    @pytest.mark.integration
    @pytest.mark.agent
    @pytest.mark.asyncio
    @patch('src.agents.general.agent.Agent')
    async def test_general_agent_integration(self, mock_agent, test_model):
        """Test general agent integration."""
        # Mock the agent
        mock_agent_instance = Mock()
        mock_agent_instance.run = AsyncMock(return_value=Mock(
            response_text="Üdvözöllek! Miben segíthetek?",
            confidence=0.9
        ))
        mock_agent.return_value = mock_agent_instance
        
        # Test general agent function
        dependencies = GeneralDependencies(
            user_context={"user_id": "test_user"},
            supabase_client=None,
            webshop_api=None
        )
        
        response = await call_general_agent(
            message="Üdvözöllek! Miben segíthetek?",
            dependencies=dependencies
        )
        assert response is not None
        assert hasattr(response, 'response_text')
        assert hasattr(response, 'confidence')
    
    @pytest.mark.integration
    @pytest.mark.agent
    @pytest.mark.asyncio
    @patch('src.agents.marketing.agent.Agent')
    async def test_marketing_agent_integration(self, mock_agent, test_model):
        """Test marketing agent integration with mocked API calls."""
        # Mock the agent run result
        mock_result = Mock()
        mock_result.output = Mock(
            response_text="Itt vannak a legújabb akciók!",
            confidence=0.8,
            promotions=[],
            newsletters=[]
        )
        
        # Mock the agent instance
        mock_agent_instance = Mock()
        mock_agent_instance.run = AsyncMock(return_value=mock_result)
        mock_agent.return_value = mock_agent_instance
        
        # Test marketing agent function with mocked dependencies
        dependencies = MarketingDependencies(
            user_context={"user_id": "test_user"},
            supabase_client=Mock(),  # Mock Supabase client
            webshop_api=Mock()       # Mock WebShop API
        )
        
        # Mock the create_marketing_agent to return our mock
        with patch('src.agents.marketing.agent.create_marketing_agent', return_value=mock_agent_instance):
            response = await call_marketing_agent(
                message="Szeretnék kapni a legújabb akciókat",
                dependencies=dependencies
            )
            
        assert response is not None
        assert hasattr(response, 'response_text')
        assert response.response_text == "Itt vannak a legújabb akciók!"


class TestErrorHandlingIntegration:
    """Integration tests for error handling."""
    
    @pytest.mark.integration
    @pytest.mark.edge_cases
    @pytest.mark.asyncio
    @patch('src.workflows.coordinator.ChatOpenAI')
    async def test_error_handling_flow(self, 
                                     mock_chat_openai,
                                     mock_workflow_config,
                                     test_model):
        """Test error handling flow."""
        # Mock the ChatOpenAI
        mock_chat_openai.return_value = Mock()
        
        # Initialize coordinator
        coordinator = get_coordinator_agent()
        
        # Test with empty string message
        response = await coordinator.process_message(
            message="",
            user=None,
            session_id="test_session"
        )
        assert response is not None
        assert hasattr(response, 'response_text')
        
        # Test with very long message (to test truncation)
        long_message = "A" * 1000
        response = await coordinator.process_message(
            message=long_message,
            user=None,
            session_id="test_session"
        )
        assert response is not None
        assert hasattr(response, 'response_text')
    
    @pytest.mark.integration
    @pytest.mark.edge_cases
    @pytest.mark.asyncio
    @patch('src.workflows.coordinator.ChatOpenAI')
    async def test_fallback_mechanism(self, 
                                    mock_chat_openai,
                                    mock_workflow_config,
                                    test_model):
        """Test fallback mechanism."""
        # Mock the ChatOpenAI
        mock_chat_openai.return_value = Mock()
        
        # Initialize coordinator
        coordinator = get_coordinator_agent()
        
        # Test agent status
        status = coordinator.get_agent_status()
        assert status is not None
        assert "agent_type" in status
        assert "status" in status 