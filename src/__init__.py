"""
Chatbuddy MVP - AI-powered omnichannel customer service chatbot.

This package contains the core components for the Chatbuddy MVP system:
- AI agents for different customer service scenarios
- LangGraph workflows for orchestration
- Pydantic AI integration for type-safe agent development
- Integration modules for external services
"""

__version__ = "0.1.0"
__author__ = "Chatbuddy Team"

# Core module exports
from . import agents
from . import integrations
from . import models
from . import workflows
from . import utils
from . import config

__all__ = [
    "agents",
    "integrations", 
    "models",
    "workflows",
    "utils",
    "config"
]
