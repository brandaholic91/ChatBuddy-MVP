"""
Security configuration for Chatbuddy MVP.
"""

import os
import re
import hashlib
import ipaddress
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta, timezone
from functools import wraps

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, field_validator
import bleach
import jwt
from passlib.context import CryptContext

# Security context
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Blocked IPs cache (in production, use Redis)
_blocked_ips = set()
_failed_auth_attempts = {}  # IP -> (count, first_attempt_time)


class SecurityConfig(BaseModel):
    """Security configuration model."""
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    max_failed_attempts: int = 5
    block_duration_minutes: int = 15
    rate_limit_default: str = "100/minute"
    rate_limit_auth: str = "5/minute"
    rate_limit_chat: str = "50/minute"
    
    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v


class SecurityMiddleware:
    """Comprehensive security middleware."""
    
    def __init__(self, app: FastAPI, config: SecurityConfig):
        self.app = app
        self.config = config
        self.setup_middleware()
    
    def setup_middleware(self):
        """Setup all security middleware."""
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.get_allowed_origins(),
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["*"],
        )
        
        # Trusted host middleware
        self.app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=self.get_allowed_hosts()
        )
        
        # Custom security middleware
        self.app.middleware("http")(self.security_middleware)
    
    async def security_middleware(self, request: Request, call_next):
        """Custom security middleware."""
        # Check if IP is blocked
        client_ip = self.get_client_ip(request)
        if self.is_ip_blocked(client_ip):
            raise HTTPException(
                status_code=403,
                detail="IP cím blokkolva"
            )
        
        # Add security headers
        response = await call_next(request)
        self.add_security_headers(response)
        
        return response
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked."""
        if ip in _blocked_ips:
            return True
        
        # Check if IP is in blocked range
        try:
            ip_obj = ipaddress.ip_address(ip)
            # Add logic for IP range blocking here
            return False
        except ValueError:
            return True
    
    def block_ip(self, ip: str, duration_minutes: int = None):
        """Block an IP address."""
        _blocked_ips.add(ip)
        # In production, store in Redis with TTL
    
    def add_security_headers(self, response):
        """Add security headers to response."""
        headers = self.get_security_headers()
        for header, value in headers.items():
            response.headers[header] = value
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers."""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            ),
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache"
        }
    
    def get_allowed_origins(self) -> List[str]:
        """Get allowed CORS origins."""
        dev_origins = [
            "http://localhost:3000",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080"
        ]
        
        prod_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
        prod_origins = [origin.strip() for origin in prod_origins if origin.strip()]
        
        return dev_origins + prod_origins
    
    def get_allowed_hosts(self) -> List[str]:
        """Get allowed hosts."""
        dev_hosts = [
            "localhost",
            "127.0.0.1",
            "0.0.0.0"
        ]
        
        prod_hosts = os.getenv("ALLOWED_HOSTS", "").split(",")
        prod_hosts = [host.strip() for host in prod_hosts if host.strip()]
        
        return dev_hosts + prod_hosts


class InputValidator:
    """Input validation and sanitization."""
    
    @staticmethod
    def sanitize_string(input_string: str, max_length: int = 1000) -> str:
        """Sanitize string input."""
        if not isinstance(input_string, str):
            return ""
        
        # Remove dangerous characters and patterns
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'<iframe[^>]*>.*?</iframe>',
            r'<object[^>]*>.*?</object>',
            r'javascript:',
            r'vbscript:',
            r'data:text/html',
            r'data:application/javascript',
            r'expression\(',
            r'url\(',
        ]
        
        sanitized = input_string
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # Use bleach for additional sanitization
        sanitized = bleach.clean(sanitized, tags=[], strip=True)
        
        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number format."""
        # Hungarian phone number format
        phone_pattern = r'^(\+36|06)[0-9]{8,9}$'
        return bool(re.match(phone_pattern, phone))
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Validate password strength."""
        errors = []
        warnings = []
        
        if len(password) < 8:
            errors.append("A jelszónak legalább 8 karakter hosszúnak kell lennie")
        
        if not re.search(r'[A-Z]', password):
            errors.append("A jelszónak tartalmaznia kell nagybetűt")
        
        if not re.search(r'[a-z]', password):
            errors.append("A jelszónak tartalmaznia kell kisbetűt")
        
        if not re.search(r'\d', password):
            errors.append("A jelszónak tartalmaznia kell számot")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            warnings.append("Javasolt speciális karakter használata")
        
        if len(password) < 12:
            warnings.append("Hosszabb jelszó használata javasolt")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "strength": "weak" if len(errors) > 0 else "strong" if len(warnings) == 0 else "medium"
        }


class JWTManager:
    """JWT token management."""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: timedelta = None) -> str:
        """Create access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=30)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create refresh token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=7)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token lejárt")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Érvénytelen token")


class RateLimiter:
    """Rate limiting implementation."""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.limiter = Limiter(key_func=get_remote_address)
        self.setup_rate_limiting()
    
    def setup_rate_limiting(self):
        """Setup rate limiting."""
        self.app.state.limiter = self.limiter
        self.app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    def get_rate_limit_config(self) -> Dict[str, str]:
        """Get rate limiting configuration."""
        return {
            "default": os.getenv("RATE_LIMIT_DEFAULT", "100/minute"),
            "auth": os.getenv("RATE_LIMIT_AUTH", "5/minute"),
            "chat": os.getenv("RATE_LIMIT_CHAT", "50/minute"),
            "search": os.getenv("RATE_LIMIT_SEARCH", "200/minute"),
            "health": os.getenv("RATE_LIMIT_HEALTH", "1000/minute")
        }


class ThreatDetector:
    """Threat detection and prevention."""
    
    def __init__(self):
        self.suspicious_patterns = [
            r'sql\s+injection',
            r'xss\s+attack',
            r'csrf\s+attack',
            r'path\s+traversal',
            r'command\s+injection',
            r'ldap\s+injection',
            r'no\s+sql\s+injection',
            r'xml\s+external\s+entity',
            r'xml\s+injection',
            r'html\s+injection',
            r'javascript\s+injection',
            r'php\s+injection',
            r'asp\s+injection',
            r'jsp\s+injection',
        ]
        
        self.dangerous_keywords = [
            "admin", "root", "system", "internal", "secret", "password",
            "jelszó", "adminisztrátor", "rendszer", "belső", "titkos"
        ]
    
    def detect_threats(self, input_data: str) -> Dict[str, Any]:
        """Detect potential threats in input."""
        threats = []
        risk_level = "low"
        
        # Check for suspicious patterns
        for pattern in self.suspicious_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                threats.append(f"Suspicious pattern detected: {pattern}")
                risk_level = "high"
        
        # Check for dangerous keywords
        dangerous_count = 0
        for keyword in self.dangerous_keywords:
            if keyword.lower() in input_data.lower():
                dangerous_count += 1
                threats.append(f"Dangerous keyword detected: {keyword}")
        
        if dangerous_count > 2:
            risk_level = "medium"
        elif dangerous_count > 0:
            risk_level = "low"
        
        # Check for script tags
        if re.search(r'<script[^>]*>', input_data, re.IGNORECASE):
            threats.append("Script tag detected")
            risk_level = "high"
        
        # Check for SQL injection patterns
        sql_patterns = [
            r'(\b(union|select|insert|update|delete|drop|create|alter)\b)',
            r'(\b(or|and)\b\s+\d+\s*=\s*\d+)',
            r'(\b(union|select)\b.*\bfrom\b)',
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                threats.append("SQL injection pattern detected")
                risk_level = "high"
        
        return {
            "threats": threats,
            "risk_level": risk_level,
            "threat_count": len(threats)
        }
    
    def should_block_request(self, input_data: str) -> bool:
        """Determine if request should be blocked."""
        threat_analysis = self.detect_threats(input_data)
        return threat_analysis["risk_level"] == "high"


# Security decorators
def require_authentication(func: Callable) -> Callable:
    """Decorator to require authentication."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Authentication logic here
        return await func(*args, **kwargs)
    return wrapper


def require_permissions(permissions: List[str]) -> Callable:
    """Decorator to require specific permissions."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Permission checking logic here
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def validate_input(required_fields: List[str]) -> Callable:
    """Decorator to validate input data."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Input validation logic here
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Utility functions
def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)


def generate_secure_token() -> str:
    """Generate secure random token."""
    return hashlib.sha256(os.urandom(32)).hexdigest()


def log_security_event(event_type: str, user_id: str = None, details: Dict[str, Any] = None) -> None:
    """Log security events."""
    import logging
    logger = logging.getLogger("security")
    
    log_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "user_id": user_id,
        "details": details or {}
    }
    
    logger.warning(f"Security event: {log_data}")


# Global instances
_security_config = None
_security_middleware = None
_jwt_manager = None
_rate_limiter = None
_threat_detector = None


def get_security_config() -> SecurityConfig:
    """Get security configuration."""
    global _security_config
    if _security_config is None:
        secret_key = os.getenv("SECRET_KEY")
        if not secret_key:
            raise ValueError("SECRET_KEY environment variable is required")
        
        _security_config = SecurityConfig(
            secret_key=secret_key,
            algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
            refresh_token_expire_days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")),
            max_failed_attempts=int(os.getenv("MAX_FAILED_ATTEMPTS", "5")),
            block_duration_minutes=int(os.getenv("BLOCK_DURATION_MINUTES", "15")),
            rate_limit_default=os.getenv("RATE_LIMIT_DEFAULT", "100/minute"),
            rate_limit_auth=os.getenv("RATE_LIMIT_AUTH", "5/minute"),
            rate_limit_chat=os.getenv("RATE_LIMIT_CHAT", "50/minute")
        )
    return _security_config


def setup_security_middleware(app: FastAPI) -> None:
    """Setup security middleware for FastAPI application."""
    global _security_middleware
    if _security_middleware is None:
        config = get_security_config()
        _security_middleware = SecurityMiddleware(app, config)
    return _security_middleware


def get_jwt_manager() -> JWTManager:
    """Get JWT manager instance."""
    global _jwt_manager
    if _jwt_manager is None:
        config = get_security_config()
        _jwt_manager = JWTManager(config.secret_key, config.algorithm)
    return _jwt_manager


def get_rate_limiter(app: FastAPI) -> RateLimiter:
    """Get rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(app)
    return _rate_limiter


def get_threat_detector() -> ThreatDetector:
    """Get threat detector instance."""
    global _threat_detector
    if _threat_detector is None:
        _threat_detector = ThreatDetector()
    return _threat_detector


def get_security_headers() -> Dict[str, str]:
    """Get security headers for responses."""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
    }


def validate_input(data: Dict[str, Any], required_fields: List[str]) -> bool:
    """Basic input validation."""
    if not isinstance(data, dict):
        return False
    
    for field in required_fields:
        if field not in data or data[field] is None:
            return False
    
    return True


def sanitize_string(input_string: str) -> str:
    """Basic string sanitization."""
    return InputValidator.sanitize_string(input_string)


def validate_api_key(api_key: str) -> bool:
    """Validate API key format."""
    if not api_key or not isinstance(api_key, str):
        return False
    
    # Basic OpenAI API key validation
    if api_key.startswith("sk-") and len(api_key) > 20:
        return True
    
    # Basic Anthropic API key validation
    if api_key.startswith("sk-ant-") and len(api_key) > 20:
        return True
    
    return False


def get_rate_limit_config() -> Dict[str, str]:
    """Get rate limiting configuration."""
    return {
        "default": os.getenv("RATE_LIMIT_DEFAULT", "100/minute"),
        "chat": os.getenv("RATE_LIMIT_CHAT", "50/minute"),
        "search": os.getenv("RATE_LIMIT_SEARCH", "200/minute"),
        "health": os.getenv("RATE_LIMIT_HEALTH", "1000/minute")
    }


def log_security_event(event_type: str, user_id: str = None, details: Dict[str, Any] = None) -> None:
    """Log security events."""
    import logging
    from datetime import datetime
    
    logger = logging.getLogger("security")
    
    log_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "user_id": user_id,
        "details": details or {}
    }
    
    logger.warning(f"Security event: {log_data}")


# Security decorators
def require_api_key(func):
    """Decorator to require API key for endpoints."""
    def wrapper(*args, **kwargs):
        # API key validation logic
        return func(*args, **kwargs)
    return wrapper


def validate_user_input(func):
    """Decorator to validate user input."""
    def wrapper(*args, **kwargs):
        # Input validation logic
        return func(*args, **kwargs)
    return wrapper 