"""
Recommendation Agent module for Chatbuddy MVP.

This module contains the Recommendation Agent implementation using:
- LangGraph for workflow orchestration
- Pydantic AI for type-safe dependency injection
- Structured output for product recommendations
- Tool-based recommendation generation
"""

from .agent import call_recommendation_agent, create_recommendation_agent

__all__ = [
    "call_recommendation_agent",
    "create_recommendation_agent"
]
