# WebSocket Real-time Kommunikáció Implementáció

## Áttekintés

A ChatBuddy MVP WebSocket implementációja valós idejű, kétirányú kommunikációt biztosít a kliens és a szerver között. Ez lehetővé teszi az azonnali válaszokat és a smooth felhasználói élményt.

## Architektúra

### Komponensek

1. **WebSocketManager** - Kapcsolatok kezelése
2. **ChatWebSocketHandler** - Chat üzenetek feldolgozása
3. **WebSocket Endpoint** - FastAPI endpoint
4. **Redis Cache Integration** - Session kezelés

### Kapcsolat Diagram

```
Kliens <---> WebSocket Endpoint <---> WebSocketManager <---> ChatHandler <---> Coordinator Agent
                |                           |                    |
                v                           v                    v
            FastAPI                   Connection Pool      Redis Cache
```

## Implementáció Részletei

### 1. WebSocketManager

A `WebSocketManager` osztály kezeli az aktív WebSocket kapcsolatokat:

```python
class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocketConnection] = {}
        self.session_connections: Dict[str, Set[str]] = {}
        self.user_connections: Dict[str, Set[str]] = {}
        self._lock = asyncio.Lock()
```

**Főbb funkciók:**
- Kapcsolatok létrehozása és eltávolítása
- Üzenetek küldése egyedi kapcsolatoknak
- Session és user alapú üzenet routing
- Kapcsolat statisztikák

### 2. ChatWebSocketHandler

A `ChatWebSocketHandler` osztály feldolgozza a chat üzeneteket:

```python
class ChatWebSocketHandler:
    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
        self.redis_cache_service = None
```

**Főbb funkciók:**
- Chat üzenetek validálása és feldolgozása
- Session kezelés Redis cache-ben
- Koordinátor agent integráció
- Hibakezelés és válaszok formázása

### 3. WebSocket Endpoint

A `/ws/chat/{session_id}` endpoint kezeli a WebSocket kapcsolatokat:

```python
@app.websocket("/ws/chat/{session_id}")
async def websocket_chat_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    connection_id = await websocket_manager.connect(websocket, session_id, user_id)
    # Üzenetek feldolgozása...
```

## Üzenet Formátumok

### Kliens -> Szerver

#### Chat Üzenet
```json
{
  "type": "chat_message",
  "content": "Szia! Szeretnék információt kapni a termékekről.",
  "session_id": "session_123",
  "user_id": "user_456",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Ping Üzenet
```json
{
  "type": "ping",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Session Info Kérés
```json
{
  "type": "session_info",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Szerver -> Kliens

#### Kapcsolat Létrehozás
```json
{
  "type": "connection_established",
  "data": {
    "connection_id": "conn_789",
    "session_id": "session_123",
    "user_id": "user_456",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

#### Chat Válasz
```json
{
  "type": "chat_response",
  "data": {
    "message_id": "msg_101",
    "content": "Üdvözöljük! Miben segíthetek?",
    "agent_type": "coordinator",
    "confidence": 0.95,
    "timestamp": "2024-01-15T10:30:05Z",
    "metadata": {
      "processing_time": 1.2,
      "agent_version": "1.0.0"
    }
  },
  "session_id": "session_123",
  "timestamp": "2024-01-15T10:30:05Z"
}
```

#### Pong Válasz
```json
{
  "type": "pong",
  "data": {
    "timestamp": "2024-01-15T10:30:00Z"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Hiba Válasz
```json
{
  "type": "error",
  "data": {
    "error_type": "empty_message",
    "error_message": "Üzenet tartalma nem lehet üres",
    "timestamp": "2024-01-15T10:30:00Z"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Session Kezelés

### Redis Cache Integráció

A session adatok Redis-ben tárolódnak:

```python
async def _get_or_create_session(self, session_id: str, user_id: Optional[str], websocket: WebSocket) -> ChatSession:
    session = await self._get_session_from_cache(session_id)
    
    if not session:
        session = ChatSession(
            session_id=session_id,
            user_id=user_id,
            context={
                "client_info": {
                    "ip_address": websocket.client.host,
                    "user_agent": websocket.headers.get("user-agent")
                }
            }
        )
    
    return session
```

### Session Adatok

- **Session ID**: Egyedi azonosító
- **User ID**: Felhasználó azonosító (opcionális)
- **Context**: Kliens információk és kontextus
- **Messages**: Chat üzenetek listája
- **Activity**: Kapcsolódás és utolsó aktivitás időpontja

## Hibakezelés

### WebSocket Hibák

1. **Kapcsolódási hiba**: WebSocket nem hozható létre
2. **Üzenet feldolgozási hiba**: Üzenet nem dolgozható fel
3. **Session hiba**: Session nem található vagy érvénytelen
4. **Validációs hiba**: Üzenet nem felel meg a formátumnak

### Hiba Válaszok

Minden hiba esetén a szerver strukturált hiba választ küld:

```python
def _create_error_response(self, error_type: str, error_message: str) -> Dict[str, Any]:
    return {
        "type": "error",
        "data": {
            "error_type": error_type,
            "error_message": error_message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
```

## Teljesítmény és Skálázhatóság

### Kapcsolat Kezelés

- **Aszinkron működés**: Minden művelet aszinkron
- **Connection pooling**: Hatékony kapcsolat kezelés
- **Memory management**: Automatikus kapcsolat tisztítás

### Redis Cache Stratégia

- **Session TTL**: 24 óra
- **Message caching**: Chat üzenetek cache-elése
- **Connection tracking**: Aktív kapcsolatok követése

### Monitoring

A `/api/v1/websocket/stats` endpoint statisztikákat ad:

```json
{
  "websocket_stats": {
    "total_connections": 5,
    "total_sessions": 3,
    "total_users": 2,
    "sessions": {
      "session_123": 2,
      "session_456": 1
    },
    "users": {
      "user_789": 3,
      "user_101": 2
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Biztonság

### Kapcsolat Validáció

- **Session ID**: Kötelező és validálni kell
- **User ID**: Opcionális, de validálni kell ha megvan
- **Rate limiting**: Üzenet küldési korlátozás
- **Input sanitization**: Üzenetek tisztítása

### Audit Logging

Minden WebSocket művelet naplózásra kerül:

- Kapcsolat létrehozása/lezárása
- Üzenet küldése/fogadása
- Hibák és kivételek

## Tesztelés

### Unit Tesztek

A `tests/test_websocket.py` fájl tartalmazza a WebSocket funkcionalitás tesztjeit:

- Kapcsolat létrehozása
- Üzenet küldése és fogadása
- Hibakezelés
- Session kezelés

### Integrációs Tesztek

- WebSocket endpoint tesztelése
- Redis cache integráció
- Koordinátor agent integráció

### Kliens Tesztelés

Az `examples/websocket_client_example.html` fájl egy teljes JavaScript kliens példa:

- Kapcsolat kezelés
- Üzenet küldés/fogadás
- Hibakezelés
- UI feedback

## Használat

### Kliens Oldal

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat/session_123?user_id=user_456');

ws.onopen = () => {
    console.log('Kapcsolat létrehozva');
};

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log('Üzenet fogadva:', message);
};

// Chat üzenet küldése
ws.send(JSON.stringify({
    type: 'chat_message',
    content: 'Szia!',
    session_id: 'session_123',
    timestamp: new Date().toISOString()
}));
```

### Szerver Oldal

A WebSocket endpoint automatikusan elérhető a FastAPI alkalmazásban:

```bash
# Szerver indítása
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# WebSocket endpoint elérhető:
# ws://localhost:8000/ws/chat/{session_id}
```

## Következő Lépések

### Jövőbeli Fejlesztések

1. **Authentication**: JWT token alapú hitelesítés
2. **Authorization**: Role-based access control
3. **Message persistence**: Üzenetek adatbázisban tárolása
4. **File upload**: Kép és dokumentum küldés
5. **Typing indicators**: Gépelés jelzése
6. **Read receipts**: Olvasási visszajelzés
7. **Message reactions**: Üzenet reakciók
8. **Group chat**: Csoportos chat támogatás

### Optimalizációk

1. **Message compression**: Üzenetek tömörítése
2. **Connection pooling**: Kapcsolat pool optimalizálás
3. **Load balancing**: Terheléselosztás
4. **CDN integration**: Content delivery network
5. **Caching strategies**: Cache stratégiák finomhangolása

## Dokumentáció

- **API Docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Spec**: `http://localhost:8000/openapi.json`

## Kapcsolódó Fájlok

- `src/integrations/websocket_manager.py` - WebSocket manager implementáció
- `src/main.py` - WebSocket endpoint
- `tests/test_websocket.py` - WebSocket tesztek
- `examples/websocket_client_example.html` - Kliens példa
- `docs/api.md` - API dokumentáció 