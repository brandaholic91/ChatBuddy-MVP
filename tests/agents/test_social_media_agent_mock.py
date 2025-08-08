# tests/agents/test_social_media_agent_mock.py

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.agents.social_media.agent import create_social_media_agent, SocialMediaDependencies, SocialMediaResponse
from src.models.agent import AgentResponse, AgentType
from src.models.user import User
from src.config.audit_logging import AuditLogger

@pytest.fixture
def social_media_agent_instance():
    return create_social_media_agent()

@pytest.fixture
def social_media_agent_instance():
    return create_social_media_agent()


@pytest.mark.unit
@pytest.mark.agents
@pytest.mark.fast
class TestSocialMediaAgentMock:
    
    @pytest.fixture
    def mock_audit_logger(self):
        return AsyncMock(spec=AuditLogger)

    @pytest.fixture
    def sample_user(self):
        return User(id="test_user_123", email="test@example.com")

    @pytest.fixture
    def mock_social_media_dependencies(self, sample_user, mock_audit_logger):
        return SocialMediaDependencies(
            user_context={"user_id": sample_user.id},
            supabase_client=AsyncMock(),
            messenger_api=AsyncMock(),
            whatsapp_api=AsyncMock(),
            template_engine=MagicMock(),
            security_context=MagicMock(),
            audit_logger=mock_audit_logger
        )
    
    async def test_agent_initialization(self, social_media_agent_instance):
        """Agent inicializálás tesztje."""
        assert social_media_agent_instance.model == 'openai:gpt-4o'
        assert social_media_agent_instance.agent_type == AgentType.SOCIAL_MEDIA
    
    async def test_messenger_webhook_processing_success(self, social_media_agent_instance, mock_social_media_dependencies):
        """Messenger webhook feldolgozás sikeres tesztje."""
        mock_webhook_data = {
            "entry": [
                {
                    "messaging": [
                        {
                            "sender": {"id": "messenger_user_1"},
                            "message": {"text": "Hello Messenger"}
                        }
                    ]
                }
            ]
        }

        with patch.object(social_media_agent_instance._agent, 'run') as mock_run:
            mock_run.return_value = SocialMediaResponse(
                response_text="Messenger webhook processed successfully",
                confidence=1.0
            )
            
            result = await social_media_agent_instance.run(
                f"Handle messenger webhook: {mock_webhook_data}", 
                deps=mock_social_media_dependencies
            )
            
            assert isinstance(result, AgentResponse)
            assert "processed successfully" in result.response_text
            assert result.confidence == 1.0
            assert result.agent_type == AgentType.SOCIAL_MEDIA
            mock_social_media_dependencies.audit_logger.log_agent_interaction.assert_called_once()

    async def test_whatsapp_webhook_processing_success(self, social_media_agent_instance, mock_social_media_dependencies):
        """WhatsApp webhook feldolgozás sikeres tesztje."""
        mock_webhook_data = {
            "entry": [
                {
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "messages": [
                                    {
                                        "from": "whatsapp_user_1",
                                        "type": "text",
                                        "text": {"body": "Hello WhatsApp"}
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        with patch.object(social_media_agent_instance._agent, 'run') as mock_run:
            mock_run.return_value = SocialMediaResponse(
                response_text="WhatsApp webhook processed successfully",
                confidence=1.0
            )
            
            result = await social_media_agent_instance.run(
                f"Handle whatsapp webhook: {mock_webhook_data}", 
                deps=mock_social_media_dependencies
            )
            
            assert isinstance(result, AgentResponse)
            assert "processed successfully" in result.response_text
            assert result.confidence == 1.0
            assert result.agent_type == AgentType.SOCIAL_MEDIA
            mock_social_media_dependencies.audit_logger.log_agent_interaction.assert_called_once()

    async def test_error_handling(self, social_media_agent_instance, mock_social_media_dependencies):
        """Hibakezelés tesztje."""
        with patch.object(social_media_agent_instance._agent, 'run') as mock_run:
            mock_run.side_effect = Exception("Social media agent error")
            
            result = await social_media_agent_instance.run("test", deps=mock_social_media_dependencies)
            
            assert isinstance(result, AgentResponse)
            assert "hiba történt" in result.response_text.lower()
            assert result.confidence == 0.0
            assert result.agent_type == AgentType.SOCIAL_MEDIA
            assert "error_type" in result.metadata
            mock_social_media_dependencies.audit_logger.log_agent_interaction.assert_called_once()
            mock_social_media_dependencies.audit_logger.log_error.assert_called_once()
