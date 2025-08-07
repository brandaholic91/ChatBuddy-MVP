"""
Cache Integráció - Optimized Redis Implementation

Ez a modul tartalmazza az optimalizált Redis cache integrációt:
- Egységes connection pool (3 helyett 1 kapcsolat)
- Intelligens TTL beállítások
- Kompresszió nagy objektumokhoz
- Performance monitoring
"""

import os

# Feature flag for optimization
REDIS_OPTIMIZATION_ENABLED = os.getenv("REDIS_OPTIMIZATION_ENABLED", "true").lower() == "true"

if REDIS_OPTIMIZATION_ENABLED:
    # Use optimized implementation
    from .optimized_redis_service import (
        OptimizedRedisCacheService as RedisCacheService,
        OptimizedSessionCache as SessionCache, 
        OptimizedPerformanceCache as PerformanceCache,
        OptimizedRateLimitCache as RateLimitCache,
        OptimizedSessionData as SessionData,
        get_redis_cache_service,
        shutdown_redis_cache_service
    )
    from .redis_connection_pool import OptimizedCacheConfig as CacheConfig
else:
    # Use original implementation
    from .redis_cache import (
        RedisCacheService,
        SessionCache,
        PerformanceCache,
        RateLimitCache,
        CacheConfig,
        SessionData,
        get_redis_cache_service,
        shutdown_redis_cache_service
    )

__all__ = [
    "RedisCacheService",
    "SessionCache", 
    "PerformanceCache",
    "RateLimitCache",
    "CacheConfig",
    "SessionData",
    "get_redis_cache_service",
    "shutdown_redis_cache_service"
] 