#!/usr/bin/env python3
"""
Vector Database Integration Test Script

Ez a script teszteli a teljes Vector Database Integration implementációt:
- OpenAI embeddings API
- pgvector similarity search
- Batch processing
- Performance monitoring
"""

import asyncio
import os
import sys
from typing import Dict, Any, List
import logging
from dotenv import load_dotenv

# .env fájl betöltése
load_dotenv()

# Projekt root hozzáadása a path-hoz
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.integrations.database.supabase_client import SupabaseClient
from src.integrations.database.vector_operations import VectorOperations
from src.integrations.database.schema_manager import SchemaManager
from src.config.logging import get_logger

logger = get_logger(__name__)


class VectorIntegrationTester:
    """Vector Database Integration tesztelő"""
    
    def __init__(self):
        """Inicializálja a tesztelőt"""
        self.supabase_client = SupabaseClient()
        self.vector_ops = VectorOperations(self.supabase_client)
        self.schema_manager = SchemaManager(self.supabase_client)
        
        # Teszt adatok
        self.test_products = [
            {
                "id": "test-product-1",
                "name": "iPhone 15 Pro Max",
                "description": "Apple iPhone 15 Pro Max 256GB Titanium, A17 Pro chip, 48MP kamera",
                "short_description": "Legújabb iPhone Pro Max modell",
                "brand": "Apple",
                "category": "Smartphones",
                "tags": ["iPhone", "Apple", "Smartphone", "5G", "Titanium"],
                "price": 499999,
                "status": "active"
            },
            {
                "id": "test-product-2", 
                "name": "Samsung Galaxy S24 Ultra",
                "description": "Samsung Galaxy S24 Ultra 256GB, Snapdragon 8 Gen 3, S Pen támogatás",
                "short_description": "Samsung flagship telefon S Pen-nel",
                "brand": "Samsung",
                "category": "Smartphones",
                "tags": ["Samsung", "Galaxy", "Smartphone", "S Pen", "Android"],
                "price": 449999,
                "status": "active"
            },
            {
                "id": "test-product-3",
                "name": "MacBook Pro 16 inch M3 Pro",
                "description": "Apple MacBook Pro 16 inch M3 Pro chip, 18GB RAM, 512GB SSD",
                "short_description": "Professzionális MacBook Pro laptop",
                "brand": "Apple",
                "category": "Laptops",
                "tags": ["MacBook", "Apple", "Laptop", "M3 Pro", "Professional"],
                "price": 899999,
                "status": "active"
            },
            {
                "id": "test-product-4",
                "name": "Dell XPS 15",
                "description": "Dell XPS 15 9530, Intel Core i7-13700H, 16GB RAM, 512GB SSD",
                "short_description": "Dell premium laptop",
                "brand": "Dell",
                "category": "Laptops", 
                "tags": ["Dell", "XPS", "Laptop", "Intel", "Windows"],
                "price": 699999,
                "status": "active"
            },
            {
                "id": "test-product-5",
                "name": "Sony WH-1000XM5",
                "description": "Sony WH-1000XM5 vezetéknélküli zajszűrős fejhallgató",
                "short_description": "Sony premium fejhallgató",
                "brand": "Sony",
                "category": "Audio",
                "tags": ["Sony", "Headphones", "Wireless", "Noise Cancelling", "Audio"],
                "price": 129999,
                "status": "active"
            }
        ]
    
    async def test_supabase_connection(self) -> bool:
        """Teszteli a Supabase kapcsolatot"""
        try:
            logger.info("🔗 Supabase kapcsolat tesztelése...")
            
            success = self.supabase_client.test_connection()
            
            if success:
                logger.info("✅ Supabase kapcsolat sikeres")
                return True
            else:
                logger.error("❌ Supabase kapcsolat sikertelen")
                return False
                
        except Exception as e:
            logger.error(f"❌ Supabase kapcsolat hiba: {e}")
            return False
    
    async def test_pgvector_extension(self) -> bool:
        """Teszteli a pgvector extension-t"""
        try:
            logger.info("🔧 pgvector extension tesztelése...")
            
            success = self.schema_manager.setup_pgvector_extension()
            
            if success:
                logger.info("✅ pgvector extension sikeresen beállítva")
                return True
            else:
                logger.error("❌ pgvector extension beállítása sikertelen")
                return False
                
        except Exception as e:
            logger.error(f"❌ pgvector extension hiba: {e}")
            return False
    
    async def test_database_schema(self) -> Dict[str, bool]:
        """Teszteli az adatbázis sémát"""
        try:
            logger.info("🏗️ Adatbázis séma beállítása...")
            
            results = self.schema_manager.setup_complete_schema()
            
            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)
            
            logger.info(f"📊 Séma beállítás: {success_count}/{total_count} sikeres")
            
            for component, success in results.items():
                if success:
                    logger.info(f"✅ {component}")
                else:
                    logger.error(f"❌ {component}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Séma beállítás hiba: {e}")
            return {"error": False}
    
    async def test_openai_embeddings(self) -> bool:
        """Teszteli az OpenAI embeddings API-t"""
        try:
            logger.info("🧠 OpenAI embeddings API tesztelése...")
            
            # Egyszerű embedding teszt
            test_text = "iPhone 15 Pro Max smartphone"
            embedding = await self.vector_ops.generate_embedding(test_text)
            
            if embedding and len(embedding) == 1536:
                logger.info(f"✅ OpenAI embedding sikeres: {len(embedding)} dimenzió")
                return True
            else:
                logger.error("❌ OpenAI embedding sikertelen")
                return False
                
        except Exception as e:
            logger.error(f"❌ OpenAI embeddings hiba: {e}")
            return False
    
    async def test_batch_embeddings(self) -> bool:
        """Teszteli a batch embedding generálást"""
        try:
            logger.info("📦 Batch embedding generálás tesztelése...")
            
            test_texts = [
                "iPhone 15 Pro Max smartphone",
                "Samsung Galaxy S24 Ultra",
                "MacBook Pro laptop",
                "Sony fejhallgató"
            ]
            
            embeddings = await self.vector_ops.generate_embeddings_batch(test_texts)
            
            valid_embeddings = [emb for emb in embeddings if emb is not None]
            
            if len(valid_embeddings) == len(test_texts):
                logger.info(f"✅ Batch embedding sikeres: {len(valid_embeddings)}/{len(test_texts)}")
                return True
            else:
                logger.warning(f"⚠️ Batch embedding részleges: {len(valid_embeddings)}/{len(test_texts)}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Batch embedding hiba: {e}")
            return False
    
    async def test_product_embeddings(self) -> bool:
        """Teszteli a termék embedding generálást"""
        try:
            logger.info("🛍️ Termék embedding generálás tesztelése...")
            
            test_product = self.test_products[0]
            embedding = await self.vector_ops.generate_product_embedding(test_product)
            
            if embedding and len(embedding) == 1536:
                logger.info(f"✅ Termék embedding sikeres: {len(embedding)} dimenzió")
                return True
            else:
                logger.error("❌ Termék embedding sikertelen")
                return False
                
        except Exception as e:
            logger.error(f"❌ Termék embedding hiba: {e}")
            return False
    
    async def test_similarity_search(self) -> bool:
        """Teszteli a similarity search-t"""
        try:
            logger.info("🔍 Similarity search tesztelése...")
            
            # Először generálunk egy query embedding-et
            query = "okos telefon"
            results = await self.vector_ops.search_similar_products(query, limit=5)
            
            if isinstance(results, list):
                logger.info(f"✅ Similarity search sikeres: {len(results)} találat")
                return True
            else:
                logger.error("❌ Similarity search sikertelen")
                return False
                
        except Exception as e:
            logger.error(f"❌ Similarity search hiba: {e}")
            return False
    
    async def test_vector_statistics(self) -> bool:
        """Teszteli a vector statisztikákat"""
        try:
            logger.info("📊 Vector statisztikák tesztelése...")
            
            stats = await self.vector_ops.get_vector_statistics()
            
            if stats:
                logger.info("✅ Vector statisztikák sikeresen lekérdezve")
                logger.info(f"📈 Statisztikák: {stats}")
                return True
            else:
                logger.error("❌ Vector statisztikák lekérdezése sikertelen")
                return False
                
        except Exception as e:
            logger.error(f"❌ Vector statisztikák hiba: {e}")
            return False
    
    async def test_schema_status(self) -> bool:
        """Teszteli a séma állapotát"""
        try:
            logger.info("🔍 Séma állapot tesztelése...")
            
            status = self.schema_manager.get_schema_status()
            
            if status:
                logger.info("✅ Séma állapot sikeresen lekérdezve")
                logger.info(f"📋 Állapot: {status}")
                return True
            else:
                logger.error("❌ Séma állapot lekérdezése sikertelen")
                return False
                
        except Exception as e:
            logger.error(f"❌ Séma állapot hiba: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Futtatja az összes tesztet"""
        logger.info("🚀 Vector Database Integration tesztek indítása...")
        
        results = {}
        
        # 1. Kapcsolat teszt
        results["supabase_connection"] = await self.test_supabase_connection()
        
        if not results["supabase_connection"]:
            logger.error("❌ Supabase kapcsolat sikertelen, tesztek leállítva")
            return results
        
        # 2. pgvector extension
        results["pgvector_extension"] = await self.test_pgvector_extension()
        
        # 3. Adatbázis séma
        schema_results = await self.test_database_schema()
        results.update(schema_results)
        
        # 4. OpenAI embeddings
        results["openai_embeddings"] = await self.test_openai_embeddings()
        
        # 5. Batch embeddings
        results["batch_embeddings"] = await self.test_batch_embeddings()
        
        # 6. Termék embeddings
        results["product_embeddings"] = await self.test_product_embeddings()
        
        # 7. Similarity search
        results["similarity_search"] = await self.test_similarity_search()
        
        # 8. Vector statisztikák
        results["vector_statistics"] = await self.test_vector_statistics()
        
        # 9. Séma állapot
        results["schema_status"] = await self.test_schema_status()
        
        # Összefoglaló
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        logger.info(f"\n📊 TESZT EREDMÉNYEK: {success_count}/{total_count} sikeres")
        
        for test_name, success in results.items():
            if success:
                logger.info(f"✅ {test_name}")
            else:
                logger.error(f"❌ {test_name}")
        
        return results


async def main():
    """Fő függvény"""
    try:
        # Környezeti változók ellenőrzése
        required_env_vars = [
            "SUPABASE_URL",
            "SUPABASE_ANON_KEY", 
            "SUPABASE_SERVICE_KEY",
            "OPENAI_API_KEY"
        ]
        
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"❌ Hiányzó környezeti változók: {missing_vars}")
            logger.error("Kérlek állítsd be ezeket a .env fájlban")
            return
        
        # Tesztelő inicializálása
        tester = VectorIntegrationTester()
        
        # Tesztek futtatása
        results = await tester.run_all_tests()
        
        # Eredmények kiértékelése
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        if success_count == total_count:
            logger.info("\n🎉 MINDEN TESZT SIKERES!")
            logger.info("✅ Vector Database Integration teljesen működőképes")
        else:
            logger.warning(f"\n⚠️ {total_count - success_count} teszt sikertelen")
            logger.warning("Kérlek ellenőrizd a hibákat és próbáld újra")
        
    except Exception as e:
        logger.error(f"❌ Kritikus hiba: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Logging beállítása
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Async main futtatása
    asyncio.run(main()) 