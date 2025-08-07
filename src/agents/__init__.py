"""
AI Agents module for Chatbuddy MVP.

This module contains specialized AI agents for different customer service scenarios:
- Coordinator agent for routing and orchestration
- Product info agent for product-related queries
- Order status agent for order tracking
- Recommendations agent for personalized suggestions
- Marketing agent for automation workflows
"""

# Agent exports
from .coordinator import get_coordinator_agent
from .product_info import call_product_info_agent, create_product_info_agent
from .order_status import call_order_status_agent, create_order_status_agent
from .recommendations import call_recommendation_agent, create_recommendation_agent
from .marketing import call_marketing_agent, create_marketing_agent
from .general import call_general_agent, create_general_agent

__all__ = [
    "get_coordinator_agent",
    "call_product_info_agent",
    "create_product_info_agent",
    "call_order_status_agent", 
    "create_order_status_agent",
    "call_recommendation_agent",
    "create_recommendation_agent",
    "call_marketing_agent",
    "create_marketing_agent",
    "call_general_agent",
    "create_general_agent"
]
