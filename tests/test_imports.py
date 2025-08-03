"""
Basic import tests to ensure all modules can be imported correctly.
"""

import pytest


def test_src_imports():
    """Test that main src module can be imported."""
    import src
    assert src.__version__ == "0.1.0"


def test_agents_imports():
    """Test that agents module can be imported."""
    from src import agents
    assert agents is not None


def test_integrations_imports():
    """Test that integrations module can be imported."""
    from src import integrations
    assert integrations is not None


def test_models_imports():
    """Test that models module can be imported."""
    from src import models
    assert models is not None


def test_workflows_imports():
    """Test that workflows module can be imported."""
    from src import workflows
    assert workflows is not None


def test_utils_imports():
    """Test that utils module can be imported."""
    from src import utils
    assert utils is not None


def test_config_imports():
    """Test that config module can be imported."""
    from src import config
    assert config is not None


@pytest.mark.unit
def test_placeholder_agents():
    """Test that agent placeholders are set correctly."""
    from src.agents import (
        coordinator_agent,
        product_info_agent,
        order_status_agent,
        recommendations_agent,
        marketing_agent
    )
    
    # All should be None for now (placeholders)
    assert coordinator_agent is None
    assert product_info_agent is None
    assert order_status_agent is None
    assert recommendations_agent is None
    assert marketing_agent is None


@pytest.mark.unit
def test_placeholder_integrations():
    """Test that integration placeholders are set correctly."""
    from src.integrations import (
        supabase_client,
        vector_client,
        shoprenter_client,
        unas_client,
        email_service,
        sms_service,
        facebook_client,
        whatsapp_client
    )
    
    # All should be None for now (placeholders)
    assert supabase_client is None
    assert vector_client is None
    assert shoprenter_client is None
    assert unas_client is None
    assert email_service is None
    assert sms_service is None
    assert facebook_client is None
    assert whatsapp_client is None 