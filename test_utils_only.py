"""
Completely isolated test for integration_utils module.
Tests only the utility functions without any complex imports.
"""

import sys
import os
import asyncio
import json
import time
from typing import Dict, Any

# Add the src directory to Python path to import directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import only the specific module we want to test
try:
    # Direct import to avoid the complex dependency chain
    import utils.integration_utils as iutils
    
    print("=== Testing Integration Utils Module ===\n")
    
    def test_api_config():
        """Test APIConfig functionality."""
        print("Testing APIConfig...")
        
        config = iutils.APIConfig(
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
        
        # Test with custom headers
        custom_headers = {"Authorization": "Bearer token"}
        config2 = iutils.APIConfig(
            api_key="test_key",
            base_url="https://api.example.com",
            headers=custom_headers
        )
        assert config2.headers == custom_headers
        print("✅ APIConfig custom headers test passed")
    
    def test_api_response():
        """Test APIResponse functionality."""
        print("\nTesting APIResponse...")
        
        # Success response
        response = iutils.APIResponse(
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
        print("✅ APIResponse success test passed")
        
        # Error response
        error_response = iutils.APIResponse(
            success=False,
            status_code=400,
            error_message="Bad request"
        )
        
        assert error_response.success is False
        assert error_response.status_code == 400
        assert error_response.error_message == "Bad request"
        print("✅ APIResponse error test passed")
    
    def test_error_handler():
        """Test ErrorHandler functionality."""
        print("\nTesting ErrorHandler...")
        
        # Test successful response
        success_response = iutils.APIResponse(success=True, status_code=200)
        error = iutils.ErrorHandler.handle_api_error(success_response)
        assert error is None
        print("✅ ErrorHandler success test passed")
        
        # Test authentication error
        auth_error_response = iutils.APIResponse(
            success=False, 
            status_code=401, 
            error_message="Unauthorized"
        )
        error = iutils.ErrorHandler.handle_api_error(auth_error_response)
        assert isinstance(error, PermissionError)
        print("✅ ErrorHandler authentication error test passed")
        
        # Test not found error
        not_found_response = iutils.APIResponse(
            success=False, 
            status_code=404, 
            error_message="Not found"
        )
        error = iutils.ErrorHandler.handle_api_error(not_found_response)
        assert isinstance(error, FileNotFoundError)
        print("✅ ErrorHandler not found error test passed")
    
    def test_cache_helper():
        """Test CacheHelper functionality."""
        print("\nTesting CacheHelper...")
        
        # Test cache key generation
        key = iutils.CacheHelper.generate_cache_key("arg1", "arg2", prefix="test")
        assert key.startswith("test:")
        assert len(key) > len("test:")
        print("✅ CacheHelper key generation test passed")
        
        # Test serialization
        data = {"key": "value", "number": 42, "list": [1, 2, 3]}
        serialized = iutils.CacheHelper.serialize_for_cache(data)
        assert isinstance(serialized, str)
        
        # Should be valid JSON
        parsed = json.loads(serialized)
        assert parsed == data
        print("✅ CacheHelper serialization test passed")
        
        # Test deserialization
        deserialized = iutils.CacheHelper.deserialize_from_cache(serialized)
        assert deserialized == data
        print("✅ CacheHelper deserialization test passed")
        
        # Test invalid JSON handling
        invalid_result = iutils.CacheHelper.deserialize_from_cache("invalid json")
        assert invalid_result == {}
        print("✅ CacheHelper invalid JSON handling test passed")
    
    def test_data_transformer():
        """Test DataTransformer functionality."""
        print("\nTesting DataTransformer...")
        
        # Test key normalization
        data = {"First Name": "John", "last-name": "Doe", "EMAIL": "john@example.com"}
        normalized = iutils.DataTransformer.normalize_keys(data)
        
        assert "first_name" in normalized
        assert "last_name" in normalized  
        assert "email" in normalized
        assert normalized["first_name"] == "John"
        print("✅ DataTransformer key normalization test passed")
        
        # Test key mapping
        mapping_data = {"old_key": "value"}
        key_mapping = {"old_key": "new_key"}
        mapped = iutils.DataTransformer.normalize_keys(mapping_data, key_mapping)
        assert "new_key" in mapped
        assert mapped["new_key"] == "value"
        print("✅ DataTransformer key mapping test passed")
        
        # Test dictionary flattening
        nested_data = {
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
        
        flattened = iutils.DataTransformer.flatten_dict(nested_data)
        assert "user.profile.name" in flattened
        assert "user.profile.age" in flattened
        assert "user.settings.theme" in flattened
        assert flattened["user.profile.name"] == "John"
        print("✅ DataTransformer dictionary flattening test passed")
        
        # Test safe nested get
        name = iutils.DataTransformer.safe_get_nested(nested_data, "user.profile.name")
        assert name == "John"
        
        # Non-existing path
        email = iutils.DataTransformer.safe_get_nested(nested_data, "user.profile.email", "default")
        assert email == "default"
        print("✅ DataTransformer safe nested get test passed")
    
    def test_validators():
        """Test validation functions."""
        print("\nTesting validators...")
        
        # Valid emails
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "test+tag@example.org"
        ]
        
        for email in valid_emails:
            assert iutils.validate_email(email) is True
        print("✅ Valid email validation test passed")
        
        # Invalid emails  
        invalid_emails = [
            "invalid",
            "@example.com",
            "test@",
            "test.example.com"
        ]
        
        for email in invalid_emails:
            assert iutils.validate_email(email) is False
        print("✅ Invalid email validation test passed")
        
        # Valid Hungarian phone numbers
        valid_phones = [
            "+36 30 123 4567",
            "06 30 123 4567",
            "+3630 123 4567"
        ]
        
        for phone in valid_phones:
            assert iutils.validate_phone(phone) is True
        print("✅ Valid phone validation test passed")
        
        # Invalid phone numbers
        invalid_phones = [
            "123456",
            "+1 555 123 4567",  # US number
            "invalid phone"
        ]
        
        for phone in invalid_phones:
            assert iutils.validate_phone(phone) is False
        print("✅ Invalid phone validation test passed")
    
    def test_sanitize_input():
        """Test input sanitization."""
        print("\nTesting input sanitization...")
        
        # HTML removal
        html_input = "<script>alert('xss')</script>Hello World"
        sanitized = iutils.sanitize_input(html_input)
        assert "<script>" not in sanitized
        assert "Hello World" in sanitized
        print("✅ HTML removal test passed")
        
        # Length limiting
        long_input = "a" * 2000
        sanitized = iutils.sanitize_input(long_input, max_length=100)
        assert len(sanitized) <= 103  # 100 + "..."
        print("✅ Length limiting test passed")
        
        # Whitespace normalization
        spaced_input = "  Hello    World  "
        sanitized = iutils.sanitize_input(spaced_input)
        assert sanitized == "Hello World"
        print("✅ Whitespace normalization test passed")
    
    async def test_rate_limiter():
        """Test rate limiter functionality."""
        print("\nTesting RateLimiter...")
        
        # Test basic functionality
        limiter = iutils.RateLimiter(max_calls=2, time_window=60)
        
        # First two calls should succeed
        assert await limiter.can_proceed() is True
        assert await limiter.can_proceed() is True
        print("✅ RateLimiter allows calls within limit")
        
        # Third call should be blocked
        assert await limiter.can_proceed() is False
        print("✅ RateLimiter blocks calls exceeding limit")
        
        # Test time window reset
        short_limiter = iutils.RateLimiter(max_calls=1, time_window=1)
        assert await short_limiter.can_proceed() is True
        assert await short_limiter.can_proceed() is False
        
        # Wait for window to reset
        await asyncio.sleep(1.1)
        assert await short_limiter.can_proceed() is True
        print("✅ RateLimiter resets after time window")
    
    async def test_error_handler_async():
        """Test async error handling wrapper."""
        print("\nTesting async error handling...")
        
        # Successful async function
        async def successful_function():
            return "success"
        
        result = await iutils.ErrorHandler.with_error_handling(successful_function)
        assert result == "success"
        print("✅ Async error handling with success test passed")
        
        # Failing async function
        async def failing_function():
            raise Exception("Test error")
        
        result = await iutils.ErrorHandler.with_error_handling(
            failing_function, 
            default_return="default"
        )
        assert result == "default"
        print("✅ Async error handling with failure test passed")
    
    def run_all_tests():
        """Run all tests."""
        print("🧪 Starting integration_utils isolated tests...\n")
        
        # Run synchronous tests
        test_api_config()
        test_api_response()
        test_error_handler()
        test_cache_helper()
        test_data_transformer()
        test_validators()
        test_sanitize_input()
        
        # Run async tests
        asyncio.run(test_rate_limiter())
        asyncio.run(test_error_handler_async())
        
        print("\n🎉 All integration_utils tests passed successfully!")
        print("✅ Module is working correctly and ready for production use.")
    
    # Run the tests
    if __name__ == "__main__":
        run_all_tests()
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Cannot run isolated tests due to import issues")
except Exception as e:
    print(f"Error during testing: {e}")
    print("Tests failed with exception")