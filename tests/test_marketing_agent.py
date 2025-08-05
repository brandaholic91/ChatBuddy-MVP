#!/usr/bin/env python3
"""
Marketing Agent Tesztelés - ChatBuddy MVP

Ez a script különböző marketing kérdésekkel teszteli a marketing agentet.
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

async def test_marketing_agent():
    """Marketing agent tesztelése különböző kérdésekkel."""
    
    print("🚀 ChatBuddy MVP - Marketing Agent Tesztelés")
    print("=" * 50)
    
    # Check environment variables
    print(f"🔧 Environment: {os.getenv('ENVIRONMENT')}")
    print(f"🔑 SECRET_KEY: {'✅ Beállítva' if os.getenv('SECRET_KEY') else '❌ Hiányzik'}")
    print(f"🤖 OPENAI_API_KEY: {'✅ Beállítva' if os.getenv('OPENAI_API_KEY') else '❌ Hiányzik'}")
    print()
    
    # Test user
    user = User(id="test_user_123", email="teszt@example.com")
    
    # Marketing teszt kérdések
    marketing_questions = [
        "Milyen akciók vannak?",  # Általános akciók
        "Van kedvezményes kód?",  # Kupon kódok
        "Szeretnék feliratkozni a hírlevélre",  # Hírlevél feliratkozás
        "Milyen promóciók érhetők el?",  # Promóciók
        "Van valamilyen kedvezmény?",  # Kedvezmények
        "Milyen hírlevelek vannak?",  # Hírlevelek
        "Szeretnék kapni a legújabb akciókat",  # Akció értesítések
        "Van valamilyen kupon kód?",  # Kupon kódok
        "Milyen személyre szabott ajánlatok vannak?",  # Személyre szabott ajánlatok
        "Szeretnék értesítést kapni az új termékekről"  # Új termék értesítések
    ]
    
    print(f"📋 {len(marketing_questions)} marketing teszt kérdés futtatása...\n")
    
    for i, question in enumerate(marketing_questions, 1):
        print(f"--- MARKETING TESZT {i}/{len(marketing_questions)} ---")
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
            print(f"💬 Válasz: {response.response_text[:300]}...")
            
            # Marketing-specifikus információk
            if hasattr(response, 'metadata') and response.metadata:
                print(f"📊 Metadata: {response.metadata}")
            
        except Exception as e:
            print(f"❌ Hiba: {str(e)}")
        
        print("-" * 50)
        await asyncio.sleep(1)  # Delay between tests
    
    print("\n✅ Marketing agent tesztelés befejezve!")

if __name__ == "__main__":
    asyncio.run(test_marketing_agent()) 