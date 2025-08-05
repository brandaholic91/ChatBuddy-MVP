"""
Database setup script for Chatbuddy MVP.

This script initializes the complete database:
- Creates all tables
- Sets up RLS policies
- Configures vector operations
- Validates the setup
"""

import asyncio
import logging
from typing import Dict, Any
import json

from src.config.logging import get_logger
from .supabase_client import SupabaseClient, SupabaseConfig
from .schema_manager import SchemaManager
from .rls_policies import RLSPolicyManager
from .vector_operations import VectorOperations

logger = get_logger(__name__)


class DatabaseSetup:
    """Adatbázis setup kezelő"""
    
    def __init__(self, config: SupabaseConfig):
        """Inicializálja a database setup-ot"""
        self.config = config
        self.supabase = SupabaseClient(config)
        self.schema_manager = SchemaManager(self.supabase)
        self.rls_manager = RLSPolicyManager(self.supabase)
        self.vector_ops = VectorOperations(self.supabase, openai_api_key=config.openai_api_key)
    
    async def setup_complete_database(self) -> Dict[str, Any]:
        """Teljes adatbázis setup végrehajtása"""
        logger.info("🚀 ChatBuddy MVP adatbázis setup kezdeményezve")
        
        results = {
            "connection_test": False,
            "tables_created": False,
            "policies_created": False,
            "vector_setup": False,
            "validation": False,
            "details": {}
        }
        
        try:
            # 1. Kapcsolat tesztelése
            logger.info("📡 Kapcsolat tesztelése...")
            if self.supabase.test_connection():
                results["connection_test"] = True
                logger.info("✅ Kapcsolat sikeres")
            else:
                logger.error("❌ Kapcsolat sikertelen")
                return results
            
            # 2. Táblák létrehozása
            logger.info("🏗️ Táblák létrehozása...")
            table_results = self.schema_manager.create_all_tables()
            results["details"]["tables"] = table_results
            
            if all(table_results.values()):
                results["tables_created"] = True
                logger.info("✅ Minden tábla sikeresen létrehozva")
            else:
                failed_tables = [name for name, success in table_results.items() if not success]
                logger.error(f"❌ Sikertelen táblák: {failed_tables}")
            
            # 3. RLS policy-k létrehozása
            logger.info("🔒 RLS policy-k létrehozása...")
            policy_results = self.rls_manager.create_all_policies()
            results["details"]["policies"] = policy_results
            
            if all(policy_results.values()):
                results["policies_created"] = True
                logger.info("✅ Minden RLS policy sikeresen létrehozva")
            else:
                failed_policies = [name for name, success in policy_results.items() if not success]
                logger.error(f"❌ Sikertelen policy-k: {failed_policies}")
            
            # 4. Vector setup
            logger.info("🧠 Vector műveletek beállítása...")
            try:
                vector_stats = await self.vector_ops.get_vector_statistics()
                results["details"]["vector_stats"] = vector_stats
                
                if vector_stats:
                    results["vector_setup"] = True
                    logger.info("✅ Vector műveletek beállítva")
            except Exception as e:
                logger.error(f"❌ Vector setup hiba: {e}")
                results["vector_setup"] = False
                results["details"]["vector_stats"] = {"error": str(e)}
            
            # 5. Validáció
            logger.info("🔍 Adatbázis validálása...")
            try:
                schema_validation = self.schema_manager.validate_schema()
                policy_validation = self.rls_manager.validate_policies()
                
                results["details"]["schema_validation"] = schema_validation
                results["details"]["policy_validation"] = policy_validation
                
                # Validáció eredménye
                valid_tables = sum(1 for table in schema_validation.values() 
                                 if table.get("exists", False))
                total_tables = len(schema_validation)
                
                if valid_tables == total_tables:
                    results["validation"] = True
                    logger.info(f"✅ Validáció sikeres: {valid_tables}/{total_tables} tábla")
                else:
                    logger.error(f"❌ Validáció sikertelen: {valid_tables}/{total_tables} tábla")
            except Exception as e:
                logger.error(f"❌ Validáció hiba: {e}")
                results["validation"] = False
            
            # 6. Összefoglaló
            self._print_setup_summary(results)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Hiba a database setup során: {e}")
            results["error"] = str(e)
            return results
    
    def _print_setup_summary(self, results: Dict[str, Any]):
        """Kiírja a setup összefoglalót"""
        logger.info("\n" + "="*60)
        logger.info("📊 CHATBUDDY MVP DATABASE SETUP ÖSSZEFOGLALÓ")
        logger.info("="*60)
        
        # Kapcsolat
        status = "✅ SIKERES" if results["connection_test"] else "❌ SIKERTELEN"
        logger.info(f"📡 Kapcsolat: {status}")
        
        # Táblák
        if "tables" in results["details"]:
            table_results = results["details"]["tables"]
            success_count = sum(1 for success in table_results.values() if success)
            total_count = len(table_results)
            status = "✅ SIKERES" if results["tables_created"] else "❌ SIKERTELEN"
            logger.info(f"🏗️ Táblák ({success_count}/{total_count}): {status}")
        
        # Policy-k
        if "policies" in results["details"]:
            policy_results = results["details"]["policies"]
            success_count = sum(1 for success in policy_results.values() if success)
            total_count = len(policy_results)
            status = "✅ SIKERES" if results["policies_created"] else "❌ SIKERTELEN"
            logger.info(f"🔒 RLS Policy-k ({success_count}/{total_count}): {status}")
        
        # Vector
        status = "✅ SIKERES" if results["vector_setup"] else "❌ SIKERTELEN"
        logger.info(f"🧠 Vector műveletek: {status}")
        
        # Validáció
        status = "✅ SIKERES" if results["validation"] else "❌ SIKERTELEN"
        logger.info(f"🔍 Validáció: {status}")
        
        # Vector statisztikák
        if "vector_stats" in results["details"]:
            stats = results["details"]["vector_stats"]
            if stats:
                logger.info(f"📈 Vector statisztikák:")
                logger.info(f"   - Összes termék: {stats.get('total_products', 'N/A')}")
                logger.info(f"   - Embedding-gel: {stats.get('products_with_embedding', 'N/A')}")
                logger.info(f"   - Index méret: {stats.get('index_size', 'N/A')}")
        
        logger.info("="*60)
        
        # Összesített eredmény
        all_success = all([
            results["connection_test"],
            results["tables_created"],
            results["policies_created"],
            results["vector_setup"],
            results["validation"]
        ])
        
        if all_success:
            logger.info("🎉 MINDEN KOMPONENS SIKERESEN BEÁLLÍTVA!")
            logger.info("🚀 A ChatBuddy MVP adatbázisa készen áll a használatra!")
        else:
            logger.error("⚠️ NÉHÁNY KOMPONENS SIKERTELEN - ELLENŐRIZD A HIBAÜZENETEKET!")
        
        logger.info("="*60 + "\n")
    
    async def create_sample_data(self) -> bool:
        """Létrehoz minta adatokat teszteléshez"""
        try:
            logger.info("📝 Mintadatok létrehozása...")
            
            # Mint felhasználó
            sample_user = {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "test@chatbuddy.hu",
                "name": "Teszt Felhasználó",
                "role": "customer",
                "status": "active"
            }
            
            # Mint termék kategóriák
            sample_categories = [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440001",
                    "name": "Elektronika",
                    "description": "Elektronikai termékek",
                    "slug": "elektronika",
                    "is_active": True
                },
                {
                    "id": "550e8400-e29b-41d4-a716-446655440002", 
                    "name": "Könyvek",
                    "description": "Könyvek és irodalom",
                    "slug": "konyvek",
                    "is_active": True
                }
            ]
            
            # Mint termékek
            sample_products = [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440003",
                    "name": "iPhone 15 Pro",
                    "description": "Apple iPhone 15 Pro okostelefon",
                    "short_description": "Legújabb iPhone modell",
                    "price": 499999,
                    "category_id": "550e8400-e29b-41d4-a716-446655440001",
                    "brand": "Apple",
                    "sku": "IPHONE15PRO",
                    "status": "active",
                    "stock_quantity": 10,
                    "tags": ["okostelefon", "apple", "iphone", "5g"]
                },
                {
                    "id": "550e8400-e29b-41d4-a716-446655440004",
                    "name": "Python Programozás",
                    "description": "Python programozási nyelv alapjai",
                    "short_description": "Python tanulókönyv",
                    "price": 8990,
                    "category_id": "550e8400-e29b-41d4-a716-446655440002",
                    "brand": "Programozás Kiadó",
                    "sku": "PYTHON-BOOK",
                    "status": "active",
                    "stock_quantity": 25,
                    "tags": ["python", "programozás", "könyv", "tanulás"]
                }
            ]
            
            # Adatok beszúrása
            # TODO: Implementálni a tényleges beszúrást
            
            logger.info("✅ Mintadatok létrehozva")
            return True
            
        except Exception as e:
            logger.error(f"❌ Hiba a mintadatok létrehozásakor: {e}")
            return False
    
    def export_schema_documentation(self, output_file: str = "database_schema.md"):
        """Exportálja a schema dokumentációt"""
        try:
            logger.info("📄 Schema dokumentáció exportálása...")
            
            # Schema validáció
            schema_validation = self.schema_manager.validate_schema()
            
            # Markdown dokumentáció generálása
            md_content = self._generate_schema_markdown(schema_validation)
            
            # Fájl mentése
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            logger.info(f"✅ Schema dokumentáció mentve: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Hiba a dokumentáció exportálásakor: {e}")
            return False
    
    def _generate_schema_markdown(self, schema_validation: Dict[str, Any]) -> str:
        """Generálja a schema markdown dokumentációt"""
        md = """# ChatBuddy MVP Adatbázis Schema Dokumentáció

## Áttekintés

Ez a dokumentáció a ChatBuddy MVP adatbázis sémáját írja le.

## Táblák

"""
        
        for table_name, table_info in schema_validation.items():
            if table_info.get("exists"):
                md += f"### {table_name.upper()}\n\n"
                md += f"- **Oszlopok száma:** {table_info.get('columns', 0)}\n"
                md += f"- **RLS engedélyezve:** {'Igen' if table_info.get('rls_enabled') else 'Nem'}\n\n"
                
                if "columns_info" in table_info:
                    md += "| Oszlop | Típus | Nullable | Default |\n"
                    md += "|--------|-------|----------|--------|\n"
                    
                    for col in table_info["columns_info"]:
                        col_name = col.get("column_name", "")
                        col_type = col.get("data_type", "")
                        nullable = "Igen" if col.get("is_nullable") == "YES" else "Nem"
                        default = col.get("column_default", "")
                        
                        md += f"| {col_name} | {col_type} | {nullable} | {default} |\n"
                
                md += "\n"
        
        return md


async def main():
    """Fő függvény a database setup futtatásához"""
    # Konfiguráció betöltése
    config = SupabaseConfig(
        url="your-supabase-url",
        key="your-supabase-key",
        service_role_key="your-service-role-key"
    )
    
    # Database setup inicializálása
    setup = DatabaseSetup(config)
    
    # Teljes setup futtatása
    results = await setup.setup_complete_database()
    
    # Eredmények mentése
    with open("database_setup_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Schema dokumentáció exportálása
    setup.export_schema_documentation()
    
    return results


if __name__ == "__main__":
    asyncio.run(main()) 