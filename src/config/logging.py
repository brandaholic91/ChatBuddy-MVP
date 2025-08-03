"""
Logging configuration for Chatbuddy MVP.
"""

import structlog
import logging
from typing import Optional
from pydantic_logfire import LogfireHandler


def setup_logging(
    log_level: str = "INFO",
    logfire_token: Optional[str] = None,
    enable_console: bool = True,
    enable_file: bool = False,
    log_file: str = "logs/chatbuddy.log"
) -> None:
    """
    Setup structured logging for Chatbuddy MVP.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        logfire_token: Logfire token for remote logging
        enable_console: Enable console logging
        enable_file: Enable file logging
        log_file: Log file path
    """
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper()),
        handlers=[]
    )
    
    # Add console handler
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter("%(message)s"))
        logging.getLogger().addHandler(console_handler)
    
    # Add file handler
    if enable_file:
        import os
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter("%(message)s"))
        logging.getLogger().addHandler(file_handler)
    
    # Add Logfire handler if token provided
    if logfire_token:
        try:
            logfire_handler = LogfireHandler(
                token=logfire_token,
                service_name="chatbuddy-mvp"
            )
            logging.getLogger().addHandler(logfire_handler)
        except Exception as e:
            logging.warning(f"Failed to setup Logfire: {e}")


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name)


# Convenience functions for common loggers
def get_agent_logger() -> structlog.BoundLogger:
    """Get logger for AI agents."""
    return get_logger("chatbuddy.agents")


def get_workflow_logger() -> structlog.BoundLogger:
    """Get logger for LangGraph workflows."""
    return get_logger("chatbuddy.workflows")


def get_integration_logger() -> structlog.BoundLogger:
    """Get logger for external integrations."""
    return get_logger("chatbuddy.integrations")


def get_api_logger() -> structlog.BoundLogger:
    """Get logger for API endpoints."""
    return get_logger("chatbuddy.api") 