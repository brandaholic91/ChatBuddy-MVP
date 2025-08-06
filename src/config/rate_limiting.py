"""
Rate Limiting System for ChatBuddy MVP.

Ez a modul implementálja a rate limiting rendszert a ChatBuddy MVP
biztonsági követelményeihez.
"""

import os
import time
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class RateLimitType(Enum):
    """Rate limit típusok."""
    USER = "user"
    IP = "ip"
    ENDPOINT = "endpoint"
    GLOBAL = "global"


class RateLimitWindow(Enum):
    """Rate limit ablak típusok."""
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"


@dataclass
class RateLimitConfig:
    """Rate limit konfiguráció."""
    limit_type: RateLimitType
    window: RateLimitWindow
    max_requests: int
    window_size: int  # seconds
    burst_size: Optional[int] = None
    cost_per_request: float = 1.0
    enabled: bool = True


@dataclass
class RateLimitState:
    """Rate limit állapot."""
    identifier: str
    limit_type: RateLimitType
    window_start: datetime
    request_count: int
    last_request_time: datetime
    blocked_until: Optional[datetime] = None
    burst_count: int = 0


class RateLimiter:
    """Rate limiting rendszer."""
    
    def __init__(self, configs: Optional[Dict[str, RateLimitConfig]] = None, use_redis: bool = False, redis_client=None):
        self.use_redis = use_redis
        self.redis_client = redis_client
        self.limit_states: Dict[str, RateLimitState] = {}
        self.configs: Dict[str, RateLimitConfig] = configs if configs is not None else self._load_default_configs()
        self.lock = asyncio.Lock()
    
    def _load_default_configs(self) -> Dict[str, RateLimitConfig]:
        """Alapértelmezett rate limit konfigurációk betöltése."""
        return {
            # User-based limits
            "user_chat": RateLimitConfig(
                limit_type=RateLimitType.USER,
                window=RateLimitWindow.MINUTE,
                max_requests=50,
                window_size=60,
                burst_size=10,
                cost_per_request=1.0
            ),
            "user_search": RateLimitConfig(
                limit_type=RateLimitType.USER,
                window=RateLimitWindow.MINUTE,
                max_requests=100,
                window_size=60,
                burst_size=20,
                cost_per_request=0.5
            ),
            "user_auth": RateLimitConfig(
                limit_type=RateLimitType.USER,
                window=RateLimitWindow.MINUTE,
                max_requests=5,
                window_size=60,
                burst_size=2,
                cost_per_request=2.0
            ),
            
            # IP-based limits
            "ip_general": RateLimitConfig(
                limit_type=RateLimitType.IP,
                window=RateLimitWindow.MINUTE,
                max_requests=200,
                window_size=60,
                burst_size=50,
                cost_per_request=1.0
            ),
            "ip_auth": RateLimitConfig(
                limit_type=RateLimitType.IP,
                window=RateLimitWindow.MINUTE,
                max_requests=10,
                window_size=60,
                burst_size=3,
                cost_per_request=2.0
            ),
            
            # Endpoint-based limits
            "endpoint_chat": RateLimitConfig(
                limit_type=RateLimitType.ENDPOINT,
                window=RateLimitWindow.MINUTE,
                max_requests=1000,
                window_size=60,
                burst_size=200,
                cost_per_request=1.0
            ),
            "endpoint_search": RateLimitConfig(
                limit_type=RateLimitType.ENDPOINT,
                window=RateLimitWindow.MINUTE,
                max_requests=2000,
                window_size=60,
                burst_size=500,
                cost_per_request=0.5
            ),
            
            # Global limits
            "global_api": RateLimitConfig(
                limit_type=RateLimitType.GLOBAL,
                window=RateLimitWindow.MINUTE,
                max_requests=10000,
                window_size=60,
                burst_size=2000,
                cost_per_request=1.0
            )
        }
    
    def _get_identifier(self, limit_type: RateLimitType, key: str) -> str:
        """Rate limit azonosító generálása."""
        return f"{limit_type.value}:{key}"
    
    def _get_window_start(self, window: RateLimitWindow) -> datetime:
        """Aktuális ablak kezdete."""
        now = datetime.now(timezone.utc)
        
        if window == RateLimitWindow.SECOND:
            return now.replace(microsecond=0)
        elif window == RateLimitWindow.MINUTE:
            return now.replace(second=0, microsecond=0)
        elif window == RateLimitWindow.HOUR:
            return now.replace(minute=0, second=0, microsecond=0)
        elif window == RateLimitWindow.DAY:
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            return now
    
    async def check_rate_limit(
        self,
        config_key: str,
        identifier: str,
        cost: float = 1.0,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Rate limit ellenőrzése.
        
        Args:
            config_key: Konfiguráció kulcs
            identifier: Azonosító (user_id, ip, endpoint)
            cost: Kérés költsége
            user_id: Felhasználó azonosító
            ip_address: IP cím
            
        Returns:
            (allowed, details)
        """
        async with self.lock:
            try:
                config = self.configs.get(config_key)
                if not config or not config.enabled:
                    return True, {"reason": "no_limit", "remaining_requests": -1}
                
                # Get current window
                window_start = self._get_window_start(config.window)
                
                # Create state key
                state_key = self._get_identifier(config.limit_type, identifier)
                
                # Get or create state
                state = await self._get_state(state_key, config, window_start)
                
                # Check if blocked
                if state.blocked_until and datetime.now(timezone.utc) < state.blocked_until:
                    return False, {
                        "reason": "blocked",
                        "blocked_until": state.blocked_until.isoformat(),
                        "retry_after": int((state.blocked_until - datetime.now(timezone.utc)).total_seconds())
                    }
                
                # Check burst limit
                if config.burst_size and state.burst_count >= config.burst_size:
                    # Block for a short period
                    state.blocked_until = datetime.now(timezone.utc) + timedelta(seconds=30)
                    await self._save_state(state_key, state)
                    
                    return False, {
                        "reason": "burst_limit_exceeded",
                        "burst_size": config.burst_size,
                        "retry_after": 30
                    }
                
                # Check regular limit
                effective_cost = cost * config.cost_per_request
                if state.request_count + effective_cost > config.max_requests:
                    # Calculate retry after
                    window_end = window_start + timedelta(seconds=config.window_size)
                    retry_after = int((window_end - datetime.now(timezone.utc)).total_seconds())
                    
                    return False, {
                        "reason": "rate_limit_exceeded",
                        "max_requests": config.max_requests,
                        "current_requests": state.request_count,
                        "retry_after": max(0, retry_after)
                    }
                
                # Update state
                state.request_count += effective_cost
                state.last_request_time = datetime.now(timezone.utc)
                state.burst_count += 1
                
                # Reset burst count if window changed
                if state.window_start != window_start:
                    state.window_start = window_start
                    state.request_count = effective_cost
                    state.burst_count = 1
                
                await self._save_state(state_key, state)
                
                return True, {
                    "reason": "allowed",
                    "remaining_requests": max(0, config.max_requests - state.request_count),
                    "reset_time": (window_start + timedelta(seconds=config.window_size)).isoformat()
                }
                
            except Exception as e:
                logger.error(f"Rate limit check error: {e}")
                # Fail open on error
                return True, {"reason": "error", "error": str(e)}
    
    async def _get_state(
        self,
        state_key: str,
        config: RateLimitConfig,
        window_start: datetime
    ) -> RateLimitState:
        """Rate limit állapot lekérése."""
        if self.use_redis and self.redis_client:
            return await self._get_redis_state(state_key, config, window_start)
        else:
            return self._get_memory_state(state_key, config, window_start)
    
    def _get_memory_state(
        self,
        state_key: str,
        config: RateLimitConfig,
        window_start: datetime
    ) -> RateLimitState:
        """Memória alapú állapot lekérése."""
        if state_key not in self.limit_states:
            self.limit_states[state_key] = RateLimitState(
                identifier=state_key,
                limit_type=config.limit_type,
                window_start=window_start,
                request_count=0,
                last_request_time=datetime.now(timezone.utc),
                burst_count=0
            )
        
        state = self.limit_states[state_key]
        
        # Reset if window changed
        if state.window_start != window_start:
            state.window_start = window_start
            state.request_count = 0
            state.burst_count = 0
            state.blocked_until = None
        
        return state
    
    async def _get_redis_state(
        self,
        state_key: str,
        config: RateLimitConfig,
        window_start: datetime
    ) -> RateLimitState:
        """Redis alapú állapot lekérése."""
        try:
            # Get state from Redis
            state_data = await self.redis_client.get(f"rate_limit:{state_key}")
            
            if state_data:
                import json
                state_dict = json.loads(state_data)  # Safe JSON deserialization
                state = RateLimitState(**state_dict)
                
                # Reset if window changed
                if state.window_start != window_start:
                    state.window_start = window_start
                    state.request_count = 0
                    state.burst_count = 0
                    state.blocked_until = None
                
                return state
            else:
                # Create new state
                return RateLimitState(
                    identifier=state_key,
                    limit_type=config.limit_type,
                    window_start=window_start,
                    request_count=0,
                    last_request_time=datetime.now(timezone.utc),
                    burst_count=0
                )
                
        except Exception as e:
            logger.error(f"Redis state retrieval error: {e}")
            # Fallback to memory state
            return self._get_memory_state(state_key, config, window_start)
    
    async def _save_state(self, state_key: str, state: RateLimitState):
        """Rate limit állapot mentése."""
        if self.use_redis and self.redis_client:
            await self._save_redis_state(state_key, state)
        else:
            self._save_memory_state(state_key, state)
    
    def _save_memory_state(self, state_key: str, state: RateLimitState):
        """Memória alapú állapot mentése."""
        self.limit_states[state_key] = state
    
    async def _save_redis_state(self, state_key: str, state: RateLimitState):
        """Redis alapú állapot mentése."""
        try:
            # Convert to dict and serialize
            state_dict = asdict(state)
            state_dict["window_start"] = state.window_start.isoformat()
            state_dict["last_request_time"] = state.last_request_time.isoformat()
            if state.blocked_until:
                state_dict["blocked_until"] = state.blocked_until.isoformat()
            
            # Save to Redis with TTL
            await self.redis_client.setex(
                f"rate_limit:{state_key}",
                3600,  # 1 hour TTL
                str(state_dict)
            )
            
        except Exception as e:
            logger.error(f"Redis state save error: {e}")
            # Fallback to memory
            self._save_memory_state(state_key, state)
    
    async def get_rate_limit_info(
        self,
        config_key: str,
        identifier: str
    ) -> Dict[str, Any]:
        """
        Rate limit információk lekérése.
        
        Args:
            config_key: Konfiguráció kulcs
            identifier: Azonosító
            
        Returns:
            Rate limit információk
        """
        try:
            config = self.configs.get(config_key)
            if not config:
                return {"error": "config_not_found"}
            
            state_key = self._get_identifier(config.limit_type, identifier)
            window_start = self._get_window_start(config.window)
            
            state = await self._get_state(state_key, config, window_start)
            
            return {
                "config_key": config_key,
                "identifier": identifier,
                "limit_type": config.limit_type.value,
                "window": config.window.value,
                "max_requests": config.max_requests,
                "current_requests": state.request_count,
                "remaining_requests": max(0, config.max_requests - state.request_count),
                "window_start": state.window_start.isoformat(),
                "window_end": (window_start + timedelta(seconds=config.window_size)).isoformat(),
                "last_request": state.last_request_time.isoformat(),
                "burst_count": state.burst_count,
                "burst_size": config.burst_size,
                "blocked_until": state.blocked_until.isoformat() if state.blocked_until else None
            }
            
        except Exception as e:
            logger.error(f"Rate limit info error: {e}")
            return {"error": str(e)}
    
    async def reset_rate_limit(
        self,
        config_key: str,
        identifier: str
    ) -> bool:
        """
        Rate limit reset.
        
        Args:
            config_key: Konfiguráció kulcs
            identifier: Azonosító
            
        Returns:
            True ha sikeres
        """
        try:
            config = self.configs.get(config_key)
            if not config:
                return False
            
            state_key = self._get_identifier(config.limit_type, identifier)
            
            if self.use_redis and self.redis_client:
                await self.redis_client.delete(f"rate_limit:{state_key}")
            else:
                if state_key in self.limit_states:
                    del self.limit_states[state_key]
            
            return True
            
        except Exception as e:
            logger.error(f"Rate limit reset error: {e}")
            return False
    
    def add_config(self, config_key: str, config: RateLimitConfig):
        """Új rate limit konfiguráció hozzáadása."""
        self.configs[config_key] = config
    
    def remove_config(self, config_key: str):
        """Rate limit konfiguráció eltávolítása."""
        if config_key in self.configs:
            del self.configs[config_key]
    
    async def cleanup_expired_states(self) -> int:
        """
        Lejárt állapotok tisztítása.
        
        Returns:
            Tisztított állapotok száma
        """
        try:
            cleaned_count = 0
            now = datetime.now(timezone.utc)
            
            # Clean memory states
            expired_keys = []
            for key, state in self.limit_states.items():
                # Check if state is older than 1 hour
                if (now - state.last_request_time) > timedelta(hours=1):
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.limit_states[key]
                cleaned_count += 1
            
            # Clean Redis states (TTL handles this automatically)
            if self.use_redis and self.redis_client:
                # Redis automatically expires keys based on TTL
                pass
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Rate limit cleanup error: {e}")
            return 0


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter(use_redis: bool = False, redis_client=None) -> RateLimiter:
    """
    Rate limiter singleton instance.
    
    Args:
        use_redis: Redis használata
        redis_client: Redis kliens
        
    Returns:
        RateLimiter instance
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(use_redis=use_redis, redis_client=redis_client)
    return _rate_limiter


# Rate limiting decorators
def rate_limit(config_key: str, identifier_func=None):
    """
    Rate limiting dekorátor.
    
    Args:
        config_key: Konfiguráció kulcs
        identifier_func: Azonosító függvény
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            rate_limiter = get_rate_limiter()
            
            # Get identifier
            if identifier_func:
                identifier = identifier_func(*args, **kwargs)
            else:
                # Default: use first argument as identifier
                identifier = str(args[0]) if args else "default"
            
            # Check rate limit
            allowed, details = await rate_limiter.check_rate_limit(config_key, identifier)
            
            if not allowed:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "rate_limit_exceeded",
                        "message": "Túl sok kérés. Kérjük, várjon egy kicsit.",
                        "retry_after": details.get("retry_after", 60),
                        "details": details
                    }
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def user_rate_limit(config_key: str):
    """Felhasználó alapú rate limiting dekorátor."""
    def get_user_id(*args, **kwargs):
        # Extract user_id from request or arguments
        # This is a simplified version - adjust based on your request structure
        for arg in args:
            if hasattr(arg, 'user_id'):
                return str(arg.user_id)
        for key, value in kwargs.items():
            if key == 'user_id':
                return str(value)
        return "anonymous"
    
    return rate_limit(config_key, get_user_id)


def ip_rate_limit(config_key: str):
    """IP alapú rate limiting dekorátor."""
    def get_ip_address(*args, **kwargs):
        # Extract IP address from request or arguments
        # This is a simplified version - adjust based on your request structure
        for arg in args:
            if hasattr(arg, 'client'):
                return str(arg.client.host)
        return "unknown"
    
    return rate_limit(config_key, get_ip_address)


# Utility functions
async def check_user_rate_limit(
    user_id: str,
    config_key: str = "user_chat",
    cost: float = 1.0
) -> Tuple[bool, Dict[str, Any]]:
    """
    Felhasználó rate limit ellenőrzése.
    
    Args:
        user_id: Felhasználó azonosító
        config_key: Konfiguráció kulcs
        cost: Kérés költsége
        
    Returns:
        (allowed, details)
    """
    rate_limiter = get_rate_limiter()
    return await rate_limiter.check_rate_limit(config_key, user_id, cost)


async def check_ip_rate_limit(
    ip_address: str,
    config_key: str = "ip_general",
    cost: float = 1.0
) -> Tuple[bool, Dict[str, Any]]:
    """
    IP rate limit ellenőrzése.
    
    Args:
        ip_address: IP cím
        config_key: Konfiguráció kulcs
        cost: Kérés költsége
        
    Returns:
        (allowed, details)
    """
    rate_limiter = get_rate_limiter()
    return await rate_limiter.check_rate_limit(config_key, ip_address, cost)


async def get_rate_limit_status(
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    config_key: str = "user_chat"
) -> Dict[str, Any]:
    """
    Rate limit státusz lekérése.
    
    Args:
        user_id: Felhasználó azonosító
        ip_address: IP cím
        config_key: Konfiguráció kulcs
        
    Returns:
        Rate limit státusz
    """
    rate_limiter = get_rate_limiter()
    
    if user_id:
        return await rate_limiter.get_rate_limit_info(config_key, user_id)
    elif ip_address:
        return await rate_limiter.get_rate_limit_info(config_key, ip_address)
    else:
        return {"error": "no_identifier_provided"}


async def reset_user_rate_limit(user_id: str, config_key: str = "user_chat") -> bool:
    """
    Felhasználó rate limit reset.
    
    Args:
        user_id: Felhasználó azonosító
        config_key: Konfiguráció kulcs
        
    Returns:
        True ha sikeres
    """
    rate_limiter = get_rate_limiter()
    return await rate_limiter.reset_rate_limit(config_key, user_id)


async def reset_ip_rate_limit(ip_address: str, config_key: str = "ip_general") -> bool:
    """
    IP rate limit reset.
    
    Args:
        ip_address: IP cím
        config_key: Konfiguráció kulcs
        
    Returns:
        True ha sikeres
    """
    rate_limiter = get_rate_limiter()
    return await rate_limiter.reset_rate_limit(config_key, ip_address) 