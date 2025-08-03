# Chatbuddy MVP: Részletes Fejlesztési Terv és Implementációs Útmutató

## Előszó a Fejlesztéshez

Ez a dokumentum egy teljes körű útmutatót nyújt a Chatbuddy MVP (omnichannel ügyfélszolgálati chatbot) fejlesztéséhez, kifejezetten AI-asszisztált kódgenerálásra optimalizálva. Minden szakasz tartalmazza a szükséges technikai specifikációkat, konkrét prompt sablonokat, valamint részletes tesztelési útmutatókat.

A fejlesztési folyamat úgy lett megtervezve, hogy minden egyes lépés után egy működő, tesztelhető komponens álljon rendelkezésre. Ez lehetővé teszi a fokozatos építkezést és a korai problémák azonosítását, miközben minimalizálja a komplex hibakeresési szituációk kialakulásának kockázatát.

## 1. Fejlesztési Környezet Előkészítése

### 1.1 Projekt Struktúra Kialakítása

Az első lépés egy jól szervezett projekt struktúra létrehozása, amely támogatja a moduláris fejlesztést és a későbbi skálázhatóságot. A projekt gyökérkönyvtárában hozd létre a következő könyvtárstruktúrát, amely tükrözi a rendszer komponenseit és lehetővé teszi a tiszta szeparációt a különböző funkcionális területek között.

```
chatbuddy-mvp/
├── src/
│   ├── agents/                 # AI ügynökök implementációi
│   │   ├── coordinator/        # Fő koordinátor ügynök
│   │   ├── product_info/       # Termékinformációs ügynök
│   │   ├── order_status/       # Rendelési státusz ügynök
│   │   └── recommendations/    # Ajánlási ügynök
│   ├── integrations/           # Külső rendszer integrációk
│   │   ├── webshop/           # Webshop API integrációk
│   │   └── database/          # Adatbázis kapcsolatok
│   ├── models/                # Adatmodellek (Pydantic)
│   ├── workflows/             # LangGraph workflow definíciók
│   ├── utils/                 # Segédeszközök és közös funkciók
│   └── config/                # Konfigurációs fájlok
├── tests/                     # Tesztek minden komponenshez
├── docs/                      # Fejlesztői dokumentáció
├── requirements.txt           # Python függőségek
└── docker-compose.yml         # Helyi fejlesztési környezet
```

### 1.2 Alapvető Függőségek Meghatározása

A projekt technológiai alapját a következő kulcsfontosságú könyvtárak képezik, amelyek mindegyike specifikus funkcionalitást lát el a rendszerben. A LangGraph biztosítja az állapotalapú workflow kezelést, a Pydantic AI pedig az intelligens ügynök funkcionalitást.

**AI és Workflow Management:**
- langgraph>=0.2.74 (állapotalapú workflow orchestration)
- pydantic-ai>=0.0.49 (AI agent framework type-safe dependency injection-nel)
- langchain>=0.3.0 (kiegészítő LLM utilities)
- openai>=1.51.0 (OpenAI API kliens)

**Web Framework és API:**
- fastapi>=0.104.0 (modern, gyors web framework API fejlesztéshez)
- uvicorn>=0.24.0 (ASGI szerver production-ready alkalmazásokhoz)
- websockets>=12.0 (valós idejű chat kommunikációhoz)
- httpx>=0.25.0 (aszinkron HTTP kliens külső API hívásokhoz)

**Adatbázis és Cache:**
- supabase>=2.3.0 (Supabase Python kliens)
- asyncpg>=0.29.0 (aszinkron PostgreSQL driver)
- redis>=5.0.0 (cache és session management)
- sqlalchemy>=2.0.0 (ORM és adatbázis absztrakció)

**Biztonság és Megfelelőség:**
- python-jose>=3.3.0 (JWT token kezelés)
- passlib>=1.7.4 (jelszó hashelés és verifikáció)
- python-multipart>=0.0.6 (file upload támogatás)

### 1.3 Környezeti Változók és Konfiguráció

A fejlesztés megkezdése előtt fontos beállítani a környezeti változókat, amelyek a különböző szolgáltatásokhoz való hozzáférést biztosítják. Készíts egy `.env` fájlt a projekt gyökérkönyvtárában, amely tartalmazza az összes szükséges konfigurációs paramétert.

```bash
# AI Provider Settings
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o
ANTHROPIC_API_KEY=your_anthropic_key_here

# Database Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
DATABASE_URL=postgresql://user:password@db.supabase.co:5432/postgres
REDIS_URL=redis://localhost:6379

# Application Settings
DEBUG=true
LOG_LEVEL=INFO
SECRET_KEY=your_secret_key_here
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:8080"]

# Webshop Integration (később)
SHOPRENTER_API_KEY=placeholder
UNAS_API_KEY=placeholder
```

## 2. Alapvető Komponensek Implementálása

### 2.1 Adatmodellek Definiálása (Pydantic)

Az első implementációs lépés az adatmodellek létrehozása, amelyek definiálják a rendszerben használt adatstruktúrákat. Ezek a modellek nemcsak a típusbiztonságot szolgálják, hanem validációt és dokumentációt is biztosítanak.

**AI Prompt Sablon a Modellek Generálásához:**

```
Generálj Pydantic modelleket egy ügyfélszolgálati chatbot számára. A modellek legyenek típusbiztosak, tartalmazzanak validációt és dokumentációt. Szükséges modellek:

1. ChatMessage - chat üzenet reprezentáció
2. UserSession - felhasználói session adatok
3. Product - termék információk
4. Order - rendelési adatok
5. CartItem - kosár elemek
6. CustomerProfile - ügyfél profil
7. ChatResponse - chatbot válasz struktúra

Minden modell tartalmazza a megfelelő Field validation-öket, datetime mezőket, és opcionális mezőket ahol szükséges. Használj magyar kommenteket a mezők magyarázatához.
```

**Példa implementáció a `src/models/chat.py` fájlhoz:**

```python
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class MessageType(str, Enum):
    """Üzenet típusok a chat rendszerben"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    ERROR = "error"

class ChatMessage(BaseModel):
    """Alapvető chat üzenet modell"""
    id: str = Field(..., description="Egyedi üzenet azonosító")
    session_id: str = Field(..., description="Session azonosító")
    type: MessageType = Field(..., description="Üzenet típusa")
    content: str = Field(..., min_length=1, description="Üzenet tartalma")
    timestamp: datetime = Field(default_factory=datetime.now, description="Üzenet létrehozásának időpontja")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="További metadata")

class UserSession(BaseModel):
    """Felhasználói session információk"""
    session_id: str = Field(..., description="Egyedi session azonosító")
    customer_id: Optional[str] = Field(default=None, description="Ügyfél azonosító ha beazonosított")
    started_at: datetime = Field(default_factory=datetime.now, description="Session kezdési időpont")
    last_activity: datetime = Field(default_factory=datetime.now, description="Utolsó aktivitás időpontja")
    context: Dict[str, Any] = Field(default_factory=dict, description="Session kontextus adatok")
    is_active: bool = Field(default=True, description="Session aktív státusza")
```

### 2.2 Koordinátor Ügynök Implementálása

A koordinátor ügynök a rendszer központi intelligenciája, amely elemzi a bejövő kéréseket és dönt arról, hogy melyik specializált ügynököt kell bevonni a válasz generálásához. Ez az ügynök implementálja a legmagasabb szintű üzleti logikát és biztosítja a konzisztens felhasználói élményt.

**AI Prompt Sablon a Koordinátor Ügynök Generálásához:**

```
Hozz létre egy Pydantic AI koordinátor ügynököt egy magyar ügyfélszolgálati chatbot számára. Az ügynök követelményei:

1. Elemezze a bejövő üzeneteket és kategorizálja őket
2. Döntsön arról, hogy melyik specializált ügynököt hívja meg:
   - product_info_agent: termékkérdések
   - order_status_agent: rendelési információk
   - recommendation_agent: termékajánlások
3. Magyar nyelvű, barátságos de professzionális kommunikáció
4. Dependency injection a session és database hozzáféréshez
5. Hiba kezelés és fallback mechanizmusok

Használj LangGraph Command objektumokat a flow vezérléshez.
```

**Példa implementáció a `src/agents/coordinator/main.py` fájlhoz:**

```python
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel
from dataclasses import dataclass
from typing import Literal, Any
import logging

logger = logging.getLogger(__name__)

@dataclass
class CoordinatorDependencies:
    """Koordinátor ügynök függőségei"""
    session_data: dict
    supabase_client: Any  # Supabase client connection
    database: Any  # SQLAlchemy database session
    user_context: dict

class AgentDecision(BaseModel):
    """Ügynök döntési modell"""
    target_agent: Literal["product_info", "order_status", "recommendation", "general"]
    confidence: float
    reasoning: str

# Koordinátor ügynök inicializálása
coordinator_agent = Agent(
    'openai:gpt-4o',
    deps_type=CoordinatorDependencies,
    output_type=AgentDecision,
    system_prompt="""
    Te egy tapasztalt magyar ügyfélszolgálati koordinátor vagy. A feladatod elemezni a bejövő kérdéseket és eldönteni, hogy melyik specializált kollégához kell irányítani őket.

    Specializált területek:
    - product_info: termékekkel kapcsolatos kérdések (leírás, ár, elérhetőség)
    - order_status: rendelési információk (státusz, szállítás, számlázás)
    - recommendation: termékajánlások és személyre szabott javaslatok
    - marketing: kosárelhagyás follow-up, kedvezmények, email/SMS kampányok
    - social_media: Facebook Messenger és WhatsApp kommunikáció kezelése
    - general: általános kérdések, köszönés, búcsúzás

    Mindig barátságos és segítőkész hangnemet használj.
    """
)

@coordinator_agent.tool
async def analyze_message_intent(
    ctx: RunContext[CoordinatorDependencies], 
    user_message: str
) -> str:
    """Elemzi a felhasználói üzenet szándékát"""
    # Itt implementálható további szándékfelismerő logika
    return f"Analyzed intent for: {user_message}"
```

### 2.3 Specializált Ügynökök Implementálása

A specializált ügynökök mindegyike egy-egy konkrét funkcionalitásért felelős, és mély szakértelemmel rendelkezik a saját területén. Ez a modularitás lehetővé teszi az egyes komponensek független fejlesztését és tesztelését.

**Termékinformációs Ügynök (Product Info Agent):**

Ez az ügynök felelős a termékekkel kapcsolatos kérdések megválaszolásáért. Hozzáfér a termékadatbázishoz, képes keresni a termékek között, és részletes információkat tud nyújtani árakról, elérhetőségről és specifikációkról.

**AI Prompt Sablon:**

```
Implementálj egy Pydantic AI ügynököt termék információk kezelésére. Az ügynök tudjon:

1. Termékeket keresni név, kategória, ár alapján
2. Részletes termékleírásokat adni
3. Készlet információkat ellenőrizni
4. Árak és akciók kommunikálása
5. Kapcsolódó termékek ajánlása

Dependency injection-nel kapja meg a Supabase és webshop API hozzáférést.
Magyar nyelvű válaszok, SEO-barát termékleírások.
```

**Helyes Pydantic AI implementáció példa:**

```python
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel
from typing import List, Optional

@dataclass
class ProductInfoDependencies:
    """Termékinformációs ügynök függőségei"""
    supabase_client: Any
    webshop_api: Any
    user_context: dict

class ProductInfo(BaseModel):
    """Termék információ válasz modell"""
    name: str
    price: float
    description: str
    availability: str
    category: str

product_info_agent = Agent(
    'openai:gpt-4o',
    deps_type=ProductInfoDependencies,
    output_type=ProductInfo,
    system_prompt="""
    Te egy szakértő termék információs asszisztens vagy magyar webshopok számára.
    Segíts a vásárlóknak részletes, pontos termék információkkal.
    """
)

@product_info_agent.tool
async def search_products(
    ctx: RunContext[ProductInfoDependencies], 
    query: str,
    category: Optional[str] = None
) -> List[dict]:
    """Termék keresés a webshop API-n keresztül"""
    results = await ctx.deps.webshop_api.search_products(
        query=query, 
        category=category
    )
    return results

@product_info_agent.tool
async def get_product_details(
    ctx: RunContext[ProductInfoDependencies], 
    product_id: str
) -> dict:
    """Részletes termék információk lekérése"""
    product = await ctx.deps.webshop_api.get_product(product_id)
    return product

# Használat:
# deps = ProductInfoDependencies(supabase_client, webshop_api, user_context)
# result = await product_info_agent.run("Keresek egy iPhone telefont", deps=deps)
```

**Rendelési Státusz Ügynök (Order Status Agent):**

Ez az ügynök a rendelésekkel kapcsolatos lekérdezéseket kezeli. Képes azonosítani az ügyfeleket, megkeresni a rendeléseiket, és pontos státusz információkat nyújtani.

```python
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

@dataclass
class OrderStatusDependencies:
    """Rendelési státusz ügynök függőségei"""
    supabase_client: Any
    webshop_api: Any
    user_context: dict

class OrderStatus(BaseModel):
    """Rendelési státusz válasz modell"""
    order_id: str
    status: str
    estimated_delivery: Optional[str]
    tracking_number: Optional[str]
    items: List[str]

order_status_agent = Agent(
    'openai:gpt-4o',
    deps_type=OrderStatusDependencies,
    output_type=OrderStatus,
    system_prompt="""
    Te egy rendelési státusz specialista vagy. Segíts az ügyfeleknek 
    nyomon követni rendeléseiket és pontos információkat adni a szállításról.
    """
)

@order_status_agent.tool
async def find_order(
    ctx: RunContext[OrderStatusDependencies], 
    order_id: Optional[str] = None,
    email: Optional[str] = None
) -> dict:
    """Rendelés keresése ID vagy email alapján"""
    if order_id:
        order = await ctx.deps.webshop_api.get_order(order_id)
    elif email and ctx.deps.user_context.get('user_id'):
        orders = await ctx.deps.webshop_api.get_user_orders(
            user_id=ctx.deps.user_context['user_id']
        )
        order = orders[0] if orders else None
    else:
        return {"error": "Rendelés azonosítás szükséges"}
    
    return order

@order_status_agent.tool
async def get_tracking_info(
    ctx: RunContext[OrderStatusDependencies], 
    tracking_number: str
) -> dict:
    """Küldemény nyomon követése"""
    tracking = await ctx.deps.webshop_api.track_shipment(tracking_number)
    return tracking
```

**Ajánlási Ügynök (Recommendation Agent):**

Az ajánlási ügynök személyre szabott termékajánlásokat generál a vásárlási előzmények, böngészési szokások és preferenciák alapján.

```python
@dataclass
class RecommendationDependencies:
    """Ajánlási ügynök függőségei"""
    supabase_client: Any
    webshop_api: Any
    user_context: dict
    recommendation_engine: Any

class ProductRecommendation(BaseModel):
    """Termékajánlás válasz modell"""
    recommended_products: List[dict]
    reasoning: str
    personalization_score: float

recommendation_agent = Agent(
    'openai:gpt-4o',
    deps_type=RecommendationDependencies,
    output_type=ProductRecommendation,
    system_prompt="""
    Te egy személyre szabott ajánlási specialista vagy. 
    Elemezd a vásárló preferenciáit és adj releváns termékajánlásokat.
    """
)

@recommendation_agent.tool
async def get_user_preferences(
    ctx: RunContext[RecommendationDependencies]
) -> dict:
    """Felhasználói preferenciák lekérése"""
    user_id = ctx.deps.user_context.get('user_id')
    if user_id:
        preferences = await ctx.deps.supabase_client.table('user_preferences').select('*').eq('user_id', user_id).execute()
        return preferences.data[0] if preferences.data else {}
    return {}

@recommendation_agent.tool
async def generate_recommendations(
    ctx: RunContext[RecommendationDependencies],
    user_query: str,
    category: Optional[str] = None
) -> List[dict]:
    """Személyre szabott ajánlások generálása"""
    user_prefs = await get_user_preferences(ctx)
    recommendations = await ctx.deps.recommendation_engine.get_recommendations(
        user_context=ctx.deps.user_context,
        preferences=user_prefs,
        query=user_query,
        category=category
    )
    return recommendations
```

### 2.4 LangGraph Workflow Integráció

**⚡ OPTIMALIZÁLT: Prebuilt Komponensek Használata**

A dokumentáció alapján a **LangGraph prebuilt komponensek** használata **90% kevesebb kódot** eredményez és **beépített error handling**-et biztosít. **Manuális StateGraph helyett `create_react_agent`-et használunk.**

**AI Prompt Sablon a Prebuilt Workflow Implementálásához:**

```
Implementálj LangGraph prebuilt komponenseket használó chatbot workflow-t:

1. create_react_agent minden specializált ügynökhöz
2. Központi koordinátor agent prebuilt tools-okkal  
3. Tool-based kommunikáció ügynökök között
4. Automatikus error handling és retry logika
5. Beépített message history management

Használj create_react_agent, ToolNode, és tools_condition prebuilt komponenseket.
```

**Helyes LangGraph Prebuilt Implementáció:**

```python
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from typing import List, Dict

# LLM modell inicializálása
llm = ChatOpenAI(model="gpt-4o", temperature=0.1)

# Koordinátor agent tools-ok definiálása
@tool
def route_to_product_info(query: str) -> str:
    """Termékinformációs ügynökhöz irányítás"""
    return f"Routing to product info agent: {query}"

@tool  
def route_to_order_status(query: str) -> str:
    """Rendelési státusz ügynökhöz irányítás"""
    return f"Routing to order status agent: {query}"

@tool
def route_to_recommendations(query: str) -> str:
    """Ajánlási ügynökhöz irányítás"""
    return f"Routing to recommendation agent: {query}"

# Koordinátor agent prebuilt komponenssel
coordinator_agent = create_react_agent(
    llm,
    tools=[route_to_product_info, route_to_order_status, route_to_recommendations],
    state_modifier="""
    Te egy magyar ügyfélszolgálati koordinátor vagy. 
    Elemezd a kérdést és irányítsd a megfelelő specialistához.
    """
)

# Specializált agent example - Product Info
@tool
async def search_products(query: str, category: str = None) -> List[Dict]:
    """Termék keresés a webshop API-n keresztül"""
    # Itt hívnánk a Pydantic AI agent-et
    return [{"name": "iPhone 15", "price": 299000, "category": "telefon"}]

product_info_agent = create_react_agent(
    llm,
    tools=[search_products],
    state_modifier="Te egy termék információs specialista vagy magyar webshopokhoz."
)

# Használat:
# messages = [{"role": "user", "content": "Keresek egy telefont"}]
# result = coordinator_agent.invoke({"messages": messages})
```

**🎯 Prebuilt vs Manual Összehasonlítás:**

| Megoldás | Kódsorok | Error Handling | Maintenance |
|----------|----------|----------------|-------------|
| **Manual StateGraph** | ~200 lines | Manuális | Nehéz |
| **Prebuilt `create_react_agent`** | ~50 lines | Automatikus | Egyszerű |

**✅ Prebuilt Előnyök:**
- **90% kevesebb boilerplate kód**
- **Beépített tool management**
- **Automatikus message routing**
- **Built-in error recovery**
- **Simplified testing**

### 2.5 Pydantic AI + LangGraph Prebuilt Integráció

**Kombinált Megoldás:** Pydantic AI agents + LangGraph prebuilt routing

```python
from dataclasses import dataclass
from langgraph.prebuilt import create_react_agent
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from typing import List, Dict, Any

# Pydantic AI Dependencies (helyes pattern)
@dataclass
class ChatbotDependencies:
    supabase_client: Any
    webshop_api: Any
    user_context: dict

# Pydantic AI Specialized Agents
class ProductInfo(BaseModel):
    name: str
    price: float
    description: str

product_agent = Agent(
    'openai:gpt-4o',
    deps_type=ChatbotDependencies,
    output_type=ProductInfo,
    system_prompt="Te egy termék információs specialista vagy."
)

@product_agent.tool
async def get_product_details(
    ctx: RunContext[ChatbotDependencies], 
    product_id: str
) -> dict:
    return await ctx.deps.webshop_api.get_product(product_id)

# LangGraph Tools for Routing (kapcsolódik Pydantic AI agents-hez)
@tool
async def handle_product_query(query: str) -> str:
    """Termékekkel kapcsolatos kérdések kezelése"""
    # Itt hívjuk a Pydantic AI agent-et
    deps = ChatbotDependencies(supabase_client, webshop_api, user_context)
    result = await product_agent.run(query, deps=deps)
    return f"Termék info: {result.output.name} - {result.output.price} Ft"

@tool
async def handle_order_query(query: str) -> str:
    """Rendelésekkel kapcsolatos kérdések kezelése"""
    # Hasonlóan más Pydantic AI agents-hez
    return f"Rendelési info feldolgozva: {query}"

# LangGraph Prebuilt Router Agent
llm = ChatOpenAI(model="gpt-4o")
main_chatbot = create_react_agent(
    llm,
    tools=[handle_product_query, handle_order_query],
    state_modifier="""
    Te a Chatbuddy ügyfélszolgálati asszisztens vagy.
    Használd a megfelelő tool-t a kérdés típusa alapján.
    """
)

# Komplett Használat:
async def process_user_message(user_message: str, user_context: dict):
    """Teljes chatbot workflow"""
    messages = [{"role": "user", "content": user_message}]
    result = main_chatbot.invoke({"messages": messages})
    return result["messages"][-1]["content"]

# Példa hívás:
# response = await process_user_message("Milyen telefonok vannak?", {"user_id": 123})
```

**🔄 Hibrid Architektúra Előnyei:**

| Komponens | Felelősség | Technológia |
|-----------|------------|-------------|
| **Routing & Orchestration** | Kérések irányítása | LangGraph `create_react_agent` |
| **Specialized Logic** | Domain-specifikus logika | Pydantic AI `Agent` |
| **Tool Integration** | API calls, DB queries | Pydantic AI `@tool` + dependency injection |
| **Error Handling** | Retry, fallback | LangGraph prebuilt + Pydantic AI validation |

**✨ Legjobb Megoldás:**
- ✅ LangGraph prebuilt - egyszerű routing és orchestration
- ✅ Pydantic AI - komplex domain logika és validáció  
- ✅ Type safety mindkét irányban
- ✅ Minimális boilerplate kód

## 3. Webshop Integráció Fejlesztése

### 3.1 API Adapter Réteg

Az API adapter réteg absztrahálja a különböző webshop rendszerek közötti különbségeket, és egységes interfészt biztosít a chatbot számára. Ez lehetővé teszi, hogy a rendszer könnyedén integrálható legyen különböző e-commerce platformokkal.

**Shoprenter API Integráció:**

A Shoprenter integráció lehetővé teszi a termékadatok, rendelési információk és ügyfél adatok valós idejű elérését. Az implementációnak kezelnie kell a rate limiting-et, a hibakezelést és a cache-elést is.

**AI Prompt Sablon:**

```
Implementálj egy Shoprenter API integration class-t Python-ban. A class tudjon:

1. Termékeket lekérdezni (GET /products)
2. Rendeléseket keresni (GET /orders)
3. Ügyfél adatokat elérni (GET /customers)
4. Rate limiting és retry mechanizmus
5. Aszinkron működés httpx-szel
6. Error handling és logging

Használj type hints-et és proper exception handling-et.
```

### 3.2 Cache Stratégia Implementálása

A cache stratégia kritikus fontosságú a teljesítmény és a felhasználói élmény szempontjából. A Redis-alapú cache réteg biztosítja a gyors adatelérést és csökkenti a külső API-k terhelését.

**Cache Konfiguráció:**
- Termékadatok: 1 óra TTL
- Rendelési státusz: 5 perc TTL
- Ügyfél profilok: 30 perc TTL
- Session adatok: 24 óra TTL

## 4. Chat Interface Fejlesztése

### 4.1 WebSocket Alapú Valós Idejű Kommunikáció

A chat interface WebSocket technológiára épül, amely lehetővé teszi a valós idejű, kétirányú kommunikációt a kliens és a szerver között. Ez biztosítja az azonnali válaszokat és a smooth felhasználói élményt.

**AI Prompt Sablon:**

```
Implementálj egy FastAPI WebSocket endpoint-ot chat kommunikációhoz:

1. WebSocket connection management
2. Session kezelés és authentication
3. Message routing a megfelelő agent-ekhez
4. Real-time response streaming
5. Error handling és reconnection logic
6. Message persistence Supabase-ben

Aszinkron működés, proper cleanup, logging.
```

### 4.2 Frontend Chat Widget

A frontend chat widget egy könnyű, beágyazható JavaScript komponens, amely bármely webshopba integrálható. A widget responsive designnal rendelkezik és támogatja a modern böngészőket.

**Funkcionális Követelmények:**
- Minimális CSS footprint
- Mobile-first responsive design
- Keyboard navigation támogatás
- Accessibility (WCAG 2.1 AA)
- Customizable theming

## 5. Tesztelési Stratégia

### 5.1 Unit Tesztek

Minden egyes ügynök és komponens számára készíteni kell unit teszteket, amelyek ellenőrzik az alapvető funkcionalitást és edge case-eket.

**AI Prompt Sablon Unit Tesztek Generálásához:**

```
Generálj pytest unit teszteket a következő komponensekhez:
- Coordinator Agent
- Product Info Agent  
- Order Status Agent
- Recommendation Agent
- WebSocket handlers
- API integrations

Tesztelj happy path-okat, error case-eket, és boundary condition-öket.
Mock-old a külső függőségeket (API-k, database).
```

### 5.2 Integrációs Tesztek

Az integrációs tesztek ellenőrzik a különböző komponensek együttműködését és a teljes workflow működését.

### 5.3 End-to-End Tesztek

Az E2E tesztek a teljes felhasználói utakat szimulálják, valós böngésző környezetben.

## 6. Deployment és Monitoring

### 6.1 Docker Containerization

A Docker containerek biztosítják a konzisztens deployment környezetet és egyszerűsítik a skálázást.

**Docker Compose konfiguráció:**

```yaml
version: '3.8'
services:
  chatbuddy-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
      - SUPABASE_SERVICE_KEY=${SUPABASE_SERVICE_KEY}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # Supabase szolgáltatásokat külsőleg használjuk
  # Lokális fejlesztéshez opcionálisan használható Supabase local dev
  # supabase:
  #   image: supabase/postgres:15.1.0.117
  #   ports:
  #     - "54322:5432"
  #   environment:
  #     - POSTGRES_PASSWORD=your-super-secret-and-long-postgres-password
```

### 6.2 Monitoring és Logging

A monitoring rendszer valós időben figyeli a teljesítményt és azonosítja a problémákat.

**Monitoring Metrikák:**
- Response time per agent
- Success rate per conversation type
- WebSocket connection metrics
- Supabase query performance
- PostgreSQL connection pool metrics
- Cache hit ratios

## 7. Biztonsági Megfelelőség

### 7.1 GDPR Compliance

A GDPR megfelelőség kritikus fontosságú a magyar piacon való működéshez.

**Implementálandó Funkciók:**
- Explicit consent management
- Data portability (export)
- Right to be forgotten (delete)
- Data minimization
- Audit logging

### 7.2 Authentication és Authorization

A biztonsági réteg JWT token alapú authentication-t és role-based authorization-t implementál.

## 8. Go-Live Checklist

### 8.1 Pre-Production Tesztek

A production környezetbe való átállás előtt végig kell futtatni egy komplett tesztelési ciklust.

**Checklist:**
- [ ] Minden unit teszt zöld
- [ ] Integrációs tesztek sikeresek
- [ ] Load testing elvégezve
- [ ] Security audit befejezve
- [ ] GDPR compliance ellenőrzése
- [ ] Backup és disaster recovery tesztelése

### 8.2 Monitoring Setup

A production monitoring rendszerének teljes konfigurálása és tesztelése.

### 8.3 Documentation

A teljes dokumentáció elkészítése az üzemeltetők és felhasználók számára.

Ez a részletes fejlesztési terv minden szükséges információt tartalmaz az MVP sikeres implementálásához. Minden szakasz konkrét, végrehajtható lépéseket és AI prompt sablonokat biztosít, amelyek segítségével lépésről lépésre felépítheted a működő rendszert.