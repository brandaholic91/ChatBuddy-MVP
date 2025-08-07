"""
Constants - Központosított konstansok és konfigurációs értékek.

Ez a modul tartalmazza az alkalmazásban használt konstansokat.
"""

from typing import Dict, Any, List
from enum import Enum


# API Timeouts
class APITimeouts:
    """API timeout konstansok."""
    DEFAULT_TIMEOUT = 30
    SLOW_TIMEOUT = 60
    FAST_TIMEOUT = 10
    
    # Service-specifikus timeout-ok
    OPENAI_TIMEOUT = 60
    SUPABASE_TIMEOUT = 30
    REDIS_TIMEOUT = 5
    WEBSHOP_TIMEOUT = 30
    EMAIL_TIMEOUT = 30
    SMS_TIMEOUT = 15


# Rate Limiting
class RateLimits:
    """Rate limiting konstansok."""
    
    # Per user limits
    USER_REQUESTS_PER_MINUTE = 60
    USER_REQUESTS_PER_HOUR = 1000
    USER_REQUESTS_PER_DAY = 10000
    
    # Per IP limits
    IP_REQUESTS_PER_MINUTE = 120
    IP_REQUESTS_PER_HOUR = 2000
    
    # Agent-specifikus limits
    AGENT_REQUESTS_PER_MINUTE = 30
    EXPENSIVE_AGENT_REQUESTS_PER_MINUTE = 10
    
    # API limits
    OPENAI_REQUESTS_PER_MINUTE = 50
    WEBSHOP_REQUESTS_PER_MINUTE = 100


# Cache TTL (Time To Live)
class CacheTTL:
    """Cache TTL konstansok másodpercekben."""
    
    # Session cache
    SESSION_TTL = 86400  # 24 óra
    USER_CONTEXT_TTL = 3600  # 1 óra
    
    # Agent response cache
    AGENT_RESPONSE_TTL = 1800  # 30 perc
    EXPENSIVE_RESPONSE_TTL = 3600  # 1 óra
    
    # Product cache
    PRODUCT_INFO_TTL = 3600  # 1 óra
    PRODUCT_SEARCH_TTL = 900  # 15 perc
    PRODUCT_PRICES_TTL = 300  # 5 perc
    
    # Marketing cache
    PROMOTION_TTL = 3600  # 1 óra
    NEWSLETTER_TTL = 7200  # 2 óra
    ANALYTICS_TTL = 1800  # 30 perc
    
    # Vector embeddings
    EMBEDDING_TTL = 86400  # 24 óra
    
    # Short-term cache
    QUICK_CACHE_TTL = 60  # 1 perc
    TEMP_CACHE_TTL = 300  # 5 perc


# Message Limits
class MessageLimits:
    """Üzenet korlátok."""
    
    MAX_MESSAGE_LENGTH = 4000
    MAX_CONTEXT_LENGTH = 16000
    MAX_RESPONSE_LENGTH = 2000
    
    # Agent-specifikus korlátok
    MAX_AGENT_CONTEXT = 8000
    MAX_TOOL_RESPONSE = 1000
    
    # Email/SMS korlátok
    MAX_EMAIL_SUBJECT = 200
    MAX_EMAIL_BODY = 10000
    MAX_SMS_LENGTH = 160


# File Upload Limits
class FileUploadLimits:
    """Fájl feltöltési korlátok."""
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    MAX_IMAGE_SIZE = 5 * 1024 * 1024   # 5 MB
    MAX_DOCUMENT_SIZE = 20 * 1024 * 1024  # 20 MB
    
    ALLOWED_IMAGE_TYPES = ['jpg', 'jpeg', 'png', 'gif', 'webp']
    ALLOWED_DOCUMENT_TYPES = ['pdf', 'doc', 'docx', 'txt']


# Database Configuration
class DatabaseConfig:
    """Adatbázis konfiguráció konstansok."""
    
    # Connection pool
    MIN_POOL_SIZE = 1
    MAX_POOL_SIZE = 10
    POOL_TIMEOUT = 30
    
    # Query limits
    MAX_QUERY_RESULTS = 1000
    DEFAULT_PAGE_SIZE = 50
    MAX_PAGE_SIZE = 200
    
    # Batch sizes
    BATCH_INSERT_SIZE = 100
    BULK_UPDATE_SIZE = 500


# Agent Configuration
class AgentConfig:
    """Ágens konfiguráció konstansok."""
    
    # Model settings
    DEFAULT_MODEL = 'openai:gpt-4o'
    FALLBACK_MODEL = 'openai:gpt-3.5-turbo'
    
    # Temperature settings
    DEFAULT_TEMPERATURE = 0.7
    CREATIVE_TEMPERATURE = 0.9
    FACTUAL_TEMPERATURE = 0.1
    
    # Token limits
    MAX_INPUT_TOKENS = 8000
    MAX_OUTPUT_TOKENS = 2000
    CONTEXT_WINDOW = 16000


# Security Configuration
class SecurityConfig:
    """Biztonsági konfiguráció konstansok."""
    
    # Password requirements
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128
    REQUIRE_SPECIAL_CHARS = True
    REQUIRE_NUMBERS = True
    REQUIRE_UPPERCASE = True
    
    # Session security
    SESSION_TIMEOUT = 3600  # 1 óra
    MAX_FAILED_LOGINS = 5
    LOCKOUT_DURATION = 900  # 15 perc
    
    # API Security
    API_KEY_LENGTH = 32
    JWT_EXPIRY = 86400  # 24 óra
    REFRESH_TOKEN_EXPIRY = 604800  # 7 nap


# Monitoring Configuration
class MonitoringConfig:
    """Monitoring konfiguráció konstansok."""
    
    # Metrics retention
    METRICS_RETENTION_DAYS = 30
    LOG_RETENTION_DAYS = 90
    TRACE_RETENTION_DAYS = 7
    
    # Alert thresholds
    ERROR_RATE_THRESHOLD = 0.05  # 5%
    RESPONSE_TIME_THRESHOLD = 2.0  # 2 másodperc
    CPU_USAGE_THRESHOLD = 0.8  # 80%
    MEMORY_USAGE_THRESHOLD = 0.85  # 85%


# Feature Flags
class FeatureFlags:
    """Feature flag-ek."""
    
    ENABLE_CACHING = True
    ENABLE_RATE_LIMITING = True
    ENABLE_MONITORING = True
    ENABLE_AUDIT_LOGGING = True
    
    # Agent features
    ENABLE_AGENT_CACHING = True
    ENABLE_TOOL_VALIDATION = True
    ENABLE_RESPONSE_STREAMING = True
    
    # Integration features
    ENABLE_WEBSHOP_SYNC = True
    ENABLE_EMAIL_MARKETING = True
    ENABLE_SMS_NOTIFICATIONS = True
    ENABLE_VECTOR_SEARCH = True


# Error Codes
class ErrorCodes:
    """Hibakódok."""
    
    # General errors
    UNKNOWN_ERROR = 'E001'
    VALIDATION_ERROR = 'E002'
    AUTHENTICATION_ERROR = 'E003'
    AUTHORIZATION_ERROR = 'E004'
    NOT_FOUND_ERROR = 'E005'
    
    # Agent errors
    AGENT_ERROR = 'A001'
    TOOL_ERROR = 'A002'
    CONTEXT_ERROR = 'A003'
    MODEL_ERROR = 'A004'
    
    # Integration errors
    DATABASE_ERROR = 'I001'
    CACHE_ERROR = 'I002'
    API_ERROR = 'I003'
    NETWORK_ERROR = 'I004'
    
    # Business logic errors
    PRODUCT_NOT_FOUND = 'B001'
    ORDER_NOT_FOUND = 'B002'
    INSUFFICIENT_STOCK = 'B003'
    INVALID_PAYMENT = 'B004'


# HTTP Status Codes
class HTTPStatus:
    """HTTP státusz kódok."""
    
    # Success
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    
    # Client errors
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    TOO_MANY_REQUESTS = 429
    
    # Server errors
    INTERNAL_SERVER_ERROR = 500
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504


# Default Values
class Defaults:
    """Alapértelmezett értékek."""
    
    # Pagination
    PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # Search
    SEARCH_LIMIT = 20
    MIN_SEARCH_LENGTH = 2
    
    # User preferences
    DEFAULT_LANGUAGE = 'hu'
    DEFAULT_CURRENCY = 'HUF'
    DEFAULT_TIMEZONE = 'Europe/Budapest'
    
    # Agent responses
    DEFAULT_CONFIDENCE = 0.8
    LOW_CONFIDENCE_THRESHOLD = 0.5
    HIGH_CONFIDENCE_THRESHOLD = 0.9


# Regex Patterns
class RegexPatterns:
    """Regex minták validációhoz."""
    
    EMAIL = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    PHONE_HU = r'^(\+36|06)[0-9]{8,9}$'
    PASSWORD = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
    UUID = r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
    SLUG = r'^[a-z0-9]+(?:-[a-z0-9]+)*$'


# Environment Variables
class EnvVars:
    """Environment változók nevei."""
    
    # Database
    SUPABASE_URL = 'SUPABASE_URL'
    SUPABASE_KEY = 'SUPABASE_ANON_KEY'
    SUPABASE_SERVICE_KEY = 'SUPABASE_SERVICE_ROLE_KEY'
    
    # Redis
    REDIS_URL = 'REDIS_URL'
    REDIS_PASSWORD = 'REDIS_PASSWORD'
    
    # OpenAI
    OPENAI_API_KEY = 'OPENAI_API_KEY'
    OPENAI_ORG_ID = 'OPENAI_ORG_ID'
    
    # Email
    SENDGRID_API_KEY = 'SENDGRID_API_KEY'
    EMAIL_FROM = 'EMAIL_FROM'
    
    # SMS
    TWILIO_ACCOUNT_SID = 'TWILIO_ACCOUNT_SID'
    TWILIO_AUTH_TOKEN = 'TWILIO_AUTH_TOKEN'
    
    # Monitoring
    SENTRY_DSN = 'SENTRY_DSN'
    OTEL_ENDPOINT = 'OTEL_ENDPOINT'
    
    # General
    ENVIRONMENT = 'ENVIRONMENT'
    DEBUG = 'DEBUG'
    SECRET_KEY = 'SECRET_KEY'


# Log Levels
class LogLevels:
    """Log szintek."""
    
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'


# Business Constants
class BusinessConstants:
    """Üzleti konstansok."""
    
    # Currency
    DEFAULT_CURRENCY = 'HUF'
    SUPPORTED_CURRENCIES = ['HUF', 'EUR', 'USD']
    
    # Discounts
    MAX_DISCOUNT_PERCENTAGE = 90
    MIN_DISCOUNT_AMOUNT = 100  # HUF
    
    # Shipping
    FREE_SHIPPING_THRESHOLD = 50000  # HUF
    DEFAULT_SHIPPING_COST = 1990  # HUF
    
    # Orders
    ORDER_TIMEOUT_MINUTES = 30
    CART_EXPIRY_DAYS = 7
    
    # Marketing
    NEWSLETTER_UNSUBSCRIBE_COOLDOWN = 30  # nap
    ABANDONED_CART_DELAY_HOURS = 24
    MAX_FOLLOW_UP_ATTEMPTS = 3


# File Paths
class FilePaths:
    """Fájl elérési utak."""
    
    # Templates
    EMAIL_TEMPLATES = 'src/integrations/marketing/templates/'
    AGENT_PROMPTS = 'src/config/prompts/'
    
    # Logs
    LOG_DIR = 'logs/'
    ERROR_LOG = 'logs/error.log'
    ACCESS_LOG = 'logs/access.log'
    
    # Data
    BACKUP_DIR = 'backups/'
    TEMP_DIR = 'temp/'
    UPLOAD_DIR = 'uploads/'