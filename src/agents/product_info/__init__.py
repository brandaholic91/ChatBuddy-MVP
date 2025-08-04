"""
Product Info Agent module for Chatbuddy MVP.

This module contains the Product Info Agent implementation using:
- LangGraph for workflow orchestration
- Pydantic AI for type-safe dependency injection
- Structured output for product information
- Tool-based product search and recommendations
"""

from .agent import call_product_info_agent, create_product_info_agent

__all__ = [
    "call_product_info_agent",
    "create_product_info_agent"
]
