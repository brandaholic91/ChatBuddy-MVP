"""
Security Integration Tests for ChatBuddy MVP.

Ez a modul teszteli a security komponensek integrációját
a LangGraph workflow-ban.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from src.workflows.langgraph_workflow import (
    _validate_security_context,
    _validate_gdpr_consent,
    route_message
)
from src.config.security import get_threat_detector, InputValidator
from src.config.gdpr_compliance import get_gdpr_compliance, ConsentType, DataCategory
from src.config.audit_logging import get_audit_logger
from src.models.agent import LangGraphState
from langchain_core.messages import HumanMessage


class TestSecurityIntegration:
    """Security integration tesztek."""
    
    @pytest.fixture
    def mock_state(self):
        """Mock LangGraph state."""
        return LangGraphState(
            messages=[HumanMessage(content="Test message")],
            current_agent="coordinator",
            user_context={"user_id": "test_user_123"},
            session_data={"session_id": "test_session"},
            error_count=0,
            retry_attempts=0,
            security_context=MagicMock(),
            gdpr_compliance=MagicMock(),
            audit_logger=MagicMock(),
            agent_data={},
            conversation_history=[],
            processing_start_time=datetime.now(timezone.utc).timestamp(),
            processing_end_time=None,
            tokens_used=None,
            cost=None,
            workflow_step="start",
            next_agent=None,
            should_continue=True
        )
    
    @pytest.mark.asyncio
    async def test_validate_security_context_success(self, mock_state):
        """Security context validation sikeres teszt."""
        result = _validate_security_context(mock_state)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_security_context_missing(self, mock_state):
        """Security context validation hiányzó context teszt."""
        mock_state["security_context"] = None
        result = _validate_security_context(mock_state)
        assert result is True  # Should allow if no security context (development mode)
    
    @pytest.mark.asyncio
    async def test_validate_gdpr_consent_success(self, mock_state):
        """GDPR consent validation sikeres teszt."""
        # Mock GDPR compliance to return True
        mock_state["gdpr_compliance"].check_user_consent = AsyncMock(return_value=True)
        
        result = await _validate_gdpr_consent(
            mock_state, 
            ConsentType.FUNCTIONAL, 
            DataCategory.PERSONAL
        )
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_gdpr_consent_failure(self, mock_state):
        """GDPR consent validation sikertelen teszt."""
        # Mock GDPR compliance to return False
        mock_state["gdpr_compliance"].check_user_consent = AsyncMock(return_value=False)
        
        result = await _validate_gdpr_consent(
            mock_state, 
            ConsentType.MARKETING, 
            DataCategory.MARKETING
        )
        assert result is False
    
    @pytest.mark.asyncio
    async def test_validate_gdpr_consent_no_compliance(self, mock_state):
        """GDPR consent validation nincs compliance teszt."""
        mock_state["gdpr_compliance"] = None
        result = await _validate_gdpr_consent(
            mock_state, 
            ConsentType.FUNCTIONAL, 
            DataCategory.PERSONAL
        )
        assert result is True  # Should allow if no GDPR compliance (development mode)
    
    @pytest.mark.asyncio
    async def test_route_message_normal_input(self, mock_state):
        """Route message normál input teszt."""
        result = route_message(mock_state)
        assert "next" in result
        assert result["next"] in ["product_agent", "order_agent", "recommendation_agent", "marketing_agent", "general_agent"]
    
    @pytest.mark.asyncio
    async def test_route_message_sanitized_input(self, mock_state):
        """Route message sanitized input teszt."""
        # Test with potentially dangerous input
        mock_state["messages"][0].content = "Test message with <script>alert('xss')</script>"
        
        result = route_message(mock_state)
        assert "next" in result
        
        # Check if content was sanitized
        assert "<script>" not in mock_state["messages"][0].content
    
    @pytest.mark.asyncio
    async def test_route_message_threat_detection(self, mock_state):
        """Route message threat detection teszt."""
        # Test with high threat input
        mock_state["messages"][0].content = "sql injection attack UNION SELECT * FROM users"
        
        with patch('src.workflows.langgraph_workflow.get_threat_detector') as mock_detector:
            mock_detector.return_value.detect_threats.return_value = {
                "risk_level": "high",
                "threats": ["SQL injection pattern detected"],
                "threat_count": 1
            }
            
            result = route_message(mock_state)
            assert result["next"] == "general_agent"  # Should route to general agent for high threat
    
    @pytest.mark.asyncio
    async def test_route_message_product_keywords(self, mock_state):
        """Route message termék kulcsszavak teszt."""
        mock_state["messages"][0].content = "Milyen telefonok vannak készleten?"
        
        result = route_message(mock_state)
        assert result["next"] == "product_agent"
    
    @pytest.mark.asyncio
    async def test_route_message_order_keywords(self, mock_state):
        """Route message rendelés kulcsszavak teszt."""
        mock_state["messages"][0].content = "Mi a rendelésem státusza?"
        
        result = route_message(mock_state)
        assert result["next"] == "order_agent"
    
    @pytest.mark.asyncio
    async def test_route_message_marketing_keywords(self, mock_state):
        """Route message marketing kulcsszavak teszt."""
        mock_state["messages"][0].content = "Milyen kedvezmények vannak?"
        
        result = route_message(mock_state)
        assert result["next"] == "marketing_agent"
    
    @pytest.mark.asyncio
    async def test_route_message_recommendation_keywords(self, mock_state):
        """Route message ajánlás kulcsszavak teszt."""
        mock_state["messages"][0].content = "Mit ajánlanál nekem?"
        
        result = route_message(mock_state)
        assert result["next"] == "recommendation_agent"
    
    @pytest.mark.asyncio
    async def test_route_message_general_fallback(self, mock_state):
        """Route message általános fallback teszt."""
        mock_state["messages"][0].content = "Üdvözöllek!"
        
        result = route_message(mock_state)
        assert result["next"] == "general_agent"
    
    @pytest.mark.asyncio
    async def test_route_message_empty_messages(self, mock_state):
        """Route message üres üzenetek teszt."""
        mock_state["messages"] = []
        
        result = route_message(mock_state)
        assert result["next"] == "general_agent"
    
    @pytest.mark.asyncio
    async def test_route_message_invalid_message(self, mock_state):
        """Route message érvénytelen üzenet teszt."""
        mock_state["messages"][0] = "invalid_message"
        
        result = route_message(mock_state)
        assert result["next"] == "general_agent"


class TestInputValidation:
    """Input validation tesztek."""
    
    def test_sanitize_string_normal_input(self):
        """Sanitize string normál input teszt."""
        input_text = "Ez egy normál üzenet."
        result = InputValidator.sanitize_string(input_text)
        assert result == input_text
    
    def test_sanitize_string_xss_attack(self):
        """Sanitize string XSS támadás teszt."""
        input_text = "Test <script>alert('xss')</script> message"
        result = InputValidator.sanitize_string(input_text)
        assert "<script>" not in result
        assert "alert('xss')" not in result
    
    def test_sanitize_string_sql_injection(self):
        """Sanitize string SQL injection teszt."""
        input_text = "Test UNION SELECT * FROM users --"
        result = InputValidator.sanitize_string(input_text)
        assert "UNION SELECT" not in result
    
    def test_sanitize_string_long_input(self):
        """Sanitize string hosszú input teszt."""
        input_text = "A" * 2000  # Very long input
        result = InputValidator.sanitize_string(input_text, max_length=1000)
        assert len(result) <= 1000
    
    def test_validate_email_valid(self):
        """Email validation érvényes teszt."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org"
        ]
        
        for email in valid_emails:
            assert InputValidator.validate_email(email) is True
    
    def test_validate_email_invalid(self):
        """Email validation érvénytelen teszt."""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "user@.com"
        ]
        
        for email in invalid_emails:
            assert InputValidator.validate_email(email) is False
    
    def test_validate_phone_valid(self):
        """Telefon validation érvényes teszt."""
        valid_phones = [
            "+36123456789",
            "06123456789"
        ]
        
        for phone in valid_phones:
            assert InputValidator.validate_phone(phone) is True
    
    def test_validate_phone_invalid(self):
        """Telefon validation érvénytelen teszt."""
        invalid_phones = [
            "123456789",
            "+3612345678",
            "0612345678",
            "invalid"
        ]
        
        for phone in invalid_phones:
            assert InputValidator.validate_phone(phone) is False


class TestThreatDetection:
    """Threat detection tesztek."""
    
    @pytest.fixture
    def threat_detector(self):
        """Threat detector instance."""
        return get_threat_detector()
    
    def test_detect_threats_normal_input(self, threat_detector):
        """Threat detection normál input teszt."""
        input_text = "Ez egy normál üzenet."
        result = threat_detector.detect_threats(input_text)
        
        assert "threats" in result
        assert "risk_level" in result
        assert "threat_count" in result
        assert result["risk_level"] == "low"
        assert result["threat_count"] == 0
    
    def test_detect_threats_xss_attack(self, threat_detector):
        """Threat detection XSS támadás teszt."""
        input_text = "<script>alert('xss')</script>"
        result = threat_detector.detect_threats(input_text)
        
        assert result["risk_level"] == "high"
        assert result["threat_count"] > 0
        assert any("script" in threat.lower() for threat in result["threats"])
    
    def test_detect_threats_sql_injection(self, threat_detector):
        """Threat detection SQL injection teszt."""
        input_text = "UNION SELECT * FROM users WHERE id = 1"
        result = threat_detector.detect_threats(input_text)
        
        assert result["risk_level"] == "high"
        assert result["threat_count"] > 0
        assert any("sql" in threat.lower() for threat in result["threats"])
    
    def test_detect_threats_dangerous_keywords(self, threat_detector):
        """Threat detection veszélyes kulcsszavak teszt."""
        input_text = "admin password secret"
        result = threat_detector.detect_threats(input_text)
        
        assert result["risk_level"] in ["low", "medium"]
        assert result["threat_count"] > 0
    
    def test_should_block_request_normal(self, threat_detector):
        """Should block request normál input teszt."""
        input_text = "Ez egy normál üzenet."
        result = threat_detector.should_block_request(input_text)
        assert result is False
    
    def test_should_block_request_high_threat(self, threat_detector):
        """Should block request magas kockázat teszt."""
        input_text = "<script>alert('xss')</script>"
        result = threat_detector.should_block_request(input_text)
        assert result is True


class TestAuditLogging:
    """Audit logging tesztek."""
    
    @pytest.fixture
    def audit_logger(self):
        """Audit logger instance."""
        return get_audit_logger()
    
    @pytest.mark.asyncio
    async def test_log_security_event(self, audit_logger):
        """Log security event teszt."""
        event_id = await audit_logger.log_security_event(
            event_type="test_threat",
            user_id="test_user",
            details={"test": "data"}
        )
        
        assert event_id != "error"
        assert len(event_id) > 0
    
    @pytest.mark.asyncio
    async def test_log_data_access(self, audit_logger):
        """Log data access teszt."""
        event_id = await audit_logger.log_data_access(
            user_id="test_user",
            data_type="test_data",
            operation="read",
            success=True
        )
        
        assert event_id != "error"
        assert len(event_id) > 0
    
    @pytest.mark.asyncio
    async def test_log_gdpr_event(self, audit_logger):
        """Log GDPR event teszt."""
        event_id = await audit_logger.log_gdpr_event(
            event_type="consent_granted",
            user_id="test_user",
            data_type="personal",
            details={"consent_type": "functional"}
        )
        
        assert event_id != "error"
        assert len(event_id) > 0


if __name__ == "__main__":
    pytest.main([__file__]) 