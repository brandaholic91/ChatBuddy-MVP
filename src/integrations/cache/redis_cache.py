#!/usr/bin/env python3
"""
Redis Cache Implementation

Ez a modul implementálja a Redis cache funkcionalitást:
- Session storage
- Performance cache
- Rate limiting
"""

import asyncio
import json
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
import uuid

import redis.asyncio as redis
from redis.exceptions import RedisError, ConnectionError

from src.config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CacheConfig:
    """Cache konfiguráció"""
    # Session storage
    session_ttl: int = 86400  # 24 óra
    session_cleanup_interval: int = 3600  # 1 óra
    
    # Performance cache
    agent_response_ttl: int = 3600  # 1 óra
    product_info_ttl: int = 1800  # 30 perc
    search_result_ttl: int = 900  # 15 perc
    embedding_cache_ttl: int = 7200  # 2 óra
    
    # Rate limiting
    rate_limit_window: int = 60  # 1 perc
    rate_limit_cleanup_interval: int = 300  # 5 perc


@dataclass
class SessionData:
    """Session adatok"""
    session_id: str
    user_id: str
    device_info: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    started_at: datetime = None
    last_activity: datetime = None
    is_active: bool = True
    expires_at: Optional[datetime] = None
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.started_at is None:
            self.started_at = datetime.now()
        if self.last_activity is None:
            self.last_activity = datetime.now()
        if self.context is None:
            self.context = {}


@dataclass
class CacheEntry:
    """Cache bejegyzés"""
    key: str
    value: Any
    ttl: int
    created_at: datetime
    expires_at: datetime
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.expires_at is None:
            self.expires_at = self.created_at + timedelta(seconds=self.ttl)


class RedisCacheManager:
    """Redis cache kezelő"""
    
    def __init__(self, redis_url: Optional[str] = None, config: Optional[CacheConfig] = None):
        """Inicializálja a Redis cache kezelőt"""
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.config = config or CacheConfig()
        self.redis_client: Optional[redis.Redis] = None
        self._connection_retries = 3
        self._connection_retry_delay = 1
        
    async def connect(self) -> bool:
        """Kapcsolódik a Redis szerverhez"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Kapcsolat tesztelése
            await self.redis_client.ping()
            logger.info("✅ Redis kapcsolat sikeres")
            return True
            
        except (RedisError, ConnectionError) as e:
            logger.error(f"❌ Redis kapcsolat hiba: {e}")
            return False
    
    async def disconnect(self):
        """Lecsatlakozik a Redis szerverről"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis kapcsolat lezárva")
    
    async def health_check(self) -> bool:
        """Redis health check"""
        try:
            if not self.redis_client:
                return False
            await self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check hiba: {e}")
            return False
    
    def _generate_key(self, prefix: str, identifier: str) -> str:
        """Cache kulcs generálása"""
        return f"{prefix}:{identifier}"
    
    async def _serialize_value(self, value: Any) -> str:
        """Érték szerializálása JSON-ba"""
        if isinstance(value, (datetime, timedelta)):
            return json.dumps(value.isoformat())
        elif hasattr(value, '__dict__'):
            # Dataclass objektumok kezelése
            if hasattr(value, '__dataclass_fields__'):
                data = {}
                for field_name, field_value in asdict(value).items():
                    if isinstance(field_value, datetime):
                        data[field_name] = field_value.isoformat()
                    elif isinstance(field_value, timedelta):
                        data[field_name] = field_value.total_seconds()
                    else:
                        data[field_name] = field_value
                return json.dumps(data)
            else:
                return json.dumps(asdict(value))
        else:
            return json.dumps(value)
    
    async def _deserialize_value(self, value: str) -> Any:
        """Érték deszerializálása JSON-ból"""
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value


class SessionCache(RedisCacheManager):
    """Session cache kezelő"""
    
    def __init__(self, redis_url: Optional[str] = None, config: Optional[CacheConfig] = None):
        super().__init__(redis_url, config)
        self.session_prefix = "session"
        self.user_sessions_prefix = "user_sessions"
    
    async def create_session(self, user_id: str, device_info: Optional[Dict] = None, 
                           ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Optional[str]:
        """Új session létrehozása"""
        try:
            session_id = str(uuid.uuid4())
            session_data = SessionData(
                session_id=session_id,
                user_id=user_id,
                device_info=device_info,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=datetime.now() + timedelta(seconds=self.config.session_ttl)
            )
            
            # Session adatok mentése
            session_key = self._generate_key(self.session_prefix, session_id)
            session_value = await self._serialize_value(session_data)
            
            await self.redis_client.setex(
                session_key,
                self.config.session_ttl,
                session_value
            )
            
            # User sessions index frissítése
            user_sessions_key = self._generate_key(self.user_sessions_prefix, user_id)
            await self.redis_client.sadd(user_sessions_key, session_id)
            await self.redis_client.expire(user_sessions_key, self.config.session_ttl)
            
            logger.info(f"Session létrehozva: {session_id} user: {user_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Session létrehozás hiba: {e}")
            return None
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """Session lekérése"""
        try:
            session_key = self._generate_key(self.session_prefix, session_id)
            session_value = await self.redis_client.get(session_key)
            
            if not session_value:
                return None
            
            session_dict = await self._deserialize_value(session_value)
            session_data = SessionData(**session_dict)
            
            # Last activity frissítése
            session_data.last_activity = datetime.now()
            await self.update_session(session_id, session_data)
            
            return session_data
            
        except Exception as e:
            logger.error(f"Session lekérés hiba: {e}")
            return None
    
    async def update_session(self, session_id: str, session_data: SessionData) -> bool:
        """Session frissítése"""
        try:
            session_key = self._generate_key(self.session_prefix, session_id)
            session_value = await self._serialize_value(session_data)
            
            await self.redis_client.setex(
                session_key,
                self.config.session_ttl,
                session_value
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Session frissítés hiba: {e}")
            return False
    
    async def delete_session(self, session_id: str) -> bool:
        """Session törlése"""
        try:
            session_key = self._generate_key(self.session_prefix, session_id)
            session_data = await self.get_session(session_id)
            
            if session_data:
                # User sessions index frissítése
                user_sessions_key = self._generate_key(self.user_sessions_prefix, session_data.user_id)
                await self.redis_client.srem(user_sessions_key, session_id)
            
            await self.redis_client.delete(session_key)
            logger.info(f"Session törölve: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Session törlés hiba: {e}")
            return False
    
    async def get_user_sessions(self, user_id: str) -> List[SessionData]:
        """Felhasználó összes session-je"""
        try:
            user_sessions_key = self._generate_key(self.user_sessions_prefix, user_id)
            session_ids = await self.redis_client.smembers(user_sessions_key)
            
            sessions = []
            for session_id in session_ids:
                session_data = await self.get_session(session_id)
                if session_data:
                    sessions.append(session_data)
            
            return sessions
            
        except Exception as e:
            logger.error(f"User sessions lekérés hiba: {e}")
            return []
    
    async def cleanup_expired_sessions(self) -> int:
        """Lejárt session-ök tisztítása"""
        try:
            # Redis automatikusan kezeli a TTL-t, de manuálisan is törölhetünk
            pattern = f"{self.session_prefix}:*"
            keys = await self.redis_client.keys(pattern)
            
            deleted_count = 0
            for key in keys:
                ttl = await self.redis_client.ttl(key)
                if ttl <= 0:
                    await self.redis_client.delete(key)
                    deleted_count += 1
            
            logger.info(f"Lejárt session-ök törölve: {deleted_count}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Session cleanup hiba: {e}")
            return 0


class PerformanceCache(RedisCacheManager):
    """Performance cache kezelő"""
    
    def __init__(self, redis_url: Optional[str] = None, config: Optional[CacheConfig] = None):
        super().__init__(redis_url, config)
        self.agent_response_prefix = "agent_response"
        self.product_info_prefix = "product_info"
        self.search_result_prefix = "search_result"
        self.embedding_cache_prefix = "embedding"
    
    async def cache_agent_response(self, query_hash: str, response: Any) -> bool:
        """Agent válasz cache-elése"""
        try:
            key = self._generate_key(self.agent_response_prefix, query_hash)
            value = await self._serialize_value(response)
            
            await self.redis_client.setex(
                key,
                self.config.agent_response_ttl,
                value
            )
            
            logger.debug(f"Agent válasz cache-elve: {query_hash}")
            return True
            
        except Exception as e:
            logger.error(f"Agent response cache hiba: {e}")
            return False
    
    async def get_cached_agent_response(self, query_hash: str) -> Optional[Any]:
        """Cache-elt agent válasz lekérése"""
        try:
            key = self._generate_key(self.agent_response_prefix, query_hash)
            value = await self.redis_client.get(key)
            
            if value:
                return await self._deserialize_value(value)
            return None
            
        except Exception as e:
            logger.error(f"Agent response cache lekérés hiba: {e}")
            return None
    
    async def cache_product_info(self, product_id: str, product_data: Dict[str, Any]) -> bool:
        """Termék információk cache-elése"""
        try:
            key = self._generate_key(self.product_info_prefix, product_id)
            value = await self._serialize_value(product_data)
            
            await self.redis_client.setex(
                key,
                self.config.product_info_ttl,
                value
            )
            
            logger.debug(f"Termék info cache-elve: {product_id}")
            return True
            
        except Exception as e:
            logger.error(f"Product info cache hiba: {e}")
            return False
    
    async def get_cached_product_info(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Cache-elt termék információk lekérése"""
        try:
            key = self._generate_key(self.product_info_prefix, product_id)
            value = await self.redis_client.get(key)
            
            if value:
                return await self._deserialize_value(value)
            return None
            
        except Exception as e:
            logger.error(f"Product info cache lekérés hiba: {e}")
            return None
    
    async def cache_search_result(self, query_hash: str, results: List[Dict[str, Any]]) -> bool:
        """Keresési eredmények cache-elése"""
        try:
            key = self._generate_key(self.search_result_prefix, query_hash)
            value = await self._serialize_value(results)
            
            await self.redis_client.setex(
                key,
                self.config.search_result_ttl,
                value
            )
            
            logger.debug(f"Search result cache-elve: {query_hash}")
            return True
            
        except Exception as e:
            logger.error(f"Search result cache hiba: {e}")
            return False
    
    async def get_cached_search_result(self, query_hash: str) -> Optional[List[Dict[str, Any]]]:
        """Cache-elt keresési eredmények lekérése"""
        try:
            key = self._generate_key(self.search_result_prefix, query_hash)
            value = await self.redis_client.get(key)
            
            if value:
                return await self._deserialize_value(value)
            return None
            
        except Exception as e:
            logger.error(f"Search result cache lekérés hiba: {e}")
            return None
    
    async def cache_embedding(self, text_hash: str, embedding: List[float]) -> bool:
        """Embedding cache-elése"""
        try:
            key = self._generate_key(self.embedding_cache_prefix, text_hash)
            value = await self._serialize_value(embedding)
            
            await self.redis_client.setex(
                key,
                self.config.embedding_cache_ttl,
                value
            )
            
            logger.debug(f"Embedding cache-elve: {text_hash}")
            return True
            
        except Exception as e:
            logger.error(f"Embedding cache hiba: {e}")
            return False
    
    async def get_cached_embedding(self, text_hash: str) -> Optional[List[float]]:
        """Cache-elt embedding lekérése"""
        try:
            key = self._generate_key(self.embedding_cache_prefix, text_hash)
            value = await self.redis_client.get(key)
            
            if value:
                return await self._deserialize_value(value)
            return None
            
        except Exception as e:
            logger.error(f"Embedding cache lekérés hiba: {e}")
            return None
    
    async def invalidate_product_cache(self, product_id: str) -> bool:
        """Termék cache érvénytelenítése"""
        try:
            key = self._generate_key(self.product_info_prefix, product_id)
            await self.redis_client.delete(key)
            logger.info(f"Termék cache érvénytelenítve: {product_id}")
            return True
            
        except Exception as e:
            logger.error(f"Product cache invalidation hiba: {e}")
            return False
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Cache statisztikák"""
        try:
            stats = {}
            
            # Agent response cache
            agent_keys = await self.redis_client.keys(f"{self.agent_response_prefix}:*")
            stats["agent_responses"] = len(agent_keys)
            
            # Product info cache
            product_keys = await self.redis_client.keys(f"{self.product_info_prefix}:*")
            stats["product_info"] = len(product_keys)
            
            # Search result cache
            search_keys = await self.redis_client.keys(f"{self.search_result_prefix}:*")
            stats["search_results"] = len(search_keys)
            
            # Embedding cache
            embedding_keys = await self.redis_client.keys(f"{self.embedding_cache_prefix}:*")
            stats["embeddings"] = len(embedding_keys)
            
            return stats
            
        except Exception as e:
            logger.error(f"Cache stats hiba: {e}")
            return {}


class RateLimitCache(RedisCacheManager):
    """Rate limiting cache kezelő"""
    
    def __init__(self, redis_url: Optional[str] = None, config: Optional[CacheConfig] = None):
        super().__init__(redis_url, config)
        self.rate_limit_prefix = "rate_limit"
        self.ip_limit_prefix = "ip_limit"
        self.user_limit_prefix = "user_limit"
    
    async def check_rate_limit(self, identifier: str, limit_type: str, max_requests: int, 
                             window_seconds: int) -> Dict[str, Any]:
        """Rate limit ellenőrzése"""
        try:
            prefix = f"{self.rate_limit_prefix}:{limit_type}"
            key = self._generate_key(prefix, identifier)
            
            # Aktuális kérés szám lekérése
            current_count = await self.redis_client.get(key)
            current_count = int(current_count) if current_count else 0
            
            # Limit ellenőrzése
            if current_count >= max_requests:
                return {
                    "allowed": False,
                    "current_count": current_count,
                    "max_requests": max_requests,
                    "reset_time": await self.redis_client.ttl(key)
                }
            
            # Kérés szám növelése
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window_seconds)
            await pipe.execute()
            
            return {
                "allowed": True,
                "current_count": current_count + 1,
                "max_requests": max_requests,
                "reset_time": window_seconds
            }
            
        except Exception as e:
            logger.error(f"Rate limit ellenőrzés hiba: {e}")
            return {"allowed": True, "error": str(e)}
    
    async def check_ip_rate_limit(self, ip_address: str, max_requests: int = 100, 
                                window_seconds: int = 60) -> Dict[str, Any]:
        """IP-alapú rate limiting"""
        return await self.check_rate_limit(
            ip_address, 
            "ip", 
            max_requests, 
            window_seconds
        )
    
    async def check_user_rate_limit(self, user_id: str, max_requests: int = 50, 
                                  window_seconds: int = 60) -> Dict[str, Any]:
        """User-alapú rate limiting"""
        return await self.check_rate_limit(
            user_id, 
            "user", 
            max_requests, 
            window_seconds
        )
    
    async def reset_rate_limit(self, identifier: str, limit_type: str) -> bool:
        """Rate limit reset"""
        try:
            prefix = f"{self.rate_limit_prefix}:{limit_type}"
            key = self._generate_key(prefix, identifier)
            await self.redis_client.delete(key)
            logger.info(f"Rate limit reset: {limit_type}:{identifier}")
            return True
            
        except Exception as e:
            logger.error(f"Rate limit reset hiba: {e}")
            return False
    
    async def get_rate_limit_info(self, identifier: str, limit_type: str) -> Dict[str, Any]:
        """Rate limit információk"""
        try:
            prefix = f"{self.rate_limit_prefix}:{limit_type}"
            key = self._generate_key(prefix, identifier)
            
            current_count = await self.redis_client.get(key)
            ttl = await self.redis_client.ttl(key)
            
            return {
                "identifier": identifier,
                "limit_type": limit_type,
                "current_count": int(current_count) if current_count else 0,
                "ttl": ttl if ttl > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Rate limit info hiba: {e}")
            return {"error": str(e)}
    
    async def cleanup_expired_limits(self) -> int:
        """Lejárt rate limit-ek tisztítása"""
        try:
            pattern = f"{self.rate_limit_prefix}:*"
            keys = await self.redis_client.keys(pattern)
            
            deleted_count = 0
            for key in keys:
                ttl = await self.redis_client.ttl(key)
                if ttl <= 0:
                    await self.redis_client.delete(key)
                    deleted_count += 1
            
            logger.info(f"Lejárt rate limit-ek törölve: {deleted_count}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Rate limit cleanup hiba: {e}")
            return 0


class RedisCacheService:
    """Redis cache szolgáltatás - fő osztály"""
    
    def __init__(self, redis_url: Optional[str] = None, config: Optional[CacheConfig] = None):
        """Inicializálja a Redis cache szolgáltatást"""
        self.config = config or CacheConfig()
        self.session_cache = SessionCache(redis_url, config)
        self.performance_cache = PerformanceCache(redis_url, config)
        self.rate_limit_cache = RateLimitCache(redis_url, config)
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> bool:
        """Redis cache szolgáltatás inicializálása"""
        try:
            # Kapcsolódás
            if not await self.session_cache.connect():
                return False
            
            # Performance cache kapcsolódása
            self.performance_cache.redis_client = self.session_cache.redis_client
            self.rate_limit_cache.redis_client = self.session_cache.redis_client
            
            # Cleanup task indítása
            self._start_cleanup_task()
            
            logger.info("✅ Redis Cache Service inicializálva")
            return True
            
        except Exception as e:
            logger.error(f"❌ Redis Cache Service inicializálás hiba: {e}")
            return False
    
    async def shutdown(self):
        """Redis cache szolgáltatás leállítása"""
        try:
            # Cleanup task leállítása
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # Kapcsolat lezárása
            await self.session_cache.disconnect()
            
            logger.info("Redis Cache Service leállítva")
            
        except Exception as e:
            logger.error(f"Redis Cache Service shutdown hiba: {e}")
    
    def _start_cleanup_task(self):
        """Cleanup task indítása"""
        async def cleanup_loop():
            while True:
                try:
                    # Session cleanup
                    await self.session_cache.cleanup_expired_sessions()
                    
                    # Rate limit cleanup
                    await self.rate_limit_cache.cleanup_expired_limits()
                    
                    # Várakozás a következő cleanup-ra
                    await asyncio.sleep(self.config.session_cleanup_interval)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Cleanup loop hiba: {e}")
                    await asyncio.sleep(60)  # 1 perc várakozás hiba esetén
        
        self._cleanup_task = asyncio.create_task(cleanup_loop())
    
    async def health_check(self) -> Dict[str, bool]:
        """Health check minden cache komponenshez"""
        return {
            "redis_connection": await self.session_cache.health_check(),
            "session_cache": await self.session_cache.health_check(),
            "performance_cache": await self.performance_cache.health_check(),
            "rate_limit_cache": await self.rate_limit_cache.health_check()
        }
    
    async def get_stats(self) -> Dict[str, Any]:
        """Cache statisztikák"""
        try:
            stats = {
                "performance_cache": await self.performance_cache.get_cache_stats(),
                "health": await self.health_check()
            }
            return stats
            
        except Exception as e:
            logger.error(f"Cache stats hiba: {e}")
            return {"error": str(e)}


# Singleton instance
_redis_cache_service: Optional[RedisCacheService] = None


async def get_redis_cache_service() -> RedisCacheService:
    """Redis cache szolgáltatás singleton instance"""
    global _redis_cache_service
    
    if _redis_cache_service is None:
        _redis_cache_service = RedisCacheService()
        await _redis_cache_service.initialize()
    
    return _redis_cache_service


async def shutdown_redis_cache_service():
    """Redis cache szolgáltatás leállítása"""
    global _redis_cache_service
    
    if _redis_cache_service:
        await _redis_cache_service.shutdown()
        _redis_cache_service = None 