# Redis Lokális Beállítás ChatBuddy MVP

Ez a dokumentáció leírja, hogyan állítsd be a Redis-t lokálisan a ChatBuddy MVP projekthez.

## 📋 Előfeltételek

- Docker Desktop telepítve és fut
- Python 3.8+ telepítve
- `.env` fájl konfigurálva

## 🚀 Gyors Indítás

### 1. Docker használatával (Ajánlott)

```bash
# Redis indítása
docker-compose up -d redis

# Vagy használd a scriptet
.\start_redis.ps1
# vagy
start_redis.bat
```

### 2. Kapcsolat tesztelése

```bash
# Python teszt script
python test_redis_connection.py

# Vagy manuálisan
docker exec -it chatbuddy-mvp_redis_1 redis-cli
```

## ⚙️ Konfiguráció

### Environment Variables

A `.env` fájlban állítsd be:

```env
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=defaultpassword
```

### Docker Compose Konfiguráció

A `docker-compose.yml` fájlban:

```yaml
redis:
  image: redis:8-alpine
  ports:
    - "6379:6379"
  command: redis-server --requirepass ${REDIS_PASSWORD:-defaultpassword} --maxmemory 256mb --maxmemory-policy allkeys-lru
  volumes:
    - redis_data:/data
  healthcheck:
    test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
    interval: 10s
    timeout: 5s
    retries: 3
  restart: unless-stopped
```

## 🔧 Redis Konfigurációs Fájl

A `redis.conf` fájl tartalmazza a részletes beállításokat:

- **Hálózat**: 127.0.0.1:6379
- **Jelszó**: defaultpassword
- **Memória**: 256MB limit
- **Persistence**: AOF és RDB
- **Teljesítmény**: Optimalizált beállítások

## 📊 Redis Adatstruktúrák

A ChatBuddy MVP a következő Redis adatstruktúrákat használja:

### 1. Session Cache
```python
# Session adatok tárolása
session_key = f"session:{session_id}"
await redis.hset(session_key, mapping={
    "user_id": user_id,
    "started_at": timestamp,
    "last_activity": timestamp,
    "context": json.dumps(context)
})
```

### 2. Performance Cache
```python
# Agent válaszok cache-elése
response_key = f"agent_response:{query_hash}"
await redis.setex(response_key, 3600, json.dumps(response))

# Termék információk cache-elése
product_key = f"product:{product_id}"
await redis.setex(product_key, 1800, json.dumps(product_data))
```

### 3. Rate Limiting
```python
# IP-alapú rate limiting
rate_key = f"rate_limit:ip:{ip_address}"
current = await redis.incr(rate_key)
if current == 1:
    await redis.expire(rate_key, 60)
```

## 🧪 Tesztelés

### Kapcsolat Teszt
```bash
python test_redis_connection.py
```

### Redis Cache Teszt
```bash
python test_redis_cache.py
```

### Manuális Teszt
```bash
# Redis CLI elérése
docker exec -it chatbuddy-mvp_redis_1 redis-cli

# Jelszó megadása
AUTH defaultpassword

# Ping teszt
PING

# Egyszerű műveletek
SET test_key "Hello Redis"
GET test_key
DEL test_key
```

## 📈 Monitoring

### Redis Info
```bash
# Redis információk lekérése
docker exec -it chatbuddy-mvp_redis_1 redis-cli INFO

# Memória használat
docker exec -it chatbuddy-mvp_redis_1 redis-cli INFO memory

# Kapcsolatok
docker exec -it chatbuddy-mvp_redis_1 redis-cli INFO clients
```

### Logok
```bash
# Redis logok megtekintése
docker logs chatbuddy-mvp_redis_1

# Valós idejű logok
docker logs -f chatbuddy-mvp_redis_1
```

## 🔒 Biztonság

### Jelszó Védelem
- Mindig használj jelszót a Redis-hez
- Ne használd az alapértelmezett jelszót production környezetben
- A jelszót environment variable-ban tárold

### Hálózati Biztonság
- Redis csak localhost-on érhető el
- Production környezetben használj VPN-t vagy tűzfalat
- Ne tedd közzé a Redis portot a nyilvános interneten

## 🚨 Hibaelhárítás

### Kapcsolat Hiba
```bash
# Ellenőrizd, hogy a konténer fut-e
docker ps

# Indítsd újra a Redis-t
docker-compose restart redis

# Ellenőrizd a logokat
docker logs chatbuddy-mvp_redis_1
```

### Memória Hiba
```bash
# Memória használat ellenőrzése
docker exec -it chatbuddy-mvp_redis_1 redis-cli INFO memory

# Memória törlése (vigyázat!)
docker exec -it chatbuddy-mvp_redis_1 redis-cli FLUSHALL
```

### Teljesítmény Problémák
```bash
# Lassú lekérdezések
docker exec -it chatbuddy-mvp_redis_1 redis-cli SLOWLOG GET 10

# Monitor mód
docker exec -it chatbuddy-mvp_redis_1 redis-cli MONITOR
```

## 📚 Hasznos Parancsok

```bash
# Redis indítása
docker-compose up -d redis

# Redis leállítása
docker-compose stop redis

# Redis újraindítása
docker-compose restart redis

# Redis törlése (adatvesztés!)
docker-compose down -v

# Redis CLI
docker exec -it chatbuddy-mvp_redis_1 redis-cli

# Redis logok
docker logs chatbuddy-mvp_redis_1

# Redis statisztikák
docker exec -it chatbuddy-mvp_redis_1 redis-cli INFO
```

## 🔗 További Források

- [Redis Hivatalos Dokumentáció](https://redis.io/documentation)
- [Redis GitHub](https://github.com/redis/redis)
- [Redis Python Kliens](https://redis-py.readthedocs.io/)
- [Redis Docker Image](https://hub.docker.com/_/redis)

## 📝 Megjegyzések

- A Redis 8.0 verziót használjuk a legújabb funkciókkal
- A memória limit 256MB fejlesztési környezetben
- Az AOF persistence biztosítja az adatok megmaradását
- A health check automatikusan ellenőrzi a Redis állapotát 