"""
General Agent module for Chatbuddy MVP.

This module contains the General Agent implementation using:
- LangGraph for workflow orchestration
- Pydantic AI for type-safe dependency injection
- Structured output for general assistance
- Tool-based help and support
"""

from .agent import call_general_agent, create_general_agent

__all__ = [
    "call_general_agent",
    "create_general_agent"
] 