"""
Unit tests for configuration components.
"""

import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.config.security import SecurityConfig
from src.config.logging import LoggingConfig
from src.config.rate_limiting import RateLimitingConfig
from src.config.gdpr_compliance import GDPRComplianceConfig
from src.config.audit_logging import AuditLoggingConfig


class TestSecurityConfig:
    """Unit tests for SecurityConfig."""
    
    @pytest.mark.unit
    @pytest.mark.security
    def test_security_config_initialization(self):
        """Test SecurityConfig initialization."""
        config = SecurityConfig()
        assert config is not None
        assert hasattr(config, 'validate_input')
        assert hasattr(config, 'sanitize_output')
    
    @pytest.mark.unit
    @pytest.mark.security
    def test_security_config_validate_input(self):
        """Test SecurityConfig input validation."""
        config = SecurityConfig()
        is_valid = config.validate_input("test input")
        assert is_valid is True
    
    @pytest.mark.unit
    @pytest.mark.security
    def test_security_config_sanitize_output(self):
        """Test SecurityConfig output sanitization."""
        config = SecurityConfig()
        sanitized = config.sanitize_output("test output")
        assert sanitized is not None
        assert isinstance(sanitized, str)
    
    @pytest.mark.unit
    @pytest.mark.security
    def test_security_config_check_permissions(self):
        """Test SecurityConfig permission checking."""
        config = SecurityConfig()
        has_permission = config.check_permissions("user_123", "read")
        assert has_permission is True


class TestLoggingConfig:
    """Unit tests for LoggingConfig."""
    
    @pytest.mark.unit
    def test_logging_config_initialization(self):
        """Test LoggingConfig initialization."""
        config = LoggingConfig()
        assert config is not None
        assert hasattr(config, 'logger')
    
    @pytest.mark.unit
    def test_logging_config_log_info(self):
        """Test LoggingConfig info logging."""
        config = LoggingConfig()
        config.log_info("Test info message")
        # Should not raise any exceptions
    
    @pytest.mark.unit
    def test_logging_config_log_error(self):
        """Test LoggingConfig error logging."""
        config = LoggingConfig()
        config.log_error("Test error message")
        # Should not raise any exceptions
    
    @pytest.mark.unit
    def test_logging_config_log_warning(self):
        """Test LoggingConfig warning logging."""
        config = LoggingConfig()
        config.log_warning("Test warning message")
        # Should not raise any exceptions


class TestRateLimitingConfig:
    """Unit tests for RateLimitingConfig."""
    
    @pytest.mark.unit
    @pytest.mark.performance
    def test_rate_limiting_config_initialization(self):
        """Test RateLimitingConfig initialization."""
        config = RateLimitingConfig()
        assert config is not None
        assert hasattr(config, 'is_allowed')
        assert hasattr(config, 'record_request')
    
    @pytest.mark.unit
    @pytest.mark.performance
    def test_rate_limiting_config_is_allowed(self):
        """Test RateLimitingConfig rate checking."""
        config = RateLimitingConfig()
        is_allowed = config.is_allowed("user_123")
        assert is_allowed is True
    
    @pytest.mark.unit
    @pytest.mark.performance
    def test_rate_limiting_config_record_request(self):
        """Test RateLimitingConfig request recording."""
        config = RateLimitingConfig()
        config.record_request("user_123")
        # Should not raise any exceptions
    
    @pytest.mark.unit
    @pytest.mark.performance
    def test_rate_limiting_config_get_limits(self):
        """Test RateLimitingConfig limit retrieval."""
        config = RateLimitingConfig()
        limits = config.get_limits("user_123")
        assert limits is not None
        assert isinstance(limits, dict)


class TestGDPRComplianceConfig:
    """Unit tests for GDPRComplianceConfig."""
    
    @pytest.mark.unit
    @pytest.mark.security
    def test_gdpr_compliance_config_initialization(self):
        """Test GDPRComplianceConfig initialization."""
        config = GDPRComplianceConfig()
        assert config is not None
        assert hasattr(config, 'check_consent')
        assert hasattr(config, 'anonymize_data')
    
    @pytest.mark.unit
    @pytest.mark.security
    def test_gdpr_compliance_config_check_consent(self):
        """Test GDPRComplianceConfig consent checking."""
        config = GDPRComplianceConfig()
        has_consent = config.check_consent("user_123", "data_processing")
        assert has_consent is True
    
    @pytest.mark.unit
    @pytest.mark.security
    def test_gdpr_compliance_config_anonymize_data(self):
        """Test GDPRComplianceConfig data anonymization."""
        config = GDPRComplianceConfig()
        anonymized = config.anonymize_data({"name": "John Doe", "email": "john@example.com"})
        assert anonymized is not None
        assert isinstance(anonymized, dict)
        assert "name" not in anonymized or anonymized["name"] != "John Doe"
    
    @pytest.mark.unit
    @pytest.mark.security
    def test_gdpr_compliance_config_get_user_rights(self):
        """Test GDPRComplianceConfig user rights retrieval."""
        config = GDPRComplianceConfig()
        rights = config.get_user_rights("user_123")
        assert rights is not None
        assert isinstance(rights, list)
        assert len(rights) > 0


class TestAuditLoggingConfig:
    """Unit tests for AuditLoggingConfig."""
    
    @pytest.mark.unit
    @pytest.mark.security
    def test_audit_logging_config_initialization(self):
        """Test AuditLoggingConfig initialization."""
        config = AuditLoggingConfig()
        assert config is not None
        assert hasattr(config, 'log_action')
        assert hasattr(config, 'get_audit_trail')
    
    @pytest.mark.unit
    @pytest.mark.security
    def test_audit_logging_config_log_action(self):
        """Test AuditLoggingConfig action logging."""
        config = AuditLoggingConfig()
        config.log_action("user_123", "read", "users", "success")
        # Should not raise any exceptions
    
    @pytest.mark.unit
    @pytest.mark.security
    def test_audit_logging_config_get_audit_trail(self):
        """Test AuditLoggingConfig audit trail retrieval."""
        config = AuditLoggingConfig()
        trail = config.get_audit_trail("user_123")
        assert trail is not None
        assert isinstance(trail, list)
    
    @pytest.mark.unit
    @pytest.mark.security
    def test_audit_logging_config_export_audit_log(self):
        """Test AuditLoggingConfig audit log export."""
        config = AuditLoggingConfig()
        export = config.export_audit_log("user_123", "2024-01-01", "2024-12-31")
        assert export is not None
        assert isinstance(export, dict) 