
import pytest
from unittest.mock import MagicMock, AsyncMock

from src.integrations.database.schema_manager import (
    SchemaManager,
    ColumnDefinition,
    TableDefinition,
    IndexDefinition,
    ConstraintDefinition,
    Migration,
    MigrationStatus
)

@pytest.fixture
def mock_supabase_client():
    """Fixture for a mock SupabaseClient"""
    client = MagicMock()
    client.enable_pgvector_extension = AsyncMock(return_value=True)
    client.execute_query = AsyncMock(return_value={"success": True})
    client.table_exists = AsyncMock(return_value=True)
    client.check_rls_enabled = AsyncMock(return_value=True)
    client.check_pgvector_extension = AsyncMock(return_value=True)
    client.check_vector_functions = AsyncMock(return_value=True)
    client.check_vector_indexes = AsyncMock(return_value=True)
    return client

@pytest.fixture
def schema_manager(mock_supabase_client):
    """Fixture for SchemaManager"""
    return SchemaManager(mock_supabase_client)

def test_column_definition():
    """Test ColumnDefinition"""
    col = ColumnDefinition(name="id", data_type="INT", primary_key=True)
    assert col.to_sql() == "id INT PRIMARY KEY"

def test_table_definition():
    """Test TableDefinition"""
    cols = [ColumnDefinition(name="id", data_type="INT")]
    table = TableDefinition(name="test", columns=cols)
    assert table.to_sql() == "CREATE TABLE test ( id INT )"

@pytest.mark.asyncio
async def test_setup_pgvector_extension(schema_manager, mock_supabase_client):
    """Test pgvector extension setup"""
    result = schema_manager.setup_pgvector_extension()
    mock_supabase_client.enable_pgvector_extension.assert_called_once()
    assert result is True

@pytest.mark.asyncio
async def test_create_vector_search_functions(schema_manager, mock_supabase_client):
    """Test vector search function creation"""
    result = schema_manager.create_vector_search_functions()
    assert mock_supabase_client.execute_query.call_count > 0
    assert result is True

@pytest.mark.asyncio
async def test_setup_products_table(schema_manager, mock_supabase_client):
    """Test products table setup"""
    result = schema_manager.setup_products_table()
    assert mock_supabase_client.execute_query.call_count > 0
    assert result is True

@pytest.mark.asyncio
async def test_setup_complete_schema(schema_manager, mock_supabase_client):
    """Test complete schema setup"""
    results = schema_manager.setup_complete_schema()
    assert len(results) > 0
    assert all(val is True for val in results.values())

@pytest.mark.asyncio
async def test_validate_schema(schema_manager, mock_supabase_client):
    """Test schema validation"""
    validation = schema_manager.validate_schema()
    assert "users" in validation
    assert await validation["users"]["exists"] is True
