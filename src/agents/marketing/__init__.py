"""
Marketing Agent module for Chatbuddy MVP.

This module contains the Marketing Agent implementation using:
- LangGraph for workflow orchestration
- Pydantic AI for type-safe dependency injection
- Structured output for marketing information
- Tool-based marketing automation
"""

from .agent import call_marketing_agent, create_marketing_agent

__all__ = [
    "call_marketing_agent",
    "create_marketing_agent"
]