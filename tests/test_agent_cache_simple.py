"""
Simple Agent Cache Manager Test - Validate the caching implementation.

This script tests the agent caching functionality to ensure 60-80% faster
response times as specified in the optimization plan.
"""

import asyncio
import time
import sys
import os
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.workflows.agent_cache_manager import (
        get_agent_cache_manager,
        get_cached_agent,
        preload_all_agents,
        get_cache_statistics
    )
    from src.models.agent import AgentType
    
    print("Agent Cache Manager Optimization Test")
    print("=" * 50)
    print("Testing the optimization: 'Agenskapcsolat cache implementalasa'")
    print("Expected result: 60-80% faster response times")
    print("=" * 50)
    
    async def test_basic_caching():
        """Test basic caching functionality."""
        print("\n1. Testing basic agent caching...")
        
        # Get cache manager
        cache_manager = get_agent_cache_manager()
        
        # Reset cache
        reset_count = cache_manager.reset_cache()
        print(f"   Cleared {reset_count} cached agents")
        
        # Test cold start
        print("\n2. Cold start test (cache miss)...")
        start_time = time.time()
        agent1 = get_cached_agent(AgentType.GENERAL)
        cold_time = time.time() - start_time
        print(f"   Cold start time: {cold_time:.4f}s")
        
        # Test warm start
        print("\n3. Warm start test (cache hit)...")
        start_time = time.time()
        agent2 = get_cached_agent(AgentType.GENERAL)
        warm_time = time.time() - start_time
        print(f"   Warm start time: {warm_time:.4f}s")
        
        # Verify same instance
        same_instance = agent1 is agent2
        print(f"   Same instance returned: {same_instance}")
        
        # Calculate improvement
        if cold_time > 0:
            improvement = ((cold_time - warm_time) / cold_time) * 100
            print(f"   Performance improvement: {improvement:.1f}%")
            
            if improvement >= 60:
                print("   SUCCESS: Target achieved (60-80%)")
            elif improvement >= 30:
                print("   PARTIAL: Good improvement but below target")
            else:
                print("   NEEDS WORK: Below expectations")
        
        # Show cache stats
        print("\n4. Cache Statistics:")
        stats = get_cache_statistics()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        return improvement if cold_time > 0 else 0
    
    async def main():
        try:
            improvement = await test_basic_caching()
            
            print("\n" + "=" * 50)
            print("FINAL RESULT:")
            if improvement >= 60:
                print("SUCCESS: Agent caching optimization achieved!")
            else:
                print(f"PARTIAL: {improvement:.1f}% improvement (target: 60-80%)")
            print("=" * 50)
            
        except Exception as e:
            print(f"ERROR: Test failed - {e}")
            import traceback
            traceback.print_exc()
    
    if __name__ == "__main__":
        asyncio.run(main())
        
except ImportError as e:
    print(f"Import error: {e}")
    print("This suggests the agent cache manager needs some dependency fixes.")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()