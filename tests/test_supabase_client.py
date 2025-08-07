
import os
import pytest
from unittest.mock import patch, Mock, MagicMock

from src.integrations.database.supabase_client import SupabaseClient, SupabaseConfig, get_supabase_client

# Test data
TEST_URL = "http://test.supabase.co"
TEST_KEY = "test_anon_key"
TEST_SERVICE_KEY = "test_service_key"

@pytest.fixture
def supabase_client():
    """Fixture for SupabaseClient"""
    with patch.dict(os.environ, {
        "SUPABASE_URL": TEST_URL,
        "SUPABASE_ANON_KEY": TEST_KEY,
        "SUPABASE_SERVICE_KEY": TEST_SERVICE_KEY
    }):
        client = SupabaseClient()
        yield client

def test_load_config(supabase_client):
    """Test configuration loading"""
    config = supabase_client._load_config()
    assert config.url == TEST_URL
    assert config.key == TEST_KEY
    assert config.service_role_key == TEST_SERVICE_KEY

@patch("src.integrations.database.supabase_client.create_client")
def test_initialize_client_success(mock_create_client):
    """Test successful client initialization"""
    mock_client = Mock()
    mock_create_client.return_value = mock_client
    
    client = SupabaseClient(config=SupabaseConfig(url=TEST_URL, key=TEST_KEY))
    
    assert client.client is not None
    mock_create_client.assert_called_once()

def test_initialize_client_missing_config():
    """Test client initialization with missing config"""
    client = SupabaseClient(config=SupabaseConfig(url="", key=""))
    assert client.client is None

@patch("src.integrations.database.supabase_client.create_client", side_effect=Exception("Connection error"))
def test_initialize_client_exception(mock_create_client):
    """Test client initialization with an exception"""
    client = SupabaseClient(config=SupabaseConfig(url=TEST_URL, key=TEST_KEY))
    assert client.client is None

def test_get_client(supabase_client):
    """Test get_client method"""
    client = supabase_client.get_client()
    assert client is not None

def test_get_client_mock_mode():
    """Test get_client in mock mode"""
    client = SupabaseClient(config=SupabaseConfig(url="", key=""))
    mock_client = client.get_client()
    assert isinstance(mock_client, Mock)

def test_get_service_client(supabase_client):
    """Test get_service_client method"""
    service_client = supabase_client.get_service_client()
    assert service_client is not None

def test_get_service_client_no_key():
    """Test get_service_client without service key"""
    client = SupabaseClient(config=SupabaseConfig(url=TEST_URL, key=TEST_KEY))
    with pytest.raises(ValueError):
        client.get_service_client()

def test_test_connection(supabase_client):
    """Test test_connection method"""
    supabase_client.client = Mock()
    assert supabase_client.test_connection() is True

def test_test_connection_failure():
    """Test test_connection on failure"""
    client = SupabaseClient(config=SupabaseConfig(url="", key=""))
    assert client.test_connection() is False

@patch.object(SupabaseClient, 'get_service_client')
def test_execute_query_ddl(mock_get_service_client, supabase_client):
    """Test execute_query with DDL"""
    mock_rpc = Mock()
    mock_rpc.execute.return_value = Mock(data=[{"success": True}])
    mock_service_client = Mock()
    mock_service_client.rpc.return_value = mock_rpc
    mock_get_service_client.return_value = mock_service_client

    response = supabase_client.execute_query("CREATE TABLE test (id int);")
    assert response == [{"success": True}]

def test_execute_query_non_ddl(supabase_client):
    """Test execute_query with non-DDL"""
    with pytest.raises(ValueError):
        supabase_client.execute_query("SELECT * FROM test;")

@patch.object(SupabaseClient, 'get_service_client')
def test_enable_pgvector_extension(mock_get_service_client, supabase_client):
    """Test enable_pgvector_extension"""
    mock_rpc = Mock()
    mock_rpc.execute.return_value = Mock(data=[{"success": True}])
    mock_service_client = Mock()
    mock_service_client.rpc.return_value = mock_rpc
    mock_get_service_client.return_value = mock_service_client

    assert supabase_client.enable_pgvector_extension() is True

def test_get_table_info_invalid_name(supabase_client):
    """Test get_table_info with invalid table name"""
    with pytest.raises(ValueError):
        supabase_client.get_table_info("invalid-table-name")

@patch.object(SupabaseClient, 'get_client')
def test_check_rls_enabled(mock_get_client, supabase_client):
    """Test check_rls_enabled"""
    mock_rpc = Mock()
    mock_rpc.execute.return_value = Mock(data=[True])
    mock_client = Mock()
    mock_client.rpc.return_value = mock_rpc
    mock_get_client.return_value = mock_client

    assert supabase_client.check_rls_enabled("test_table") is True

@patch.object(SupabaseClient, 'get_client')
def test_table_exists(mock_get_client, supabase_client):
    """Test table_exists method"""
    mock_select = Mock()
    mock_select.execute.return_value = Mock(data=[])
    mock_table = Mock()
    mock_table.select.return_value = mock_select
    mock_client = Mock()
    mock_client.table.return_value = mock_table
    mock_get_client.return_value = mock_client

    assert supabase_client.table_exists("test_table") is True
