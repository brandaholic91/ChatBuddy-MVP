"""
Agent Cache Manager Test - Validate the caching implementation.

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

from src.workflows.agent_cache_manager import (
    get_agent_cache_manager,
    get_cached_agent,
    preload_all_agents,
    get_cache_statistics
)
from src.models.agent import AgentType


async def test_agent_cache_performance():
    """Test agent cache performance improvements."""
    print("🧪 Testing Agent Cache Performance")
    print("=" * 50)
    
    # Get cache manager
    cache_manager = get_agent_cache_manager()
    
    # Test 1: Reset cache to start fresh
    print("\n1. Resetting cache for clean test...")
    reset_count = cache_manager.reset_cache()
    print(f"   Cleared {reset_count} cached agents")
    
    # Test 2: Cold start performance (no cache)
    print("\n2. Testing cold start performance (no cache)...")
    cold_start_times = []
    
    for agent_type in [AgentType.GENERAL, AgentType.PRODUCT_INFO, AgentType.ORDER_STATUS]:
        start_time = time.time()
        try:
            agent = get_cached_agent(agent_type)
            end_time = time.time()
            cold_time = end_time - start_time
            cold_start_times.append((agent_type.value, cold_time))
            print(f"   {agent_type.value}: {cold_time:.3f}s (cache miss)")
        except Exception as e:
            print(f"   {agent_type.value}: FAILED - {e}")
    
    # Test 3: Warm start performance (with cache)
    print("\n3. Testing warm start performance (with cache)...")
    warm_start_times = []
    
    for agent_type in [AgentType.GENERAL, AgentType.PRODUCT_INFO, AgentType.ORDER_STATUS]:
        start_time = time.time()
        try:
            agent = get_cached_agent(agent_type)
            end_time = time.time()
            warm_time = end_time - start_time
            warm_start_times.append((agent_type.value, warm_time))
            print(f"   {agent_type.value}: {warm_time:.3f}s (cache hit)")
        except Exception as e:
            print(f"   {agent_type.value}: FAILED - {e}")
    
    # Test 4: Calculate performance improvements
    print("\n4. Performance Analysis:")
    print("   " + "-" * 40)
    
    total_cold_time = sum(time for _, time in cold_start_times)
    total_warm_time = sum(time for _, time in warm_start_times)
    
    if total_cold_time > 0:
        improvement = ((total_cold_time - total_warm_time) / total_cold_time) * 100
        print(f"   Total cold start time: {total_cold_time:.3f}s")
        print(f"   Total warm start time: {total_warm_time:.3f}s")
        print(f"   Performance improvement: {improvement:.1f}%")
        print(f"   Target: 60-80% improvement")
        
        if improvement >= 60:
            print("   ✅ PERFORMANCE TARGET ACHIEVED!")
        elif improvement >= 30:
            print("   🟡 GOOD IMPROVEMENT (but below target)")
        else:
            print("   ❌ IMPROVEMENT BELOW EXPECTATIONS")
    else:
        print("   ❌ Could not calculate performance improvement")
    
    # Test 5: Show cache statistics
    print("\n5. Cache Statistics:")
    stats = get_cache_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    return improvement if total_cold_time > 0 else 0


async def test_agent_preloading():
    """Test agent preloading functionality."""
    print("\n🚀 Testing Agent Preloading")
    print("=" * 50)
    
    # Reset cache first
    cache_manager = get_agent_cache_manager()
    cache_manager.reset_cache()
    
    # Test preloading
    print("\n1. Preloading all agents...")
    start_time = time.time()
    results = await preload_all_agents()
    end_time = time.time()
    preload_time = end_time - start_time
    
    successful_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    
    print(f"   Preload time: {preload_time:.3f}s")
    print(f"   Success rate: {successful_count}/{total_count}")
    
    # Show individual results
    print("\n2. Preloading Results:")
    for agent_type, success in results.items():
        status = "✅" if success else "❌"
        print(f"   {status} {agent_type.value}")
    
    return successful_count, total_count


async def test_cache_management():
    """Test cache management features."""
    print("\n🛠️ Testing Cache Management")
    print("=" * 50)
    
    cache_manager = get_agent_cache_manager()
    
    # Test 1: Cache some agents
    print("\n1. Caching some agents...")
    get_cached_agent(AgentType.GENERAL)
    get_cached_agent(AgentType.PRODUCT_INFO)
    
    # Test 2: Get agent info
    print("\n2. Agent Information:")
    for agent_type in [AgentType.GENERAL, AgentType.PRODUCT_INFO, AgentType.ORDER_STATUS]:
        info = cache_manager.get_agent_info(agent_type)
        if info:
            print(f"   {agent_type.value}:")
            print(f"     Created: {info['created_at']}")
            print(f"     Usage count: {info['usage_count']}")
            print(f"     Age: {info['age_minutes']:.1f} minutes")
        else:
            print(f"   {agent_type.value}: Not cached")
    
    # Test 3: Health check
    print("\n3. Health Check:")
    health = await cache_manager.health_check()
    print(f"   Healthy agents: {len(health['healthy_agents'])}")
    print(f"   Unhealthy agents: {len(health['unhealthy_agents'])}")
    
    # Test 4: Cleanup
    print("\n4. Testing cleanup...")
    cleaned = cache_manager.cleanup_stale_agents(max_idle_hours=0)  # Clean all
    print(f"   Cleaned {cleaned} stale agents")


async def main():
    """Main test function."""
    print("🎯 Agent Cache Manager Optimization Test")
    print("=" * 60)
    print("Testing the optimization: 'Ágenskapcsolat cache implementálása'")
    print("Expected result: 60-80% faster response times")
    print("=" * 60)
    
    try:
        # Run all tests
        improvement = await test_agent_cache_performance()
        await test_agent_preloading()
        await test_cache_management()
        
        # Final summary
        print("\n" + "=" * 60)
        print("📋 FINAL SUMMARY")
        print("=" * 60)
        
        if improvement >= 60:
            print("✅ OPTIMIZATION SUCCESSFUL!")
            print(f"   Performance improvement: {improvement:.1f}%")
            print("   Target: 60-80% improvement - ACHIEVED")
        elif improvement >= 30:
            print("🟡 OPTIMIZATION PARTIALLY SUCCESSFUL")
            print(f"   Performance improvement: {improvement:.1f}%")
            print("   Target: 60-80% improvement - PARTIALLY ACHIEVED")
        else:
            print("❌ OPTIMIZATION NEEDS IMPROVEMENT")
            print(f"   Performance improvement: {improvement:.1f}%")
            print("   Target: 60-80% improvement - NOT ACHIEVED")
        
        # Show final stats
        stats = get_cache_statistics()
        print(f"\nCache Statistics:")
        print(f"   Hit rate: {stats['hit_rate_percentage']}%")
        print(f"   Total requests: {stats['total_requests']}")
        print(f"   Cached agents: {stats['cached_agents_count']}")
        print(f"   Memory usage: {stats['memory_usage']}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())