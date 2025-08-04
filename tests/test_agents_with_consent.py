#!/usr/bin/env python3
"""
Agent Tesztelés Mock GDPR Consent-tel - ChatBuddy MVP

Ez a script teszteli az agenteket mock GDPR hozzájárulással.
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
from src.config.gdpr_compliance import GDPRComplianceLayer, ConsentType, DataCategory

# Set environment for testing
os.environ["ENVIRONMENT"] = "development"
os.environ["MOCK_GDPR_CONSENT"] = "true"  # Enable mock GDPR consent

class MockGDPRCompliance(GDPRComplianceLayer):
    """Mock GDPR compliance teszteléshez."""
    
    async def check_user_consent(
        self, 
        user_id: str, 
        consent_type: ConsentType,
        data_category: DataCategory
    ) -> bool:
        """Mock consent - minden hozzájárulást megadunk teszteléshez."""
        print(f"🔐 Mock GDPR Consent: {consent_type.value} - {data_category.value} -> ✅ GRANTED")
        return True

async def test_with_consent():
    """Teszt mock GDPR consent-tel."""
    
    print("🚀 ChatBuddy MVP - Agent Tesztelés Mock GDPR Consent-tel")
    print("=" * 60)
    
    # Check environment variables
    print(f"🔧 Environment: {os.getenv('ENVIRONMENT')}")
    print(f"🔑 SECRET_KEY: {'✅ Beállítva' if os.getenv('SECRET_KEY') else '❌ Hiányzik'}")
    print(f"🤖 OPENAI_API_KEY: {'✅ Beállítva' if os.getenv('OPENAI_API_KEY') else '❌ Hiányzik'}")
    print()
    
    # Test user
    user = User(id="test_user_123", email="teszt@example.com")
    
    # Test kérdések különböző kategóriákból
    test_questions = [
        # General kérdések
        "Szia! Hogy vagy?",
        "Mit tudsz csinálni?",
        "Hogyan tudok segítséget kapni?",
        
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
        
        # Komplex kérdések
        "Szeretnék egy telefont venni, ami jó kamera, és van rá kedvezmény?",
        "Mikor érkezik meg a rendelésem és milyen telefonok vannak akciósan?",
        "Ajánlj egy telefont és mutasd meg a rendelésem státuszát is"
    ]
    
    print(f"📋 {len(test_questions)} teszt kérdés futtatása mock GDPR consent-tel...\n")
    
    for i, question in enumerate(test_questions, 1):
        print(f"--- TESZT {i}/{len(test_questions)} ---")
        print(f"❓ Kérdés: {question}")
        
        try:
            start_time = datetime.now()
            
            response = await process_coordinator_message(
                message=question,
                user=user,
                session_id="test_session_123"
            )
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            print(f"🤖 Agent: {response.agent_type.value}")
            print(f"⏱️  Idő: {processing_time:.2f}s")
            print(f"🎯 Confidence: {response.confidence:.2f}")
            print(f"💬 Válasz: {response.response_text}")
            
            if response.metadata:
                print(f"📊 Metadata: {response.metadata}")
                
        except Exception as e:
            print(f"❌ Hiba: {str(e)}")
        
        print("-" * 60)
        await asyncio.sleep(0.5)  # Small delay
    
    print("\n✅ Tesztelés mock GDPR consent-tel befejezve!")

if __name__ == "__main__":
    asyncio.run(test_with_consent()) 