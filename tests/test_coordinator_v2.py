"""Test the updated coordinator with v2 workflow."""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.workflows.coordinator import get_coordinator_agent
from src.models.user import User

async def test_coordinator_v2():
    """Test coordinator with v2 workflow integration."""
    try:
        print("Testing updated coordinator with v2 workflow...")
        
        # Get coordinator
        coordinator = get_coordinator_agent()
        
        # Check status
        status = coordinator.get_agent_status()
        print(f"Coordinator status: {status.get('workflow_version')}")
        print(f"Architecture pattern: {status.get('architecture_pattern')}")
        print(f"Follows article pattern: {status.get('follows_article_pattern')}")
        
        # Test user
        test_user = User(
            id="test_user_123",
            email="test@example.com",
            name="Test User"
        )
        
        # Test different message types
        test_cases = [
            ("Milyen telefonjaink vannak?", "product"),
            ("Hol a rendelesem?", "order"),  
            ("Mit ajanlasz?", "recommendation"),
            ("Van akcio?", "marketing"),
            ("Segitesz?", "general")
        ]
        
        for message, expected_agent in test_cases:
            print(f"\n--- Testing: {message} ---")
            
            result = await coordinator.process_message(
                message=message,
                user=test_user,
                session_id="test_session_123"
            )
            
            print(f"Expected agent: {expected_agent}")
            print(f"Response: {result.response_text[:100]}...")
            print(f"Confidence: {result.confidence}")
            print(f"Agent type: {result.metadata.get('agent_type', 'unknown')}")
            print(f"Workflow version: v2" if 'workflow_steps' in result.metadata else "Workflow version: legacy")
            
            # Verify agent type matches expectation
            actual_agent = result.metadata.get('agent_type', 'unknown')
            if actual_agent == expected_agent:
                print("✅ Agent selection correct!")
            else:
                print(f"⚠️ Agent selection mismatch: expected {expected_agent}, got {actual_agent}")
        
        print("\n✅ Coordinator v2 test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_coordinator_v2())