"""
Agent Cache Manager - Centralized agent instance caching for performance optimization.

This module implements a singleton pattern for agent caching to avoid reinitializing
agents on every request, providing 60-80% faster response times as specified in the
optimization plan.
"""

import asyncio
import time
from typing import Dict, Any, Optional, Type
from dataclasses import dataclass
from threading import Lock
from datetime import datetime, timedelta

from pydantic_ai import Agent

from ..agents.general.agent import create_general_agent
from ..agents.product_info.agent import create_product_info_agent
from ..agents.order_status.agent import create_order_status_agent
from ..agents.recommendations.agent import create_recommendation_agent
from ..agents.marketing.agent import create_marketing_agent
from ..agents.social_media.agent import create_social_media_agent
from ..models.agent import AgentType


@dataclass
class CachedAgent:
    """Cached agent container with metadata."""
    agent: Agent
    created_at: datetime
    last_used: datetime
    usage_count: int
    agent_type: AgentType
    status: str = "active"


class AgentCacheManager:
    """
    Centralized agent cache manager implementing singleton pattern.
    
    This class manages agent instances in memory to avoid reinitializing
    them on every request, providing significant performance improvements.
    """
    
    _instance: Optional['AgentCacheManager'] = None
    _lock = Lock()
    
    def __new__(cls) -> 'AgentCacheManager':
        """Singleton pattern implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the agent cache manager."""
        if hasattr(self, '_initialized'):
            return
        
        self._agent_cache: Dict[AgentType, CachedAgent] = {}
        self._initialization_lock = Lock()
        self._stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "total_requests": 0,
            "agents_created": 0,
            "last_cleanup": datetime.now()
        }
        self._initialized = True
    
    def get_agent(self, agent_type: AgentType) -> Agent:
        """
        Get cached agent instance or create new one.
        
        Args:
            agent_type: Type of agent to retrieve
            
        Returns:
            Cached or newly created agent instance
        """
        self._stats["total_requests"] += 1
        
        # Check if agent is already cached
        if agent_type in self._agent_cache:
            cached_agent = self._agent_cache[agent_type]
            
            # Update usage statistics
            cached_agent.last_used = datetime.now()
            cached_agent.usage_count += 1
            self._stats["cache_hits"] += 1
            
            return cached_agent.agent
        
        # Agent not cached, create new instance
        with self._initialization_lock:
            # Double-check after acquiring lock
            if agent_type in self._agent_cache:
                cached_agent = self._agent_cache[agent_type]
                cached_agent.last_used = datetime.now()
                cached_agent.usage_count += 1
                self._stats["cache_hits"] += 1
                return cached_agent.agent
            
            # Create new agent instance
            agent = self._create_agent(agent_type)
            
            # Cache the agent
            now = datetime.now()
            cached_agent = CachedAgent(
                agent=agent,
                created_at=now,
                last_used=now,
                usage_count=1,
                agent_type=agent_type
            )
            
            self._agent_cache[agent_type] = cached_agent
            self._stats["cache_misses"] += 1
            self._stats["agents_created"] += 1
            
            return agent
    
    def _create_agent(self, agent_type: AgentType) -> Agent:
        """
        Create new agent instance based on type.
        
        Args:
            agent_type: Type of agent to create
            
        Returns:
            New agent instance
            
        Raises:
            ValueError: If agent type is not supported
        """
        agent_creators = {
            AgentType.GENERAL: create_general_agent,
            AgentType.PRODUCT_INFO: create_product_info_agent,
            AgentType.ORDER_STATUS: create_order_status_agent,
            AgentType.RECOMMENDATION: create_recommendation_agent,
            AgentType.MARKETING: create_marketing_agent,
            AgentType.SOCIAL_MEDIA: create_social_media_agent,
        }
        
        if agent_type not in agent_creators:
            raise ValueError(f"Unsupported agent type: {agent_type}")
        
        try:
            return agent_creators[agent_type]()
        except Exception as e:
            raise RuntimeError(f"Failed to create agent {agent_type}: {str(e)}")
    
    def preload_agents(self, agent_types: Optional[list[AgentType]] = None) -> Dict[AgentType, bool]:
        """
        Preload agent instances for faster access.
        
        Args:
            agent_types: List of agent types to preload. If None, preloads all types.
            
        Returns:
            Dictionary mapping agent types to success status
        """
        if agent_types is None:
            agent_types = list(AgentType)
        
        results = {}
        
        for agent_type in agent_types:
            try:
                self.get_agent(agent_type)
                results[agent_type] = True
            except Exception as e:
                print(f"Failed to preload agent {agent_type}: {e}")
                results[agent_type] = False
        
        return results
    
    def invalidate_agent(self, agent_type: AgentType) -> bool:
        """
        Invalidate cached agent instance.
        
        Args:
            agent_type: Type of agent to invalidate
            
        Returns:
            True if agent was invalidated, False if not cached
        """
        if agent_type in self._agent_cache:
            del self._agent_cache[agent_type]
            return True
        return False
    
    def cleanup_stale_agents(self, max_idle_hours: int = 24) -> int:
        """
        Clean up agents that haven't been used for a specified time.
        
        Args:
            max_idle_hours: Maximum idle time in hours before cleanup
            
        Returns:
            Number of agents cleaned up
        """
        now = datetime.now()
        max_idle_delta = timedelta(hours=max_idle_hours)
        
        agents_to_remove = []
        
        for agent_type, cached_agent in self._agent_cache.items():
            if now - cached_agent.last_used > max_idle_delta:
                agents_to_remove.append(agent_type)
        
        for agent_type in agents_to_remove:
            del self._agent_cache[agent_type]
        
        self._stats["last_cleanup"] = now
        return len(agents_to_remove)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        hit_rate = 0.0
        if self._stats["total_requests"] > 0:
            hit_rate = (self._stats["cache_hits"] / self._stats["total_requests"]) * 100
        
        return {
            "cache_hits": self._stats["cache_hits"],
            "cache_misses": self._stats["cache_misses"],
            "total_requests": self._stats["total_requests"],
            "hit_rate_percentage": round(hit_rate, 2),
            "agents_created": self._stats["agents_created"],
            "cached_agents_count": len(self._agent_cache),
            "cached_agent_types": list(self._agent_cache.keys()),
            "last_cleanup": self._stats["last_cleanup"].isoformat(),
            "memory_usage": self._estimate_memory_usage()
        }
    
    def _estimate_memory_usage(self) -> str:
        """
        Estimate memory usage of cached agents.
        
        Returns:
            Estimated memory usage string
        """
        # Rough estimation - each agent ~10-50MB depending on model size
        base_size_mb = len(self._agent_cache) * 25  # Average 25MB per agent
        return f"~{base_size_mb}MB"
    
    def get_agent_info(self, agent_type: AgentType) -> Optional[Dict[str, Any]]:
        """
        Get information about a cached agent.
        
        Args:
            agent_type: Type of agent
            
        Returns:
            Agent information or None if not cached
        """
        if agent_type not in self._agent_cache:
            return None
        
        cached_agent = self._agent_cache[agent_type]
        now = datetime.now()
        
        return {
            "agent_type": agent_type.value,
            "created_at": cached_agent.created_at.isoformat(),
            "last_used": cached_agent.last_used.isoformat(),
            "usage_count": cached_agent.usage_count,
            "age_minutes": (now - cached_agent.created_at).total_seconds() / 60,
            "idle_minutes": (now - cached_agent.last_used).total_seconds() / 60,
            "status": cached_agent.status
        }
    
    def reset_cache(self) -> int:
        """
        Reset the entire agent cache.
        
        Returns:
            Number of agents that were cached before reset
        """
        count = len(self._agent_cache)
        self._agent_cache.clear()
        
        # Reset statistics
        self._stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "total_requests": 0,
            "agents_created": 0,
            "last_cleanup": datetime.now()
        }
        
        return count
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on cached agents.
        
        Returns:
            Health check results
        """
        healthy_agents = []
        unhealthy_agents = []
        
        for agent_type, cached_agent in self._agent_cache.items():
            try:
                # Simple health check - verify agent is accessible
                if hasattr(cached_agent.agent, 'model'):
                    healthy_agents.append(agent_type.value)
                    cached_agent.status = "healthy"
                else:
                    unhealthy_agents.append(agent_type.value)
                    cached_agent.status = "unhealthy"
            except Exception as e:
                unhealthy_agents.append(f"{agent_type.value}: {str(e)}")
                cached_agent.status = "error"
        
        return {
            "healthy_agents": healthy_agents,
            "unhealthy_agents": unhealthy_agents,
            "total_cached": len(self._agent_cache),
            "health_check_timestamp": datetime.now().isoformat()
        }


# Global singleton instance
_agent_cache_manager: Optional[AgentCacheManager] = None


def get_agent_cache_manager() -> AgentCacheManager:
    """
    Get the global agent cache manager instance.
    
    Returns:
        AgentCacheManager singleton instance
    """
    global _agent_cache_manager
    if _agent_cache_manager is None:
        _agent_cache_manager = AgentCacheManager()
    return _agent_cache_manager


def get_cached_agent(agent_type: AgentType) -> Agent:
    """
    Get cached agent instance.
    
    Args:
        agent_type: Type of agent to retrieve
        
    Returns:
        Cached agent instance
    """
    cache_manager = get_agent_cache_manager()
    return cache_manager.get_agent(agent_type)


async def preload_all_agents() -> Dict[AgentType, bool]:
    """
    Preload all agent types for faster access.
    
    Returns:
        Dictionary mapping agent types to success status
    """
    cache_manager = get_agent_cache_manager()
    return cache_manager.preload_agents()


def get_cache_statistics() -> Dict[str, Any]:
    """
    Get agent cache statistics.
    
    Returns:
        Cache statistics dictionary
    """
    cache_manager = get_agent_cache_manager()
    return cache_manager.get_cache_stats()