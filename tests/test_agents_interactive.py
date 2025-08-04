#!/usr/bin/env python3
"""
Interaktív Agent Tesztelés - ChatBuddy MVP

Ez a script lehetővé teszi az agentek közvetlen tesztelését különböző kérdésekkel.
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.workflows.coordinator import process_coordinator_message
from src.models.user import User
from src.config.audit_logging import get_audit_logger
from src.config.gdpr_compliance import get_gdpr_compliance
from src.config.security import get_threat_detector, InputValidator

# Mock dependencies for testing
class MockSupabaseClient:
    """Mock Supabase client for testing."""
    
    async def get_user(self, user_id: str) -> Dict[str, Any]:
        return {
            "id": user_id,
            "name": "Teszt Felhasználó",
            "email": "teszt@example.com",
            "preferences": {
                "language": "hu",
                "notifications": True
            }
        }
    
    async def get_user_orders(self, user_id: str) -> list:
        return [
            {
                "id": "ORD-001",
                "status": "processing",
                "items": [{"name": "iPhone 15", "price": 299000}],
                "total": 299000,
                "created_at": "2024-01-15T10:30:00Z"
            }
        ]

class MockWebshopAPI:
    """Mock webshop API for testing."""
    
    async def search_products(self, query: str, category: str = None) -> list:
        products = [
            {
                "id": "PROD-001",
                "name": "iPhone 15 Pro",
                "price": 399000,
                "category": "telefon",
                "description": "Apple iPhone 15 Pro 128GB",
                "availability": "in_stock"
            },
            {
                "id": "PROD-002", 
                "name": "Samsung Galaxy S24",
                "price": 299000,
                "category": "telefon",
                "description": "Samsung Galaxy S24 256GB",
                "availability": "in_stock"
            }
        ]
        
        if category:
            return [p for p in products if p["category"] == category]
        return products
    
    async def get_product(self, product_id: str) -> Dict[str, Any]:
        return {
            "id": product_id,
            "name": "iPhone 15 Pro",
            "price": 399000,
            "category": "telefon",
            "description": "Apple iPhone 15 Pro 128GB",
            "availability": "in_stock",
            "specifications": {
                "screen": "6.1 inch",
                "storage": "128GB",
                "color": "Titanium"
            }
        }

async def setup_test_environment():
    """Test környezet beállítása."""
    print("🔧 Test környezet beállítása...")
    
    # Mock dependencies
    supabase_client = MockSupabaseClient()
    webshop_api = MockWebshopAPI()
    
    # Initialize security components
    threat_detector = get_threat_detector()
    audit_logger = get_audit_logger()
    gdpr_compliance = get_gdpr_compliance()
    
    print("✅ Test környezet beállítva")
    return {
        "supabase_client": supabase_client,
        "webshop_api": webshop_api,
        "threat_detector": threat_detector,
        "audit_logger": audit_logger,
        "gdpr_compliance": gdpr_compliance
    }

async def test_agent_response(message: str, user_id: str = "test_user_123") -> None:
    """Teszteli egy üzenet feldolgozását az agentekkel."""
    
    print(f"\n🤖 AGENT TESZT: '{message}'")
    print("=" * 60)
    
    try:
        # Create test user
        user = User(id=user_id, email="teszt@example.com")
        
        # Process message through coordinator
        start_time = datetime.now()
        response = await process_coordinator_message(
            message=message,
            user=user,
            session_id="test_session_123"
        )
        end_time = datetime.now()
        
        # Display results
        print(f"⏱️  Feldolgozási idő: {(end_time - start_time).total_seconds():.2f} másodperc")
        print(f"🤖 Használt agent: {response.agent_type.value}")
        print(f"🎯 Confidence: {response.confidence:.2f}")
        print(f"📝 Válasz: {response.response_text}")
        
        if response.metadata:
            print(f"📊 Metadata: {response.metadata}")
            
    except Exception as e:
        print(f"❌ Hiba: {str(e)}")
        import traceback
        traceback.print_exc()

async def interactive_test():
    """Interaktív tesztelés."""
    
    print("🚀 ChatBuddy MVP - Interaktív Agent Tesztelés")
    print("=" * 60)
    
    # Setup test environment
    await setup_test_environment()
    
    # Test scenarios
    test_scenarios = [
        # Termék kérdések
        "Milyen telefonok vannak?",
        "Mennyibe kerül az iPhone 15?",
        "Van Samsung telefon készleten?",
        "Mutasd a legdrágább telefont!",
        
        # Rendelés kérdések
        "Mi a rendelésem státusza?",
        "Mikor érkezik meg a csomagom?",
        "Melyik rendelésem van folyamatban?",
        "Szeretném követni a szállítást",
        
        # Ajánlások
        "Ajánlj nekem egy telefont",
        "Milyen telefonok népszerűek?",
        "Mit ajánlasz 300 ezer forintért?",
        "Hasonló telefonok az iPhone-hoz",
        
        # Marketing kérdések
        "Milyen akciók vannak?",
        "Van kedvezményes kód?",
        "Szeretnék feliratkozni a hírlevélre",
        "Milyen promóciók érhetők el?",
        
        # Általános kérdések
        "Szia! Hogy vagy?",
        "Mit tudsz csinálni?",
        "Hogyan tudok segítséget kapni?",
        "Mik a nyitvatartási idők?",
        
        # Komplex kérdések
        "Szeretnék egy telefont venni, ami jó kamera, és van rá kedvezmény?",
        "Mikor érkezik meg a rendelésem és milyen telefonok vannak akciósan?",
        "Ajánlj egy telefont és mutasd meg a rendelésem státuszát is"
    ]
    
    print(f"\n📋 {len(test_scenarios)} teszt forgatókönyv betöltve")
    print("\nVálassz opciót:")
    print("1. Futtasd az összes tesztet")
    print("2. Interaktív mód (saját kérdések)")
    print("3. Kilépés")
    
    while True:
        try:
            choice = input("\nVálasztás (1-3): ").strip()
            
            if choice == "1":
                print(f"\n🔄 Futtatom az összes tesztet ({len(test_scenarios)} db)...")
                for i, scenario in enumerate(test_scenarios, 1):
                    print(f"\n--- TESZT {i}/{len(test_scenarios)} ---")
                    await test_agent_response(scenario)
                    await asyncio.sleep(1)  # Small delay between tests
                print(f"\n✅ Összes teszt befejezve!")
                
            elif choice == "2":
                print("\n💬 Interaktív mód - írd be a kérdéseket (vagy 'kilép' a kilépéshez)")
                while True:
                    user_input = input("\nKérdés: ").strip()
                    if user_input.lower() in ['kilép', 'exit', 'quit']:
                        break
                    if user_input:
                        await test_agent_response(user_input)
                        
            elif choice == "3":
                print("👋 Viszlát!")
                break
                
            else:
                print("❌ Érvénytelen választás. Próbáld újra.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Viszlát!")
            break
        except Exception as e:
            print(f"❌ Hiba: {str(e)}")

if __name__ == "__main__":
    # Set environment for testing
    os.environ["ENVIRONMENT"] = "development"
    os.environ["OPENAI_API_KEY"] = "test_key"  # Mock key for testing
    
    # Run interactive test
    asyncio.run(interactive_test()) 