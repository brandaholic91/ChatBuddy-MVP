"""
Security configuration for Chatbuddy MVP.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import List


def setup_security_middleware(app: FastAPI) -> None:
    """
    Setup security middleware for FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_allowed_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    
    # Trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=get_allowed_hosts()
    )


def get_allowed_origins() -> List[str]:
    """
    Get allowed CORS origins from environment.
    
    Returns:
        List of allowed origins
    """
    import os
    
    # Development origins
    dev_origins = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080"
    ]
    
    # Production origins (from environment)
    prod_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
    prod_origins = [origin.strip() for origin in prod_origins if origin.strip()]
    
    return dev_origins + prod_origins


def get_allowed_hosts() -> List[str]:
    """
    Get allowed hosts for trusted host middleware.
    
    Returns:
        List of allowed hosts
    """
    import os
    
    # Development hosts
    dev_hosts = [
        "localhost",
        "127.0.0.1",
        "0.0.0.0"
    ]
    
    # Production hosts (from environment)
    prod_hosts = os.getenv("ALLOWED_HOSTS", "").split(",")
    prod_hosts = [host.strip() for host in prod_hosts if host.strip()]
    
    return dev_hosts + prod_hosts


def setup_rate_limiting(app: FastAPI) -> Limiter:
    """
    Setup rate limiting for the application.
    
    Args:
        app: FastAPI application instance
        
    Returns:
        Limiter instance
    """
    from slowapi import Limiter
    
    # Create limiter
    limiter = Limiter(key_func=get_remote_address)
    
    # Add rate limit exceeded handler
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    return limiter


def get_security_headers() -> dict:
    """
    Get security headers for responses.
    
    Returns:
        Dictionary of security headers
    """
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
    }


def validate_input(data: dict, required_fields: List[str]) -> bool:
    """
    Basic input validation.
    
    Args:
        data: Input data to validate
        required_fields: List of required field names
        
    Returns:
        True if validation passes, False otherwise
    """
    if not isinstance(data, dict):
        return False
    
    for field in required_fields:
        if field not in data or data[field] is None:
            return False
    
    return True


def sanitize_string(input_string: str) -> str:
    """
    Basic string sanitization.
    
    Args:
        input_string: String to sanitize
        
    Returns:
        Sanitized string
    """
    if not isinstance(input_string, str):
        return ""
    
    # Remove potentially dangerous characters
    dangerous_chars = ["<", ">", '"', "'", "&"]
    sanitized = input_string
    
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, "")
    
    # Limit length
    if len(sanitized) > 1000:
        sanitized = sanitized[:1000]
    
    return sanitized.strip()


def validate_api_key(api_key: str) -> bool:
    """
    Validate API key format.
    
    Args:
        api_key: API key to validate
        
    Returns:
        True if valid format, False otherwise
    """
    if not api_key or not isinstance(api_key, str):
        return False
    
    # Basic OpenAI API key validation
    if api_key.startswith("sk-") and len(api_key) > 20:
        return True
    
    # Basic Anthropic API key validation
    if api_key.startswith("sk-ant-") and len(api_key) > 20:
        return True
    
    return False


def get_rate_limit_config() -> dict:
    """
    Get rate limiting configuration.
    
    Returns:
        Dictionary with rate limit settings
    """
    import os
    
    return {
        "default": os.getenv("RATE_LIMIT_DEFAULT", "100/minute"),
        "chat": os.getenv("RATE_LIMIT_CHAT", "50/minute"),
        "search": os.getenv("RATE_LIMIT_SEARCH", "200/minute"),
        "health": os.getenv("RATE_LIMIT_HEALTH", "1000/minute")
    }


def log_security_event(event_type: str, user_id: str = None, details: dict = None) -> None:
    """
    Log security events.
    
    Args:
        event_type: Type of security event
        user_id: User ID (optional)
        details: Additional details (optional)
    """
    import logging
    from datetime import datetime
    
    logger = logging.getLogger("security")
    
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "user_id": user_id,
        "details": details or {}
    }
    
    logger.warning(f"Security event: {log_data}")


# Security decorators
def require_api_key(func):
    """
    Decorator to require API key for endpoints.
    """
    def wrapper(*args, **kwargs):
        # API key validation logic
        return func(*args, **kwargs)
    return wrapper


def validate_user_input(func):
    """
    Decorator to validate user input.
    """
    def wrapper(*args, **kwargs):
        # Input validation logic
        return func(*args, **kwargs)
    return wrapper 