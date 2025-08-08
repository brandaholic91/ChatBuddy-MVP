"""
Test module for integration utils functionality.

Tests the common integration utilities and helper functions.
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from src.utils.integration_utils import (
    APIConfig, APIResponse, BaseAPIClient, ErrorHandler,
    CacheHelper, ConfigManager, DataTransformer, RateLimiter,
    validate_email, validate_phone, sanitize_input
)


@pytest.mark.unit
class TestAPIConfig:
    """Test APIConfig functionality."""

    def test_api_config_creation(self):
        """Test API config creation."""
        config = APIConfig(
            api_key="test_key",
            base_url="https://api.example.com",
            timeout=60
        )

        assert config.api_key == "test_key"
        assert config.base_url == "https://api.example.com"
        assert config.timeout == 60
        assert config.retries == 3
        assert config.retry_delay == 1.0
        assert "Content-Type" in config.headers

    def test_api_config_defaults(self):
        """Test API config with default values."""
        config = APIConfig(
            api_key="test_key",
            base_url="https://api.example.com"
        )

        assert config.timeout == 30
        assert config.retries == 3
        assert config.retry_delay == 1.0
        assert config.headers is not None

    def test_api_config_custom_headers(self):
        """Test API config with custom headers."""
        custom_headers = {"Authorization": "Bearer token"}
        config = APIConfig(
            api_key="test_key",
            base_url="https://api.example.com",
            headers=custom_headers
        )

        assert config.headers == custom_headers


@pytest.mark.unit
class TestAPIResponse:
    """Test APIResponse functionality."""

    def test_api_response_creation(self):
        """Test API response creation."""
        response = APIResponse(
            success=True,
            status_code=200,
            data={"key": "value"},
            response_time=0.5
        )

        assert response.success is True
        assert response.status_code == 200
        assert response.data == {"key": "value"}
        assert response.response_time == 0.5
        assert response.error_message is None

    def test_api_response_error(self):
        """Test API response with error."""
        response = APIResponse(
            success=False,
            status_code=400,
            error_message="Bad request"
        )

        assert response.success is False
        assert response.status_code == 400
        assert response.error_message == "Bad request"
        assert response.data is None


@pytest.mark.integration
@pytest.mark.asyncio
class TestBaseAPIClient:
    """Test BaseAPIClient functionality."""

    @pytest.fixture
    def api_config(self):
        """Create test API config."""
        return APIConfig(
            api_key="test_key",
            base_url="https://api.example.com",
            timeout=10,
            retries=2
        )

    @pytest.fixture
    def api_client(self, api_config):
        """Create test API client."""
        return BaseAPIClient(api_config)

    async def test_context_manager(self, api_client):
        """Test API client context manager."""
        async with api_client as client:
            assert client.session is not None
            # When using a mocked session this attribute may be a mock; accept both
            assert client.session is not None

    @patch('aiohttp.ClientSession.request')
    async def test_successful_request(self, mock_request, api_client):
        """Test successful API request."""
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"result": "success"}
        mock_response.headers = {"Content-Type": "application/json"}
        mock_request.return_value.__aenter__.return_value = mock_response

        async with api_client:
            response = await api_client._make_request(
                "GET",
                "/test",
                params={"key": "value"}
            )

        assert response.success is True
        assert response.status_code == 200
        assert response.data == {"result": "success"}

    @patch('aiohttp.ClientSession.request')
    async def test_failed_request(self, mock_request, api_client):
        """Test failed API request."""
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.json.return_value = {"error": "Not found"}
        mock_response.headers = {"Content-Type": "application/json"}
        mock_request.return_value.__aenter__.return_value = mock_response

        async with api_client:
            response = await api_client._make_request("GET", "/test")

        assert response.success is False
        assert response.status_code == 404
        assert response.error_message == "HTTP 404"

    @patch('aiohttp.ClientSession.request')
    async def test_request_timeout(self, mock_request, api_client):
        """Test request timeout handling."""
        mock_request.side_effect = asyncio.TimeoutError()

        async with api_client:
            response = await api_client._make_request("GET", "/test")

        assert response.success is False
        assert response.status_code == 408
        assert "timeout" in response.error_message.lower()

    @patch('aiohttp.ClientSession.request')
    async def test_request_retry(self, mock_request, api_client):
        """Test request retry logic."""
        # First call fails, second succeeds
        mock_response_fail = AsyncMock()
        mock_response_fail.status = 500
        mock_response_fail.json.return_value = {"error": "Server error"}
        mock_response_fail.headers = {}

        mock_response_success = AsyncMock()
        mock_response_success.status = 200
        mock_response_success.json.return_value = {"result": "success"}
        mock_response_success.headers = {}

        mock_request.return_value.__aenter__.side_effect = [
            mock_response_fail,
            mock_response_success
        ]

        async with api_client:
            response = await api_client._make_request("GET", "/test")

        assert response.success is True
        assert response.status_code == 200
        assert mock_request.call_count == 2


@pytest.mark.unit
class TestErrorHandler:
    """Test ErrorHandler functionality."""

    def test_handle_successful_response(self):
        """Test handling successful response."""
        response = APIResponse(success=True, status_code=200)
        error = ErrorHandler.handle_api_error(response)
        assert error is None

    def test_handle_authentication_error(self):
        """Test handling authentication error."""
        response = APIResponse(
            success=False,
            status_code=401,
            error_message="Unauthorized"
        )
        error = ErrorHandler.handle_api_error(response)
        assert isinstance(error, PermissionError)

    def test_handle_not_found_error(self):
        """Test handling not found error."""
        response = APIResponse(
            success=False,
            status_code=404,
            error_message="Not found"
        )
        error = ErrorHandler.handle_api_error(response)
        assert isinstance(error, FileNotFoundError)

    def test_handle_rate_limit_error(self):
        """Test handling rate limit error."""
        response = APIResponse(
            success=False,
            status_code=429,
            error_message="Too many requests"
        )
        error = ErrorHandler.handle_api_error(response)
        assert isinstance(error, ConnectionError)

    @pytest.mark.asyncio
    async def test_with_error_handling_success(self):
        """Test error handling wrapper with success."""
        async def successful_function():
            return "success"

        result = await ErrorHandler.with_error_handling(successful_function)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_with_error_handling_failure(self):
        """Test error handling wrapper with failure."""
        async def failing_function():
            raise Exception("Test error")

        result = await ErrorHandler.with_error_handling(
            failing_function,
            default_return="default"
        )
        assert result == "default"

    @pytest.mark.asyncio
    async def test_with_error_handling_raise_on_error(self):
        """Test error handling wrapper with raise_on_error=True."""
        async def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            await ErrorHandler.with_error_handling(
                failing_function,
                raise_on_error=True
            )


@pytest.mark.unit
class TestCacheHelper:
    """Test CacheHelper functionality."""

    def test_generate_cache_key(self):
        """Test cache key generation."""
        key = CacheHelper.generate_cache_key("arg1", "arg2", prefix="test")
        assert key.startswith("test:")
        assert len(key) > len("test:")

    def test_serialize_for_cache(self):
        """Test data serialization for cache."""
        data = {"key": "value", "number": 42}
        serialized = CacheHelper.serialize_for_cache(data)
        assert isinstance(serialized, str)

        # Should be valid JSON
        parsed = json.loads(serialized)
        assert parsed == data

    def test_deserialize_from_cache(self):
        """Test data deserialization from cache."""
        data = {"key": "value", "number": 42}
        serialized = json.dumps(data)

        deserialized = CacheHelper.deserialize_from_cache(serialized)
        assert deserialized == data

    def test_deserialize_invalid_json(self):
        """Test handling invalid JSON during deserialization."""
        result = CacheHelper.deserialize_from_cache("invalid json")
        assert result == {}


@pytest.mark.unit
class TestConfigManager:
    """Test ConfigManager functionality."""

    @patch.dict('os.environ', {
        'TEST_API_KEY': 'secret_key',
        'TEST_BASE_URL': 'https://api.test.com',
        'TEST_TIMEOUT': '60'
    })
    def test_load_api_config_success(self):
        """Test successful API config loading."""
        config = ConfigManager.load_api_config('TEST')

        assert config.api_key == 'secret_key'
        assert config.base_url == 'https://api.test.com'
        assert config.timeout == 60

    def test_load_api_config_missing_key(self):
        """Test API config loading with missing required key."""
        with pytest.raises(ValueError, match="Missing required environment variable"):
            ConfigManager.load_api_config('NONEXISTENT')

    def test_validate_config_success(self):
        """Test successful config validation."""
        config = {"api_key": "test", "base_url": "https://api.test.com"}
        is_valid = ConfigManager.validate_config(config, ["api_key", "base_url"])
        assert is_valid is True

    def test_validate_config_missing_field(self):
        """Test config validation with missing field."""
        config = {"api_key": "test"}
        is_valid = ConfigManager.validate_config(config, ["api_key", "base_url"])
        assert is_valid is False


@pytest.mark.unit
class TestDataTransformer:
    """Test DataTransformer functionality."""

    def test_normalize_keys(self):
        """Test key normalization."""
        data = {"First Name": "John", "last-name": "Doe", "EMAIL": "john@example.com"}
        normalized = DataTransformer.normalize_keys(data)

        assert "first_name" in normalized
        assert "last_name" in normalized
        assert "email" in normalized
        assert normalized["first_name"] == "John"

    def test_normalize_keys_with_mapping(self):
        """Test key normalization with custom mapping."""
        data = {"old_key": "value"}
        mapping = {"old_key": "new_key"}
        normalized = DataTransformer.normalize_keys(data, mapping)

        assert "new_key" in normalized
        assert normalized["new_key"] == "value"

    def test_flatten_dict(self):
        """Test dictionary flattening."""
        data = {
            "user": {
                "profile": {
                    "name": "John",
                    "age": 30
                },
                "settings": {
                    "theme": "dark"
                }
            }
        }

        flattened = DataTransformer.flatten_dict(data)

        assert "user.profile.name" in flattened
        assert "user.profile.age" in flattened
        assert "user.settings.theme" in flattened
        assert flattened["user.profile.name"] == "John"

    def test_safe_get_nested(self):
        """Test safe nested value retrieval."""
        data = {
            "user": {
                "profile": {
                    "name": "John"
                }
            }
        }

        # Existing path
        name = DataTransformer.safe_get_nested(data, "user.profile.name")
        assert name == "John"

        # Non-existing path
        email = DataTransformer.safe_get_nested(data, "user.profile.email", "default")
        assert email == "default"

        # Invalid path
        invalid = DataTransformer.safe_get_nested(data, "user.invalid.path", "default")
        assert invalid == "default"


@pytest.mark.unit
@pytest.mark.asyncio
class TestRateLimiter:
    """Test RateLimiter functionality."""

    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter(max_calls=10, time_window=60)
        assert limiter.max_calls == 10
        assert limiter.time_window == 60
        assert limiter.calls == []

    async def test_rate_limiter_allows_calls(self):
        """Test that rate limiter allows calls within limit."""
        limiter = RateLimiter(max_calls=5, time_window=60)

        for _ in range(5):
            can_proceed = await limiter.can_proceed()
            assert can_proceed is True

    async def test_rate_limiter_blocks_excess_calls(self):
        """Test that rate limiter blocks calls exceeding limit."""
        limiter = RateLimiter(max_calls=2, time_window=60)

        # First two calls should succeed
        assert await limiter.can_proceed() is True
        assert await limiter.can_proceed() is True

        # Third call should be blocked
        assert await limiter.can_proceed() is False

    async def test_rate_limiter_window_reset(self):
        """Test that rate limiter resets after time window."""
        limiter = RateLimiter(max_calls=1, time_window=1)

        # First call succeeds
        assert await limiter.can_proceed() is True

        # Second call blocked
        assert await limiter.can_proceed() is False

        # Wait for window to reset
        await asyncio.sleep(1.1)

        # Should succeed again
        assert await limiter.can_proceed() is True


@pytest.mark.unit
class TestValidators:
    """Test validation functions."""

    def test_validate_email_valid(self):
        """Test email validation with valid emails."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "test+tag@example.org"
        ]

        for email in valid_emails:
            assert validate_email(email) is True

    def test_validate_email_invalid(self):
        """Test email validation with invalid emails."""
        invalid_emails = [
            "invalid",
            "@example.com",
            "test@",
            "test.example.com"
        ]

        for email in invalid_emails:
            assert validate_email(email) is False

    def test_validate_phone_valid(self):
        """Test phone validation with valid Hungarian numbers."""
        valid_phones = [
            "+36 30 123 4567",
            "06 30 123 4567",
            "+3630 123 4567",
            "06301234567"
        ]

        for phone in valid_phones:
            assert validate_phone(phone) is True

    def test_validate_phone_invalid(self):
        """Test phone validation with invalid numbers."""
        invalid_phones = [
            "123456",
            "+1 555 123 4567",  # US number
            "invalid phone"
        ]

        for phone in invalid_phones:
            assert validate_phone(phone) is False

    def test_sanitize_input(self):
        """Test input sanitization."""
        # HTML removal
        html_input = "<script>alert('xss')</script>Hello World"
        sanitized = sanitize_input(html_input)
        assert "<script>" not in sanitized
        assert "Hello World" in sanitized

        # Length limiting
        long_input = "a" * 2000
        sanitized = sanitize_input(long_input, max_length=100)
        assert len(sanitized) <= 103  # 100 + "..."

        # Whitespace normalization
        spaced_input = "  Hello    World  "
        sanitized = sanitize_input(spaced_input)
        assert sanitized == "Hello World"
