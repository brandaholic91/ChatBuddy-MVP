"""
Redis Connection Pool Optimization - Unified connection management with performance improvements.

This module implements the Redis optimization specified in the optimization plan:
- Unified Redis connection pool (instead of 3 separate connections)
- Intelligent TTL settings based on usage patterns
- Compression for large objects to reduce memory usage
- Performance monitoring and connection health management
"""

import asyncio
import gzip
import json
import os
import pickle
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
import hashlib
from contextlib import asynccontextmanager

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool
from redis.exceptions import RedisError, ConnectionError, TimeoutError

from src.config.logging import get_logger

logger = get_logger(__name__)


@dataclass 
class OptimizedCacheConfig:
    """Optimized cache configuration with intelligent TTL settings."""
    
    # Connection pool settings
    max_connections: int = 20
    retry_on_timeout: bool = True
    socket_connect_timeout: int = 5
    socket_timeout: int = 10
    health_check_interval: int = 30
    
    # Intelligent TTL settings (based on usage patterns)
    session_ttl: int = 1800  # 30 minutes (optimized from 24h)
    performance_cache_ttl: int = 900  # 15 minutes (optimized)
    rate_limit_ttl: int = 3600  # 1 hour (kept as is)
    
    # Specific cache types with intelligent TTL
    agent_response_ttl: int = 900  # 15 minutes (frequently accessed)
    product_info_ttl: int = 3600  # 1 hour (changes less frequently)
    search_result_ttl: int = 600  # 10 minutes (search results change)
    embedding_cache_ttl: int = 7200  # 2 hours (expensive to compute)
    user_context_ttl: int = 1800  # 30 minutes (session-related)
    
    # Compression settings
    compression_threshold: int = 1024  # Compress objects larger than 1KB
    compression_level: int = 6  # Good balance between speed and compression
    
    # Cleanup intervals
    session_cleanup_interval: int = 1800  # 30 minutes
    performance_cleanup_interval: int = 900  # 15 minutes
    rate_limit_cleanup_interval: int = 3600  # 1 hour
    
    # Memory optimization
    memory_usage_threshold: float = 0.8  # Trigger cleanup at 80% memory usage
    max_memory_policy: str = "allkeys-lru"  # LRU eviction policy


@dataclass
class CacheMetrics:
    """Cache performance metrics."""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    errors: int = 0
    compression_saves: int = 0
    total_memory_saved: int = 0
    avg_response_time: float = 0.0
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0
    
    @property
    def compression_rate(self) -> float:
        """Calculate compression effectiveness."""
        return (self.compression_saves / self.sets * 100) if self.sets > 0 else 0.0


class OptimizedRedisConnectionPool:
    """
    Optimized Redis connection pool manager.
    
    Provides unified connection management, intelligent caching,
    compression, and performance monitoring.
    """
    
    _instance: Optional['OptimizedRedisConnectionPool'] = None
    _lock = asyncio.Lock()
    
    def __new__(cls) -> 'OptimizedRedisConnectionPool':
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the optimized Redis connection pool."""
        if hasattr(self, '_initialized'):
            return
        
        self.config = OptimizedCacheConfig()
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        
        # Connection pool
        self._pool: Optional[ConnectionPool] = None
        self._redis_client: Optional[redis.Redis] = None
        
        # Metrics tracking
        self._metrics = CacheMetrics()
        
        # Connection state
        self._connected = False
        self._connection_retries = 3
        self._last_health_check = None
        
        # Cleanup tasks
        self._cleanup_tasks: List[asyncio.Task] = []
        
        self._initialized = True
    
    async def initialize(self) -> bool:
        """Initialize the Redis connection pool."""
        try:
            # Create connection pool
            self._pool = ConnectionPool.from_url(
                self.redis_url,
                max_connections=self.config.max_connections,
                retry_on_timeout=self.config.retry_on_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                socket_timeout=self.config.socket_timeout,
                health_check_interval=self.config.health_check_interval,
                decode_responses=False  # We handle encoding/decoding manually
            )
            
            # Create Redis client with the pool
            self._redis_client = redis.Redis(
                connection_pool=self._pool,
                decode_responses=False
            )
            
            # Test connection
            await self._redis_client.ping()
            self._connected = True
            
            # Configure Redis memory policy
            try:
                await self._redis_client.config_set(
                    "maxmemory-policy", 
                    self.config.max_memory_policy
                )
            except Exception as e:
                logger.warning(f"Could not set memory policy: {e}")
            
            # Start cleanup tasks
            self._start_cleanup_tasks()
            
            logger.info(f"✅ Optimized Redis connection pool initialized with {self.config.max_connections} connections")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Redis connection pool: {e}")
            self._connected = False
            return False
    
    async def shutdown(self):
        """Shutdown the Redis connection pool."""
        try:
            # Stop cleanup tasks
            for task in self._cleanup_tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # Close Redis client and pool
            if self._redis_client:
                await self._redis_client.close()
            
            if self._pool:
                await self._pool.disconnect()
            
            self._connected = False
            logger.info("✅ Redis connection pool shutdown complete")
            
        except Exception as e:
            logger.error(f"❌ Error during Redis shutdown: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check."""
        try:
            start_time = time.time()
            
            # Basic ping
            await self._redis_client.ping()
            ping_time = time.time() - start_time
            
            # Get Redis info
            redis_info = await self._redis_client.info()
            
            # Check pool status
            pool_info = {
                "max_connections": self.config.max_connections,
                "created_connections": self._pool.created_connections if self._pool else 0,
                "available_connections": len(self._pool._available_connections) if self._pool else 0,
                "in_use_connections": len(self._pool._in_use_connections) if self._pool else 0
            }
            
            # Memory usage
            used_memory = redis_info.get("used_memory", 0)
            max_memory = redis_info.get("maxmemory", 0)
            memory_usage = (used_memory / max_memory * 100) if max_memory > 0 else 0
            
            self._last_health_check = datetime.now()
            
            return {
                "status": "healthy",
                "ping_time_ms": round(ping_time * 1000, 2),
                "connected": self._connected,
                "pool_info": pool_info,
                "memory_usage_percent": round(memory_usage, 2),
                "used_memory_mb": round(used_memory / 1024 / 1024, 2),
                "cache_metrics": {
                    "hit_rate": round(self._metrics.hit_rate, 2),
                    "compression_rate": round(self._metrics.compression_rate, 2),
                    "total_operations": self._metrics.hits + self._metrics.misses + self._metrics.sets,
                    "avg_response_time_ms": round(self._metrics.avg_response_time * 1000, 2)
                },
                "last_check": self._last_health_check.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    def _should_compress(self, data: bytes) -> bool:
        """Determine if data should be compressed."""
        return len(data) >= self.config.compression_threshold
    
    def _compress_data(self, data: bytes) -> Tuple[bytes, bool]:
        """Compress data if it exceeds threshold."""
        if self._should_compress(data):
            try:
                compressed = gzip.compress(data, compresslevel=self.config.compression_level)
                if len(compressed) < len(data):  # Only use if actually smaller
                    self._metrics.compression_saves += 1
                    self._metrics.total_memory_saved += len(data) - len(compressed)
                    return compressed, True
            except Exception as e:
                logger.warning(f"Compression failed: {e}")
        
        return data, False
    
    def _decompress_data(self, data: bytes, is_compressed: bool) -> bytes:
        """Decompress data if it was compressed."""
        if is_compressed:
            try:
                return gzip.decompress(data)
            except Exception as e:
                logger.error(f"Decompression failed: {e}")
                return data
        return data
    
    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value to bytes."""
        try:
            if isinstance(value, (str, int, float, bool)):
                return json.dumps(value).encode('utf-8')
            else:
                # Use pickle for complex objects
                return pickle.dumps(value)
        except Exception as e:
            logger.error(f"Serialization failed: {e}")
            return str(value).encode('utf-8')
    
    def _deserialize_value(self, data: bytes, metadata: Dict[str, Any]) -> Any:
        """Deserialize bytes to value."""
        try:
            # Check if it's JSON or pickle based on metadata
            if metadata.get('type') == 'json':
                return json.loads(data.decode('utf-8'))
            else:
                return pickle.loads(data)
        except Exception as e:
            logger.error(f"Deserialization failed: {e}")
            return data.decode('utf-8', errors='ignore')
    
    def _generate_cache_key(self, prefix: str, key: str) -> str:
        """Generate standardized cache key."""
        # Add prefix for namespacing
        return f"chatbuddy:v1:{prefix}:{key}"
    
    def _get_ttl_for_type(self, cache_type: str) -> int:
        """Get intelligent TTL based on cache type."""
        ttl_mapping = {
            'session': self.config.session_ttl,
            'agent_response': self.config.agent_response_ttl,
            'product_info': self.config.product_info_ttl,
            'search_result': self.config.search_result_ttl,
            'embedding': self.config.embedding_cache_ttl,
            'user_context': self.config.user_context_ttl,
            'rate_limit': self.config.rate_limit_ttl,
            'performance': self.config.performance_cache_ttl
        }
        
        return ttl_mapping.get(cache_type, self.config.performance_cache_ttl)
    
    async def set(self, key: str, value: Any, cache_type: str = 'performance', 
                  ttl: Optional[int] = None, nx: bool = False) -> bool:
        """
        Set a value in cache with optimization.
        
        Args:
            key: Cache key
            value: Value to cache
            cache_type: Type of cache for intelligent TTL
            ttl: Custom TTL (overrides intelligent TTL)
            nx: Only set if key doesn't exist
        """
        if not self._connected:
            return False
        
        start_time = time.time()
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(cache_type, key)
            
            # Serialize value
            serialized_data = self._serialize_value(value)
            
            # Determine data type for deserialization
            data_type = 'json' if isinstance(value, (str, int, float, bool, list, dict)) else 'pickle'
            
            # Compress if needed
            compressed_data, is_compressed = self._compress_data(serialized_data)
            
            # Create metadata
            metadata = {
                'type': data_type,
                'compressed': is_compressed,
                'created_at': datetime.now().isoformat(),
                'size_original': len(serialized_data),
                'size_stored': len(compressed_data)
            }
            
            # Get TTL
            effective_ttl = ttl if ttl is not None else self._get_ttl_for_type(cache_type)
            
            # Store data and metadata
            pipe = self._redis_client.pipeline()
            
            if nx:
                pipe.set(cache_key, compressed_data, ex=effective_ttl, nx=True)
                pipe.set(f"{cache_key}:meta", json.dumps(metadata).encode('utf-8'), ex=effective_ttl, nx=True)
            else:
                pipe.setex(cache_key, effective_ttl, compressed_data)
                pipe.setex(f"{cache_key}:meta", effective_ttl, json.dumps(metadata).encode('utf-8'))
            
            results = await pipe.execute()
            success = results[0] is not False
            
            # Update metrics
            if success:
                self._metrics.sets += 1
                self._update_avg_response_time(time.time() - start_time)
            else:
                self._metrics.errors += 1
            
            return success
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            self._metrics.errors += 1
            return False
    
    async def get(self, key: str, cache_type: str = 'performance') -> Optional[Any]:
        """
        Get a value from cache with decompression.
        
        Args:
            key: Cache key
            cache_type: Type of cache
        """
        if not self._connected:
            return None
        
        start_time = time.time()
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(cache_type, key)
            
            # Get data and metadata
            pipe = self._redis_client.pipeline()
            pipe.get(cache_key)
            pipe.get(f"{cache_key}:meta")
            results = await pipe.execute()
            
            data, metadata_raw = results
            
            if data is None:
                self._metrics.misses += 1
                return None
            
            # Parse metadata
            metadata = {}
            if metadata_raw:
                try:
                    metadata = json.loads(metadata_raw.decode('utf-8'))
                except Exception:
                    pass
            
            # Decompress if needed
            decompressed_data = self._decompress_data(data, metadata.get('compressed', False))
            
            # Deserialize
            value = self._deserialize_value(decompressed_data, metadata)
            
            # Update metrics
            self._metrics.hits += 1
            self._update_avg_response_time(time.time() - start_time)
            
            return value
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self._metrics.errors += 1
            return None
    
    async def delete(self, key: str, cache_type: str = 'performance') -> bool:
        """Delete a key from cache."""
        if not self._connected:
            return False
        
        try:
            cache_key = self._generate_cache_key(cache_type, key)
            
            # Delete both data and metadata
            pipe = self._redis_client.pipeline()
            pipe.delete(cache_key)
            pipe.delete(f"{cache_key}:meta")
            results = await pipe.execute()
            
            success = any(results)
            if success:
                self._metrics.deletes += 1
            
            return success
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            self._metrics.errors += 1
            return False
    
    async def exists(self, key: str, cache_type: str = 'performance') -> bool:
        """Check if key exists in cache."""
        if not self._connected:
            return False
        
        try:
            cache_key = self._generate_cache_key(cache_type, key)
            return await self._redis_client.exists(cache_key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: int, cache_type: str = 'performance') -> bool:
        """Set expiration for a key."""
        if not self._connected:
            return False
        
        try:
            cache_key = self._generate_cache_key(cache_type, key)
            return await self._redis_client.expire(cache_key, ttl)
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {e}")
            return False
    
    async def incr(self, key: str, amount: int = 1, cache_type: str = 'performance') -> Optional[int]:
        """Increment a numeric value."""
        if not self._connected:
            return None
        
        try:
            cache_key = self._generate_cache_key(cache_type, key)
            return await self._redis_client.incr(cache_key, amount)
        except Exception as e:
            logger.error(f"Cache incr error for key {key}: {e}")
            return None
    
    async def get_keys_by_pattern(self, pattern: str, cache_type: str = 'performance') -> List[str]:
        """Get keys matching pattern."""
        if not self._connected:
            return []
        
        try:
            cache_pattern = self._generate_cache_key(cache_type, pattern)
            keys = await self._redis_client.keys(cache_pattern)
            # Remove the cache prefix to return original keys
            prefix = self._generate_cache_key(cache_type, '')
            return [key.decode('utf-8').replace(prefix, '') for key in keys]
        except Exception as e:
            logger.error(f"Cache keys error for pattern {pattern}: {e}")
            return []
    
    def _update_avg_response_time(self, response_time: float):
        """Update average response time metric."""
        total_ops = self._metrics.hits + self._metrics.misses + self._metrics.sets
        if total_ops == 1:
            self._metrics.avg_response_time = response_time
        else:
            # Exponential moving average
            alpha = 0.1
            self._metrics.avg_response_time = (
                alpha * response_time + 
                (1 - alpha) * self._metrics.avg_response_time
            )
    
    def _start_cleanup_tasks(self):
        """Start background cleanup tasks."""
        async def cleanup_expired_keys():
            """Clean up expired keys periodically."""
            while True:
                try:
                    # Let Redis handle TTL expiration automatically
                    # This is just for monitoring and logging
                    await asyncio.sleep(self.config.performance_cleanup_interval)
                    
                    if self._connected:
                        # Log cache statistics periodically
                        stats = await self.get_performance_stats()
                        logger.info(f"Cache stats - Hit rate: {stats['hit_rate']:.1f}%, "
                                  f"Compression: {stats['compression_rate']:.1f}%, "
                                  f"Memory saved: {stats['memory_saved_mb']:.1f}MB")
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Cleanup task error: {e}")
                    await asyncio.sleep(60)
        
        cleanup_task = asyncio.create_task(cleanup_expired_keys())
        self._cleanup_tasks.append(cleanup_task)
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        try:
            health = await self.health_check()
            
            return {
                "hit_rate": self._metrics.hit_rate,
                "cache_operations": {
                    "hits": self._metrics.hits,
                    "misses": self._metrics.misses,
                    "sets": self._metrics.sets,
                    "deletes": self._metrics.deletes,
                    "errors": self._metrics.errors
                },
                "compression": {
                    "compression_rate": self._metrics.compression_rate,
                    "compression_saves": self._metrics.compression_saves,
                    "memory_saved_bytes": self._metrics.total_memory_saved,
                    "memory_saved_mb": round(self._metrics.total_memory_saved / 1024 / 1024, 2)
                },
                "performance": {
                    "avg_response_time_ms": round(self._metrics.avg_response_time * 1000, 2),
                    "connection_pool": health.get("pool_info", {}),
                    "memory_usage_percent": health.get("memory_usage_percent", 0)
                },
                "configuration": {
                    "ttl_settings": {
                        "session": self.config.session_ttl,
                        "performance": self.config.performance_cache_ttl,
                        "agent_response": self.config.agent_response_ttl,
                        "product_info": self.config.product_info_ttl
                    },
                    "compression_threshold_bytes": self.config.compression_threshold,
                    "max_connections": self.config.max_connections
                },
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e), "last_updated": datetime.now().isoformat()}
    
    @asynccontextmanager
    async def pipeline(self):
        """Context manager for Redis pipeline operations."""
        if not self._connected:
            raise ConnectionError("Redis not connected")
        
        pipe = self._redis_client.pipeline()
        try:
            yield pipe
            await pipe.execute()
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            raise
    
    async def reset_metrics(self):
        """Reset performance metrics."""
        self._metrics = CacheMetrics()
        logger.info("Cache metrics reset")


# Global singleton instance
_optimized_redis_pool: Optional[OptimizedRedisConnectionPool] = None


async def get_optimized_redis_pool() -> OptimizedRedisConnectionPool:
    """
    Get the optimized Redis connection pool singleton.
    
    Returns:
        OptimizedRedisConnectionPool instance
    """
    global _optimized_redis_pool
    
    if _optimized_redis_pool is None:
        async with OptimizedRedisConnectionPool._lock:
            if _optimized_redis_pool is None:
                _optimized_redis_pool = OptimizedRedisConnectionPool()
                await _optimized_redis_pool.initialize()
    
    return _optimized_redis_pool


async def shutdown_optimized_redis_pool():
    """Shutdown the optimized Redis connection pool."""
    global _optimized_redis_pool
    
    if _optimized_redis_pool:
        await _optimized_redis_pool.shutdown()
        _optimized_redis_pool = None