"""
Test script for the new workflow implementation.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.workflows.langgraph_workflow_v2 import get_correct_workflow_manager


async def test_new_workflow():
    """Test the new workflow implementation."""
    try:
        print("Testing new LangGraph + Pydantic AI workflow...")
        
        # Get workflow manager
        manager = get_correct_workflow_manager()
        
        # Test multiple queries
        test_cases = [
            "Milyen telefonjaink vannak?",  # product
            "Hol a rendelesem?",  # order
            "Mit ajanlasz nekem?",  # recommendation
            "Van kedvezmeny?",  # marketing
            "Szia, segitesz?"  # general
        ]
        
        for i, test_message in enumerate(test_cases):
            print(f"\n--- Test {i+1}: {test_message} ---")
            
            # Process message
            result = await manager.process_message(
                user_message=test_message,
                user_context={"user_id": "test_user"},
                security_context={}
            )
            
            print(f"Active agent: {result.get('active_agent', 'unknown')}")
            
            # Check agent responses
            agent_responses = result.get('agent_responses', {})
            if agent_responses:
                active_agent = result.get('active_agent')
                if active_agent in agent_responses:
                    response = agent_responses[active_agent]
                    print(f"Response: {response.get('response_text', 'No response')[:80]}...")
                    print(f"Mock mode: {response.get('metadata', {}).get('mock_mode', False)}")
            
        return  # Exit after multiple tests
        
        print("\nWorkflow execution completed!")
        print(f"Active agent: {result.get('active_agent', 'unknown')}")
        print(f"Workflow steps: {result.get('workflow_steps', [])}")
        
        # Check messages
        messages = result.get('messages', [])
        print(f"Messages count: {len(messages)}")
        
        if len(messages) >= 2:
            last_message = messages[-1]
            print(f"AI Response: {last_message.content[:100]}...")
        
        # Check agent responses
        agent_responses = result.get('agent_responses', {})
        if agent_responses:
            print(f"Agent responses: {list(agent_responses.keys())}")
        
        print("Test completed successfully!")
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_new_workflow())