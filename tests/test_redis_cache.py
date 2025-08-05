#!/usr/bin/env python3
"""
Redis Cache Integration Test Script

Ez a script teszteli a Redis cache implementációt:
- Session storage
- Performance cache
- Rate limiting
"""

import asyncio
import os
import sys
import time
import hashlib
from typing import Dict, Any, List
import logging

# Projekt root hozzáadása a path-hoz
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from src.integrations.cache import (
    RedisCacheService, 
    SessionCache, 
    PerformanceCache, 
    RateLimitCache,
    CacheConfig,
    SessionData,
    get_redis_cache_service
)
from src.config.logging import get_logger

logger = get_logger(__name__)


class RedisCacheTester:
    """Redis Cache tesztelő"""
    
    def __init__(self):
        """Inicializálja a tesztelőt"""
        self.cache_service = None
        
        # Teszt adatok
        self.test_user_id = "test-user-123"
        self.test_session_id = None
        self.test_product_id = "test-product-456"
        self.test_query = "iPhone 15 Pro Max smartphone"
        
    async def test_redis_connection(self) -> bool:
        """Teszteli a Redis kapcsolatot"""
        try:
            logger.info("🔗 Redis kapcsolat tesztelése...")
            
            # Explicit Redis URL átadása
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            redis_password = os.getenv("REDIS_PASSWORD", "defaultpassword")
            
            if not redis_url:
                logger.error("❌ REDIS_URL környezeti változó nincs beállítva")
                return False
            
            # Jelszó hozzáadása a Redis URL-hez
            logger.info(f"🔑 Redis jelszó: {redis_password}")
            logger.info(f"🔍 Redis URL részletek: {redis_url.split('@')[0]}")
            
            # Ellenőrizzük, hogy már van-e jelszó a URL-ben
            if redis_password and "@" not in redis_url:
                # redis://localhost:6379 -> redis://:password@localhost:6379
                if redis_url.startswith("redis://"):
                    redis_url = redis_url.replace("redis://", f"redis://:{redis_password}@")
                elif redis_url.startswith("rediss://"):
                    redis_url = redis_url.replace("rediss://", f"rediss://:{redis_password}@")
                logger.info(f"🔐 Jelszó hozzáadva a Redis URL-hez")
            else:
                logger.info(f"⚠️ Jelszó nem került hozzáadásra")
            
            logger.info(f"📍 Redis URL: {redis_url}")
            
            # Redis cache service létrehozása explicit URL-lel
            from src.integrations.cache import RedisCacheService
            self.cache_service = RedisCacheService(redis_url=redis_url)
            await self.cache_service.initialize()
            
            health = await self.cache_service.health_check()
            
            if health["redis_connection"]:
                logger.info("✅ Redis kapcsolat sikeres")
                return True
            else:
                logger.error("❌ Redis kapcsolat sikertelen")
                return False
                
        except Exception as e:
            logger.error(f"❌ Redis kapcsolat hiba: {e}")
            return False
    
    async def test_session_cache(self) -> bool:
        """Teszteli a session cache-t"""
        try:
            logger.info("🔄 Session cache tesztelése...")
            
            # Session létrehozása
            session_id = await self.cache_service.session_cache.create_session(
                user_id=self.test_user_id,
                device_info={"browser": "Chrome", "os": "Windows"},
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0..."
            )
            
            if not session_id:
                logger.error("❌ Session létrehozás sikertelen")
                return False
            
            self.test_session_id = session_id
            logger.info(f"✅ Session létrehozva: {session_id}")
            
            # Session lekérése
            session_data = await self.cache_service.session_cache.get_session(session_id)
            
            if not session_data:
                logger.error("❌ Session lekérés sikertelen")
                return False
            
            if session_data.user_id != self.test_user_id:
                logger.error("❌ Session adatok nem egyeznek")
                return False
            
            logger.info("✅ Session lekérés sikeres")
            
            # Session frissítése
            session_data.context["test_key"] = "test_value"
            success = await self.cache_service.session_cache.update_session(session_id, session_data)
            
            if not success:
                logger.error("❌ Session frissítés sikertelen")
                return False
            
            logger.info("✅ Session frissítés sikeres")
            
            # User sessions lekérése
            user_sessions = await self.cache_service.session_cache.get_user_sessions(self.test_user_id)
            
            if not user_sessions:
                logger.error("❌ User sessions lekérés sikertelen")
                return False
            
            logger.info(f"✅ User sessions lekérés sikeres: {len(user_sessions)} session")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Session cache hiba: {e}")
            return False
    
    async def test_performance_cache(self) -> bool:
        """Teszteli a performance cache-t"""
        try:
            logger.info("⚡ Performance cache tesztelése...")
            
            # Termék info cache
            test_product_data = {
                "id": self.test_product_id,
                "name": "iPhone 15 Pro Max",
                "price": 499999,
                "brand": "Apple",
                "description": "Legújabb iPhone modell"
            }
            
            # Cache-elés
            success = await self.cache_service.performance_cache.cache_product_info(
                self.test_product_id, 
                test_product_data
            )
            
            if not success:
                logger.error("❌ Termék info cache-elés sikertelen")
                return False
            
            logger.info("✅ Termék info cache-elve")
            
            # Cache-elt adatok lekérése
            cached_data = await self.cache_service.performance_cache.get_cached_product_info(
                self.test_product_id
            )
            
            if not cached_data:
                logger.error("❌ Cache-elt termék info lekérés sikertelen")
                return False
            
            if cached_data["name"] != test_product_data["name"]:
                logger.error("❌ Cache-elt adatok nem egyeznek")
                return False
            
            logger.info("✅ Cache-elt termék info lekérés sikeres")
            
            # Search result cache
            test_search_results = [
                {"id": "1", "name": "iPhone 15 Pro Max", "similarity": 0.95},
                {"id": "2", "name": "iPhone 15 Pro", "similarity": 0.85}
            ]
            
            query_hash = hashlib.md5(self.test_query.encode()).hexdigest()
            
            # Search result cache-elés
            success = await self.cache_service.performance_cache.cache_search_result(
                query_hash, 
                test_search_results
            )
            
            if not success:
                logger.error("❌ Search result cache-elés sikertelen")
                return False
            
            logger.info("✅ Search result cache-elve")
            
            # Cache-elt search result lekérése
            cached_results = await self.cache_service.performance_cache.get_cached_search_result(
                query_hash
            )
            
            if not cached_results:
                logger.error("❌ Cache-elt search result lekérés sikertelen")
                return False
            
            if len(cached_results) != len(test_search_results):
                logger.error("❌ Cache-elt search result nem egyezik")
                return False
            
            logger.info("✅ Cache-elt search result lekérés sikeres")
            
            # Embedding cache
            test_embedding = [0.1, 0.2, 0.3, 0.4, 0.5] * 300  # 1500 dimenzió
            text_hash = hashlib.md5(self.test_query.encode()).hexdigest()
            
            # Embedding cache-elés
            success = await self.cache_service.performance_cache.cache_embedding(
                text_hash, 
                test_embedding
            )
            
            if not success:
                logger.error("❌ Embedding cache-elés sikertelen")
                return False
            
            logger.info("✅ Embedding cache-elve")
            
            # Cache-elt embedding lekérése
            cached_embedding = await self.cache_service.performance_cache.get_cached_embedding(
                text_hash
            )
            
            if not cached_embedding:
                logger.error("❌ Cache-elt embedding lekérés sikertelen")
                return False
            
            if len(cached_embedding) != len(test_embedding):
                logger.error("❌ Cache-elt embedding nem egyezik")
                return False
            
            logger.info("✅ Cache-elt embedding lekérés sikeres")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Performance cache hiba: {e}")
            return False
    
    async def test_rate_limiting(self) -> bool:
        """Teszteli a rate limiting-et"""
        try:
            logger.info("🚦 Rate limiting tesztelése...")
            
            test_ip = "192.168.1.100"
            test_user = "test-user-456"
            
            # IP rate limit teszt
            for i in range(3):
                result = await self.cache_service.rate_limit_cache.check_ip_rate_limit(
                    test_ip, 
                    max_requests=5, 
                    window_seconds=60
                )
                
                if not result["allowed"]:
                    logger.error(f"❌ IP rate limit túllépve: {result}")
                    return False
                
                logger.info(f"✅ IP rate limit {i+1}/3: {result}")
            
            # User rate limit teszt
            for i in range(3):
                result = await self.cache_service.rate_limit_cache.check_user_rate_limit(
                    test_user, 
                    max_requests=5, 
                    window_seconds=60
                )
                
                if not result["allowed"]:
                    logger.error(f"❌ User rate limit túllépve: {result}")
                    return False
                
                logger.info(f"✅ User rate limit {i+1}/3: {result}")
            
            # Rate limit info lekérése
            ip_info = await self.cache_service.rate_limit_cache.get_rate_limit_info(
                test_ip, 
                "ip"
            )
            
            if "error" in ip_info:
                logger.error(f"❌ Rate limit info hiba: {ip_info}")
                return False
            
            logger.info(f"✅ Rate limit info: {ip_info}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Rate limiting hiba: {e}")
            return False
    
    async def test_cache_stats(self) -> bool:
        """Teszteli a cache statisztikákat"""
        try:
            logger.info("📊 Cache statisztikák tesztelése...")
            
            stats = await self.cache_service.get_stats()
            
            if "error" in stats:
                logger.error(f"❌ Cache stats hiba: {stats}")
                return False
            
            logger.info("✅ Cache statisztikák lekérdezve")
            logger.info(f"📈 Stats: {stats}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Cache stats hiba: {e}")
            return False
    
    async def cleanup_test_data(self) -> bool:
        """Tisztítja a teszt adatokat"""
        try:
            logger.info("🧹 Teszt adatok tisztítása...")
            
            # Session törlése
            if self.test_session_id:
                await self.cache_service.session_cache.delete_session(self.test_session_id)
                logger.info("✅ Teszt session törölve")
            
            # Rate limit reset
            await self.cache_service.rate_limit_cache.reset_rate_limit("192.168.1.100", "ip")
            await self.cache_service.rate_limit_cache.reset_rate_limit("test-user-456", "user")
            logger.info("✅ Rate limit-ek resetelve")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Cleanup hiba: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Futtatja az összes tesztet"""
        logger.info("🚀 Redis Cache Integration tesztek indítása...")
        
        results = {}
        
        # 1. Redis kapcsolat
        results["redis_connection"] = await self.test_redis_connection()
        
        if not results["redis_connection"]:
            logger.error("❌ Redis kapcsolat sikertelen, tesztek leállítva")
            return results
        
        # 2. Session cache
        results["session_cache"] = await self.test_session_cache()
        
        # 3. Performance cache
        results["performance_cache"] = await self.test_performance_cache()
        
        # 4. Rate limiting
        results["rate_limiting"] = await self.test_rate_limiting()
        
        # 5. Cache statisztikák
        results["cache_stats"] = await self.test_cache_stats()
        
        # 6. Cleanup
        results["cleanup"] = await self.cleanup_test_data()
        
        # Összefoglaló
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        logger.info(f"\n📊 TESZT EREDMÉNYEK: {success_count}/{total_count} sikeres")
        
        for test_name, success in results.items():
            if success:
                logger.info(f"✅ {test_name}")
            else:
                logger.error(f"❌ {test_name}")
        
        return results


async def main():
    """Fő függvény"""
    try:
        # Környezeti változók betöltése
        load_dotenv()
        
        # Környezeti változók ellenőrzése
        required_env_vars = [
            "REDIS_URL"
        ]
        
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"❌ Hiányzó környezeti változók: {missing_vars}")
            logger.error("Kérlek állítsd be ezeket a .env fájlban")
            return
        
        # Tesztelő inicializálása
        tester = RedisCacheTester()
        
        # Tesztek futtatása
        results = await tester.run_all_tests()
        
        # Eredmények kiértékelése
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        if success_count == total_count:
            logger.info("\n🎉 MINDEN TESZT SIKERES!")
            logger.info("✅ Redis Cache Integration teljesen működőképes")
        else:
            logger.warning(f"\n⚠️ {total_count - success_count} teszt sikertelen")
            logger.warning("Kérlek ellenőrizd a hibákat és próbáld újra")
        
    except Exception as e:
        logger.error(f"❌ Kritikus hiba: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Logging beállítása
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Async main futtatása
    asyncio.run(main()) 