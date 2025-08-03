"""
LangGraph workflows for Chatbuddy MVP.

This module contains LangGraph workflow definitions for:
- Main chat workflow orchestration
- Multi-agent routing and coordination
- State management and persistence
- Error handling and recovery
"""

# Workflow exports
from .coordinator import (
    CoordinatorAgent,
    CoordinatorState,
    MessageCategory,
    get_coordinator_agent,
    process_chat_message
)

# Placeholder exports for other workflows (will be implemented)
main_chat_workflow = None
product_info_workflow = None
order_status_workflow = None
recommendations_workflow = None
marketing_workflow = None

__all__ = [
    "main_chat_workflow",
    "CoordinatorAgent",
    "CoordinatorState", 
    "MessageCategory",
    "get_coordinator_agent",
    "process_chat_message",
    "product_info_workflow",
    "order_status_workflow", 
    "recommendations_workflow",
    "marketing_workflow"
]
