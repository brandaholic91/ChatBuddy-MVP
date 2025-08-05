#!/usr/bin/env python3
"""
Redis kapcsolat teszt script ChatBuddy MVP projekthez
Használat: python test_redis_connection.py
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Environment variables betöltése
load_dotenv()

async def test_redis_connection():
    """Redis kapcsolat tesztelése"""
    print("🔍 Redis kapcsolat tesztelése...")
    
    # Redis URL ellenőrzése
    redis_url = os.getenv("REDIS_URL")
    redis_password = os.getenv("REDIS_PASSWORD")
    
    if not redis_url:
        print("❌ REDIS_URL környezeti változó nincs beállítva!")
        print("Adja hozzá a .env fájlhoz:")
        print("REDIS_URL=redis://localhost:6379")
        return False
    
    if not redis_password:
        print("❌ REDIS_PASSWORD környezeti változó nincs beállítva!")
        print("Adja hozzá a .env fájlhoz:")
        print("REDIS_PASSWORD=defaultpassword")
        return False
    
    print(f"📍 Redis URL: {redis_url}")
    print(f"🔑 Jelszó: {'*' * len(redis_password)}")
    
    try:
        # Redis kapcsolat tesztelése
        import redis.asyncio as redis
        
        # Redis kliens létrehozása
        r = redis.from_url(
            redis_url,
            password=redis_password,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
        # Ping teszt
        print("🏓 Ping teszt...")
        pong = await r.ping()
        if pong:
            print("✅ Ping sikeres!")
        else:
            print("❌ Ping sikertelen!")
            return False
        
        # Egyszerű írás/olvasás teszt
        print("📝 Írás/olvasás teszt...")
        test_key = "chatbuddy_test"
        test_value = "Hello Redis!"
        
        await r.set(test_key, test_value, ex=60)  # 60 másodperc TTL
        retrieved_value = await r.get(test_key)
        
        if retrieved_value == test_value:
            print("✅ Írás/olvasás sikeres!")
        else:
            print(f"❌ Írás/olvasás sikertelen! Várt: {test_value}, Kapott: {retrieved_value}")
            return False
        
        # Törlés
        await r.delete(test_key)
        
        # Redis info lekérése
        print("📊 Redis információk...")
        info = await r.info()
        print(f"   Redis verzió: {info.get('redis_version', 'N/A')}")
        print(f"   Kapcsolatok: {info.get('connected_clients', 'N/A')}")
        print(f"   Használt memória: {info.get('used_memory_human', 'N/A')}")
        print(f"   Uptime: {info.get('uptime_in_seconds', 'N/A')} másodperc")
        
        # Kapcsolat lezárása
        await r.close()
        
        print("✅ Redis kapcsolat teszt sikeres!")
        return True
        
    except redis.ConnectionError as e:
        print(f"❌ Redis kapcsolat hiba: {e}")
        print("Ellenőrizd, hogy:")
        print("1. A Redis konténer fut-e: docker ps")
        print("2. A Redis URL helyes-e: redis://localhost:6379")
        print("3. A jelszó helyes-e")
        return False
        
    except Exception as e:
        print(f"❌ Váratlan hiba: {e}")
        return False

async def test_redis_operations():
    """Redis műveletek tesztelése"""
    print("\n🔧 Redis műveletek tesztelése...")
    
    try:
        import redis.asyncio as redis
        
        redis_url = os.getenv("REDIS_URL")
        redis_password = os.getenv("REDIS_PASSWORD")
        
        r = redis.from_url(
            redis_url,
            password=redis_password,
            decode_responses=True
        )
        
        # Hash műveletek
        print("📋 Hash műveletek...")
        await r.hset("user:1", mapping={
            "name": "Teszt Felhasználó",
            "email": "teszt@example.com",
            "last_login": "2024-01-01"
        })
        user_data = await r.hgetall("user:1")
        if user_data:
            print("✅ Hash műveletek sikeresek!")
        
        # List műveletek
        print("📝 List műveletek...")
        await r.lpush("chat:session:1", "Üzenet 1", "Üzenet 2", "Üzenet 3")
        messages = await r.lrange("chat:session:1", 0, -1)
        if len(messages) == 3:
            print("✅ List műveletek sikeresek!")
        
        # Set műveletek
        print("🔢 Set műveletek...")
        await r.sadd("online_users", "user1", "user2", "user3")
        online_count = await r.scard("online_users")
        if online_count == 3:
            print("✅ Set műveletek sikeresek!")
        
        # Sorted Set műveletek
        print("📊 Sorted Set műveletek...")
        await r.zadd("leaderboard", {
            "player1": 100,
            "player2": 200,
            "player3": 150
        })
        top_player = await r.zrevrange("leaderboard", 0, 0, withscores=True)
        if top_player and top_player[0][1] == 200:
            print("✅ Sorted Set műveletek sikeresek!")
        
        # TTL teszt
        print("⏰ TTL teszt...")
        await r.setex("temp_key", 5, "ideiglenes érték")
        ttl = await r.ttl("temp_key")
        if ttl > 0:
            print("✅ TTL működik!")
        
        # Tisztítás
        await r.delete("user:1", "chat:session:1", "online_users", "leaderboard", "temp_key")
        
        await r.close()
        print("✅ Minden Redis művelet sikeres!")
        return True
        
    except Exception as e:
        print(f"❌ Redis műveletek hiba: {e}")
        return False

async def main():
    """Fő teszt funkció"""
    print("🚀 Redis teszt indítása ChatBuddy MVP projekthez...")
    print("=" * 50)
    
    # Kapcsolat teszt
    connection_ok = await test_redis_connection()
    if not connection_ok:
        print("\n❌ Redis kapcsolat teszt sikertelen!")
        sys.exit(1)
    
    # Műveletek teszt
    operations_ok = await test_redis_operations()
    if not operations_ok:
        print("\n❌ Redis műveletek teszt sikertelen!")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 Minden Redis teszt sikeres!")
    print("✅ A Redis készen áll a ChatBuddy MVP használatára!")

if __name__ == "__main__":
    asyncio.run(main()) 