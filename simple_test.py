#!/usr/bin/env python3
"""
Egyszerű Agent Tesztelés - ChatBuddy MVP

Ez a script néhány alapvető kérdéssel teszteli az agenteket.
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

async def simple_test():
    """Egyszerű teszt néhány kérdéssel."""
    
    print("🚀 ChatBuddy MVP - Egyszerű Agent Tesztelés")
    print("=" * 50)
    
    # Check environment variables
    print(f"🔧 Environment: {os.getenv('ENVIRONMENT')}")
    print(f"🔑 SECRET_KEY: {'✅ Beállítva' if os.getenv('SECRET_KEY') else '❌ Hiányzik'}")
    print(f"🤖 OPENAI_API_KEY: {'✅ Beállítva' if os.getenv('OPENAI_API_KEY') else '❌ Hiányzik'}")
    print()
    
    # Test user
    user = User(id="test_user_123", email="teszt@example.com")
    
    # Egyszerű teszt kérdések
    test_questions = [
        "Szia! Hogy vagy?",  # General
        "Milyen telefonok vannak?",  # Product
        "Mi a rendelésem státusza?",  # Order
        "Ajánlj nekem egy telefont",  # Recommendation
        "Milyen akciók vannak?"  # Marketing
    ]
    
    print(f"📋 {len(test_questions)} teszt kérdés futtatása...\n")
    
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
            print(f"💬 Válasz: {response.response_text[:200]}...")
            
        except Exception as e:
            print(f"❌ Hiba: {str(e)}")
        
        print("-" * 50)
        await asyncio.sleep(1)  # Delay between tests
    
    print("\n✅ Egyszerű tesztelés befejezve!")

if __name__ == "__main__":
    asyncio.run(simple_test()) 