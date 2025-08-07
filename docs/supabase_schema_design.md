# 🗄️ ChatBuddy MVP - Supabase Schema Design

## 📋 Áttekintés

Ez a dokumentáció a ChatBuddy MVP adatbázis sémáját írja le, amely Supabase-en alapul és pgvector támogatással rendelkezik a vector similarity search-hez.

## 🏗️ Adatbázis Architektúra

### Komponensek

1. **Supabase Client** - Kapcsolat kezelés és konfiguráció
2. **Schema Manager** - Táblák létrehozása és kezelése
3. **RLS Policy Manager** - Row Level Security policy-k
4. **Vector Operations** - pgvector műveletek és embedding kezelés
5. **Database Setup** - Teljes adatbázis inicializálás

## 📊 Táblák

### 1. Users Tábla

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'customer' CHECK (role IN ('customer', 'admin', 'support', 'agent')),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended', 'pending')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb
);
```

**Indexek:**
- `idx_users_email` - Email cím kereséshez
- `idx_users_role` - Szerepkör alapú szűréshez
- `idx_users_status` - Státusz alapú szűréshez
- `idx_users_created_at` - Dátum alapú rendezéshez

### 2. User Profiles Tábla

```sql
CREATE TABLE user_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    phone VARCHAR(50),
    address TEXT,
    city VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100) DEFAULT 'Hungary',
    birth_date DATE,
    gender VARCHAR(20),
    language VARCHAR(10) DEFAULT 'hu',
    timezone VARCHAR(50) DEFAULT 'Europe/Budapest',
    avatar_url TEXT,
    bio TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 3. User Preferences Tábla

```sql
CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    notification_email BOOLEAN DEFAULT TRUE,
    notification_sms BOOLEAN DEFAULT FALSE,
    notification_push BOOLEAN DEFAULT TRUE,
    marketing_emails BOOLEAN DEFAULT TRUE,
    newsletter BOOLEAN DEFAULT FALSE,
    chat_history BOOLEAN DEFAULT TRUE,
    auto_save_cart BOOLEAN DEFAULT TRUE,
    product_recommendations BOOLEAN DEFAULT TRUE,
    personalized_offers BOOLEAN DEFAULT TRUE,
    theme VARCHAR(20) DEFAULT 'light',
    language VARCHAR(10) DEFAULT 'hu',
    currency VARCHAR(10) DEFAULT 'HUF',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 4. Products Tábla (pgvector támogatással)

```sql
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    short_description TEXT,
    price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
    original_price DECIMAL(10,2) CHECK (original_price >= 0),
    currency VARCHAR(10) DEFAULT 'HUF',
    category_id UUID,
    brand VARCHAR(100),
    sku VARCHAR(100) UNIQUE,
    barcode VARCHAR(100),
    weight DECIMAL(8,3) CHECK (weight >= 0),
    dimensions JSONB DEFAULT '{}'::jsonb,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'out_of_stock', 'discontinued', 'draft')),
    product_type VARCHAR(50) DEFAULT 'physical' CHECK (product_type IN ('physical', 'digital', 'service', 'subscription')),
    stock_quantity INTEGER DEFAULT 0,
    min_stock_level INTEGER DEFAULT 0,
    max_stock_level INTEGER,
    is_featured BOOLEAN DEFAULT FALSE,
    is_bestseller BOOLEAN DEFAULT FALSE,
    is_new BOOLEAN DEFAULT FALSE,
    is_on_sale BOOLEAN DEFAULT FALSE,
    sale_percentage INTEGER CHECK (sale_percentage >= 0 AND sale_percentage <= 100),
    tags TEXT[] DEFAULT '{}',
    images TEXT[] DEFAULT '{}',
    main_image TEXT,
    embedding VECTOR(1536), -- OpenAI text-embedding-ada-002 dimenzió
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Indexek:**
- `idx_products_name` - Full-text search (magyar nyelv)
- `idx_products_category` - Kategória alapú szűrés
- `idx_products_brand` - Márka alapú szűrés
- `idx_products_status` - Státusz alapú szűrés
- `idx_products_price` - Ár alapú rendezés
- `idx_products_sku` - SKU keresés
- `idx_products_tags` - Tag alapú keresés
- `idx_products_created_at` - Dátum alapú rendezés
- `idx_products_embedding` - Vector similarity search (HNSW index)

### 5. Product Categories Tábla

```sql
CREATE TABLE product_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    parent_id UUID REFERENCES product_categories(id),
    slug VARCHAR(255) UNIQUE NOT NULL,
    image_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    level INTEGER DEFAULT 0,
    path TEXT[] DEFAULT '{}',
    product_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 6. Orders Tábla

```sql
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number VARCHAR(100) UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded', 'partially_refunded', 'returned', 'on_hold')),
    payment_status VARCHAR(50) DEFAULT 'pending' CHECK (payment_status IN ('pending', 'authorized', 'paid', 'failed', 'refunded', 'partially_refunded', 'cancelled')),
    payment_method VARCHAR(50) CHECK (payment_method IN ('credit_card', 'debit_card', 'bank_transfer', 'cash_on_delivery', 'paypal', 'apple_pay', 'google_pay', 'crypto')),
    subtotal DECIMAL(10,2) NOT NULL CHECK (subtotal >= 0),
    tax_amount DECIMAL(10,2) DEFAULT 0 CHECK (tax_amount >= 0),
    shipping_amount DECIMAL(10,2) DEFAULT 0 CHECK (shipping_amount >= 0),
    discount_amount DECIMAL(10,2) DEFAULT 0 CHECK (discount_amount >= 0),
    total_amount DECIMAL(10,2) NOT NULL CHECK (total_amount >= 0),
    currency VARCHAR(10) DEFAULT 'HUF',
    shipping_method VARCHAR(50) CHECK (shipping_method IN ('standard', 'express', 'next_day', 'same_day', 'pickup', 'international')),
    shipping_address JSONB DEFAULT '{}'::jsonb,
    billing_address JSONB DEFAULT '{}'::jsonb,
    tracking_number VARCHAR(100),
    tracking_url TEXT,
    estimated_delivery TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 7. Order Items Tábla

```sql
CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id),
    variant_id UUID,
    product_name VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0),
    total_price DECIMAL(10,2) NOT NULL CHECK (total_price >= 0),
    discount_amount DECIMAL(10,2) DEFAULT 0 CHECK (discount_amount >= 0),
    tax_amount DECIMAL(10,2) DEFAULT 0 CHECK (tax_amount >= 0),
    attributes JSONB DEFAULT '{}'::jsonb,
    image_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 8. Chat Sessions Tábla

```sql
CREATE TABLE chat_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    context JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    agent_used VARCHAR(100),
    message_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 9. Chat Messages Tábla

```sql
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL CHECK (type IN ('user', 'assistant', 'system', 'error', 'tool')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    agent_used VARCHAR(100),
    confidence DECIMAL(3,2) CHECK (confidence >= 0 AND confidence <= 1),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 10. Audit Logs Tábla

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_id UUID REFERENCES chat_sessions(session_id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    details JSONB DEFAULT '{}'::jsonb,
    ip_address INET,
    user_agent TEXT,
    severity VARCHAR(20) DEFAULT 'info' CHECK (severity IN ('debug', 'info', 'warning', 'error', 'critical')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 11. User Consents Tábla (GDPR Compliance)

```sql
CREATE TABLE user_consents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    consent_type VARCHAR(100) NOT NULL,
    consent_version VARCHAR(20) NOT NULL,
    granted BOOLEAN NOT NULL,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    revoked_at TIMESTAMP WITH TIME ZONE,
    ip_address INET,
    user_agent TEXT,
    consent_text TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## 🔒 Row Level Security (RLS) Policy-k

### Users Tábla Policy-k

```sql
-- Felhasználók csak saját adataikat láthatják
CREATE POLICY "Users can view own profile"
ON users FOR SELECT
TO authenticated
USING (auth.uid() = id);

-- Felhasználók csak saját adataikat módosíthatják
CREATE POLICY "Users can update own profile"
ON users FOR UPDATE
TO authenticated
USING (auth.uid() = id)
WITH CHECK (auth.uid() = id);

-- Adminok minden felhasználót láthatnak
CREATE POLICY "Admins can view all users"
ON users FOR SELECT
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM users 
        WHERE id = auth.uid() AND role = 'admin'
    )
);
```

### Products Tábla Policy-k

```sql
-- Mindenki láthatja az aktív termékeket
CREATE POLICY "Public can view active products"
ON products FOR SELECT
TO authenticated, anon
USING (status = 'active');

-- Adminok minden terméket láthatnak és módosíthatnak
CREATE POLICY "Admins can manage all products"
ON products FOR ALL
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM users 
        WHERE id = auth.uid() AND role = 'admin'
    )
);
```

### Orders Tábla Policy-k

```sql
-- Felhasználók csak saját rendeléseiket láthatják
CREATE POLICY "Users can view own orders"
ON orders FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

-- Felhasználók saját rendeléseiket létrehozhatják
CREATE POLICY "Users can create own orders"
ON orders FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);
```

## 🧠 Vector Operations (pgvector)

### Embedding Generálás

```python
async def generate_embedding(self, text: str) -> Optional[List[float]]:
    """Generál egy embedding-et a megadott szövegből"""
    # OpenAI text-embedding-ada-002 használata
    # 1536 dimenziós vektor
```

### Similarity Search

```sql
-- Vector similarity search példa
SELECT 
    id, name, description, price, brand, 
    embedding <=> '[0.1, 0.2, ...]' AS similarity,
    metadata
FROM products 
WHERE status = 'active' 
AND embedding IS NOT NULL
ORDER BY embedding <=> '[0.1, 0.2, ...]'
LIMIT 10;
```

### HNSW Index

```sql
-- HNSW index a similarity search optimalizálásához
CREATE INDEX idx_products_embedding 
ON products USING hnsw (embedding vector_cosine_ops);
```

## 🔐 GDPR Compliance

### Right to be Forgotten

```sql
-- GDPR "right to be forgotten" funkció
CREATE OR REPLACE FUNCTION delete_user_data(user_uuid UUID)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- Audit log a törlésről
    INSERT INTO audit_logs (
        user_id, action, resource_type, resource_id, 
        details, severity, created_at
    ) VALUES (
        user_uuid, 'gdpr_data_deletion', 'user', user_uuid,
        '{"reason": "GDPR right to be forgotten"}', 'info', NOW()
    );
    
    -- Törlés sorrend: függőségek miatt
    DELETE FROM user_consents WHERE user_id = user_uuid;
    DELETE FROM chat_messages WHERE session_id IN (
        SELECT session_id FROM chat_sessions WHERE user_id = user_uuid
    );
    DELETE FROM chat_sessions WHERE user_id = user_uuid;
    DELETE FROM order_items WHERE order_id IN (
        SELECT id FROM orders WHERE user_id = user_uuid
    );
    DELETE FROM orders WHERE user_id = user_uuid;
    DELETE FROM user_preferences WHERE user_id = user_uuid;
    DELETE FROM user_profiles WHERE user_id = user_uuid;
    DELETE FROM audit_logs WHERE user_id = user_uuid;
    
    -- Felhasználó adatok anonimizálása (törlés helyett)
    UPDATE users SET 
        email = 'deleted_' || id || '@deleted.com',
        name = 'Deleted User',
        metadata = jsonb_build_object('deleted_at', NOW(), 'gdpr_deletion', true),
        status = 'inactive'
    WHERE id = user_uuid;
END;
$$;
```

## 📊 Audit Trail

### Automatikus Audit Log

```sql
-- Automatikus audit log trigger funkció
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    user_uuid UUID;
    action_type TEXT;
    resource_type TEXT;
    resource_id UUID;
BEGIN
    -- Felhasználó azonosítása
    user_uuid := auth.uid();
    
    -- Művelet típusa meghatározása
    IF TG_OP = 'INSERT' THEN
        action_type := 'create';
        resource_id := NEW.id;
    ELSIF TG_OP = 'UPDATE' THEN
        action_type := 'update';
        resource_id := NEW.id;
    ELSIF TG_OP = 'DELETE' THEN
        action_type := 'delete';
        resource_id := OLD.id;
    END IF;
    
    -- Resource típus meghatározása
    resource_type := TG_TABLE_NAME;
    
    -- Audit log beszúrása
    INSERT INTO audit_logs (
        user_id, action, resource_type, resource_id,
        details, severity, created_at
    ) VALUES (
        user_uuid, action_type, resource_type, resource_id,
        jsonb_build_object(
            'table', TG_TABLE_NAME,
            'operation', TG_OP,
            'old_data', CASE WHEN TG_OP = 'UPDATE' OR TG_OP = 'DELETE' 
                            THEN to_jsonb(OLD) ELSE '{}'::jsonb END,
            'new_data', CASE WHEN TG_OP = 'INSERT' OR TG_OP = 'UPDATE' 
                            THEN to_jsonb(NEW) ELSE '{}'::jsonb END
        ),
        'info', NOW()
    );
    
    RETURN COALESCE(NEW, OLD);
END;
$$;
```

## 🚀 Használat

### Database Setup Futtatása

```python
from src.integrations.database.setup_database import DatabaseSetup, SupabaseConfig

# Konfiguráció
config = SupabaseConfig(
    url="your-supabase-url",
    key="your-supabase-key",
    service_role_key="your-service-role-key"
)

# Database setup
setup = DatabaseSetup(config)
results = await setup.setup_complete_database()
```

### Vector Search Használata

```python
from src.integrations.database.vector_operations import VectorOperations

# Vector operations
vector_ops = VectorOperations(supabase_client)

# Similarity search
results = await vector_ops.search_similar_products("iPhone 15 Pro", limit=10)

# Hibrid keresés
filters = {
    "category_id": "electronics",
    "min_price": 100000,
    "max_price": 500000
}
results = await vector_ops.hybrid_search("okostelefon", filters, limit=10)
```

## 📈 Teljesítmény Optimalizálás

### Indexek

- **B-tree indexek** - Egyszerű keresésekhez
- **GIN indexek** - Full-text search és array típusokhoz
- **HNSW indexek** - Vector similarity search-hez

### Konfiguráció

```sql
-- Vector search optimalizálás
SET maintenance_work_mem = '2GB';
SET work_mem = '256MB';
SET shared_buffers = '1GB';
SET effective_cache_size = '4GB';

-- HNSW index paraméterek
SET hnsw.ef_search = 100;
SET hnsw.iterative_scan = strict_order;
```

## 🔍 Monitoring és Validáció

### Schema Validáció

```python
# Schema validáció
schema_validation = schema_manager.validate_schema()
for table, info in schema_validation.items():
    print(f"{table}: {info['exists']} - {info['columns']} oszlop")
```

### Vector Statisztikák

```python
# Vector statisztikák
stats = await vector_ops.get_vector_statistics()
print(f"Összes termék: {stats['total_products']}")
print(f"Embedding-gel: {stats['products_with_embedding']}")
print(f"Index méret: {stats['index_size']}")
```

## 📝 Következő Lépések

1. **OpenAI API integráció** - Tényleges embedding generálás
2. **Redis cache** - Session és performance cache
3. **Batch processing** - Nagy mennyiségű adat feldolgozása
4. **Monitoring** - Teljesítmény metrikák
5. **Backup stratégia** - Adatbázis biztonsági mentések

## ✅ Ellenőrzőlista

- [x] Táblák létrehozása
- [x] RLS policy-k beállítása
- [x] pgvector extension engedélyezése
- [x] Vector indexek létrehozása
- [x] GDPR compliance funkciók
- [x] Audit trail rendszer
- [x] Tesztelési framework
- [x] Dokumentáció
- [ ] OpenAI API integráció
- [ ] Redis cache implementáció
- [ ] Production deployment 