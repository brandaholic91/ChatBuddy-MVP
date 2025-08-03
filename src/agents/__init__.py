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
from .product_info import get_product_info_agent
# from .order_status import order_status_agent
# from .recommendations import recommendations_agent
# from .marketing import marketing_agent

# Agent instances - lazy loading to avoid OpenAI API key issues
coordinator_agent = None
product_info_agent = None
order_status_agent = None
recommendations_agent = None
marketing_agent = None

__all__ = [
    "coordinator_agent",
    "product_info_agent", 
    "order_status_agent",
    "recommendations_agent",
    "marketing_agent"
]
