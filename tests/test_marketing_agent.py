"""
Marketing Agent Tests - LangGraph + Pydantic AI hibrid architektúra.

Ez a modul teszteli a Marketing Agent funkcionalitását:
- Email és SMS küldés
- Kampány létrehozás és kezelés
- Engagement követés
- Kedvezmény kódok generálása
- Marketing metrikák lekérése
- Kosárelhagyás follow-up
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any

from src.agents.marketing.agent import (
    create_marketing_agent,
    MarketingAgent,
    get_marketing_agent,
    process_marketing_query
)
from src.agents.marketing.tools import (
    MarketingDependencies,
    EmailSendResult,
    SMSSendResult,
    CampaignCreateResult,
    EngagementTrackResult,
    DiscountGenerateResult,
    MetricsResult,
    AbandonedCartFollowupResult
)
from src.models.agent import AgentType, AgentResponse
from src.models.user import User
from src.config.security_prompts import SecurityContext, SecurityLevel
from src.config.audit_logging import SecurityAuditLogger


class TestMarketingAgent:
    """Marketing Agent teszt osztály."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock dependencies a marketing agent-hez."""
        return MarketingDependencies(
            supabase_client=AsyncMock(),
            email_service=AsyncMock(),
            sms_service=AsyncMock(),
            user_context={
                "user_id": "test_user_123",
                "email": "test@example.com",
                "phone": "+36123456789",
                "session_id": "test_session_123",
                "preferences": {}
            },
            security_context=SecurityContext(
                user_id="test_user_123",
                session_id="test_session_123",
                security_level=SecurityLevel.SENSITIVE,
                permissions=["marketing"],
                data_access_scope=["email", "sms"],
                gdpr_compliant=True
            ),
            audit_logger=SecurityAuditLogger()
        )
    
    @pytest.fixture
    def test_user(self):
        """Teszt felhasználó."""
        return User(
            id="test_user_123",
            email="test@example.com",
            name="Test User",
            phone="+36123456789"
        )
    
    @pytest.mark.asyncio
    async def test_create_marketing_agent(self):
        """Marketing agent létrehozásának tesztelése."""
        agent = create_marketing_agent()
        assert agent is not None
        assert hasattr(agent, 'run')
    
    @pytest.mark.asyncio
    async def test_marketing_agent_email_query(self, mock_dependencies):
        """Email küldés lekérdezés tesztelése."""
        agent = create_marketing_agent()
        
        # Mock email service response
        mock_dependencies.email_service.send_email.return_value = {
            "success": True,
            "message_id": "email_123"
        }
        
        result = await agent.run(
            "Küldj emailt a test@example.com címre a welcome template-tel",
            deps=mock_dependencies
        )
        
        assert result.output is not None
        assert result.output.response_text is not None
        assert "email" in result.output.response_text.lower() or "üzenet" in result.output.response_text.lower()
    
    @pytest.mark.asyncio
    async def test_marketing_agent_sms_query(self, mock_dependencies):
        """SMS küldés lekérdezés tesztelése."""
        agent = create_marketing_agent()
        
        # Mock SMS service response
        mock_dependencies.sms_service.send_sms.return_value = {
            "success": True,
            "message_id": "sms_123"
        }
        
        result = await agent.run(
            "Küldj SMS-t a +36123456789 számra a notification template-tel",
            deps=mock_dependencies
        )
        
        assert result.output is not None
        assert result.output.response_text is not None
        assert "sms" in result.output.response_text.lower() or "üzenet" in result.output.response_text.lower()
    
    @pytest.mark.asyncio
    async def test_marketing_agent_campaign_query(self, mock_dependencies):
        """Kampány létrehozás lekérdezés tesztelése."""
        agent = create_marketing_agent()
        
        result = await agent.run(
            "Hozz létre egy új kampányt 'Nyári Akció' névvel",
            deps=mock_dependencies
        )
        
        assert result.output is not None
        assert result.output.response_text is not None
        assert "kampány" in result.output.response_text.lower() or "campaign" in result.output.response_text.lower()
    
    @pytest.mark.asyncio
    async def test_marketing_agent_discount_query(self, mock_dependencies):
        """Kedvezmény generálás lekérdezés tesztelése."""
        agent = create_marketing_agent()
        
        result = await agent.run(
            "Generálj egy 10% kedvezmény kódot",
            deps=mock_dependencies
        )
        
        assert result.output is not None
        assert result.output.response_text is not None
        assert "kedvezmény" in result.output.response_text.lower() or "kód" in result.output.response_text.lower()
    
    @pytest.mark.asyncio
    async def test_marketing_agent_metrics_query(self, mock_dependencies):
        """Metrikák lekérdezés tesztelése."""
        agent = create_marketing_agent()
        
        result = await agent.run(
            "Mutasd a marketing metrikákat",
            deps=mock_dependencies
        )
        
        assert result.output is not None
        assert result.output.response_text is not None
        assert "metrikák" in result.output.response_text.lower() or "statisztika" in result.output.response_text.lower()
    
    @pytest.mark.asyncio
    async def test_marketing_agent_abandoned_cart_query(self, mock_dependencies):
        """Kosárelhagyás follow-up lekérdezés tesztelése."""
        agent = create_marketing_agent()
        
        result = await agent.run(
            "Küldj follow-up emailt a kosárelhagyásra",
            deps=mock_dependencies
        )
        
        assert result.output is not None
        assert result.output.response_text is not None
        assert "kosár" in result.output.response_text.lower() or "follow" in result.output.response_text.lower()
    
    @pytest.mark.asyncio
    async def test_marketing_agent_general_query(self, mock_dependencies):
        """Általános marketing lekérdezés tesztelése."""
        agent = create_marketing_agent()
        
        result = await agent.run(
            "Mit tudsz a marketing automatizálásról?",
            deps=mock_dependencies
        )
        
        assert result.output is not None
        assert result.output.response_text is not None
        assert len(result.output.response_text) > 0


class TestMarketingAgentTools:
    """Marketing Agent Tools teszt osztály."""
    
    @pytest.fixture
    def mock_context(self):
        """Mock RunContext a tool tesztekhez."""
        context = MagicMock()
        context.deps = MarketingDependencies(
            supabase_client=AsyncMock(),
            email_service=AsyncMock(),
            sms_service=AsyncMock(),
            user_context={
                "user_id": "test_user_123",
                "email": "test@example.com",
                "phone": "+36123456789"
            },
            security_context=SecurityContext(
                user_id="test_user_123",
                session_id="test_session_123",
                security_level=SecurityLevel.SENSITIVE,
                permissions=["marketing"],
                data_access_scope=["email", "sms"],
                gdpr_compliant=True
            ),
            audit_logger=SecurityAuditLogger()
        )
        return context
    
    @pytest.mark.asyncio
    async def test_send_email_tool(self, mock_context):
        """Email küldés tool tesztelése."""
        from src.agents.marketing.tools import send_email
        
        result = await send_email(
            ctx=mock_context,
            template_id="welcome",
            recipient_email="test@example.com",
            subject="Üdvözöllek!",
            variables={"name": "Test User"}
        )
        
        assert isinstance(result, EmailSendResult)
        assert result.success is True
        assert result.message_id is not None
        assert result.error_message is None
    
    @pytest.mark.asyncio
    async def test_send_sms_tool(self, mock_context):
        """SMS küldés tool tesztelése."""
        from src.agents.marketing.tools import send_sms
        
        result = await send_sms(
            ctx=mock_context,
            template_id="notification",
            recipient_phone="+36123456789",
            variables={"message": "Test message"}
        )
        
        assert isinstance(result, SMSSendResult)
        assert result.success is True
        assert result.message_id is not None
        assert result.error_message is None
    
    @pytest.mark.asyncio
    async def test_create_campaign_tool(self, mock_context):
        """Kampány létrehozás tool tesztelése."""
        from src.agents.marketing.tools import create_campaign
        
        result = await create_campaign(
            ctx=mock_context,
            name="Test Campaign",
            campaign_type="promotional",
            template_id="default",
            target_audience={"age_group": "18-35"},
            schedule=None
        )
        
        assert isinstance(result, CampaignCreateResult)
        assert result.success is True
        assert result.campaign_id is not None
        assert result.error_message is None
    
    @pytest.mark.asyncio
    async def test_track_engagement_tool(self, mock_context):
        """Engagement követés tool tesztelése."""
        from src.agents.marketing.tools import track_engagement
        
        result = await track_engagement(
            ctx=mock_context,
            message_id="msg_123",
            event_type="open",
            metadata={"ip": "192.168.1.1"}
        )
        
        assert isinstance(result, EngagementTrackResult)
        assert result.success is True
        assert result.event_id is not None
        assert result.error_message is None
    
    @pytest.mark.asyncio
    async def test_generate_discount_code_tool(self, mock_context):
        """Kedvezmény kód generálás tool tesztelése."""
        from src.agents.marketing.tools import generate_discount_code
        
        result = await generate_discount_code(
            ctx=mock_context,
            discount_type="percentage",
            value=10.0,
            valid_days=30
        )
        
        assert isinstance(result, DiscountGenerateResult)
        assert result.success is True
        assert result.discount_code is not None
        assert result.error_message is None
    
    @pytest.mark.asyncio
    async def test_get_campaign_metrics_tool(self, mock_context):
        """Kampány metrikák lekérés tool tesztelése."""
        from src.agents.marketing.tools import get_campaign_metrics
        
        result = await get_campaign_metrics(
            ctx=mock_context,
            campaign_id="camp_123",
            date_from="2024-01-01",
            date_to="2024-12-31"
        )
        
        assert isinstance(result, MetricsResult)
        assert result.success is True
        assert result.metrics is not None
        assert result.error_message is None
    
    @pytest.mark.asyncio
    async def test_send_abandoned_cart_followup_tool(self, mock_context):
        """Kosárelhagyás follow-up tool tesztelése."""
        from src.agents.marketing.tools import send_abandoned_cart_followup
        
        cart_items = [
            {"id": "prod_1", "name": "Test Product", "price": 1000.0, "quantity": 1}
        ]
        
        result = await send_abandoned_cart_followup(
            ctx=mock_context,
            cart_id="cart_123",
            user_email="test@example.com",
            cart_items=cart_items
        )
        
        assert isinstance(result, AbandonedCartFollowupResult)
        assert result.success is True
        assert result.message_id is not None
        assert result.discount_code is not None
        assert result.error_message is None


class TestMarketingAgentIntegration:
    """Marketing Agent integrációs tesztek."""
    
    @pytest.fixture
    def marketing_agent(self):
        """Marketing agent instance."""
        return MarketingAgent()
    
    @pytest.fixture
    def test_user(self):
        """Teszt felhasználó."""
        return User(
            id="test_user_123",
            email="test@example.com",
            name="Test User",
            phone="+36123456789"
        )
    
    @pytest.mark.asyncio
    async def test_marketing_agent_process_message(self, marketing_agent, test_user):
        """Marketing agent üzenet feldolgozás tesztelése."""
        response = await marketing_agent.process_message(
            message="Küldj emailt a test@example.com címre",
            user=test_user,
            session_id="test_session_123"
        )
        
        assert isinstance(response, AgentResponse)
        assert response.agent_type == AgentType.MARKETING
        assert response.response_text is not None
        assert len(response.response_text) > 0
        assert response.confidence >= 0.0
        assert response.confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_marketing_agent_error_handling(self, marketing_agent):
        """Marketing agent hibakezelés tesztelése."""
        # Test with invalid input
        response = await marketing_agent.process_message(
            message="",  # Empty message
            user=None,
            session_id="test_session_123"
        )
        
        assert isinstance(response, AgentResponse)
        assert response.agent_type == AgentType.MARKETING
        assert response.response_text is not None
        assert len(response.response_text) > 0
    
    @pytest.mark.asyncio
    async def test_get_marketing_agent_singleton(self):
        """Marketing agent singleton pattern tesztelése."""
        agent1 = get_marketing_agent()
        agent2 = get_marketing_agent()
        
        assert agent1 is agent2  # Same instance
    
    @pytest.mark.asyncio
    async def test_process_marketing_query_function(self, test_user):
        """process_marketing_query függvény tesztelése."""
        response = await process_marketing_query(
            message="Mutasd a marketing metrikákat",
            user=test_user,
            session_id="test_session_123"
        )
        
        assert isinstance(response, AgentResponse)
        assert response.agent_type == AgentType.MARKETING
        assert response.response_text is not None
        assert len(response.response_text) > 0


class TestMarketingAgentSecurity:
    """Marketing Agent biztonsági tesztek."""
    
    @pytest.fixture
    def marketing_agent(self):
        """Marketing agent instance."""
        return MarketingAgent()
    
    @pytest.mark.asyncio
    async def test_marketing_agent_sql_injection_protection(self, marketing_agent):
        """SQL injection védelem tesztelése."""
        malicious_message = "'; DROP TABLE users; --"
        
        response = await marketing_agent.process_message(
            message=malicious_message,
            user=None,
            session_id="test_session_123"
        )
        
        assert isinstance(response, AgentResponse)
        assert response.agent_type == AgentType.MARKETING
        # Should not crash or expose sensitive information
        assert "DROP TABLE" not in response.response_text
    
    @pytest.mark.asyncio
    async def test_marketing_agent_xss_protection(self, marketing_agent):
        """XSS védelem tesztelése."""
        malicious_message = "<script>alert('xss')</script>"
        
        response = await marketing_agent.process_message(
            message=malicious_message,
            user=None,
            session_id="test_session_123"
        )
        
        assert isinstance(response, AgentResponse)
        assert response.agent_type == AgentType.MARKETING
        # Should not contain script tags in response
        assert "<script>" not in response.response_text
    
    @pytest.mark.asyncio
    async def test_marketing_agent_sensitive_data_protection(self, marketing_agent):
        """Érzékeny adatok védelmének tesztelése."""
        sensitive_message = "password: admin123, api_key: secret_key_456"
        
        response = await marketing_agent.process_message(
            message=sensitive_message,
            user=None,
            session_id="test_session_123"
        )
        
        assert isinstance(response, AgentResponse)
        assert response.agent_type == AgentType.MARKETING
        # Should not expose sensitive information
        assert "admin123" not in response.response_text
        assert "secret_key_456" not in response.response_text


class TestMarketingAgentPerformance:
    """Marketing Agent teljesítmény tesztek."""
    
    @pytest.fixture
    def marketing_agent(self):
        """Marketing agent instance."""
        return MarketingAgent()
    
    @pytest.mark.asyncio
    async def test_marketing_agent_response_time(self, marketing_agent):
        """Válaszidő tesztelése."""
        import time
        
        start_time = time.time()
        
        response = await marketing_agent.process_message(
            message="Küldj emailt",
            user=None,
            session_id="test_session_123"
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert isinstance(response, AgentResponse)
        assert response.agent_type == AgentType.MARKETING
        # Response should be reasonably fast (under 10 seconds for this test)
        assert response_time < 10.0
    
    @pytest.mark.asyncio
    async def test_marketing_agent_concurrent_requests(self, marketing_agent):
        """Párhuzamos kérések tesztelése."""
        import asyncio
        
        async def make_request(message: str) -> AgentResponse:
            return await marketing_agent.process_message(
                message=message,
                user=None,
                session_id=f"session_{message}"
            )
        
        # Make multiple concurrent requests
        messages = [
            "Küldj emailt",
            "Küldj SMS-t",
            "Hozz létre kampányt",
            "Generálj kedvezményt",
            "Mutasd metrikákat"
        ]
        
        tasks = [make_request(msg) for msg in messages]
        responses = await asyncio.gather(*tasks)
        
        assert len(responses) == len(messages)
        for response in responses:
            assert isinstance(response, AgentResponse)
            assert response.agent_type == AgentType.MARKETING
            assert response.response_text is not None


# Test data for various scenarios
@pytest.fixture
def marketing_test_data(self) -> Dict[str, Any]:
    """Teszt adatok a marketing agent-hez."""
    return {
        "email_templates": [
            {"id": "welcome", "name": "Üdvözlő Email", "subject": "Üdvözöllek!"},
            {"id": "abandoned_cart", "name": "Kosárelhagyás", "subject": "Visszahívjuk a kosarát!"},
            {"id": "promotional", "name": "Promóciós", "subject": "Különleges ajánlat!"}
        ],
        "sms_templates": [
            {"id": "notification", "name": "Értesítés", "content": "Új üzeneted van!"},
            {"id": "reminder", "name": "Emlékeztető", "content": "Ne felejtsd el a kosaradat!"}
        ],
        "campaign_types": [
            "welcome", "abandoned_cart", "promotional", "newsletter", "birthday"
        ],
        "discount_types": [
            "percentage", "fixed", "free_shipping", "buy_one_get_one"
        ]
    }


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"]) 