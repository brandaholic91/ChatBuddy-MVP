-- Products tábla javítás - Hiányzó oszlopok hozzáadása
-- Futtasd ezt a scriptet a Supabase SQL Editor-ben

-- 1. Brand oszlop hozzáadása (ha még nincs)
ALTER TABLE products ADD COLUMN IF NOT EXISTS brand TEXT;

-- 2. Metadata oszlop hozzáadása (ha még nincs)
ALTER TABLE products ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';

-- 3. Status oszlop hozzáadása (ha még nincs)
ALTER TABLE products ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active';

-- 4. Short_description oszlop hozzáadása (ha még nincs)
ALTER TABLE products ADD COLUMN IF NOT EXISTS short_description TEXT;

-- 5. Tags oszlop hozzáadása (ha még nincs)
ALTER TABLE products ADD COLUMN IF NOT EXISTS tags TEXT[];

-- 6. Stock_quantity oszlop hozzáadása (ha még nincs)
ALTER TABLE products ADD COLUMN IF NOT EXISTS stock_quantity INTEGER DEFAULT 0;

-- 7. Is_featured oszlop hozzáadása (ha még nincs)
ALTER TABLE products ADD COLUMN IF NOT EXISTS is_featured BOOLEAN DEFAULT FALSE;

-- 8. Is_bestseller oszlop hozzáadása (ha még nincs)
ALTER TABLE products ADD COLUMN IF NOT EXISTS is_bestseller BOOLEAN DEFAULT FALSE;

-- 9. Is_new oszlop hozzáadása (ha még nincs)
ALTER TABLE products ADD COLUMN IF NOT EXISTS is_new BOOLEAN DEFAULT FALSE;

-- 10. Embedding oszlop hozzáadása (ha még nincs)
ALTER TABLE products ADD COLUMN IF NOT EXISTS embedding VECTOR(1536);

-- 11. Updated_at trigger függvény létrehozása
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 12. Updated_at trigger létrehozása a products táblához
DROP TRIGGER IF EXISTS update_products_updated_at ON products;
CREATE TRIGGER update_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 13. Vector indexek létrehozása (ha még nincsenek)
CREATE INDEX IF NOT EXISTS idx_products_embedding_hnsw 
ON products 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_products_embedding_ivfflat 
ON products 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 14. RPC függvények újra létrehozása
CREATE OR REPLACE FUNCTION search_products(
    query_embedding VECTOR(1536),
    similarity_threshold FLOAT DEFAULT 0.5,
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    name TEXT,
    description TEXT,
    price DECIMAL(10,2),
    brand TEXT,
    category_id UUID,
    similarity FLOAT,
    metadata JSONB
)
LANGUAGE SQL
AS $$
SELECT
    p.id,
    p.name,
    p.description,
    p.price,
    p.brand,
    p.category_id,
    1 - (p.embedding <=> query_embedding) AS similarity,
    p.metadata
FROM products p
WHERE p.status = 'active' 
AND p.embedding IS NOT NULL
AND 1 - (p.embedding <=> query_embedding) >= similarity_threshold
ORDER BY p.embedding <=> query_embedding
LIMIT match_count;
$$;

-- 15. Ellenőrzés
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'products' 
ORDER BY ordinal_position; 