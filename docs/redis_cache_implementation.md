# Redis Cache Implementation - Dokumentáció

## Áttekintés

A Redis Cache Implementation a Chatbuddy MVP rendszer teljesítményének optimalizálására szolgál. A Redis in-memory adatbázist használja a következő funkciókhoz:

- **Session Storage**: Chat session adatok és felhasználói kontextus kezelése
- **Performance Cache**: Agent válaszok, termék információk és keresési eredmények cache-elése
- **Rate Limiting**: IP és felhasználó alapú kérés korlátozás

## Architektúra

### Komponensek

```
RedisCacheService
├── SessionCache
│   ├── Session létrehozás/törlés
│   ├── Session lekérés/frissítés
│   └── User sessions kezelés
├── PerformanceCache
│   ├── Agent response cache
│   ├── Product info cache
│   ├── Search result cache
│   └── Embedding cache
└── RateLimitCache
    ├── IP-based rate limiting
    ├── User-based rate limiting
    └── Rate limit info/cleanup
```

### Adatstruktúrák

#### SessionData
```python
@dataclass
class SessionData:
    session_id: str
    user_id: str
    device_info: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    started_at: datetime
    last_activity: datetime
    is_active: bool
    expires_at: Optional[datetime]
    context: Dict[str, Any]
```

#### CacheConfig
```python
@dataclass
class CacheConfig:
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
```

## Implementáció

### 1. Session Storage

#### Session létrehozása
```python
session_id = await cache_service.session_cache.create_session(
    user_id="user123",
    device_info={"browser": "Chrome", "os": "Windows"},
    ip_address="192.168.1.100",
    user_agent="Mozilla/5.0..."
)
```

#### Session lekérése
```python
session_data = await cache_service.session_cache.get_session(session_id)
if session_data:
    print(f"User: {session_data.user_id}")
    print(f"Last activity: {session_data.last_activity}")
```

#### Session frissítése
```python
session_data.context["preferences"] = {"language": "hu"}
success = await cache_service.session_cache.update_session(session_id, session_data)
```

#### User sessions lekérése
```python
user_sessions = await cache_service.session_cache.get_user_sessions("user123")
for session in user_sessions:
    print(f"Session: {session.session_id}")
```

### 2. Performance Cache

#### Termék információk cache-elése
```python
product_data = {
    "id": "product123",
    "name": "iPhone 15 Pro Max",
    "price": 499999,
    "brand": "Apple"
}

success = await cache_service.performance_cache.cache_product_info(
    "product123", 
    product_data
)
```

#### Cache-elt termék információk lekérése
```python
cached_data = await cache_service.performance_cache.get_cached_product_info("product123")
if cached_data:
    print(f"Product: {cached_data['name']}")
```

#### Keresési eredmények cache-elése
```python
search_results = [
    {"id": "1", "name": "iPhone 15 Pro Max", "similarity": 0.95},
    {"id": "2", "name": "iPhone 15 Pro", "similarity": 0.85}
]

query_hash = hashlib.md5("iPhone 15".encode()).hexdigest()
success = await cache_service.performance_cache.cache_search_result(
    query_hash, 
    search_results
)
```

#### Embedding cache-elés
```python
text_hash = hashlib.md5("iPhone 15 Pro Max".encode()).hexdigest()
embedding = [0.1, 0.2, 0.3, ...]  # 1536 dimenzió

success = await cache_service.performance_cache.cache_embedding(
    text_hash, 
    embedding
)
```

### 3. Rate Limiting

#### IP-alapú rate limiting
```python
result = await cache_service.rate_limit_cache.check_ip_rate_limit(
    ip_address="192.168.1.100",
    max_requests=100,
    window_seconds=60
)

if result["allowed"]:
    print(f"Request allowed: {result['current_count']}/{result['max_requests']}")
else:
    print(f"Rate limit exceeded. Reset in {result['reset_time']} seconds")
```

#### User-alapú rate limiting
```python
result = await cache_service.rate_limit_cache.check_user_rate_limit(
    user_id="user123",
    max_requests=50,
    window_seconds=60
)
```

#### Rate limit információk
```python
info = await cache_service.rate_limit_cache.get_rate_limit_info(
    "user123", 
    "user"
)
print(f"Current count: {info['current_count']}")
print(f"TTL: {info['ttl']} seconds")
```

## Integráció

### Vector Operations Cache

A vector operations automatikusan használja a cache-t:

```python
# generate_embedding automatikusan cache-eli az embedding-eket
embedding = await vector_ops.generate_embedding("iPhone 15 Pro Max")

# search_similar_products cache-eli a keresési eredményeket
results = await vector_ops.search_similar_products("okos telefon", limit=10)
```

### Main Application

A main.py automatikusan inicializálja a Redis cache szolgáltatást:

```python
# Startup
redis_cache_service = await get_redis_cache_service()

# Health check
health = await redis_cache_service.health_check()

# Shutdown
await shutdown_redis_cache_service()
```

## Konfiguráció

### Környezeti változók

```bash
# Redis kapcsolat
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=your-redis-password-here-minimum-8-characters
```

### Cache konfiguráció testreszabása

```python
from src.integrations.cache import CacheConfig

custom_config = CacheConfig(
    session_ttl=7200,  # 2 óra
    agent_response_ttl=1800,  # 30 perc
    product_info_ttl=900,  # 15 perc
    search_result_ttl=600,  # 10 perc
    embedding_cache_ttl=3600  # 1 óra
)

cache_service = RedisCacheService(config=custom_config)
```

## Teljesítmény

### Cache hatékonyság

- **Session Storage**: 24 órás TTL, automatikus cleanup
- **Performance Cache**: 
  - Agent responses: 1 óra
  - Product info: 30 perc
  - Search results: 15 perc
  - Embeddings: 2 óra
- **Rate Limiting**: 1 perces ablak, automatikus cleanup

### Monitoring

```python
# Cache statisztikák
stats = await cache_service.get_stats()
print(f"Agent responses: {stats['performance_cache']['agent_responses']}")
print(f"Product info: {stats['performance_cache']['product_info']}")
print(f"Search results: {stats['performance_cache']['search_results']}")
print(f"Embeddings: {stats['performance_cache']['embeddings']}")

# Health check
health = await cache_service.health_check()
print(f"Redis connection: {health['redis_connection']}")
```

## Tesztelés

### Teszt script futtatása

```bash
python test_redis_cache.py
```

### Tesztelt funkciók

1. **Redis kapcsolat**
2. **Session cache**
   - Session létrehozás
   - Session lekérés
   - Session frissítés
   - User sessions
3. **Performance cache**
   - Termék info cache
   - Search result cache
   - Embedding cache
4. **Rate limiting**
   - IP rate limit
   - User rate limit
   - Rate limit info
5. **Cache statisztikák**
6. **Cleanup**

## Hibakezelés

### Kapcsolat hibák

```python
try:
    cache_service = await get_redis_cache_service()
except Exception as e:
    logger.warning(f"Redis cache unavailable: {e}")
    # Fallback to database-only operations
```

### Cache hibák

```python
try:
    cached_data = await cache_service.performance_cache.get_cached_product_info(product_id)
    if cached_data:
        return cached_data
except Exception as e:
    logger.warning(f"Cache error: {e}")

# Fallback to database query
return await database.get_product_info(product_id)
```

## Biztonság

### Redis biztonság

- **Jelszó védelem**: REDIS_PASSWORD környezeti változó
- **Hálózati izoláció**: Redis csak lokálisan elérhető
- **TTL kezelés**: Automatikus adatok törlése
- **Cleanup**: Rendszeres lejárt adatok tisztítása

### Adatvédelem

- **Session adatok**: Felhasználói kontextus biztonságos tárolása
- **Cache adatok**: Érzékeny információk nem kerülnek cache-elésre
- **Rate limiting**: DDoS védelem és fair use policy

## Következő lépések

### Jövőbeli fejlesztések

1. **Cluster támogatás**: Redis Cluster konfiguráció
2. **Persistence**: RDB/AOF backup konfiguráció
3. **Monitoring**: Redis Monitor és Grafana dashboard
4. **Cache warming**: Előre betöltött cache adatok
5. **Distributed locking**: Redis alapú lock mechanizmus

### Optimalizációk

1. **Connection pooling**: Redis kapcsolat pool optimalizálás
2. **Pipeline operations**: Batch Redis műveletek
3. **Compression**: Cache adatok tömörítése
4. **Eviction policies**: LRU/LFU cache eviction
5. **Memory optimization**: Redis memória használat optimalizálás

## Összefoglaló

A Redis Cache Implementation sikeresen integrálva van a Chatbuddy MVP rendszerbe és biztosítja:

- ✅ **Session Storage**: Felhasználói session adatok kezelése
- ✅ **Performance Cache**: Gyors adatelérés és teljesítmény optimalizálás
- ✅ **Rate Limiting**: Biztonságos kérés kezelés
- ✅ **Automatikus cleanup**: Memória optimalizálás
- ✅ **Health monitoring**: Rendszer állapot követés
- ✅ **Hibakezelés**: Robusztus működés

A cache rendszer jelentősen javítja a rendszer teljesítményét és felhasználói élményét, miközben biztonságos és skálázható megoldást nyújt. 