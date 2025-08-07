#!/usr/bin/env python3
"""
Gyors Agent Tesztelés - ChatBuddy MVP

Ez a script gyorsan teszteli az agenteket néhány alapvető kérdéssel.
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
# Use real API key from .env file (don't override it)

async def quick_test():
    """Gyors teszt az agentekkel."""
    
    print("🚀 ChatBuddy MVP - Gyors Agent Tesztelés")
    print("=" * 50)
    
    # Check environment variables
    print(f"🔧 Environment: {os.getenv('ENVIRONMENT')}")
    print(f"🔑 SECRET_KEY: {'✅ Beállítva' if os.getenv('SECRET_KEY') else '❌ Hiányzik'}")
    print(f"🤖 OPENAI_API_KEY: {'✅ Beállítva' if os.getenv('OPENAI_API_KEY') else '❌ Hiányzik'}")
    print()
    
    # Test user
    user = User(id="test_user_123", email="teszt@example.com")
    
    # Test kérdések
    test_questions = [
        "Szia! Hogy vagy?",
        "Milyen telefonok vannak?",
        "Mi a rendelésem státusza?",
        "Ajánlj nekem egy telefont",
        "Milyen akciók vannak?"
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
            print(f"💬 Válasz: {response.response_text}")
            
            if response.metadata:
                print(f"📊 Metadata: {response.metadata}")
                
        except Exception as e:
            print(f"❌ Hiba: {str(e)}")
        
        print("-" * 50)
        await asyncio.sleep(0.5)  # Small delay
    
    print("\n✅ Gyors tesztelés befejezve!")

if __name__ == "__main__":
    asyncio.run(quick_test()) 