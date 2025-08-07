"""
Coordinator Agent module for Chatbuddy MVP.

This module contains the Coordinator Agent implementation using:
- LangGraph for workflow orchestration
- Pydantic AI for type-safe dependency injection
- Multi-agent routing and categorization
- Complex state management
"""

from ...workflows.coordinator import get_coordinator_agent, CoordinatorAgent

__all__ = [
    "get_coordinator_agent",
    "CoordinatorAgent"
]
