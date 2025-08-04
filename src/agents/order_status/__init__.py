"""
Order Status Agent module for Chatbuddy MVP.

This module contains the Order Status Agent implementation using:
- LangGraph for workflow orchestration
- Pydantic AI for type-safe dependency injection
- Structured output for order status information
- Tool-based order tracking and management
"""

from .agent import call_order_status_agent, create_order_status_agent

__all__ = [
    "call_order_status_agent",
    "create_order_status_agent"
]
