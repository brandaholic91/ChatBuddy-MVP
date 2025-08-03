"""
Product Info Agent module for Chatbuddy MVP.

This module contains the Product Info Agent implementation using:
- LangGraph for workflow orchestration
- Pydantic AI for type-safe dependency injection
- Structured output for product information
- Tool-based product search and recommendations
"""

from .agent import ProductInfoAgent, get_product_info_agent
from .tools import (
    search_products,
    get_product_details,
    get_product_reviews,
    get_related_products,
    check_product_availability,
    get_product_pricing
)

__all__ = [
    "ProductInfoAgent",
    "get_product_info_agent",
    "search_products",
    "get_product_details", 
    "get_product_reviews",
    "get_related_products",
    "check_product_availability",
    "get_product_pricing"
]
