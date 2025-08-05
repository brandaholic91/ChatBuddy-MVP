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
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from decimal import Decimal
import os

from openai import AsyncOpenAI
from src.config.logging import get_logger
from .supabase_client import SupabaseClient
from src.integrations.cache import get_redis_cache_service

logger = get_logger(__name__)


class VectorOperations:
    """Vector műveletek kezelő"""
    
    def __init__(self, supabase_client: SupabaseClient, openai_api_key: str):
        """Inicializálja a vector operations kezelőt"""
        self.supabase = supabase_client
        self.embedding_dimension = 1536  # OpenAI text-embedding-3-small
        if not openai_api_key:
            raise ValueError("OpenAI API kulcs szükséges")
        self.openai_client = AsyncOpenAI(
            api_key=openai_api_key
        )
        self.embedding_model = "text-embedding-3-small"
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generál egy embedding-et a megadott szövegből OpenAI API-val"""
        try:
            if not text.strip():
                logger.warning("Üres szöveg az embedding generálásához")
                return None
            
            # Cache ellenőrzése
            try:
                cache_service = await get_redis_cache_service()
                text_hash = hashlib.md5(text.encode()).hexdigest()
                cached_embedding = await cache_service.performance_cache.get_cached_embedding(text_hash)
                
                if cached_embedding:
                    logger.debug(f"Cache-elt embedding használva: {text_hash}")
                    return cached_embedding
            except Exception as cache_error:
                logger.warning(f"Cache hiba, OpenAI API használata: {cache_error}")
            
            # OpenAI embeddings API hívás
            response = await self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            
            embedding = response.data[0].embedding
            
            # Cache-elés
            try:
                if cache_service:
                    text_hash = hashlib.md5(text.encode()).hexdigest()
                    await cache_service.performance_cache.cache_embedding(text_hash, embedding)
            except Exception as cache_error:
                logger.warning(f"Embedding cache-elés hiba: {cache_error}")
            
            logger.debug(f"Embedding generálva {len(embedding)} dimenzióval")
            return embedding
            
        except Exception as e:
            logger.error(f"Hiba az embedding generálásakor: {e}")
            return None
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Batch embedding generálás több szöveghez"""
        try:
            if not texts:
                return []
            
            # Szűrjük ki az üres szövegeket
            valid_texts = [text for text in texts if text.strip()]
            if not valid_texts:
                logger.warning("Nincs érvényes szöveg a batch embedding generáláshoz")
                return [None] * len(texts)
            
            # OpenAI batch embeddings API hívás
            response = await self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=valid_texts
            )
            
            embeddings = [data.embedding for data in response.data]
            
            # Visszaadunk None-t az üres szövegekhez
            result = []
            text_index = 0
            for original_text in texts:
                if original_text.strip():
                    result.append(embeddings[text_index])
                    text_index += 1
                else:
                    result.append(None)
            
            logger.info(f"Batch embedding generálva: {len(embeddings)}/{len(texts)} sikeres")
            return result
            
        except Exception as e:
            logger.error(f"Hiba a batch embedding generálásakor: {e}")
            return [None] * len(texts)
    
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
                if isinstance(product_data["tags"], list):
                    text_parts.extend(product_data["tags"])
                else:
                    text_parts.append(str(product_data["tags"]))
            
            if product_data.get("category"):
                text_parts.append(f"Category: {product_data['category']}")
            
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
            client = self.supabase.get_client()
            
            result = client.table("products").update({
                "embedding": embedding,
                "updated_at": "now()"
            }).eq("id", product_id).execute()
            
            if result.data:
                logger.info(f"Termék embedding frissítve: {product_id}")
                return True
            else:
                logger.warning(f"Termék nem található: {product_id}")
                return False
            
        except Exception as e:
            logger.error(f"Hiba a termék embedding frissítésekor: {e}")
            return False
    
    async def batch_update_product_embeddings(self, products: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Batch frissíti több termék embedding-jét"""
        results = {}
        
        # Batch embedding generálás
        product_texts = []
        for product in products:
            text_parts = []
            
            if product.get("name"):
                text_parts.append(product["name"])
            if product.get("description"):
                text_parts.append(product["description"])
            if product.get("short_description"):
                text_parts.append(product["short_description"])
            if product.get("brand"):
                text_parts.append(f"Brand: {product['brand']}")
            if product.get("tags"):
                if isinstance(product["tags"], list):
                    text_parts.extend(product["tags"])
                else:
                    text_parts.append(str(product["tags"]))
            if product.get("category"):
                text_parts.append(f"Category: {product['category']}")
            
            combined_text = " ".join(text_parts)
            product_texts.append(combined_text)
        
        # Batch embedding generálás
        embeddings = await self.generate_embeddings_batch(product_texts)
        
        # Adatbázis frissítések
        client = self.supabase.get_client()
        
        for i, product in enumerate(products):
            product_id = product.get("id")
            if not product_id:
                logger.warning("Termék ID hiányzik")
                results[f"product_{i}"] = False
                continue
            
            embedding = embeddings[i]
            if not embedding:
                logger.warning(f"Nem sikerült embedding generálni a termékhez: {product_id}")
                results[product_id] = False
                continue
            
            try:
                result = client.table("products").update({
                    "embedding": embedding,
                    "updated_at": "now()"
                }).eq("id", product_id).execute()
                
                results[product_id] = bool(result.data)
                
            except Exception as e:
                logger.error(f"Hiba a termék embedding frissítésekor: {product_id} - {e}")
                results[product_id] = False
        
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
            # Cache ellenőrzése
            try:
                cache_service = await get_redis_cache_service()
                query_hash = hashlib.md5(f"{query_text}:{limit}:{similarity_threshold}".encode()).hexdigest()
                cached_results = await cache_service.performance_cache.get_cached_search_result(query_hash)
                
                if cached_results:
                    logger.debug(f"Cache-elt search result használva: {query_hash}")
                    return cached_results
            except Exception as cache_error:
                logger.warning(f"Cache hiba, adatbázis keresés: {cache_error}")
            
            # Query embedding generálása
            query_embedding = await self.generate_embedding(query_text)
            
            if not query_embedding:
                logger.error("Nem sikerült query embedding generálni")
                return []
            
            # Vector similarity search pgvector-rel
            client = self.supabase.get_client()
            
            # pgvector similarity search query
            result = await client.rpc(
                "search_products",
                {
                    "query_embedding": query_embedding,
                    "similarity_threshold": similarity_threshold,
                    "match_count": limit
                }
            ).execute()
            
            if not result.data:
                logger.info("Nincs találat a similarity search-ben")
                return []
            
            # Szűrés similarity threshold alapján
            filtered_results = []
            for item in result.data:
                similarity = float(item.get("similarity", 0))
                if similarity >= similarity_threshold:
                    item["similarity_score"] = similarity
                    filtered_results.append(item)
            
            # Cache-elés
            try:
                if cache_service:
                    query_hash = hashlib.md5(f"{query_text}:{limit}:{similarity_threshold}".encode()).hexdigest()
                    await cache_service.performance_cache.cache_search_result(query_hash, filtered_results)
            except Exception as cache_error:
                logger.warning(f"Search result cache-elés hiba: {cache_error}")
            
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
            
            client = self.supabase.get_client()
            
            # Kategória-specifikus similarity search
            result = await client.rpc(
                "search_products_by_category",
                {
                    "query_embedding": query_embedding,
                    "category_id": category_id,
                    "match_count": limit
                }
            ).execute()
            
            if not result.data:
                return []
            
            # Similarity score kiszámítása
            for item in result.data:
                item["similarity_score"] = float(item.get("similarity", 0))
            
            logger.info(f"Category search: {len(result.data)} találat")
            return result.data
            
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
            client = self.supabase.get_client()
            
            # Felhasználói preferenciák lekérdezése
            user_prefs_result = await client.table("user_preferences").select(
                "product_recommendations, personalized_offers"
            ).eq("user_id", user_id).execute()
            
            if not user_prefs_result.data:
                logger.warning(f"Felhasználói preferenciák nem találhatók: {user_id}")
                return []
            
            prefs = user_prefs_result.data[0]
            
            if not prefs.get("product_recommendations", True):
                logger.info(f"Termékajánlások le vannak tiltva: {user_id}")
                return []
            
            # Felhasználói interakciók alapján ajánlás
            # TODO: Implementálni a felhasználói viselkedés elemzését
            
            # Egyelőre featured/bestseller termékek
            result = client.table("products").select(
                "id, name, description, price, brand, is_featured, is_bestseller, is_new, metadata"
            ).eq("status", "active").order("is_featured", desc=True).order("is_bestseller", desc=True).limit(limit).execute()
            
            logger.info(f"Termékajánlások generálva: {len(result.data)} termék")
            return result.data
            
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
            
            client = self.supabase.get_client()
            
            # Alap query builder
            query = client.table("products").select(
                "id, name, description, price, brand, category_id, metadata"
            ).eq("status", "active")
            
            # Szűrők hozzáadása
            if filters:
                if filters.get("category_id"):
                    query = query.eq("category_id", filters["category_id"])
                
                if filters.get("brand"):
                    query = query.eq("brand", filters["brand"])
                
                if filters.get("min_price"):
                    query = query.gte("price", filters["min_price"])
                
                if filters.get("max_price"):
                    query = query.lte("price", filters["max_price"])
                
                if filters.get("in_stock"):
                    query = query.gt("stock_quantity", 0)
            
            # Vector similarity search hozzáadása
            # Megjegyzés: Ez egy egyszerűsített implementáció
            # A teljes hibrid search-hez custom RPC függvény kell
            
            result = query.limit(limit).execute()
            
            if not result.data:
                return []
            
            # Similarity score kiszámítása (egyszerűsített)
            for item in result.data:
                # TODO: Implementálni a valódi similarity számítást
                item["similarity_score"] = 0.8  # Placeholder
            
            logger.info(f"Hibrid keresés: {len(result.data)} találat")
            return result.data
            
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
                "REINDEX INDEX CONCURRENTLY idx_products_embedding;",
                
                # Statisztikák frissítése
                "ANALYZE products;"
            ]
            
            for query in optimization_queries:
                try:
                    self.supabase.execute_query(query)
                except Exception as e:
                    logger.warning(f"Index optimalizálási hiba: {e}")
                    continue
            
            logger.info("Vector indexek optimalizálva")
            return True
            
        except Exception as e:
            logger.error(f"Hiba a vector indexek optimalizálásakor: {e}")
            return False
    
    async def get_vector_statistics(self) -> Dict[str, Any]:
        """Lekéri a vector adatbázis statisztikáit"""
        try:
            stats = {}
            client = self.supabase.get_client()
            
            # Termékek száma embedding-gel
            result = client.table("products").select("id, embedding").execute()
            
            total_products = len(result.data)
            products_with_embedding = sum(1 for item in result.data if item.get("embedding"))
            products_without_embedding = total_products - products_with_embedding
            
            stats.update({
                "total_products": total_products,
                "products_with_embedding": products_with_embedding,
                "products_without_embedding": products_without_embedding,
                "embedding_coverage": f"{(products_with_embedding/total_products*100):.1f}%" if total_products > 0 else "0%"
            })
            
            # Embedding dimenziók
            if products_with_embedding > 0:
                sample_embedding = next(item["embedding"] for item in result.data if item.get("embedding"))
                stats["embedding_dimensions"] = len(sample_embedding)
            
            logger.info(f"Vector statisztikák lekérdezve")
            return stats
            
        except Exception as e:
            logger.error(f"Hiba a vector statisztikák lekérdezésekor: {e}")
            return {}
    
    async def cleanup_orphaned_embeddings(self) -> int:
        """Törli a árva embedding-eket"""
        try:
            client = self.supabase.get_client()
            
            # Termékek embedding-jeinek tisztítása
            result = client.table("products").update({
                "embedding": None
            }).or_("name.is.null,name.eq.''").or_("description.is.null,description.eq.''").execute()
            
            cleaned_count = len(result.data) if result.data else 0
            
            logger.info(f"Árva embedding-ek törölve: {cleaned_count}")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Hiba az árva embedding-ek törlésekor: {e}")
            return 0 