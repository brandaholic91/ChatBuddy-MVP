# 🚀 Chatbuddy MVP Fejlesztési Terv - Lépésről Lépésre

## 📊 Jelenlegi Projekt Állapot

**✅ Már elkészült:**
- Projekt struktúra és alapvető konfiguráció
- FastAPI alkalmazás alapjai (main.py)
- Docker környezet (docker-compose.yml)
- Környezeti változók konfiguráció (.env_example)
- Logging és security middleware
- Health check endpoint-ok
- **Adatmodellek implementálása (src/models/) - ELKÉSZÜLT**
- **Koordinátor Agent implementálása (src/workflows/coordinator.py) - ELKÉSZÜLT**
- **FastAPI szerver sikeresen fut (http://localhost:8000) - ELKÉSZÜLT**
- **Chat endpoint működik (/api/v1/chat) - ELKÉSZÜLT**

**🔄 Következő lépések prioritás szerint:**

## 🎯 1. FÁZIS: Alapvető AI Agent Implementáció (1-2 hét)

### 1.1 Adatmodellek Implementálása ✅
**Prioritás: KRITIKUS** - **BEFEJEZVE**
- [x] Pydantic modellek létrehozása (`src/models/chat.py`, `src/models/product.py`, `src/models/user.py`, `src/models/order.py`, `src/models/agent.py`, `src/models/marketing.py`)
- [x] Pydantic validációk és dokumentáció
- [x] Unit tesztek implementálása és futtatása
- [x] Virtuális környezet problémák megoldása (Python 3.13 kompatibilitás)
- [x] Pydantic V2 migráció (json_encoders eltávolítása)

### 1.2 Koordinátor Agent Implementálása ✅
**Prioritás: KRITIKUS** - **BEFEJEZVE**
- [x] LangGraph prebuilt `create_react_agent` használata
- [x] Üzenet routing és kategorizálás
- [x] Tool definitions és dependency injection pattern
- [x] Unit tesztek koordinátor agent-hez
- [x] FastAPI integráció chat endpoint-tal

### 1.3 Specializált Agent-ek Alapjai
**Prioritás: MAGAS**
- Product Info Agent (termékkeresés)
- Order Status Agent (rendelési információk)
- Recommendation Agent (ajánlások)

### 1.4 WebSocket Chat Interface
**Prioritás: MAGAS**
- Valós idejű kommunikáció
- Session kezelés
- Message persistence

## 🎯 2. FÁZIS: Adatbázis és Integráció (1 hét)

### 2.1 Supabase Schema Design
**Prioritás: KRITIKUS**
- Táblák létrehozása (users, products, orders, chat_sessions)
- pgvector extension beállítása
- Row Level Security (RLS) policies

### 2.2 Vector Database Integráció
**Prioritás: MAGAS**
- OpenAI embeddings API integráció
- Semantic search implementáció
- Termék embedding batch processing

### 2.3 Redis Cache Implementáció
**Prioritás: KÖZEPES**
- Session storage
- Performance cache
- Rate limiting

## 🎯 3. FÁZIS: Webshop Integráció (1-2 hét)

### 3.1 API Adapter Réteg
**Prioritás: MAGAS**
- Shoprenter API integráció
- UNAS API integráció
- Egységes webshop interface

### 3.2 Termékadat Szinkronizáció
**Prioritás: MAGAS**
- Automatikus termék import
- Készlet frissítések
- Ár változások kezelése

## 🎯 4. FÁZIS: Marketing Automation (1-2 hét)

### 4.1 Kosárelhagyás Follow-up
**Prioritás: MAGAS**
- Celery background tasks
- Email/SMS automatikus küldés
- Kedvezmény kódok generálása

### 4.2 Email/SMS Integráció
**Prioritás: KÖZEPES**
- SendGrid email service
- Twilio SMS service
- Template engine

## 🎯 5. FÁZIS: Social Media Integráció (1 hét)

### 5.1 Facebook Messenger
**Prioritás: KÖZEPES**
- Messenger Platform API
- Carousel üzenetek
- Quick reply gombok

### 5.2 WhatsApp Business
**Prioritás: KÖZEPES**
- WhatsApp Business API
- Template üzenetek
- Interaktív válaszok

## 🎯 6. FÁZIS: Tesztelés és Deployment (1 hét)

### 6.1 Tesztelési Stratégia
**Prioritás: MAGAS**
- Unit tesztek minden agent-hez
- Integrációs tesztek
- End-to-end tesztek

### 6.2 Production Deployment
**Prioritás: MAGAS**
- Docker image optimalizálás
- Monitoring és logging
- SSL/TLS beállítás

## 📋 Részletes Implementációs Terv

### 1. HÉT: AI Agent Alapok

**Nap 1-2: Adatmodellek**
```python
# src/models/chat.py
class ChatMessage(BaseModel):
    id: str
    session_id: str
    type: MessageType
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]]

# src/models/product.py
class Product(BaseModel):
    id: str
    name: str
    description: str
    price: float
    category: str
    embedding: Optional[List[float]]
```

**Nap 3-4: Koordinátor Agent**
```python
# src/agents/coordinator/main.py
from langgraph.prebuilt import create_react_agent

@tool
async def route_to_product_info(query: str) -> str:
    """Termékinformációs ügynökhöz irányítás"""
    return await product_info_agent.run(query)

coordinator_agent = create_react_agent(
    llm,
    tools=[route_to_product_info, route_to_order_status, route_to_recommendations]
)
```

**Nap 5-7: Specializált Agent-ek**
```python
# src/agents/product_info/main.py
@dataclass
class ProductInfoDependencies:
    supabase_client: Any
    webshop_api: Any
    user_context: dict

product_info_agent = Agent(
    'openai:gpt-4o',
    deps_type=ProductInfoDependencies,
    output_type=ProductInfo
)
```

### 2. HÉT: Adatbázis és Integráció

**Nap 1-2: Supabase Schema**
```sql
-- Users tábla
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR UNIQUE NOT NULL,
    name VARCHAR,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Products tábla pgvector-rel
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    description TEXT,
    price DECIMAL(10,2),
    category VARCHAR,
    embedding vector(1536),
    available BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Nap 3-4: Vector Database**
```python
# src/integrations/vector/main.py
async def create_product_embedding(product_text: str) -> List[float]:
    """Termék embedding generálása OpenAI API-val"""
    response = await openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=product_text
    )
    return response.data[0].embedding

async def semantic_search(query: str, limit: int = 10) -> List[Product]:
    """Semantic search termékek között"""
    query_embedding = await create_product_embedding(query)
    # pgvector similarity search
```

**Nap 5-7: Redis Cache**
```python
# src/integrations/cache/main.py
class RedisCache:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        """Session adatok lekérése cache-ből"""
        data = await self.redis.get(f"session:{session_id}")
        return json.loads(data) if data else None
```

### 3. HÉT: Webshop Integráció

**Nap 1-3: API Adapter**
```python
# src/integrations/webshop/shoprenter.py
class ShoprenterAPI:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def search_products(self, query: str) -> List[Product]:
        """Termék keresés Shoprenter API-n keresztül"""
        response = await self.client.get(
            f"{self.base_url}/products",
            params={"search": query},
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return [Product(**item) for item in response.json()["data"]]
```

**Nap 4-7: Termékadat Szinkronizáció**
```python
# src/integrations/webshop/sync.py
class ProductSync:
    def __init__(self, webshop_api: ShoprenterAPI, supabase_client: Any):
        self.webshop_api = webshop_api
        self.supabase_client = supabase_client
    
    async def sync_products(self):
        """Termékek szinkronizálása webshop-ból"""
        products = await self.webshop_api.get_all_products()
        for product in products:
            embedding = await create_product_embedding(product.description)
            await self.supabase_client.table("products").upsert({
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "embedding": embedding
            }).execute()
```

### 4. HÉT: Marketing Automation

**Nap 1-3: Kosárelhagyás Follow-up**
```python
# src/agents/marketing/cart_abandonment.py
@celery_app.task
def send_abandoned_cart_email(cart_id: str, user_email: str):
    """Kosárelhagyás email küldése"""
    discount_code = generate_discount_code()
    email_content = render_email_template(
        "abandoned_cart.html",
        cart_id=cart_id,
        discount_code=discount_code
    )
    sendgrid_client.send_email(
        to_email=user_email,
        subject="Visszahívjuk a kosarát!",
        html_content=email_content
    )
```

**Nap 4-7: Email/SMS Integráció**
```python
# src/integrations/marketing/email.py
class EmailService:
    def __init__(self, sendgrid_api_key: str):
        self.client = SendGridAPIClient(sendgrid_api_key)
    
    async def send_abandoned_cart_email(self, user_email: str, cart_items: List[dict]) -> bool:
        """Kosárelhagyás email küldése"""
        template_data = {
            "cart_items": cart_items,
            "discount_code": generate_discount_code(),
            "total_value": sum(item["price"] for item in cart_items)
        }
        
        email_content = render_template("abandoned_cart.html", **template_data)
        
        message = Mail(
            from_email="no-reply@yourwebshop.com",
            to_emails=user_email,
            subject="Visszahívjuk a kosarát!",
            html_content=email_content
        )
        
        try:
            response = self.client.send(message)
            return response.status_code == 202
        except Exception as e:
            logger.error(f"Email küldés sikertelen: {e}")
            return False
```

### 5. HÉT: Social Media Integráció

**Nap 1-3: Facebook Messenger**
```python
# src/integrations/social_media/facebook.py
class FacebookMessengerAPI:
    def __init__(self, page_access_token: str):
        self.page_access_token = page_access_token
        self.base_url = "https://graph.facebook.com/v18.0"
    
    async def send_carousel_message(self, recipient_id: str, products: List[dict]):
        """Carousel üzenet küldése termékekkel"""
        elements = []
        for product in products[:10]:  # Facebook max 10 elem
            elements.append({
                "title": product["name"],
                "subtitle": f"{product['price']} Ft",
                "image_url": product["image_url"],
                "buttons": [{
                    "type": "web_url",
                    "url": product["url"],
                    "title": "Megnézem"
                }]
            })
        
        message_data = {
            "recipient": {"id": recipient_id},
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "generic",
                        "elements": elements
                    }
                }
            }
        }
        
        response = requests.post(
            f"{self.base_url}/me/messages",
            params={"access_token": self.page_access_token},
            json=message_data
        )
        return response.status_code == 200
```

**Nap 4-7: WhatsApp Business**
```python
# src/integrations/social_media/whatsapp.py
class WhatsAppBusinessAPI:
    def __init__(self, access_token: str, phone_number_id: str):
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.base_url = "https://graph.facebook.com/v18.0"
    
    async def send_template_message(self, to_number: str, template_name: str, parameters: dict):
        """Template üzenet küldése WhatsApp-on"""
        message_data = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": "hu"
                },
                "components": []
            }
        }
        
        # Parameter hozzáadása ha van
        if parameters:
            message_data["template"]["components"].append({
                "type": "body",
                "parameters": [
                    {"type": "text", "text": value} 
                    for value in parameters.values()
                ]
            })
        
        response = requests.post(
            f"{self.base_url}/{self.phone_number_id}/messages",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json=message_data
        )
        return response.status_code == 200
```

### 6. HÉT: Tesztelés és Deployment

**Nap 1-3: Tesztelési Stratégia**
```python
# tests/test_agents.py
import pytest
from src.agents.coordinator.main import coordinator_agent

@pytest.mark.asyncio
async def test_coordinator_agent_product_query():
    """Koordinátor agent tesztelése termék kérdéssel"""
    messages = [{"role": "user", "content": "Keresek egy telefont"}]
    result = coordinator_agent.invoke({"messages": messages})
    
    assert result["messages"][-1]["content"] is not None
    assert "termék" in result["messages"][-1]["content"].lower()

# tests/test_integrations.py
@pytest.mark.asyncio
async def test_supabase_connection():
    """Supabase kapcsolat tesztelése"""
    from src.integrations.database.main import get_supabase_client
    
    client = get_supabase_client()
    response = await client.table("products").select("*").limit(1).execute()
    
    assert response is not None
    assert "data" in response
```

**Nap 4-7: Production Deployment**
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  chatbuddy-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    restart: unless-stopped
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

## 🎯 Kritikus Sikerfaktorok

### 1. **AI Agent Teljesítmény**
- LangGraph prebuilt komponensek használata (90% kevesebb kód)
- Pydantic AI dependency injection pattern
- Type-safe architektúra

### 2. **Vector Database Optimalizálás**
- OpenAI embeddings API hatékony használata
- pgvector similarity search optimalizálás
- Batch processing nagy termékadatbázisokhoz

### 3. **Marketing Automation ROI**
- 10-15% cart recovery rate cél
- Automatikus kedvezmény kódok
- Multi-channel follow-up (email, SMS, social media)

### 4. **Production Ready**
- Docker containerization
- Monitoring és logging
- Security és GDPR compliance

## 📈 Teljesítmény Metrikák

| Metrika | Cél | Mérési Pont |
|---------|-----|-------------|
| **Response Time** | < 2 másodperc | Agent válaszidő |
| **Cart Recovery Rate** | 10-15% | Kosárelhagyás follow-up |
| **Vector Search Accuracy** | > 85% | Semantic search relevancia |
| **Uptime** | > 99.5% | Production availability |
| **Error Rate** | < 1% | API hiba arány |

## 🚀 Következő Azonnali Lépések

1. **✅ Ma:** Adatmodellek implementálása (`src/models/`) - **ELKÉSZÜLT**
2. **✅ Ma:** Koordinátor agent LangGraph prebuilt komponensekkel - **ELKÉSZÜLT**
3. **✅ Ma:** FastAPI szerver elindítása és chat endpoint tesztelése - **ELKÉSZÜLT**
4. **Holnap:** Specializált agent-ek implementálása (Product Info, Order Status, Recommendation)
5. **Ezen a héten:** WebSocket chat interface és Supabase schema design
6. **Jövő héten:** Vector database integráció és Redis cache

## 📋 Napi Feladatok Checklist

### 1. HÉT - AI Agent Alapok

**Hétfő:**
- [x] Adatmodellek létrehozása (`src/models/chat.py`, `src/models/product.py`, `src/models/user.py`, `src/models/order.py`, `src/models/agent.py`, `src/models/marketing.py`)
- [x] Pydantic validációk és dokumentáció
- [x] Unit tesztek modellekhez
- [x] Virtuális környezet problémák megoldása (Python 3.13 kompatibilitás)
- [x] Pydantic V2 migráció (json_encoders eltávolítása)

**Kedd:**
- [x] Koordinátor agent alapstruktúra
- [x] LangGraph prebuilt `create_react_agent` setup
- [x] Tool definitions
- [x] Unit tesztek koordinátor agent-hez
- [x] FastAPI integráció chat endpoint-tal

**Szerda:**
- [ ] Product Info Agent implementáció
- [ ] Dependency injection pattern
- [ ] Agent tesztelés

**Csütörtök:**
- [ ] Order Status Agent implementáció
- [ ] Recommendation Agent alapjai
- [ ] Agent-ek közötti kommunikáció

**Péntek:**
- [ ] WebSocket chat interface alapjai
- [ ] Session kezelés
- [ ] Message persistence

**Hétvége:**
- [ ] Integrációs tesztek
- [ ] Dokumentáció frissítése
- [ ] Következő hét tervezése

### 2. HÉT - Adatbázis és Integráció

**Hétfő:**
- [ ] Supabase projekt beállítása
- [ ] Schema design (users, products, orders, chat_sessions)
- [ ] pgvector extension engedélyezése

**Kedd:**
- [ ] Vector database integráció
- [ ] OpenAI embeddings API setup
- [ ] Semantic search implementáció

**Szerda:**
- [ ] Redis cache implementáció
- [ ] Session storage
- [ ] Performance cache

**Csütörtök:**
- [ ] Database connection pooling
- [ ] Error handling és retry logic
- [ ] Monitoring setup

**Péntek:**
- [ ] Adatbázis tesztek
- [ ] Performance optimalizálás
- [ ] Dokumentáció

### 3. HÉT - Webshop Integráció

**Hétfő:**
- [ ] Shoprenter API integráció
- [ ] API adapter réteg
- [ ] Error handling és rate limiting

**Kedd:**
- [ ] UNAS API integráció
- [ ] Egységes webshop interface
- [ ] API tesztek

**Szerda:**
- [ ] Termékadat szinkronizáció
- [ ] Automatikus import
- [ ] Készlet frissítések

**Csütörtök:**
- [ ] Ár változások kezelése
- [ ] Batch processing
- [ ] Monitoring és alerting

**Péntek:**
- [ ] Integrációs tesztek
- [ ] Performance optimalizálás
- [ ] Dokumentáció

### 4. HÉT - Marketing Automation

**Hétfő:**
- [ ] Celery background tasks setup
- [ ] Kosárelhagyás detektálás
- [ ] Email template engine

**Kedd:**
- [ ] SendGrid email integráció
- [ ] Abandoned cart email küldés
- [ ] Kedvezmény kódok generálása

**Szerda:**
- [ ] Twilio SMS integráció
- [ ] SMS template-ek
- [ ] Multi-channel follow-up

**Csütörtök:**
- [ ] Marketing automation workflow
- [ ] A/B tesztelés
- [ ] ROI mérés

**Péntek:**
- [ ] Marketing tesztek
- [ ] Performance monitoring
- [ ] Dokumentáció

### 5. HÉT - Social Media Integráció

**Hétfő:**
- [ ] Facebook Messenger Platform setup
- [ ] Messenger API integráció
- [ ] Carousel üzenetek

**Kedd:**
- [ ] Quick reply gombok
- [ ] Template üzenetek
- [ ] Messenger tesztek

**Szerda:**
- [ ] WhatsApp Business API setup
- [ ] WhatsApp template üzenetek
- [ ] Interaktív válaszok

**Csütörtök:**
- [ ] Social media workflow
- [ ] Multi-platform kommunikáció
- [ ] Monitoring

**Péntek:**
- [ ] Social media tesztek
- [ ] Performance optimalizálás
- [ ] Dokumentáció

### 6. HÉT - Tesztelés és Deployment

**Hétfő:**
- [ ] Unit tesztek minden komponenshez
- [ ] Integrációs tesztek
- [ ] End-to-end tesztek

**Kedd:**
- [ ] Load testing
- [ ] Performance testing
- [ ] Security testing

**Szerda:**
- [ ] Docker image optimalizálás
- [ ] Production deployment
- [ ] Monitoring setup

**Csütörtök:**
- [ ] SSL/TLS beállítás
- [ ] Backup stratégia
- [ ] Disaster recovery

**Péntek:**
- [ ] Go-live checklist
- [ ] Dokumentáció végső ellenőrzés
- [ ] Production monitoring

## 🔧 Technológiai Stack Részletek

### AI és Workflow Management
- **LangGraph**: Prebuilt komponensek, 90% kevesebb boilerplate kód
- **Pydantic AI**: Type-safe dependency injection, domain-specifikus logika
- **OpenAI GPT-4o**: Elsődleges LLM modell
- **Anthropic Claude-3-5-sonnet**: Fallback LLM modell
- **OpenAI text-embedding-3-small**: Vector embeddings

### Backend és API
- **FastAPI**: Modern, gyors web framework
- **WebSocket**: Valós idejű chat kommunikáció
- **Uvicorn**: ASGI szerver production-ready alkalmazásokhoz
- **httpx**: Aszinkron HTTP kliens külső API hívásokhoz

### Adatbázis és Cache
- **Supabase**: PostgreSQL + pgvector extension
- **Redis**: Session storage, performance cache, Celery broker
- **asyncpg**: Aszinkron PostgreSQL driver
- **SQLAlchemy**: ORM és adatbázis absztrakció

### Marketing és Kommunikáció
- **SendGrid**: Email szolgáltatás
- **Twilio**: SMS szolgáltatás
- **Celery**: Background task processing
- **Jinja2**: Template engine

### Social Media
- **Facebook Messenger Platform**: Carousel üzenetek, quick reply gombok
- **WhatsApp Business API**: Template üzenetek, interaktív válaszok

### Monitoring és Logging
- **Pydantic Logfire**: AI agent teljesítmény és strukturált logging
- **Structlog**: Strukturált logging
- **Prometheus**: Metrikák és monitoring

### Development Tools
- **pytest**: Tesztelési framework
- **black**: Kód formázás
- **isort**: Import rendezés
- **mypy**: Type checking
- **pre-commit**: Git hooks

## 📚 Dokumentáció és Források

### Hivatalos Dokumentációk
- [LangGraph Prebuilt Components](https://langchain-ai.github.io/langgraph/how-tos/state-graphs/)
- [Pydantic AI Documentation](https://ai.pydantic.dev/)
- [Supabase pgvector Guide](https://supabase.com/docs/guides/ai/vector-embeddings)
- [FastAPI WebSocket](https://fastapi.tiangolo.com/advanced/websockets/)

### Implementációs Útmutatók
- `docs/pydantic_ai_pattern_fixes.md` - C opció javítások
- `docs/langgraph_prebuilt_optimization.md` - B opció optimalizáció
- `docs/vector_database_integration.md` - Supabase pgvector implementáció
- `docs/marketing_automation_features.md` - Marketing automation
- `docs/social_media_integration.md` - Social media integráció

### Tesztelési Stratégia
- Unit tesztek minden agent-hez és komponenshez
- Integrációs tesztek API-k és adatbázis kapcsolatokhoz
- End-to-end tesztek teljes felhasználói utakhoz
- Performance és load tesztek production előtt

## 🎯 Sikeres MVP Kritériumok

### Funkcionális Követelmények
- ✅ Magyar nyelvű chatbot kommunikáció
- ✅ Termékkeresés és információ szolgáltatás
- ✅ Rendelési státusz lekérdezés
- ✅ Személyre szabott termékajánlások
- ✅ Kosárelhagyás follow-up automatikus küldéssel
- ✅ Multi-channel kommunikáció (email, SMS, social media)
- ✅ Vector-alapú semantic search
- ✅ Real-time chat interface

### Technikai Követelmények
- ✅ < 2 másodperc response time
- ✅ > 99.5% uptime
- ✅ < 1% error rate
- ✅ GDPR compliance
- ✅ Enterprise-grade security
- ✅ Scalable architecture
- ✅ Comprehensive monitoring

### Üzleti Követelmények
- ✅ 10-15% cart recovery rate
- ✅ > 85% vector search accuracy
- ✅ Multi-webshop támogatás
- ✅ Marketing automation ROI
- ✅ Customer satisfaction improvement

Ez a terv biztosítja a fokozatos építkezést és a korai problémák azonosítását, miközben minden lépés után egy működő, tesztelhető komponens áll rendelkezésre. 