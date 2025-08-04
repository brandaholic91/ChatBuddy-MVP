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
    get_coordinator_agent,
    process_coordinator_message
)

from .langgraph_workflow import (
    get_workflow_manager,
    create_langgraph_workflow
)

__all__ = [
    "CoordinatorAgent",
    "get_coordinator_agent",
    "process_coordinator_message",
    "get_workflow_manager",
    "create_langgraph_workflow"
]
