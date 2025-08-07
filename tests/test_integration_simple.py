"""Simple integration test for the new workflow."""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.workflows.langgraph_workflow_v2 import get_correct_workflow_manager

async def test_simple_integration():
    """Simple integration test."""
    try:
        print("Testing simple integration...")
        
        manager = get_correct_workflow_manager()
        
        # Test basic message
        result = await manager.process_message(
            user_message="Szia! Milyen telefonjaink vannak?",
            user_context={"user_id": "test"},
            security_context={}
        )
        
        print(f"Active agent: {result.get('active_agent')}")
        print(f"Workflow steps: {result.get('workflow_steps')}")
        
        # Check messages
        messages = result.get('messages', [])
        print(f"Messages count: {len(messages)}")
        if len(messages) >= 2:
            print(f"AI Response: {messages[-1].content[:100]}...")
        
        # Check agent responses
        agent_responses = result.get('agent_responses', {})
        print(f"Agent responses available: {list(agent_responses.keys())}")
        
        if result.get('active_agent') in agent_responses:
            response = agent_responses[result['active_agent']]
            print(f"Response text: {response.get('response_text', '')[:100]}...")
            print(f"Confidence: {response.get('confidence', 0)}")
            
        print("✅ Integration test successful!")
        
        return result
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_simple_integration())
    if result:
        print(f"\n🎉 Final state keys: {list(result.keys())}")