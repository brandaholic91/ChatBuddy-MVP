# Vektoradatbázis Integráció - Supabase pgvector

## 🔍 Áttekintés

A Chatbuddy MVP projektben Supabase pgvector extension-t használjuk vektoradatbázisként a semantic search, RAG (Retrieval-Augmented Generation), és termékajánlási funkciók megvalósításához.

---

## 🎯 **Miért Vektoradatbázis?**

### **Hagyományos vs. Vektoralapú Keresés:**

| Hagyományos SQL | Vektoralapú Semantic Search |
|-----------------|----------------------------|
| `WHERE title LIKE '%iPhone%'` | Hasonlóság-alapú keresés embeddingek között |
| Pontos szövegegyezés | Jelentés-alapú keresés |
| Szinonimákat nem ismeri fel | "telefon", "mobil", "smartphone" → ugyanaz |
| Nyelvfüggő | Többnyelvű támogatás |

### **Használati Esetek:**
- **🔍 Semantic Search**: "Keresek egy jó telefont" → iPhone, Samsung, Xiaomi eredmények
- **🧠 RAG Implementation**: Releváns termékadatokkal kiegészített LLM válaszok
- **🎯 Recommendation Engine**: Hasonló termékek automatikus ajánlása
- **💬 FAQ Matching**: Felhasználói kérdések automatikus FAQ-hoz rendelése

---

## 🏗️ **Architektúra**

### **Supabase pgvector Stack:**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Query    │ -> │  OpenAI Embed   │ -> │  pgvector DB    │
│ "jó telefon"    │    │ text-embed-3-sm │    │ similarity <->  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        v
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ LLM Response    │ <- │ Pydantic AI     │ <- │ Top 5 Results   │
│ + Product Data  │    │ Agent + RAG     │    │ {name, price}   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Dependency Injection Pattern:**
```python
@dataclass
class ProductDependencies:
    webshop_api: Any
    vector_db: Any        # Supabase pgvector kapcsolat
    user_context: dict

@product_agent.tool
async def semantic_search(ctx: RunContext[ProductDependencies], query: str):
    embedding = await get_openai_embedding(query)
    return await ctx.deps.vector_db.similarity_search(embedding, limit=5)
```

---

## 🛠️ **Implementációs Részletek**

### **1. Database Schema (Supabase)**
```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Products table with embeddings
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    price DECIMAL(10,2),
    category TEXT,
    embedding VECTOR(1536),  -- OpenAI text-embedding-3-small dimenzió
    created_at TIMESTAMP DEFAULT NOW()
);

-- Vector similarity index
CREATE INDEX ON products USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Semantic search function
CREATE OR REPLACE FUNCTION search_products(
    query_embedding VECTOR(1536),
    similarity_threshold FLOAT DEFAULT 0.5,
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    id INT,
    title TEXT,
    description TEXT,
    price DECIMAL(10,2),
    similarity FLOAT
)
LANGUAGE SQL
AS $$
SELECT
    p.id,
    p.title,
    p.description,
    p.price,
    1 - (p.embedding <=> query_embedding) AS similarity
FROM products p
WHERE 1 - (p.embedding <=> query_embedding) > similarity_threshold
ORDER BY p.embedding <=> query_embedding
LIMIT match_count;
$$;
```

### **2. Python Integration**
```python
import openai
from supabase import create_client
import numpy as np

class VectorSearchService:
    def __init__(self, supabase_client, openai_client):
        self.supabase = supabase_client
        self.openai = openai_client
    
    async def get_embedding(self, text: str) -> List[float]:
        """OpenAI embedding generálása"""
        response = await self.openai.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    
    async def semantic_search(self, query: str, limit: int = 5) -> List[dict]:
        """Semantic search végrehajtása"""
        query_embedding = await self.get_embedding(query)
        
        result = self.supabase.rpc('search_products', {
            'query_embedding': query_embedding,
            'match_count': limit,
            'similarity_threshold': 0.5
        }).execute()
        
        return result.data
    
    async def batch_embed_products(self, products: List[dict]):
        """Batch embedding processing nagy adatbázisokhoz"""
        batch_size = 100
        for i in range(0, len(products), batch_size):
            batch = products[i:i + batch_size]
            
            texts = [f"{p['title']} {p['description']}" for p in batch]
            embeddings = await self.get_embeddings_batch(texts)
            
            # Supabase batch update
            updates = [
                {"id": p["id"], "embedding": emb} 
                for p, emb in zip(batch, embeddings)
            ]
            
            self.supabase.table('products').upsert(updates).execute()
```

### **3. Pydantic AI Integration**
```python
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext

@dataclass
class ChatbotDependencies:
    vector_search: VectorSearchService
    webshop_api: Any
    user_context: dict

product_agent = Agent(
    'openai:gpt-4o',
    deps_type=ChatbotDependencies,
    system_prompt="""
    Te egy termék szakértő vagy. Használj semantic search-t 
    releváns termékek megtalálásához.
    """
)

@product_agent.tool
async def find_similar_products(
    ctx: RunContext[ChatbotDependencies], 
    query: str
) -> List[dict]:
    """Hasonló termékek keresése vektorkeresés alapján"""
    results = await ctx.deps.vector_search.semantic_search(query)
    return [
        {
            "title": r["title"],
            "price": f"{r['price']} Ft",
            "similarity": f"{r['similarity']:.2%}"
        }
        for r in results
    ]

@product_agent.tool
async def get_product_recommendations(
    ctx: RunContext[ChatbotDependencies], 
    product_id: int
) -> List[dict]:
    """Termékajánlások egy adott termék alapján"""
    # Get the product's embedding
    product = ctx.deps.webshop_api.get_product(product_id)
    
    # Find similar products
    similar = await ctx.deps.vector_search.semantic_search(
        f"{product['title']} {product['description']}"
    )
    
    return [s for s in similar if s["id"] != product_id][:3]
```

---

## ⚙️ **Környezeti Változók**

Az `.env_example` fájl frissítése:
```bash
# AI Provider Settings
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Vector Database Configuration (pgvector)
VECTOR_SIMILARITY_THRESHOLD=0.5
VECTOR_SEARCH_LIMIT=10
EMBEDDING_BATCH_SIZE=100

# Supabase (PostgreSQL + pgvector)
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
```

---

## 📦 **Dependencies Frissítése**

`requirements.txt` kiegészítés:
```bash
# Vector Database (pgvector)
pgvector>=0.2.5
sentence-transformers>=2.2.0  # Backup embedding option
numpy>=1.24.0
```

---

## 🔄 **Migration Path**

### **1. Supabase Setup:**
```sql
-- 1. Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Add embedding column to existing products table
ALTER TABLE products ADD COLUMN embedding VECTOR(1536);

-- 3. Create vector index
CREATE INDEX ON products USING ivfflat (embedding vector_cosine_ops);
```

### **2. Data Migration:**
```python
async def migrate_existing_products():
    """Meglévő termékek embedding-jeinek generálása"""
    products = supabase.table('products').select('*').is_('embedding', 'null').execute()
    
    vector_service = VectorSearchService(supabase, openai_client)
    await vector_service.batch_embed_products(products.data)
    
    print(f"Migrated {len(products.data)} products with embeddings")
```

### **3. Testing:**
```python
async def test_vector_search():
    """Vector search tesztelése"""
    vector_service = VectorSearchService(supabase, openai_client)
    
    results = await vector_service.semantic_search("okos telefon")
    
    for result in results:
        print(f"Title: {result['title']}")
        print(f"Similarity: {result['similarity']:.2%}")
        print("---")
```

---

## 📈 **Performance Optimalizációk**

### **1. Indexing Strategy:**
```sql
-- IVFFlat index nagy adatbázisokhoz
CREATE INDEX ON products USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- HNSW index még jobb performance-hez (pgvector 0.5.0+)
CREATE INDEX ON products USING hnsw (embedding vector_cosine_ops);
```

### **2. Query Optimization:**
```python
# Batch embedding generation
async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
    response = await self.openai.embeddings.create(
        model="text-embedding-3-small",
        input=texts  # Batch processing
    )
    return [d.embedding for d in response.data]

# Connection pooling
from sqlalchemy.pool import QueuePool
engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=0
)
```

### **3. Caching Strategy:**
```python
from functools import lru_cache
import redis

class CachedVectorService(VectorSearchService):
    def __init__(self, supabase_client, openai_client, redis_client):
        super().__init__(supabase_client, openai_client)
        self.redis = redis_client
    
    async def get_embedding(self, text: str) -> List[float]:
        # Check cache first
        cache_key = f"embedding:{hash(text)}"
        cached = await self.redis.get(cache_key)
        
        if cached:
            return json.loads(cached)
        
        # Generate and cache
        embedding = await super().get_embedding(text)
        await self.redis.setex(cache_key, 3600, json.dumps(embedding))
        
        return embedding
```

---

## 🎯 **Következő Lépések**

1. **✅ README és dokumentáció frissítve**
2. **✅ Environment konfigurációk hozzáadva**  
3. **✅ Requirements.txt frissítve**
4. **🔄 Supabase pgvector setup**
5. **🔄 Migration scripts implementálása**
6. **🔄 Vector search service fejlesztése**
7. **🔄 Pydantic AI integration tesztelése**

---

## 📚 **Referenciák**

- [Supabase pgvector Guide](https://supabase.com/docs/guides/database/extensions/pgvector)
- [OpenAI Embeddings API](https://platform.openai.com/docs/guides/embeddings)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [Vector Similarity Search Best Practices](https://github.com/pgvector/pgvector#performance)