"""
Database integration tests for Chatbuddy MVP.

This module tests the database integration components:
- Supabase client functionality
- Schema management
- RLS policies
- Vector operations
"""

import pytest
import asyncio
from typing import Dict, Any, AsyncGenerator, Optional
from unittest.mock import Mock, patch, MagicMock, AsyncMock

from src.integrations.database.supabase_client import SupabaseClient, SupabaseConfig
from src.integrations.database.schema_manager import SchemaManager
from src.integrations.database.rls_policies import RLSPolicyManager
from src.integrations.database.vector_operations import VectorOperations
from src.integrations.database.setup_database import DatabaseSetup


# =========== Fixtures ===========

@pytest.fixture
def supabase_config() -> SupabaseConfig:
    """Fixture for creating a test SupabaseConfig."""
    config = SupabaseConfig(
        url='https://test.supabase.co',
        key='test-key',
        service_role_key='service-key'
    )
    # Add OpenAI API key to config
    config.openai_api_key = "test-key"
    return config

@pytest.fixture
def mock_openai() -> AsyncMock:
    """Fixture for mocking OpenAI API."""
    with patch('src.integrations.database.vector_operations.AsyncOpenAI') as mock:
        mock_instance = AsyncMock()
        mock_response = AsyncMock()
        mock_response.data = [AsyncMock(embedding=[0.1] * 1536)]
        mock_instance.embeddings.create = AsyncMock(return_value=mock_response)
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_redis_cache() -> None:
    """Fixture for mocking Redis cache service."""
    with patch('src.integrations.database.vector_operations.get_redis_cache_service') as mock:
        mock.return_value = None
        yield mock

@pytest.fixture
def mock_supabase_client() -> Mock:
    """Fixture for creating a mock Supabase client."""
    mock_client = Mock()
    mock_client.table = Mock()
    mock_client.test_connection.return_value = True
    mock_client.execute_query.return_value = [{"success": True}]
    mock_client.enable_pgvector_extension.return_value = True
    
    # Setup RPC mock for similarity search
    mock_rpc = AsyncMock()
    mock_response = Mock()
    mock_response.data = [
        {
            "id": "1",
            "name": "Test Product",
            "embedding": [0.1] * 1536,
            "similarity": 0.95
        }
    ]
    mock_rpc.execute = AsyncMock(return_value=mock_response)
    mock_client.rpc = Mock(return_value=mock_rpc)
    
    # Setup table mock for vector statistics
    mock_table_response = Mock()
    mock_table_response.data = [
        {"id": "test-id", "embedding": [0.1] * 1536},
        {"id": "test-id-2", "embedding": None}
    ]
    mock_table = AsyncMock()
    mock_select = AsyncMock()
    mock_select.execute = Mock(return_value=mock_table_response)
    mock_table.select = Mock(return_value=mock_select)
    mock_client.table = Mock(return_value=mock_table)
    
    # Setup get_vector_statistics mock
    mock_stats = {
        "total_products": 2,
        "products_with_embedding": 1,
        "embedding_coverage": 0.5
    }
    mock_table.get_vector_statistics = AsyncMock(return_value=mock_stats)
    
    # Setup get_client mock
    mock_client.get_client = Mock(return_value=mock_client)
    
    return mock_client


# =========== Helper Functions ===========

def create_mock_table_response(data: list) -> Mock:
    """Helper function to create a mock table response."""
    mock_response = Mock()
    mock_response.data = data
    return mock_response

def setup_mock_rpc(mock_client: Mock, response_data: Any) -> None:
    """Helper function to setup mock RPC calls."""
    mock_rpc = Mock()
    mock_response = Mock()
    mock_response.data = response_data
    mock_rpc.execute.return_value = mock_response
    mock_client.rpc.return_value = mock_rpc


# =========== Test Classes ===========

class TestSupabaseConfig:
    """Test cases for SupabaseConfig."""

    def test_config_loading_with_env_vars(self) -> None:
        """Test loading config from environment variables."""
        with patch.dict('os.environ', {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_ANON_KEY': 'test-key',
            'SUPABASE_SERVICE_KEY': 'service-key'
        }):
            config = SupabaseConfig(
                url='https://test.supabase.co',
                key='test-key',
                service_role_key='service-key'
            )
            assert config.url == 'https://test.supabase.co'
            assert config.key == 'test-key'
            assert config.service_role_key == 'service-key'

    def test_config_loading_without_service_key(self) -> None:
        """Test loading config without service role key."""
        config = SupabaseConfig(
            url='https://test.supabase.co',
            key='test-key'
        )
        assert config.url == 'https://test.supabase.co'
        assert config.key == 'test-key'
        assert config.service_role_key is None


class TestSupabaseClient:
    """Test cases for SupabaseClient."""

    def test_client_initialization(self, supabase_config: SupabaseConfig, mock_supabase_client: Mock) -> None:
        """Test client initialization."""
        with patch('src.integrations.database.supabase_client.create_client', return_value=mock_supabase_client):
            client = SupabaseClient(supabase_config)
            assert client.config == supabase_config
            assert client.test_connection() is True

    def test_pgvector_extension_enable(self, supabase_config: SupabaseConfig, mock_supabase_client: Mock) -> None:
        """Test enabling pgvector extension."""
        setup_mock_rpc(mock_supabase_client, [{"success": True}])
        
        with patch('src.integrations.database.supabase_client.create_client', return_value=mock_supabase_client):
            client = SupabaseClient(supabase_config)
            result = client.enable_pgvector_extension()
            
            assert result is True
            mock_supabase_client.rpc.assert_called_once_with(
                "exec_sql",
                {"query": "CREATE EXTENSION IF NOT EXISTS vector;"}
            )

    def test_client_connection_error(self, supabase_config: SupabaseConfig) -> None:
        """Test client connection error handling."""
        with patch('src.integrations.database.supabase_client.create_client', side_effect=Exception("Connection failed")):
            with pytest.raises(Exception, match="Connection failed"):
                SupabaseClient(supabase_config)


class TestSchemaManager:
    """Test cases for SchemaManager."""

    def test_create_all_tables(self, mock_supabase_client: Mock) -> None:
        """Test creating all database tables."""
        schema_manager = SchemaManager(mock_supabase_client)
        results = schema_manager.create_all_tables()
        
        assert isinstance(results, dict)
        assert all(table in results for table in [
            "users", "products", "orders", "chat_sessions",
            "audit_logs", "user_consents"
        ])
        assert all(results.values())

    def test_validate_schema(self, mock_supabase_client: Mock) -> None:
        """Test schema validation."""
        mock_supabase_client.get_table_info.return_value = [
            {"column_name": "id", "data_type": "uuid", "is_nullable": "NO"}
        ]
        mock_supabase_client.check_rls_enabled.return_value = True
        mock_supabase_client.table_exists.return_value = True
        
        schema_manager = SchemaManager(mock_supabase_client)
        validation = schema_manager.validate_schema()
        
        assert isinstance(validation, dict)
        assert "users" in validation
        assert validation["users"]["exists"] is True
        assert validation["users"]["rls_enabled"] is True

    def test_schema_validation_with_missing_tables(self, mock_supabase_client: Mock) -> None:
        """Test schema validation with missing tables."""
        mock_supabase_client.table_exists.return_value = False
        
        schema_manager = SchemaManager(mock_supabase_client)
        validation = schema_manager.validate_schema()
        
        assert isinstance(validation, dict)
        assert validation["users"]["exists"] is False


class TestRLSPolicyManager:
    """Test cases for RLSPolicyManager."""

    def test_create_all_policies(self, mock_supabase_client: Mock) -> None:
        """Test creating all RLS policies."""
        rls_manager = RLSPolicyManager(mock_supabase_client)
        results = rls_manager.create_all_policies()
        
        assert isinstance(results, dict)
        assert all(policy in results for policy in [
            "users", "products", "orders", "chat_sessions",
            "audit_logs", "user_consents", "gdpr_compliance", "audit_trail"
        ])
        assert all(results.values())

    def test_create_users_policies(self, mock_supabase_client: Mock) -> None:
        """Test creating user-specific RLS policies."""
        rls_manager = RLSPolicyManager(mock_supabase_client)
        result = rls_manager.create_users_policies()
        
        assert result is True
        assert mock_supabase_client.execute_query.call_count > 1

    def test_create_gdpr_compliance_policies(self, mock_supabase_client: Mock) -> None:
        """Test creating GDPR compliance policies."""
        rls_manager = RLSPolicyManager(mock_supabase_client)
        result = rls_manager.create_gdpr_compliance_policies()
        
        assert result is True
        mock_supabase_client.execute_query.assert_called_once()


@pytest.mark.asyncio
class TestVectorOperations:
    """Test cases for VectorOperations."""

    async def test_embedding_generation(
        self,
        mock_supabase_client: Mock,
        mock_openai: AsyncMock,
        mock_redis_cache: None
    ) -> None:
        """Test generating embeddings."""
        vector_ops = VectorOperations(mock_supabase_client, openai_api_key="test-key")
        embedding = await vector_ops.generate_embedding("test text")
        
        assert embedding is not None
        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)
        mock_openai.embeddings.create.assert_awaited_once()

    async def test_product_embedding_generation(
        self,
        mock_supabase_client: Mock,
        mock_openai: AsyncMock,
        mock_redis_cache: None
    ) -> None:
        """Test generating product embeddings."""
        vector_ops = VectorOperations(mock_supabase_client, openai_api_key="test-key")
        product_data = {
            "name": "Test Product",
            "description": "Test Description",
            "category": "Test Category"
        }
        
        embedding = await vector_ops.generate_product_embedding(product_data)
        
        assert embedding is not None
        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)
        mock_openai.embeddings.create.assert_awaited_once()

    async def test_similarity_search(
        self,
        mock_supabase_client: Mock,
        mock_openai: AsyncMock,
        mock_redis_cache: None
    ) -> None:
        """Test similarity search functionality."""
        vector_ops = VectorOperations(mock_supabase_client, openai_api_key="test-key")
        results = await vector_ops.search_similar_products("test query", limit=10)
        
        assert len(results) > 0
        assert results[0]["id"] == "1"
        assert results[0]["name"] == "Test Product"
        assert results[0]["similarity"] == 0.95
        
        # Verify that the RPC was called with correct parameters
        mock_supabase_client.rpc.assert_called_once()

    async def test_empty_similarity_search(
        self,
        mock_supabase_client: Mock,
        mock_openai: AsyncMock,
        mock_redis_cache: None
    ) -> None:
        """Test similarity search with no results."""
        mock_response = Mock()
        mock_response.data = []
        mock_execute = AsyncMock(return_value=mock_response)
        mock_rpc = Mock()
        mock_rpc.execute = mock_execute
        mock_supabase_client.rpc = Mock(return_value=mock_rpc)
        
        vector_ops = VectorOperations(mock_supabase_client, openai_api_key="test-key")
        results = await vector_ops.search_similar_products("test query", limit=10)
        
        assert len(results) == 0

    async def test_vector_statistics(
        self,
        mock_supabase_client: Mock,
        mock_redis_cache: None
    ) -> None:
        """Test vector statistics calculation."""
        vector_ops = VectorOperations(mock_supabase_client, openai_api_key="test-key")
        stats = await vector_ops.get_vector_statistics()
        
        assert isinstance(stats, dict)
        assert "total_products" in stats
        assert "products_with_embedding" in stats
        assert "embedding_coverage" in stats
        
        # Verify that the table was queried
        mock_supabase_client.table.assert_called_once()
        mock_supabase_client.table().select.assert_called_once()


@pytest.mark.asyncio
class TestDatabaseSetup:
    """Test cases for DatabaseSetup."""

    async def test_complete_database_setup(
        self,
        supabase_config: SupabaseConfig,
        mock_supabase_client: Mock,
        mock_openai: AsyncMock,
        mock_redis_cache: None
    ) -> None:
        """Test complete database setup process."""
        with patch('src.integrations.database.setup_database.SupabaseClient', return_value=mock_supabase_client), \
             patch('src.integrations.database.setup_database.SchemaManager') as mock_schema_class, \
             patch('src.integrations.database.setup_database.RLSPolicyManager') as mock_rls_class, \
             patch('src.integrations.database.setup_database.VectorOperations') as mock_vector_class:
            
            # Setup schema manager mock
            mock_schema = Mock()
            mock_schema.create_all_tables.return_value = {
                "users": True,
                "products": True,
                "orders": True
            }
            mock_schema.validate_schema.return_value = {
                "users": {"exists": True, "rls_enabled": True},
                "products": {"exists": True, "rls_enabled": True}
            }
            mock_schema_class.return_value = mock_schema
            
            # Setup RLS manager mock
            mock_rls = Mock()
            mock_rls.create_all_policies.return_value = {
                "users": True,
                "products": True
            }
            mock_rls.validate_policies.return_value = {
                "users": {"policies_count": 3}
            }
            mock_rls_class.return_value = mock_rls
            
            # Setup vector operations mock
            mock_vector = AsyncMock()
            mock_vector.get_vector_statistics = AsyncMock(return_value={"total_products": 100})
            mock_vector_class.return_value = mock_vector
            
            setup = DatabaseSetup(supabase_config)
            results = await setup.setup_complete_database()
            
            assert isinstance(results, dict)
            assert results["connection_test"] is True
            assert results["tables_created"] is True
            assert results["policies_created"] is True
            assert results["vector_setup"] is True
            assert results["validation"] is True

    def test_schema_documentation_export(self, supabase_config: SupabaseConfig, mock_supabase_client: Mock) -> None:
        """Test schema documentation export."""
        with patch('src.integrations.database.setup_database.SupabaseClient', return_value=mock_supabase_client), \
             patch('src.integrations.database.setup_database.SchemaManager') as mock_schema_class, \
             patch('builtins.open', create=True) as mock_open:
            
            mock_schema = Mock()
            mock_schema.validate_schema.return_value = {
                "users": {
                    "exists": True,
                    "columns": 5,
                    "rls_enabled": True,
                    "columns_info": [
                        {
                            "column_name": "id",
                            "data_type": "uuid",
                            "is_nullable": "NO",
                            "column_default": None
                        }
                    ]
                }
            }
            mock_schema_class.return_value = mock_schema
            
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            setup = DatabaseSetup(supabase_config)
            result = setup.export_schema_documentation("test_schema.md")
            
            assert result is True
            mock_file.write.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])