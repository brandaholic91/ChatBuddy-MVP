# LangGraph SDK Authentication Implementation

## Áttekintés

A `src/config/langgraph_auth.py` fájl implementálja a LangGraph SDK authentikáció kezelését a Chatbuddy MVP projektben. Ez a modul lehetővé teszi a LangGraph Cloud szolgáltatáshoz való biztonságos kapcsolódást.

## Funkciók

### LangGraphAuthManager osztály

A fő authentikációs kezelő osztály, amely:

- **Konfiguráció betöltése**: Környezeti változók alapján
- **Authentikáció**: LangGraph SDK kliens inicializálása
- **Kapcsolat tesztelése**: API kapcsolat validálása
- **Kliens kezelés**: Authentikált kliens visszaadása
- **Kapcsolat lezárás**: Biztonságos cleanup

### Globális függvények

- `get_langgraph_client()`: LangGraph kliens lekérése
- `initialize_langgraph_auth()`: Authentikáció inicializálása
- `shutdown_langgraph_auth()`: Authentikáció leállítása

## Környezeti változók

```bash
# LangGraph SDK (optional - LangGraph Cloud szolgáltatáshoz)
LANGGRAPH_API_KEY=your-langgraph-api-key-here-minimum-20-characters
LANGGRAPH_PROJECT_ID=your-langgraph-project-id-here
LANGGRAPH_ENVIRONMENT=development
LANGGRAPH_TIMEOUT=30
```

## Használat

### Alapvető használat

```python
from src.config.langgraph_auth import get_langgraph_client

# LangGraph kliens lekérése
client = await get_langgraph_client()

if client:
    # LangGraph SDK műveletek
    result = await client.some_operation()
else:
    # LangGraph nem elérhető
    print("LangGraph SDK nem elérhető")
```

### Inicializálás és leállítás

```python
from src.config.langgraph_auth import initialize_langgraph_auth, shutdown_langgraph_auth

# Alkalmazás indításakor
await initialize_langgraph_auth()

# Alkalmazás leállításakor
await shutdown_langgraph_auth()
```

## Integráció a main.py-ban

A `main.py` fájlban automatikusan megtörténik:

1. **Indítás**: `initialize_langgraph_auth()` hívása
2. **Leállítás**: `shutdown_langgraph_auth()` hívása
3. **Hiba kezelés**: Graceful degradation ha nem sikerül

## Biztonsági szempontok

### Környezeti változók védelme

- API kulcsok csak `.env` fájlban tárolva
- Production környezetben environment variables használata
- `.env.example` nem tartalmaz valós kulcsokat

### Hibakezelés

- Graceful degradation ha LangGraph nem elérhető
- Részletes logging minden művelethez
- Exception handling minden kritikus ponton

### Kapcsolat kezelés

- Timeout beállítások
- Kapcsolat tesztelése inicializáláskor
- Biztonságos cleanup leállításkor

## Tesztelés

A `tests/test_langgraph_auth.py` fájl tartalmazza a teljes tesztlefedettséget:

- **Unit tesztek**: Minden metódus tesztelése
- **Integrációs tesztek**: Teljes folyamat tesztelése
- **Mock tesztek**: Külső függőségek mock-olása
- **Hiba esetek**: Sikertelen authentikáció tesztelése

### Teszt futtatása

```bash
# Összes LangGraph auth teszt
pytest tests/test_langgraph_auth.py -v

# Specifikus teszt osztály
pytest tests/test_langgraph_auth.py::TestLangGraphAuthManager -v

# Async tesztek
pytest tests/test_langgraph_auth.py -v --asyncio-mode=auto
```

## Fejlesztési állapot

### ✅ Implementált funkciók

- [x] LangGraphAuthManager osztály
- [x] Környezeti változók kezelése
- [x] Authentikáció inicializálása
- [x] Kliens lekérése
- [x] Kapcsolat lezárása
- [x] Hibakezelés
- [x] Logging
- [x] Tesztelés
- [x] Main.py integráció

### 🔄 Jövőbeli fejlesztések

- [ ] Kapcsolat pooling
- [ ] Retry mechanizmus
- [ ] Health check endpoint
- [ ] Metrikák gyűjtése
- [ ] Rate limiting integráció

## Hibaelhárítás

### Gyakori problémák

1. **"LANGGRAPH_API_KEY nincs beállítva"**
   - Megoldás: Állítsd be a `LANGGRAPH_API_KEY` környezeti változót

2. **"LangGraph SDK authentikáció sikertelen"**
   - Ellenőrizd az API kulcs érvényességét
   - Ellenőrizd a hálózati kapcsolatot
   - Nézd meg a részletes logokat

3. **"LangGraph kliens nem elérhető"**
   - Az authentikáció nem sikerült
   - Használj fallback mechanizmust

### Debug mód

```python
import logging
logging.getLogger('src.config.langgraph_auth').setLevel(logging.DEBUG)
```

## Kapcsolódó dokumentáció

- [LangGraph SDK Documentation](https://docs.langchain.com/langgraph)
- [LangGraph Cloud](https://cloud.langchain.com)
- [Security Implementation](security_implementation.md)
- [API Documentation](api.md) 