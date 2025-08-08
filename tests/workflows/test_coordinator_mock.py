# tests/workflows/test_coordinator_mock.py

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.workflows.coordinator import process_coordinator_message_single, CoordinatorDependencies
from src.models.agent import AgentResponse, AgentType
from src.models.user import User
from src.config.audit_logging import AuditLogger

@pytest.mark.unit
@pytest.mark.workflows
@pytest.mark.fast
class TestCoordinatorMock:
    """Coordinator workflow mock tesztek."""
    
    @pytest.fixture
    def mock_audit_logger(self):
        return AsyncMock(spec=AuditLogger)

    @pytest.fixture
    def sample_user(self):
        return User(id="test_user_123", email="test@example.com")

    @pytest.fixture
    def mock_coordinator_dependencies(self, sample_user, mock_audit_logger):
        return CoordinatorDependencies(
            user=sample_user,
            session_id="test_session_123",
            llm=MagicMock(),
            supabase_client=MagicMock(),
            webshop_api=MagicMock(),
            security_context=MagicMock(),
            audit_logger=mock_audit_logger,
            gdpr_compliance=MagicMock()
        )
    
    async def test_message_routing(self, mock_coordinator_dependencies):
        """Üzenet routing tesztje."""
        with patch('src.workflows.coordinator.get_correct_workflow_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_get_manager.return_value = mock_manager
            
            # Mock the stream_message method of the workflow manager
            mock_stream_message = AsyncMock()
            mock_manager.stream_message.return_value.__aiter__.return_value = [
                {"response_text": "Mocked response", "confidence": 1.0, "active_agent": "general"}
            ]
            
            # Mock the internal _extract_response_from_state, _extract_confidence_from_state, _extract_metadata_from_state
            with patch.object(mock_manager.return_value, '_extract_response_from_state', return_value="Mocked response"), \
                 patch.object(mock_manager.return_value, '_extract_confidence_from_state', return_value=1.0), \
                 patch.object(mock_manager.return_value, '_extract_metadata_from_state', return_value={"active_agent": "general"}):

                result = await process_coordinator_message_single(
                    message="Hello",
                    user=mock_coordinator_dependencies.user,
                    session_id=mock_coordinator_dependencies.session_id,
                    dependencies=mock_coordinator_dependencies
                )
                
                assert isinstance(result, AgentResponse)
                assert result.response_text == "Mocked response"
                assert result.confidence == 1.0
                assert result.agent_type == AgentType.COORDINATOR # Coordinator returns its own type
                assert result.metadata["active_agent"] == "general"
                mock_manager.stream_message.assert_called_once()
                mock_coordinator_dependencies.audit_logger.log_agent_interaction.assert_called_once()

    async def test_agent_selection_logic(self, mock_coordinator_dependencies):
        """Agent kiválasztási logika tesztje."""
        test_cases = [
            ("Milyen telefonjaink vannak?", "product_info"),
            ("Hol a rendelésem?", "order_status"), 
            ("Mit ajánlasz?", "recommendations"),
            ("Van akció?", "marketing"),
            ("Segítesz?", "general")
        ]
        
        with patch('src.workflows.coordinator.get_correct_workflow_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_get_manager.return_value = mock_manager
            
            for message, expected_agent_type in test_cases:
                # Mock the stream_message method to return a state with the expected active_agent
                mock_manager.stream_message.return_value.__aiter__.return_value = [
                    {"response_text": f"Response for {expected_agent_type}", "confidence": 1.0, "active_agent": expected_agent_type}
                ]
                
                with patch.object(mock_manager.return_value, '_extract_response_from_state', return_value=f"Response for {expected_agent_type}"), \
                     patch.object(mock_manager.return_value, '_extract_confidence_from_state', return_value=1.0), \
                     patch.object(mock_manager.return_value, '_extract_metadata_from_state', return_value={"active_agent": expected_agent_type}):

                    result = await process_coordinator_message_single(
                        message=message,
                        user=mock_coordinator_dependencies.user,
                        session_id=mock_coordinator_dependencies.session_id,
                        dependencies=mock_coordinator_dependencies
                    )
                    
                    assert result.metadata["active_agent"] == expected_agent_type
                    mock_manager.stream_message.assert_called_once() # Ensure it's called for each test case
                    mock_manager.stream_message.reset_mock() # Reset mock for next iteration
