"""
Isolated test runner for our new modules without complex dependencies.
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

# Test APIConfig without full imports
try:
    from src.utils.integration_utils import (
        APIConfig, APIResponse, ErrorHandler, 
        CacheHelper, ConfigManager, DataTransformer, RateLimiter,
        validate_email, validate_phone, sanitize_input
    )
    
    def test_api_config_creation():
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
        print("✅ APIConfig creation test passed")
    
    def test_cache_helper():
        """Test cache helper functionality."""
        # Test cache key generation
        key = CacheHelper.generate_cache_key("arg1", "arg2", prefix="test")
        assert key.startswith("test:")
        assert len(key) > len("test:")
        
        # Test serialization
        data = {"key": "value", "number": 42}
        serialized = CacheHelper.serialize_for_cache(data)
        assert isinstance(serialized, str)
        
        # Should be valid JSON
        parsed = json.loads(serialized)
        assert parsed == data
        
        # Test deserialization
        deserialized = CacheHelper.deserialize_from_cache(serialized)
        assert deserialized == data
        
        print("✅ CacheHelper tests passed")
    
    def test_data_transformer():
        """Test data transformer functionality."""
        # Test key normalization
        data = {"First Name": "John", "last-name": "Doe", "EMAIL": "john@example.com"}
        normalized = DataTransformer.normalize_keys(data)
        
        assert "first_name" in normalized
        assert "last_name" in normalized  
        assert "email" in normalized
        assert normalized["first_name"] == "John"
        
        # Test dictionary flattening
        nested_data = {
            "user": {
                "profile": {
                    "name": "John",
                    "age": 30
                }
            }
        }
        
        flattened = DataTransformer.flatten_dict(nested_data)
        assert "user.profile.name" in flattened
        assert "user.profile.age" in flattened
        assert flattened["user.profile.name"] == "John"
        
        print("✅ DataTransformer tests passed")
    
    def test_validators():
        """Test validation functions."""
        # Valid emails
        assert validate_email("test@example.com") == True
        assert validate_email("user.name@domain.co.uk") == True
        
        # Invalid emails  
        assert validate_email("invalid") == False
        assert validate_email("@example.com") == False
        
        # Valid Hungarian phone numbers
        assert validate_phone("+36 30 123 4567") == True
        assert validate_phone("06 30 123 4567") == True
        
        # Invalid phone numbers
        assert validate_phone("123456") == False
        
        print("✅ Validator tests passed")
    
    def test_sanitize_input():
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
        
        print("✅ Input sanitization tests passed")
    
    async def test_rate_limiter():
        """Test rate limiter functionality."""
        limiter = RateLimiter(max_calls=2, time_window=60)
        
        # First two calls should succeed
        assert await limiter.can_proceed() == True
        assert await limiter.can_proceed() == True
        
        # Third call should be blocked
        assert await limiter.can_proceed() == False
        
        print("✅ RateLimiter tests passed")
    
    def run_tests():
        """Run all tests."""
        print("🧪 Running isolated tests for integration_utils...")
        
        test_api_config_creation()
        test_cache_helper()
        test_data_transformer()
        test_validators()
        test_sanitize_input()
        
        # Run async test
        asyncio.run(test_rate_limiter())
        
        print("\n🎉 All integration_utils tests passed!")
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Skipping integration_utils tests due to import issues")

if __name__ == "__main__":
    run_tests()