## Javítási Terv a WebSocket Teszt Hibához

### **Probléma Diagnózis:**

A `AssertionError: assert 'error' == 'chat_response'` hiba azt jelzi, hogy a teszt `'chat_response'` típust várt, de `'error'` típust kapott. Ez azt jelenti, hogy a WebSocket üzenet feldolgozás során hiba történt.

### **Hiba Oka:**

A teszt a következő üzenetet küldi:
```python
chat_message = {
    "type": "chat_message",
    "content": "Teszt üzenet",
    "session_id": session_id,
    "timestamp": datetime.now(timezone.utc).isoformat()
}
```

De a `_handle_chat_message` metódusban valószínűleg hiba történik, és `'error'` típusú választ ad vissza.

### **Javítási Terv:**

#### 1. **JSON Serialization Probléma**
A hivatalos dokumentáció szerint a WebSocket JSON kommunikáció során a következő problémák lehetnek:

**Probléma:** A `agent_response.agent_type.value` vagy `agent_response.confidence` értékek nem JSON-serializable-ok.

**Javítás:**
```python
# A válasz létrehozásánál biztosítani kell, hogy minden érték JSON-serializable legyen
"agent_type": str(agent_response.agent_type.value),
"confidence": float(agent_response.confidence) if agent_response.confidence else 0.0,
```

#### 2. **Exception Handling**
A hivatalos dokumentáció szerint a WebSocket hibakezelésnél a következőket kell figyelembe venni:

**Probléma:** A `process_coordinator_message` hívás során kivétel történhet.

**Javítás:**
```python
try:
    agent_response = await process_coordinator_message(
        message=content,
        user=user,
        session_id=session_id
    )
except Exception as e:
    logger.error(f"Hiba a coordinator agent hívásakor: {e}")
    return self._create_error_response("agent_error", "Agent feldolgozási hiba")
```

#### 3. **Session Cache Probléma**
A Redis cache deserializáció során ugyanaz a probléma lehet, mint a korábbi coordinator cache hibánál.

**Probléma:** A cache-ből visszaolvasott adat nem megfelelő formátumban van.

**Javítás:**
```python
async def _get_session_from_cache(self, session_id: str) -> Optional[ChatSession]:
    if not self.redis_cache_service:
        return None
    
    try:
        session_data = await self.redis_cache_service.session_cache.get_session(session_id)
        if session_data and isinstance(session_data, dict):  # Ellenőrizzük a típust
            # Biztonságos deserializáció
            return ChatSession(
                session_id=session_data.get("session_id"),
                user_id=session_data.get("user_id"),
                # ... többi mező
            )
    except Exception as e:
        logger.error(f"Hiba a session cache olvasásakor: {e}")
        return None
```

#### 4. **WebSocket Exception Handling**
A hivatalos dokumentáció szerint a WebSocket hibakezelésnél a `WebSocketException`-t kell használni:

**Javítás:**
```python
from fastapi import WebSocketException

# A WebSocket endpoint-ban
try:
    response = await chat_handler.handle_message(websocket, connection_id, message_data)
    await websocket.send_json(response)
except Exception as e:
    logger.error(f"Hiba a WebSocket kommunikációban: {e}")
    raise WebSocketException(code=1011, reason="Internal error")
```

#### 5. **Teszt Mock Adatok**
A tesztben a mock adatok nem megfelelőek lehetnek.

**Javítás:**
```python
# A tesztben biztosítani kell, hogy a mock agent_response megfelelő formátumban legyen
mock_response = type('MockResponse', (), {
    'response_text': 'Mock válasz',
    'agent_type': type('MockAgentType', (), {'value': 'general'})(),
    'confidence': 0.8,
    'processing_time': 0.1,
    'metadata': {}
})()
```

### **Összefoglaló:**

A WebSocket teszt hiba valószínűleg a következő okokból adódik:
1. **JSON serialization hiba** - nem serializable értékek
2. **Exception handling** - a coordinator agent hívás során kivétel
3. **Session cache probléma** - Redis deserializáció hiba
4. **Mock adatok** - nem megfelelő teszt adatok

A javítások a hivatalos dokumentáció alapján a következők:
- Biztonságos JSON serialization
- Megfelelő exception handling
- WebSocketException használata
- Mock adatok javítása

```python
chat_message = {
    "type": "chat_message",
    "content": "Teszt üzenet",
    "session_id": session_id,
    "timestamp": datetime.now(timezone.utc).isoformat()
}
```

```python
# A válasz létrehozásánál biztosítani kell, hogy minden érték JSON-serializable legyen
"agent_type": str(agent_response.agent_type.value),
"confidence": float(agent_response.confidence) if agent_response.confidence else 0.0,
```

```python
try:
    agent_response = await process_coordinator_message(
        message=content,
        user=user,
        session_id=session_id
    )
except Exception as e:
    logger.error(f"Hiba a coordinator agent hívásakor: {e}")
    return self._create_error_response("agent_error", "Agent feldolgozási hiba")
```

```python
async def _get_session_from_cache(self, session_id: str) -> Optional[ChatSession]:
    if not self.redis_cache_service:
        return None
    
    try:
        session_data = await self.redis_cache_service.session_cache.get_session(session_id)
        if session_data and isinstance(session_data, dict):  # Ellenőrizzük a típust
            # Biztonságos deserializáció
            return ChatSession(
                session_id=session_data.get("session_id"),
                user_id=session_data.get("user_id"),
                # ... többi mező
            )
    except Exception as e:
        logger.error(f"Hiba a session cache olvasásakor: {e}")
        return None
```

```python
from fastapi import WebSocketException

# A WebSocket endpoint-ban
try:
    response = await chat_handler.handle_message(websocket, connection_id, message_data)
    await websocket.send_json(response)
except Exception as e:
    logger.error(f"Hiba a WebSocket kommunikációban: {e}")
    raise WebSocketException(code=1011, reason="Internal error")
```

```python
# A tesztben biztosítani kell, hogy a mock agent_response megfelelő formátumban legyen
mock_response = type('MockResponse', (), {
    'response_text': 'Mock válasz',
    'agent_type': type('MockAgentType', (), {'value': 'general'})(),
    'confidence': 0.8,
    'processing_time': 0.1,
    'metadata': {}
})()
```

