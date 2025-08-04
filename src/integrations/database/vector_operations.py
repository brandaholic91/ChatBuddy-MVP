"""
Vector operations for Chatbuddy MVP.

This module provides vector database operations:
- OpenAI embeddings generation
- Vector similarity search
- Batch processing
- Performance optimization
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from decimal import Decimal

from src.config.logging import get_logger
from .supabase_client import SupabaseClient

logger = get_logger(__name__)


class VectorOperations:
    """Vector műveletek kezelő"""
    
    def __init__(self, supabase_client: SupabaseClient):
        """Inicializálja a vector operations kezelőt"""
        self.supabase = supabase_client
        self.embedding_dimension = 1536  # OpenAI text-embedding-ada-002
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generál egy embedding-et a megadott szövegből"""
        try:
            # TODO: OpenAI API integráció
            # Egyelőre mock embedding
            import random
            embedding = [random.uniform(-1, 1) for _ in range(self.embedding_dimension)]
            
            # Normalizálás
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = [x / norm for x in embedding]
            
            logger.debug(f"Embedding generálva {len(embedding)} dimenzióval")
            return embedding
            
        except Exception as e:
            logger.error(f"Hiba az embedding generálásakor: {e}")
            return None
    
    async def generate_product_embedding(self, product_data: Dict[str, Any]) -> Optional[List[float]]:
        """Generál embedding-et egy termékhez"""
        try:
            # Termék szöveges adatok összegyűjtése
            text_parts = []
            
            if product_data.get("name"):
                text_parts.append(product_data["name"])
            
            if product_data.get("description"):
                text_parts.append(product_data["description"])
            
            if product_data.get("short_description"):
                text_parts.append(product_data["short_description"])
            
            if product_data.get("brand"):
                text_parts.append(f"Brand: {product_data['brand']}")
            
            if product_data.get("tags"):
                text_parts.extend(product_data["tags"])
            
            # Szöveg összefűzése
            combined_text = " ".join(text_parts)
            
            if not combined_text.strip():
                logger.warning("Nincs szöveges adat az embedding generálásához")
                return None
            
            # Embedding generálása
            embedding = await self.generate_embedding(combined_text)
            return embedding
            
        except Exception as e:
            logger.error(f"Hiba a termék embedding generálásakor: {e}")
            return None
    
    async def update_product_embedding(self, product_id: str, product_data: Dict[str, Any]) -> bool:
        """Frissíti egy termék embedding-jét"""
        try:
            embedding = await self.generate_product_embedding(product_data)
            
            if not embedding:
                logger.warning(f"Nem sikerült embedding generálni a termékhez: {product_id}")
                return False
            
            # Embedding frissítése az adatbázisban
            query = """
            UPDATE products 
            SET embedding = %s, updated_at = NOW()
            WHERE id = %s;
            """
            
            self.supabase.execute_query(query, {
                "embedding": embedding,
                "product_id": product_id
            })
            
            logger.info(f"Termék embedding frissítve: {product_id}")
            return True
            
        except Exception as e:
            logger.error(f"Hiba a termék embedding frissítésekor: {e}")
            return False
    
    async def batch_update_product_embeddings(self, products: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Batch frissíti több termék embedding-jét"""
        results = {}
        
        for product in products:
            product_id = product.get("id")
            if not product_id:
                logger.warning("Termék ID hiányzik")
                continue
            
            success = await self.update_product_embedding(product_id, product)
            results[product_id] = success
            
            # Rate limiting
            await asyncio.sleep(0.1)
        
        success_count = sum(1 for success in results.values() if success)
        logger.info(f"Batch embedding frissítés: {success_count}/{len(products)} sikeres")
        
        return results
    
    async def search_similar_products(
        self, 
        query_text: str, 
        limit: int = 10, 
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Keres hasonló termékeket"""
        try:
            # Query embedding generálása
            query_embedding = await self.generate_embedding(query_text)
            
            if not query_embedding:
                logger.error("Nem sikerült query embedding generálni")
                return []
            
            # Vector similarity search
            query = """
            SELECT 
                id, name, description, price, brand, 
                embedding <=> %s AS similarity,
                metadata
            FROM products 
            WHERE status = 'active' 
            AND embedding IS NOT NULL
            ORDER BY embedding <=> %s
            LIMIT %s;
            """
            
            results = self.supabase.execute_query(query, {
                "query_embedding": query_embedding,
                "limit": limit
            })
            
            # Szűrés similarity threshold alapján
            filtered_results = []
            for result in results:
                similarity = 1 - float(result["similarity"])  # pgvector távolságot használ
                if similarity >= similarity_threshold:
                    result["similarity_score"] = similarity
                    filtered_results.append(result)
            
            logger.info(f"Similarity search: {len(filtered_results)} találat")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Hiba a similarity search során: {e}")
            return []
    
    async def search_products_by_category(
        self, 
        category_id: str, 
        query_text: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Keres termékeket kategória szerint"""
        try:
            query_embedding = await self.generate_embedding(query_text)
            
            if not query_embedding:
                return []
            
            query = """
            SELECT 
                id, name, description, price, brand, 
                embedding <=> %s AS similarity,
                metadata
            FROM products 
            WHERE status = 'active' 
            AND category_id = %s
            AND embedding IS NOT NULL
            ORDER BY embedding <=> %s
            LIMIT %s;
            """
            
            results = self.supabase.execute_query(query, {
                "query_embedding": query_embedding,
                "category_id": category_id,
                "limit": limit
            })
            
            # Similarity score kiszámítása
            for result in results:
                result["similarity_score"] = 1 - float(result["similarity"])
            
            logger.info(f"Category search: {len(results)} találat")
            return results
            
        except Exception as e:
            logger.error(f"Hiba a category search során: {e}")
            return []
    
    async def get_product_recommendations(
        self, 
        user_id: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Termékajánlások generálása felhasználói preferenciák alapján"""
        try:
            # Felhasználói preferenciák lekérdezése
            user_query = """
            SELECT 
                up.product_recommendations,
                up.personalized_offers,
                u.metadata as user_metadata
            FROM user_preferences up
            JOIN users u ON up.user_id = u.id
            WHERE up.user_id = %s;
            """
            
            user_prefs = self.supabase.execute_query(user_query, {"user_id": user_id})
            
            if not user_prefs:
                logger.warning(f"Felhasználói preferenciák nem találhatók: {user_id}")
                return []
            
            prefs = user_prefs[0]
            
            if not prefs.get("product_recommendations", True):
                logger.info(f"Termékajánlások le vannak tiltva: {user_id}")
                return []
            
            # Felhasználói interakciók alapján ajánlás
            # TODO: Implementálni a felhasználói viselkedés elemzését
            
            # Egyelőre random ajánlások
            query = """
            SELECT 
                id, name, description, price, brand,
                is_featured, is_bestseller, is_new,
                metadata
            FROM products 
            WHERE status = 'active'
            ORDER BY RANDOM()
            LIMIT %s;
            """
            
            results = self.supabase.execute_query(query, {"limit": limit})
            
            logger.info(f"Termékajánlások generálva: {len(results)} termék")
            return results
            
        except Exception as e:
            logger.error(f"Hiba a termékajánlások generálásakor: {e}")
            return []
    
    async def hybrid_search(
        self, 
        query_text: str, 
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Hibrid keresés: vector + szöveges szűrők"""
        try:
            query_embedding = await self.generate_embedding(query_text)
            
            if not query_embedding:
                return []
            
            # Alap query
            base_query = """
            SELECT 
                id, name, description, price, brand, category_id,
                embedding <=> %s AS similarity,
                metadata
            FROM products 
            WHERE status = 'active' 
            AND embedding IS NOT NULL
            """
            
            params = {"query_embedding": query_embedding}
            
            # Szűrők hozzáadása
            if filters:
                if filters.get("category_id"):
                    base_query += " AND category_id = %s"
                    params["category_id"] = filters["category_id"]
                
                if filters.get("brand"):
                    base_query += " AND brand = %s"
                    params["brand"] = filters["brand"]
                
                if filters.get("min_price"):
                    base_query += " AND price >= %s"
                    params["min_price"] = filters["min_price"]
                
                if filters.get("max_price"):
                    base_query += " AND price <= %s"
                    params["max_price"] = filters["max_price"]
                
                if filters.get("in_stock"):
                    base_query += " AND stock_quantity > 0"
            
            # Rendezés és limit
            base_query += " ORDER BY embedding <=> %s LIMIT %s;"
            params["limit"] = limit
            
            results = self.supabase.execute_query(base_query, params)
            
            # Similarity score kiszámítása
            for result in results:
                result["similarity_score"] = 1 - float(result["similarity"])
            
            logger.info(f"Hibrid keresés: {len(results)} találat")
            return results
            
        except Exception as e:
            logger.error(f"Hiba a hibrid keresés során: {e}")
            return []
    
    async def optimize_vector_indexes(self) -> bool:
        """Optimalizálja a vector indexeket"""
        try:
            # HNSW index paraméterek finomhangolása
            optimization_queries = [
                "SET maintenance_work_mem = '2GB';",
                "SET work_mem = '256MB';",
                "SET shared_buffers = '1GB';",
                "SET effective_cache_size = '4GB';",
                
                # HNSW index újraépítése
                """
                REINDEX INDEX CONCURRENTLY idx_products_embedding;
                """,
                
                # Statisztikák frissítése
                "ANALYZE products;"
            ]
            
            for query in optimization_queries:
                self.supabase.execute_query(query)
            
            logger.info("Vector indexek optimalizálva")
            return True
            
        except Exception as e:
            logger.error(f"Hiba a vector indexek optimalizálásakor: {e}")
            return False
    
    async def get_vector_statistics(self) -> Dict[str, Any]:
        """Lekéri a vector adatbázis statisztikáit"""
        try:
            stats = {}
            
            # Termékek száma embedding-gel
            query = """
            SELECT 
                COUNT(*) as total_products,
                COUNT(embedding) as products_with_embedding,
                COUNT(*) - COUNT(embedding) as products_without_embedding
            FROM products;
            """
            
            product_stats = self.supabase.execute_query(query)
            if product_stats:
                stats.update(product_stats[0])
            
            # Index méret
            query = """
            SELECT 
                pg_size_pretty(pg_relation_size('idx_products_embedding')) as index_size
            """
            
            index_stats = self.supabase.execute_query(query)
            if index_stats:
                stats["index_size"] = index_stats[0]["index_size"]
            
            # Embedding dimenziók
            query = """
            SELECT 
                vector_dims(embedding) as dimensions
            FROM products 
            WHERE embedding IS NOT NULL 
            LIMIT 1;
            """
            
            dim_stats = self.supabase.execute_query(query)
            if dim_stats:
                stats["embedding_dimensions"] = dim_stats[0]["dimensions"]
            
            logger.info(f"Vector statisztikák lekérdezve")
            return stats
            
        except Exception as e:
            logger.error(f"Hiba a vector statisztikák lekérdezésekor: {e}")
            return {}
    
    async def cleanup_orphaned_embeddings(self) -> int:
        """Törli a árva embedding-eket"""
        try:
            # Termékek embedding-jeinek tisztítása
            query = """
            UPDATE products 
            SET embedding = NULL 
            WHERE embedding IS NOT NULL 
            AND (name IS NULL OR name = '')
            AND (description IS NULL OR description = '');
            """
            
            result = self.supabase.execute_query(query)
            
            logger.info("Árva embedding-ek törölve")
            return 1  # TODO: Return actual affected rows count
            
        except Exception as e:
            logger.error(f"Hiba az árva embedding-ek törlésekor: {e}")
            return 0 