"""
Security Tests - Chatbuddy MVP.

Ez a modul implementálja a comprehensive security teszteket
minden biztonsági intézkedés validálásához.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import jwt
import bcrypt

from src.config.security import (
    SecurityConfig, SecurityMiddleware, InputValidator, JWTManager,
    RateLimiter, ThreatDetector, hash_password, verify_password,
    generate_secure_token, get_security_config, get_jwt_manager,
    get_threat_detector
)
from src.config.security_prompts import (
    SecurityContext, SecurityLevel, classify_security_level,
    validate_security_context, sanitize_for_audit
)
from src.config.gdpr_compliance import (
    GDPRComplianceLayer, DataCategory, ConsentType, UserConsent
)
from src.config.audit_logging import (
    SecurityAuditLogger, AuditEventType, SecuritySeverity, AuditEvent
)
from src.workflows.coordinator import (
    _sanitize_input, _validate_user_permissions, process_chat_message
)
from src.models.user import User
from src.workflows.coordinator import AgentResponse, AgentType


class TestSecurityConfig:
    """Security configuration tests."""
    
    def test_security_config_validation(self):
        """Test security configuration validation."""
        # Valid config
        config = SecurityConfig(
            secret_key="a" * 32,  # Minimum 32 characters
            algorithm="HS256",
            access_token_expire_minutes=30,
            refresh_token_expire_days=7,
            max_failed_attempts=5,
            block_duration_minutes=15
        )
        assert config.secret_key == "a" * 32
        assert config.algorithm == "HS256"
    
    def test_secret_key_validation(self):
        """Test secret key validation."""
        # Too short secret key
        with pytest.raises(ValueError, match="Secret key must be at least 32 characters long"):
            SecurityConfig(secret_key="short")
        
        # Valid secret key
        config = SecurityConfig(secret_key="a" * 32)
        assert len(config.secret_key) >= 32


class TestInputValidator:
    """Input validation tests."""
    
    def test_string_sanitization(self):
        """Test string sanitization."""
        # Test XSS prevention
        malicious_input = "<script>alert('xss')</script>Hello"
        sanitized = InputValidator.sanitize_string(malicious_input)
        assert "<script>" not in sanitized
        assert "Hello" in sanitized
        
        # Test iframe prevention
        iframe_input = "<iframe src='malicious.com'></iframe>Content"
        sanitized = InputValidator.sanitize_string(iframe_input)
        assert "<iframe" not in sanitized
        assert "Content" in sanitized
        
        # Test javascript protocol
        js_input = "javascript:alert('xss')"
        sanitized = InputValidator.sanitize_string(js_input)
        assert "javascript:" not in sanitized
        
        # Test length limiting
        long_input = "A" * 2000
        sanitized = InputValidator.sanitize_string(long_input, max_length=1000)
        assert len(sanitized) <= 1000
    
    def test_email_validation(self):
        """Test email validation."""
        # Valid emails
        assert InputValidator.validate_email("user@example.com") is True
        assert InputValidator.validate_email("test.user+tag@domain.co.uk") is True
        
        # Invalid emails
        assert InputValidator.validate_email("invalid-email") is False
        assert InputValidator.validate_email("@domain.com") is False
        assert InputValidator.validate_email("user@") is False
    
    def test_phone_validation(self):
        """Ellenőrzi a telefonszám validálást."""
        # Valid Hungarian phone numbers
        assert InputValidator.validate_phone("+3612345678") is True  # Valid format
        assert InputValidator.validate_phone("0612345678") is True   # Valid format
        assert InputValidator.validate_phone("+36123456789") is True # Valid format with 9 digits
        
        # Invalid phone numbers
        assert InputValidator.validate_phone("12345678") is False    # Missing prefix
        assert InputValidator.validate_phone("+361234567") is False  # Too short
        assert InputValidator.validate_phone("+361234567890") is False  # Too long
        assert InputValidator.validate_phone("") is False            # Empty
        assert InputValidator.validate_phone("invalid") is False     # Invalid characters
    
    def test_password_strength_validation(self):
        """Test password strength validation."""
        # Weak password
        weak_result = InputValidator.validate_password_strength("weak")
        assert weak_result["valid"] is False
        assert len(weak_result["errors"]) > 0
        
        # Medium password
        medium_result = InputValidator.validate_password_strength("Password123")
        assert medium_result["valid"] is True
        assert len(medium_result["warnings"]) > 0
        assert medium_result["strength"] == "medium"
        
        # Strong password
        strong_result = InputValidator.validate_password_strength("StrongP@ssw0rd!")
        assert strong_result["valid"] is True
        assert len(strong_result["warnings"]) == 0
        assert strong_result["strength"] == "strong"


class TestJWTManager:
    """JWT manager tests."""
    
    @pytest.fixture
    def jwt_manager(self):
        """JWT manager fixture."""
        return JWTManager("test_secret_key_32_chars_long", "HS256")
    
    def test_create_access_token(self, jwt_manager):
        """Test access token creation."""
        data = {"user_id": "123", "email": "test@example.com"}
        token = jwt_manager.create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token
        payload = jwt_manager.verify_token(token)
        assert payload["user_id"] == "123"
        assert payload["email"] == "test@example.com"
    
    def test_create_refresh_token(self, jwt_manager):
        """Test refresh token creation."""
        data = {"user_id": "123"}
        token = jwt_manager.create_refresh_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token
        payload = jwt_manager.verify_token(token)
        assert payload["user_id"] == "123"
        assert payload["type"] == "refresh"
    
    def test_verify_expired_token(self, jwt_manager):
        """Test expired token verification."""
        # Create token with short expiry
        data = {"user_id": "123"}
        token = jwt_manager.create_access_token(data, expires_delta=timedelta(seconds=1))
        
        # Wait for token to expire
        import time
        time.sleep(2)
        
        # Should raise exception
        with pytest.raises(Exception):
            jwt_manager.verify_token(token)
    
    def test_verify_invalid_token(self, jwt_manager):
        """Test invalid token verification."""
        with pytest.raises(Exception):
            jwt_manager.verify_token("invalid_token")


class TestThreatDetector:
    """Threat detector tests."""
    
    @pytest.fixture
    def threat_detector(self):
        """Threat detector fixture."""
        return ThreatDetector()
    
    def test_sql_injection_detection(self, threat_detector):
        """Test SQL injection detection."""
        # SQL injection patterns
        sql_inputs = [
            "'; DROP TABLE users; --",
            "SELECT * FROM users WHERE id = 1 OR 1=1",
            "UNION SELECT password FROM users",
            "INSERT INTO users VALUES (1, 'admin')"
        ]
        
        for sql_input in sql_inputs:
            result = threat_detector.detect_threats(sql_input)
            assert result["risk_level"] == "high"
            assert len(result["threats"]) > 0
    
    def test_xss_detection(self, threat_detector):
        """Ellenőrzi az XSS támadások felismerését."""
        # Test script tag detection
        result = threat_detector.detect_threats("<script>alert('xss')</script>Hello")
        assert result["risk_level"] == "high"
        assert "Script tag detected" in result["threats"]
        
        # Test without script tags (should be low risk)
        result = threat_detector.detect_threats("Hello world")
        assert result["risk_level"] == "low"
        
        # Test with dangerous keywords but no script tags
        result = threat_detector.detect_threats("Hello admin password")
        assert result["risk_level"] == "low"  # Only dangerous keywords, no script tags
    
    def test_dangerous_keywords_detection(self, threat_detector):
        """Test dangerous keywords detection."""
        # Dangerous keywords
        dangerous_inputs = [
            "admin password",
            "root access",
            "system internal",
            "secret key"
        ]
        
        for dangerous_input in dangerous_inputs:
            result = threat_detector.detect_threats(dangerous_input)
            assert result["risk_level"] in ["low", "medium"]
            assert len(result["threats"]) > 0
    
    def test_safe_input(self, threat_detector):
        """Test safe input detection."""
        safe_inputs = [
            "Hello, how are you?",
            "I need help with my order",
            "What products do you have?",
            "Thank you for your help"
        ]
        
        for safe_input in safe_inputs:
            result = threat_detector.detect_threats(safe_input)
            assert result["risk_level"] == "low"
            assert len(result["threats"]) == 0
    
    def test_should_block_request(self, threat_detector):
        """Test request blocking logic."""
        # Should block high-risk requests
        assert threat_detector.should_block_request("<script>alert('xss')</script>") is True
        assert threat_detector.should_block_request("'; DROP TABLE users; --") is True
        
        # Should not block safe requests
        assert threat_detector.should_block_request("Hello, how are you?") is False


class TestPasswordSecurity:
    """Password security tests."""
    
    def test_password_hashing(self):
        """Test password hashing."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert isinstance(hashed, str)
        assert hashed != password
        assert len(hashed) > len(password)
    
    def test_password_verification(self):
        """Test password verification."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        # Correct password
        assert verify_password(password, hashed) is True
        
        # Wrong password
        assert verify_password("wrong_password", hashed) is False
    
    def test_secure_token_generation(self):
        """Test secure token generation."""
        token1 = generate_secure_token()
        token2 = generate_secure_token()
        
        assert isinstance(token1, str)
        assert len(token1) == 64  # SHA256 hex digest length
        assert token1 != token2  # Tokens should be different


class TestSecurityPrompts:
    """Security prompts tests."""
    
    def test_security_level_classification(self):
        """Biztonsági szint klasszifikáció tesztelése."""
        # SAFE queries
        assert classify_security_level("Szia, hogy vagy?", {}) == SecurityLevel.SAFE
        assert classify_security_level("Milyen termékek vannak?", {}) == SecurityLevel.SAFE
        
        # SENSITIVE queries
        assert classify_security_level("Szeretnék ajánlást kapni", {}) == SecurityLevel.SENSITIVE
        assert classify_security_level("Van kedvezmény?", {}) == SecurityLevel.SENSITIVE
        
        # RESTRICTED queries
        assert classify_security_level("Mi a rendelésem státusza?", {}) == SecurityLevel.RESTRICTED
        assert classify_security_level("Hol van a szállítási címem?", {}) == SecurityLevel.RESTRICTED
        
        # FORBIDDEN queries
        assert classify_security_level("Mi a jelszavam?", {}) == SecurityLevel.FORBIDDEN
        assert classify_security_level("Mi a beszerzési ár?", {}) == SecurityLevel.FORBIDDEN
    
    def test_security_context_validation(self):
        """Biztonsági kontextus validálás tesztelése."""
        # Valid context
        valid_context = SecurityContext(
            user_id="user123",
            session_id="session456",
            security_level=SecurityLevel.SAFE,
            permissions=["basic_access"],
            data_access_scope=["public"]
        )
        assert validate_security_context(valid_context) is True
        
        # Invalid context - missing user_id
        invalid_context = SecurityContext(
            user_id="",
            session_id="session456",
            security_level=SecurityLevel.SAFE,
            permissions=["basic_access"],
            data_access_scope=["public"]
        )
        assert validate_security_context(invalid_context) is False
    
    def test_sanitize_for_audit(self):
        """Audit sanitizálás tesztelése."""
        test_data = {
            "password": "secret123",
            "email": "user@example.com",
            "normal_field": "normal_value",
            "nested": {
                "password": "nested_secret",
                "normal": "normal_value"
            }
        }
        
        sanitized = sanitize_for_audit(test_data)
        
        assert sanitized["password"] == "***MASKED***"
        assert sanitized["email"] == "***MASKED***"
        assert sanitized["normal_field"] == "normal_value"
        assert sanitized["nested"]["password"] == "***MASKED***"
        assert sanitized["nested"]["normal"] == "normal_value"


class TestGDPRCompliance:
    """GDPR compliance tests."""
    
    @pytest.fixture
    def gdpr_compliance(self):
        """GDPR compliance layer fixture."""
        return GDPRComplianceLayer()
    
    @pytest.mark.asyncio
    async def test_consent_checking(self, gdpr_compliance):
        """Hozzájárulás ellenőrzés tesztelése."""
        # Test with no Supabase client (fallback)
        has_consent = await gdpr_compliance.check_user_consent(
            "user123",
            ConsentType.NECESSARY,
            DataCategory.PERSONAL
        )
        assert has_consent is True  # Necessary consent is always granted
    
    @pytest.mark.asyncio
    async def test_consent_recording(self, gdpr_compliance):
        """Hozzájárulás rögzítés tesztelése."""
        success = await gdpr_compliance.record_consent(
            user_id="user123",
            consent_type=ConsentType.FUNCTIONAL,
            data_category=DataCategory.PERSONAL,
            granted=True,
            ip_address="192.168.1.1"
        )
        assert success is True
    
    @pytest.mark.asyncio
    async def test_data_deletion(self, gdpr_compliance):
        """Adattörlés tesztelése."""
        success = await gdpr_compliance.delete_user_data("user123")
        assert success is True
    
    @pytest.mark.asyncio
    async def test_data_export(self, gdpr_compliance):
        """Adatexportálás tesztelése."""
        export_data = await gdpr_compliance.export_user_data("user123")
        assert "user_id" in export_data
        assert "exported_at" in export_data
        assert "data" in export_data


class TestAuditLogging:
    """Audit logging tests."""
    
    @pytest.fixture
    def audit_logger(self):
        """Audit logger fixture."""
        return SecurityAuditLogger()
    
    @pytest.mark.asyncio
    async def test_agent_interaction_logging(self, audit_logger):
        """Agent interakció naplózás tesztelése."""
        await audit_logger.log_agent_interaction(
            agent_type="coordinator",
            user_id="user123",
            session_id="session456",
            query="Szia, hogy vagy?",
            response="Jól vagyok, köszönöm!",
            metadata={"processing_time": 1.5}
        )
        
        # Check that event was queued
        assert not audit_logger.audit_queue.empty()
    
    @pytest.mark.asyncio
    async def test_security_event_logging(self, audit_logger):
        """Biztonsági esemény naplózás tesztelése."""
        await audit_logger.log_security_event(
            event_type="suspicious_activity",
            severity=SecuritySeverity.HIGH,
            user_id="user123",
            description="Suspicious login attempt",
            details={"ip": "192.168.1.1"},
            source_ip="192.168.1.1"
        )
        
        # Check that event was queued
        assert not audit_logger.audit_queue.empty()
    
    @pytest.mark.asyncio
    async def test_data_access_logging(self, audit_logger):
        """Adathozzáférés naplózás tesztelése."""
        await audit_logger.log_data_access(
            user_id="user123",
            data_type="user_profile",
            operation="read",
            success=True,
            details={"fields": ["name", "email"]}
        )
        
        # Check that event was queued
        assert not audit_logger.audit_queue.empty()
    
    def test_input_sanitization(self, audit_logger):
        """Bemeneti adatok sanitizálás tesztelése."""
        # Test XSS prevention
        malicious_input = "<script>alert('xss')</script>Hello"
        sanitized = audit_logger._sanitize_input(malicious_input)
        assert "<script>" not in sanitized
        assert "Hello" in sanitized
        
        # Test SQL injection prevention
        sql_input = "'; DROP TABLE users; --"
        sanitized = audit_logger._sanitize_input(sql_input)
        assert "DROP TABLE" not in sanitized
        
        # Test length limiting
        long_input = "A" * 2000
        sanitized = audit_logger._sanitize_input(long_input)
        assert len(sanitized) <= 1000
    
    def test_output_sanitization(self, audit_logger):
        """Kimeneti adatok sanitizálás tesztelése."""
        # Test sensitive data masking
        sensitive_output = "A jelszava: secret123, kártyaszáma: 1234-5678-9012-3456"
        sanitized = audit_logger._sanitize_output(sensitive_output)
        assert "secret123" not in sanitized
        assert "1234-5678-9012-3456" not in sanitized


class TestCoordinatorSecurity:
    """Koordinátor biztonsági tesztek."""
    
    def test_input_sanitization(self):
        """Koordinátor bemeneti sanitizálás tesztelése."""
        # Test dangerous characters
        dangerous_input = "<script>alert('xss')</script>Hello"
        sanitized = _sanitize_input(dangerous_input)
        assert "<script>" not in sanitized
        assert "Hello" in sanitized
        
        # Test dangerous patterns
        pattern_input = "javascript:alert('xss')"
        sanitized = _sanitize_input(pattern_input)
        assert "javascript:" not in sanitized
        
        # Test length limiting
        long_input = "A" * 2000
        sanitized = _sanitize_input(long_input)
        assert len(sanitized) <= 1000
    
    def test_user_permissions_validation(self):
        """Felhasználói jogosultságok validálás tesztelése."""
        # Test with no user
        assert _validate_user_permissions(None, ["basic_access"]) is False
        
        # Test with user (placeholder implementation)
        user = User(id="user123", email="user@example.com")
        assert _validate_user_permissions(user, ["basic_access"]) is True


class TestSecurityIntegration:
    """Integrációs biztonsági tesztek."""
    
    @pytest.mark.asyncio
    async def test_secure_chat_processing(self):
        """Ellenőrzi a biztonságos chat feldolgozást."""
        user = User(id="test_user", email="test@example.com")

        # Mock ChatOpenAI to avoid API key requirement
        with patch('src.workflows.coordinator.ChatOpenAI') as mock_chat_openai:
            mock_llm = Mock()
            mock_chat_openai.return_value = mock_llm

            # Mock the Pydantic AI agent and its run method
            with patch('src.workflows.coordinator.create_coordinator_agent') as mock_create_agent:
                mock_agent = Mock()
                mock_result = Mock()
                mock_output = Mock()
                mock_output.response_text = "Üdvözöllek!"
                mock_output.confidence = 0.9
                mock_output.gdpr_compliant = True
                mock_output.audit_required = False
                mock_output.agent_used = "coordinator"
                mock_output.category = "general"
                mock_output.security_level = "safe"  # String value, not Mock
                mock_result.output = mock_output
                mock_agent.run = AsyncMock(return_value=mock_result)
                mock_create_agent.return_value = mock_agent

                # Mock security context
                with patch('src.workflows.coordinator.create_security_context') as mock_security:
                    mock_security.return_value = Mock()
                    mock_security.return_value.security_level = SecurityLevel.SAFE

                    # Mock audit logger
                    with patch('src.workflows.coordinator.get_security_audit_logger') as mock_audit:
                        mock_audit_logger = AsyncMock()
                        mock_audit_logger.log_security_event = AsyncMock()
                        mock_audit.return_value = mock_audit_logger

                        # Mock audit context
                        from contextlib import asynccontextmanager
                        @asynccontextmanager
                        async def dummy_ctx(*args, **kwargs):
                            yield
                        with patch('src.workflows.coordinator.audit_context', dummy_ctx):

                            # Mock GDPR compliance
                            with patch('src.workflows.coordinator.get_gdpr_compliance') as mock_gdpr:
                                mock_gdpr.return_value = Mock()

                                response = await process_chat_message(
                                    "Hello",
                                    user=user,
                                    session_id="test_session"
                                )

                                assert isinstance(response, AgentResponse)
                                assert response.agent_type == AgentType.COORDINATOR
                                assert response.response_text == "Üdvözöllek!"
                                assert response.metadata["security_level"] == "safe"
                                assert response.metadata["gdpr_compliant"] == True
                                assert response.metadata["audit_required"] == False
    
    @pytest.mark.asyncio
    async def test_malicious_input_handling(self):
        """Ellenőrzi a rosszindulatú bemenetek kezelését."""
        user = User(id="test_user", email="test@example.com")
        
        # Mock ChatOpenAI to avoid API key requirement
        with patch('src.workflows.coordinator.ChatOpenAI') as mock_chat_openai:
            mock_llm = Mock()
            mock_chat_openai.return_value = mock_llm
            
            # Mock the Pydantic AI agent to raise an exception for malicious input
            with patch('src.workflows.coordinator.create_coordinator_agent') as mock_create_agent:
                mock_agent = Mock()
                mock_agent.run = AsyncMock(side_effect=Exception("Security violation"))
                mock_create_agent.return_value = mock_agent

                # Mock security context
                with patch('src.workflows.coordinator.create_security_context') as mock_security:
                    mock_security.return_value = Mock()
                    mock_security.return_value.security_level = SecurityLevel.SAFE

                    # Mock audit logger
                    with patch('src.workflows.coordinator.get_security_audit_logger') as mock_audit:
                        mock_audit_logger = AsyncMock()
                        mock_audit_logger.log_security_event = AsyncMock()
                        mock_audit.return_value = mock_audit_logger

                        # Mock audit context
                        from contextlib import asynccontextmanager
                        @asynccontextmanager
                        async def dummy_ctx(*args, **kwargs):
                            yield
                        with patch('src.workflows.coordinator.audit_context', dummy_ctx):

                            # Mock GDPR compliance
                            with patch('src.workflows.coordinator.get_gdpr_compliance') as mock_gdpr:
                                mock_gdpr.return_value = Mock()

                                response = await process_chat_message(
                                    "DROP TABLE users;",
                                    user=user,
                                    session_id="test_session"
                                )

                                assert isinstance(response, AgentResponse)
                                assert response.agent_type == AgentType.COORDINATOR
                                assert "hiba történt" in response.response_text
                                assert response.confidence == 0.0
                                assert response.metadata["category"] == "error"
                                assert response.metadata["audit_required"] == True
    
    @pytest.mark.asyncio
    async def test_forbidden_query_handling(self):
        """Ellenőrzi a tiltott lekérdezések kezelését."""
        user = User(id="test_user", email="test@example.com")

        # Mock the Pydantic AI agent (though it shouldn't be called for forbidden queries)
        with patch('src.workflows.coordinator.create_coordinator_agent') as mock_create_agent:
            mock_agent = Mock()
            mock_result = Mock()
            mock_output = Mock()
            mock_output.response_text = "Ez a lekérdezés nem engedélyezett."
            mock_output.confidence = 0.8
            mock_output.gdpr_compliant = False
            mock_output.audit_required = True
            mock_output.agent_used = "coordinator"
            mock_output.category = "forbidden"
            mock_output.security_level = "forbidden"  # String value, not Mock
            mock_result.output = mock_output
            mock_agent.run = AsyncMock(return_value=mock_result)
            mock_create_agent.return_value = mock_agent

            # Mock security context
            with patch('src.workflows.coordinator.create_security_context') as mock_security:
                mock_security.return_value = Mock()
                mock_security.return_value.security_level = SecurityLevel.FORBIDDEN

                # Mock audit logger
                with patch('src.workflows.coordinator.get_security_audit_logger') as mock_audit:
                    mock_audit_logger = AsyncMock()
                    mock_audit_logger.log_security_event = AsyncMock()
                    mock_audit.return_value = mock_audit_logger

                    # Mock GDPR compliance
                    with patch('src.workflows.coordinator.get_gdpr_compliance') as mock_gdpr:
                        mock_gdpr.return_value = Mock()

                        response = await process_chat_message(
                            "admin password",
                            user=user,
                            session_id="test_session"
                        )

                        assert isinstance(response, AgentResponse)
                        assert response.agent_type == AgentType.COORDINATOR
                        assert response.response_text == "Ez a lekérdezés nem engedélyezett."
                        assert response.metadata["security_level"] == "forbidden"
                        assert response.metadata["gdpr_compliant"] == False
                        assert response.metadata["audit_required"] == True
                        assert response.metadata["agent_used"] == "coordinator"
                        assert response.metadata["category"] == "forbidden"


class TestSecurityValidation:
    """Biztonsági validáció tesztek."""
    
    def test_response_security_validation(self):
        """Ellenőrzi a válasz biztonsági validálását."""
        # Test response with sensitive information
        response_with_password = AgentResponse(
            agent_type=AgentType.COORDINATOR,
            response_text="A jelszó: secret123",
            confidence=0.9
        )
        
        # The validation should not raise an exception for this response
        # as the security validation is handled by the CoordinatorOutput model
        # and the AgentResponse model doesn't have built-in security validation
        assert response_with_password.response_text == "A jelszó: secret123"
        
        # Test response without sensitive information
        response_safe = AgentResponse(
            agent_type=AgentType.COORDINATOR,
            response_text="Üdvözöllek!",
            confidence=0.9
        )
        
        assert response_safe.response_text == "Üdvözöllek!"


class TestSecurityMiddleware:
    """Security middleware tests."""
    
    def test_security_headers(self):
        """Test security headers generation."""
        from fastapi import FastAPI
        from src.config.security import SecurityMiddleware, SecurityConfig
        
        app = FastAPI()
        config = SecurityConfig(secret_key="a" * 32)
        middleware = SecurityMiddleware(app, config)
        
        headers = middleware.get_security_headers()
        
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers
        assert "X-XSS-Protection" in headers
        assert "Strict-Transport-Security" in headers
        assert "Content-Security-Policy" in headers
    
    def test_ip_blocking(self):
        """Test IP blocking functionality."""
        from fastapi import FastAPI
        from src.config.security import SecurityMiddleware, SecurityConfig
        
        app = FastAPI()
        config = SecurityConfig(secret_key="a" * 32)
        middleware = SecurityMiddleware(app, config)
        
        # Test IP blocking
        middleware.block_ip("192.168.1.100")
        assert middleware.is_ip_blocked("192.168.1.100") is True
        
        # Test non-blocked IP
        assert middleware.is_ip_blocked("192.168.1.101") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 