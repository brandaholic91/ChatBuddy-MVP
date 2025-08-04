"""
Redis-alapú Rate Limiting - Chatbuddy MVP.

Ez a modul implementálja a Redis-alapú rate limiting rendszert
a production-ready rate limiting-hoz.
"""

import os
import time
import asyncio
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import redis.asyncio as redis
from fastapi import HTTPException, Request
import structlog

logger = structlog.get_logger(__name__)

# Redis connection
redis_client: Optional[redis.Redis] = None


class RedisRateLimiter:
    """Redis-alapú rate limiter."""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.client = None
        self.default_limits = {
            "default": "100/minute",
            "auth": "5/minute", 
            "chat": "50/minute",
            "api": "200/minute",
            "admin": "1000/minute"
        }
    
    async def connect(self):
        """Redis kapcsolat létrehozása."""
        try:
            self.client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            await self.client.ping()
            logger.info("Redis rate limiter kapcsolat sikeres")
        except Exception as e:
            logger.error(f"Redis kapcsolat hiba: {e}")
            # Fallback to in-memory rate limiting
            self.client = None
    
    async def check_rate_limit(
        self, 
        key: str, 
        limit: str, 
        window: int = 60
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Rate limit ellenőrzése.
        
        Args:
            key: Rate limit kulcs (pl. user_id, ip)
            limit: Limit string (pl. "100/minute")
            window: Időablak másodpercben
            
        Returns:
            (allowed, info) tuple
        """
        if not self.client:
            # Fallback to in-memory
            return await self._check_memory_rate_limit(key, limit, window)
        
        try:
            # Parse limit string
            count, period = self._parse_limit(limit)
            
            # Create Redis key
            redis_key = f"rate_limit:{key}:{period}"
            current_time = int(time.time())
            
            # Get current count
            pipe = self.client.pipeline()
            pipe.zremrangebyscore(redis_key, 0, current_time - window)
            pipe.zadd(redis_key, {str(current_time): current_time})
            pipe.zcard(redis_key)
            pipe.expire(redis_key, window)
            results = await pipe.execute()
            
            current_count = results[2]
            allowed = current_count <= count
            
            return allowed, {
                "limit": count,
                "remaining": max(0, count - current_count),
                "reset_time": current_time + window,
                "current_count": current_count
            }
            
        except Exception as e:
            logger.error(f"Rate limit ellenőrzés hiba: {e}")
            # Fallback to in-memory
            return await self._check_memory_rate_limit(key, limit, window)
    
    async def _check_memory_rate_limit(
        self, 
        key: str, 
        limit: str, 
        window: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """In-memory rate limiting fallback."""
        # Simple in-memory implementation
        count, period = self._parse_limit(limit)
        current_time = int(time.time())
        
        # This is a simplified version - in production use proper in-memory storage
        return True, {
            "limit": count,
            "remaining": count,
            "reset_time": current_time + window,
            "current_count": 0
        }
    
    def _parse_limit(self, limit: str) -> Tuple[int, str]:
        """Limit string feldolgozása."""
        try:
            count_str, period = limit.split("/")
            count = int(count_str)
            return count, period
        except:
            # Default fallback
            return 100, "minute"
    
    async def get_rate_limit_info(self, key: str, limit: str) -> Dict[str, Any]:
        """Rate limit információk lekérése."""
        allowed, info = await self.check_rate_limit(key, limit)
        return {
            "allowed": allowed,
            **info
        }
    
    async def reset_rate_limit(self, key: str, period: str = "minute"):
        """Rate limit reset."""
        if self.client:
            redis_key = f"rate_limit:{key}:{period}"
            await self.client.delete(redis_key)


class RateLimitMiddleware:
    """Rate limiting middleware."""
    
    def __init__(self, rate_limiter: RedisRateLimiter):
        self.rate_limiter = rate_limiter
    
    async def __call__(self, request: Request, call_next):
        """Middleware handler."""
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Determine rate limit based on endpoint
        limit = self._get_rate_limit_for_endpoint(request.url.path)
        
        # Check rate limit
        allowed, info = await self.rate_limiter.check_rate_limit(client_id, limit)
        
        if not allowed:
            logger.warning(
                "Rate limit túllépve",
                client_id=client_id,
                endpoint=request.url.path,
                limit=limit
            )
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit túllépve",
                    "retry_after": info["reset_time"] - int(time.time()),
                    "limit": info["limit"],
                    "remaining": info["remaining"]
                }
            )
        
        # Add rate limit headers
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(info["reset_time"])
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Kliens azonosító meghatározása."""
        # Try to get user ID from token first
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                # Extract user ID from JWT token
                token = auth_header.split(" ")[1]
                # TODO: Implement JWT decode to get user_id
                # user_id = decode_jwt(token).get("user_id")
                # if user_id:
                #     return f"user:{user_id}"
            except:
                pass
        
        # Fallback to IP address
        return f"ip:{request.client.host}"
    
    def _get_rate_limit_for_endpoint(self, path: str) -> str:
        """Rate limit meghatározása endpoint alapján."""
        if path.startswith("/auth"):
            return "5/minute"
        elif path.startswith("/chat"):
            return "50/minute"
        elif path.startswith("/admin"):
            return "1000/minute"
        elif path.startswith("/api"):
            return "200/minute"
        else:
            return "100/minute"


# Global rate limiter instance
_rate_limiter: Optional[RedisRateLimiter] = None


async def get_rate_limiter() -> RedisRateLimiter:
    """Rate limiter singleton."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RedisRateLimiter()
        await _rate_limiter.connect()
    return _rate_limiter


async def check_rate_limit(key: str, limit: str) -> bool:
    """Rate limit ellenőrzése."""
    limiter = await get_rate_limiter()
    allowed, _ = await limiter.check_rate_limit(key, limit)
    return allowed


async def get_rate_limit_info(key: str, limit: str) -> Dict[str, Any]:
    """Rate limit információk."""
    limiter = await get_rate_limiter()
    return await limiter.get_rate_limit_info(key, limit) 