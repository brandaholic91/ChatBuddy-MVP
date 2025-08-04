#!/usr/bin/env python3
"""
Részletes Routing Teszt - ChatBuddy MVP

Ez a script részletesen teszteli a routing-ot és mutatja,
hogy melyik agent valójában dolgozza fel a kérdést.
"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.workflows.coordinator import process_coordinator_message
from src.models.user import User

# Set environment for testing
os.environ["ENVIRONMENT"] = "development"
os.environ["MOCK_GDPR_CONSENT"] = "true"  # Enable mock GDPR consent

async def test_routing_detailed():
    """Részletes routing teszt."""
    
    print("🔍 ChatBuddy MVP - Részletes Routing Teszt")
    print("=" * 60)
    print("Ez a teszt mutatja, hogy melyik agent valójában dolgozza fel a kérdést.")
    print("A 'Agent' mező mindig 'COORDINATOR' lesz, de a routing belül történik.")
    print("A 'metadata' mezőben látható, hogy melyik agent dolgozta fel.")
    print()
    
    # Check environment variables
    print(f"🔧 Environment: {os.getenv('ENVIRONMENT')}")
    print(f"🔑 SECRET_KEY: {'✅ Beállítva' if os.getenv('SECRET_KEY') else '❌ Hiányzik'}")
    print(f"🤖 OPENAI_API_KEY: {'✅ Beállítva' if os.getenv('OPENAI_API_KEY') else '❌ Hiányzik'}")
    print()
    
    # Test user
    user = User(id="test_user_123", email="teszt@example.com")
    
    # Teszt kérdések routing kulcsszavakkal
    test_questions = [
        {
            "question": "Szia! Hogy vagy?",
            "expected_routing": "general_agent",
            "keywords": "általános kérdés"
        },
        {
            "question": "Milyen telefonok vannak?",
            "expected_routing": "product_agent", 
            "keywords": "termék, telefon"
        },
        {
            "question": "Mi a rendelésem státusza?",
            "expected_routing": "order_agent",
            "keywords": "rendelés, státusz"
        },
        {
            "question": "Ajánlj nekem egy telefont",
            "expected_routing": "recommendation_agent",
            "keywords": "ajánl"
        },
        {
            "question": "Milyen akciók vannak?",
            "expected_routing": "marketing_agent",
            "keywords": "akció"
        },
        {
            "question": "Keresek egy iPhone-t",
            "expected_routing": "product_agent",
            "keywords": "keres, termék"
        },
        {
            "question": "Mikor érkezik meg a szállításom?",
            "expected_routing": "order_agent",
            "keywords": "szállítás, megérkezik"
        },
        {
            "question": "Mit ajánlasz hasonló termékeket?",
            "expected_routing": "recommendation_agent",
            "keywords": "hasonló, ajánl"
        },
        {
            "question": "Van kedvezményes kupon?",
            "expected_routing": "marketing_agent",
            "keywords": "kedvezmény, kupon"
        }
    ]
    
    print(f"📋 {len(test_questions)} routing teszt futtatása...\n")
    
    for i, test_case in enumerate(test_questions, 1):
        question = test_case["question"]
        expected_routing = test_case["expected_routing"]
        keywords = test_case["keywords"]
        
        print(f"--- ROUTING TESZT {i}/{len(test_questions)} ---")
        print(f"❓ Kérdés: {question}")
        print(f"🎯 Várható routing: {expected_routing}")
        print(f"🔑 Kulcsszavak: {keywords}")
        
        try:
            start_time = datetime.now()
            
            response = await process_coordinator_message(
                message=question,
                user=user,
                session_id=f"test_session_{i}"
            )
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            print(f"🤖 Agent típus: {response.agent_type.value}")
            print(f"⏱️  Idő: {processing_time:.2f}s")
            print(f"🎯 Confidence: {response.confidence:.2f}")
            
            # Routing információ kinyerése
            metadata = response.metadata
            actual_routing = "unknown"
            
            if "workflow_summary" in metadata:
                workflow_summary = metadata["workflow_summary"]
                if "current_agent" in workflow_summary:
                    actual_routing = workflow_summary["current_agent"]
                elif "agent_type" in workflow_summary:
                    actual_routing = workflow_summary["agent_type"]
            
            # LangGraph használat ellenőrzése
            langgraph_used = metadata.get("langgraph_used", False)
            
            print(f"🔄 LangGraph használva: {'✅ Igen' if langgraph_used else '❌ Nem'}")
            print(f"🎯 Tényleges routing: {actual_routing}")
            
            # Routing egyezés ellenőrzése
            routing_match = "✅ EGYEZIK" if actual_routing == expected_routing else "❌ NEM EGYEZIK"
            print(f"📊 Routing egyezés: {routing_match}")
            
            print(f"💬 Válasz: {response.response_text[:150]}...")
            
            # Metaadatok részletei
            if metadata:
                print(f"📋 Metaadatok:")
                for key, value in list(metadata.items())[:3]:  # Csak az első 3
                    if isinstance(value, dict):
                        print(f"   {key}: {str(value)[:100]}...")
                    else:
                        print(f"   {key}: {str(value)[:100]}...")
            
        except Exception as e:
            print(f"❌ Hiba: {str(e)}")
        
        print("-" * 60)
        await asyncio.sleep(1)  # Delay between tests
    
    print("\n📊 ROUTING TESZT ÖSSZEFOGLALÓ:")
    print("=" * 60)
    print("✅ Ha a 'LangGraph használva: ✅ Igen' és a 'Tényleges routing'")
    print("   megfelel a 'Várható routing'-nak, akkor a routing MŰKÖDIK!")
    print()
    print("🔍 A 'Agent típus' mindig 'COORDINATOR' lesz, mert a koordinátor")
    print("   agent kezeli a kommunikációt, de belül a megfelelő agent dolgozza fel.")
    print()
    print("🎯 A routing kulcsszó-alapú és a következő sorrendben történik:")
    print("   1. Marketing Agent (kedvezmény, akció, promóció)")
    print("   2. Recommendation Agent (ajánl, hasonló, népszerű)")
    print("   3. Order Agent (rendelés, szállítás, státusz)")
    print("   4. Product Agent (termék, telefon, ár)")
    print("   5. General Agent (minden más)")
    print()
    print("✅ Részletes routing tesztelés befejezve!")

if __name__ == "__main__":
    asyncio.run(test_routing_detailed()) 