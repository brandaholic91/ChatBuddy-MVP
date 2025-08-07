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
    
    # FunctionToolset objektum helyes kezelése
    print(f"Agent tools: {agent1._function_toolset}")  # Len() helyett közvetlen elérés
    # Vagy használjuk a megfelelő metódust a tools számának lekéréséhez
    if hasattr(agent1._function_toolset, 'tools'):
        print(f"Number of tools: {len(agent1._function_toolset.tools)}")
    elif hasattr(agent1._function_toolset, '__len__'):
        print(f"Number of tools: {len(agent1._function_toolset)}")
    else:
        print("Tools object doesn't support len(), showing object directly")

if __name__ == "__main__":
    test_singleton()