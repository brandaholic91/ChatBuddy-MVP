# Chatbuddy MVP - Projekt Struktúra

## Áttekintés

Ez a dokumentum részletezi a Chatbuddy MVP projekt teljes mappahierarchináját és fájlszervezését.

## Teljes Projekt Struktúra

```
chatbuddy-mvp/
├── src/                                # Főforrás könyvtár
│   ├── __init__.py
│   ├── agents/                         # AI ügynökök implementációi
│   │   ├── __init__.py
│   │   ├── coordinator/                # Fő koordinátor ügynök
│   │   │   └── __init__.py
│   │   ├── product_info/               # Termékinformációs ügynök
│   │   │   └── __init__.py
│   │   ├── order_status/               # Rendelési státusz ügynök
│   │   │   └── __init__.py
│   │   └── recommendations/            # Ajánlási ügynök
│   │       └── __init__.py
│   ├── integrations/                   # Külső rendszer integrációk
│   │   ├── __init__.py
│   │   ├── webshop/                   # Webshop API integrációk
│   │   │   └── __init__.py
│   │   └── database/                  # Supabase kapcsolatok
│   │       └── __init__.py
│   ├── models/                        # Pydantic adatmodellek
│   │   └── __init__.py
│   ├── workflows/                     # LangGraph workflow definíciók
│   │   └── __init__.py
│   ├── utils/                         # Segédeszközök és közös funkciók
│   │   └── __init__.py
│   └── config/                        # Konfigurációs fájlok
│       └── __init__.py
├── tests/                             # Tesztek minden komponenshez
├── docs/                              # Fejlesztői dokumentáció
│   └── project_structure.md           # Ez a fájl
├── requirements.txt                   # Python függőségek
├── .env_example                       # Környezeti változók sablon
├── .gitignore                         # Git ignore fájl
├── Dockerfile                         # Docker image konfiguráció
├── docker-compose.yml                 # Docker Compose konfiguráció
├── README.md                          # Projekt dokumentáció
├── chatbuddy_mvp_feljesztési terv_langgraph+pydentic_ai.md
├── chatbuddy-context-engineering-guide.md
├── CONTEXT ENGINEERING PROMPTS.txt
└── termékesítési és üzleti terv-chatbuddy-1.0.pdf
```

## Könyvtár Funkcionalitás

### `/src` - Forráskód

**Fő alkalmazás könyvtár, ahol az összes Python kód található.**

#### `/src/agents` - AI Ügynökök
- **coordinator/**: Központi koordinátor ügynök, amely elemzi a kéréseket és dönt a megfelelő specializált ügynök kiválasztásáról
- **product_info/**: Termékekkel kapcsolatos kérdések kezelése (leírás, ár, elérhetőség)
- **order_status/**: Rendelési információk és státusz lekérdezések
- **recommendations/**: Személyre szabott termékajánlások generálása
- **marketing/**: Marketing automation, kosárelhagyás follow-up és kampánykezelés

#### `/src/integrations` - Külső Integrációk
- **webshop/**: Webshop API-k integrációja (Shoprenter, UNAS, stb.)
- **database/**: Supabase adatbázis kapcsolatok és műveletek
- **vector/**: pgvector embeddings és semantic search
- **marketing/**: Email/SMS szolgáltatások (SendGrid, Twilio)
- **social_media/**: Facebook Messenger és WhatsApp Business API integrációk

#### `/src/models` - Adatmodellek
Pydantic modellek az alkalmazás adatstruktúráinak definiálásához:
- Chat üzenetek
- Felhasználói profilok
- Termék információk
- Rendelési adatok

#### `/src/workflows` - LangGraph Prebuilt Agents
**OPTIMALIZÁLT:** LangGraph `create_react_agent` prebuilt komponensek manuális StateGraph helyett.  
- Koordinátor agent routing logikával
- Specializált agent implementations
- Tool definitions és integrations

#### `/src/utils` - Segédeszközök
Közös funkciók és utility osztályok:
- Logging
- Validáció
- Közös konstansok
- Helper függvények

#### `/src/config` - Konfigurációk
Alkalmazás konfigurációs fájlok:
- Environment beállítások
- AI provider konfigurációk
- Adatbázis beállítások

### `/tests` - Tesztek

Unit tesztek, integrációs tesztek és end-to-end tesztek helye.

### `/docs` - Dokumentáció

Fejlesztői dokumentáció, API specifikációk és technikai leírások.

## Konfigurációs Fájlok

### `requirements.txt`
Python package függőségek listája verzióinformációkkal.

### `.env_example`
Környezeti változók sablon fájl. Production környezetben `.env` néven kell másolni és kitölteni.

### `Dockerfile`
Docker image építési utasítások Python 3.11 alapon.

### `docker-compose.yml`
Lokális fejlesztési környezet konfigurációja Redis és Supabase integrációval.

### `.gitignore`
Git verziókezelésből kizárandó fájlok és könyvtárak.

## Moduláris Architektúra

A projekt moduláris felépítését a következő elvek vezérlik:

1. **Separation of Concerns**: Minden modul egy specifikus felelősségi körért felelős
2. **Loose Coupling**: Minimális függőségek a modulok között  
3. **High Cohesion**: Kapcsolódó funkciók egy modulban vannak
4. **Testability**: Minden modul külön tesztelhető
5. **Scalability**: Könnyű új ügynökök vagy integrációk hozzáadása

## Fejlesztési Munkafolyamat

1. **Feature fejlesztés**: Új funkciók a megfelelő `src/` alkönyvtárba kerülnek
2. **Tesztelés**: Minden új kód tesztelése a `tests/` könyvtárban
3. **Dokumentálás**: Új funkcionalitás dokumentálása a `docs/` könyvtárban
4. **Integration**: Docker és CI/CD pipeline használata

## Import Konvenciók

Relatív importálás használata a projekt moduljai között:

```python
# Helyes relatív import
from ..models.chat import ChatMessage
from .coordinator.main import CoordinatorAgent

# Kerülendő abszolút import
from src.models.chat import ChatMessage
```

## Következő Lépések

1. **Pydantic modellek implementálása** (`src/models/`)
2. **Koordinátor ügynök fejlesztése** (`src/agents/coordinator/`)
3. **Supabase integráció** (`src/integrations/database/`)
4. **Unit tesztek írása** (`tests/`)

Ez a projekt struktúra biztosítja a tiszta, karbantartható és skálázható kódbázist a Chatbuddy MVP fejlesztéséhez.