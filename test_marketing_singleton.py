"""Test marketing agent singleton pattern."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.agents.marketing.agent import create_marketing_agent

def test_singleton():
    print("Testing marketing agent singleton...")
    
    # Create first instance
    agent1 = create_marketing_agent()
    print(f"Agent 1 ID: {id(agent1)}")
    
    # Create second instance
    agent2 = create_marketing_agent()
    print(f"Agent 2 ID: {id(agent2)}")
    
    # Should be the same instance
    if agent1 is agent2:
        print("✅ Singleton working correctly!")
    else:
        print("❌ Singleton NOT working!")
    
    # Check tools
    print(f"Agent tools: {len(agent1._function_tools)} tools")
    for tool_name, tool in agent1._function_tools.items():
        print(f"  - {tool_name}")

if __name__ == "__main__":
    test_singleton()