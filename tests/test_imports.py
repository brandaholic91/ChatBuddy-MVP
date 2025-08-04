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
    # Test that agents module can be imported
    from src.agents import coordinator, general, marketing, order_status, product_info, recommendations
    
    # All should be importable modules
    assert coordinator is not None
    assert general is not None
    assert marketing is not None
    assert order_status is not None
    assert product_info is not None
    assert recommendations is not None


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