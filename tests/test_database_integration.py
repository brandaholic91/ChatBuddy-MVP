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
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from src.integrations.database.supabase_client import SupabaseClient, SupabaseConfig
from src.integrations.database.schema_manager import SchemaManager
from src.integrations.database.rls_policies import RLSPolicyManager
from src.integrations.database.vector_operations import VectorOperations
from src.integrations.database.setup_database import DatabaseSetup


class TestSupabaseClient:
    """Supabase kliens tesztelése"""
    
    def test_config_loading(self):
        """Teszteli a konfiguráció betöltését"""
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
    
    def test_client_initialization(self):
        """Teszteli a kliens inicializálását"""
        config = SupabaseConfig(
            url='https://test.supabase.co',
            key='test-key'
        )
        
        with patch('src.integrations.database.supabase_client.create_client') as mock_create:
            mock_client = Mock()
            mock_create.return_value = mock_client
            
            client = SupabaseClient(config)
            
            assert client.config == config
            mock_create.assert_called_once()
    
    def test_connection_test(self):
        """Teszteli a kapcsolat tesztelését"""
        config = SupabaseConfig(
            url='https://test.supabase.co',
            key='test-key'
        )
        
        with patch('src.integrations.database.supabase_client.create_client') as mock_create:
            mock_client = Mock()
            mock_table = Mock()
            mock_response = Mock()
            mock_response.data = []
            
            mock_table.select.return_value.limit.return_value.execute.return_value = mock_response
            mock_client.table.return_value = mock_table
            mock_create.return_value = mock_client
            
            client = SupabaseClient(config)
            result = client.test_connection()
            
            assert result is True
            mock_client.table.assert_called_once_with("users")
    
    def test_pgvector_extension_enable(self):
        """Teszteli a pgvector extension engedélyezését"""
        config = SupabaseConfig(
            url='https://test.supabase.co',
            key='test-key'
        )
        
        with patch('src.integrations.database.supabase_client.create_client') as mock_create:
            mock_client = Mock()
            mock_rpc = Mock()
            mock_response = Mock()
            mock_response.data = []
            
            mock_rpc.execute.return_value = mock_response
            mock_client.rpc.return_value = mock_rpc
            mock_create.return_value = mock_client
            
            client = SupabaseClient(config)
            result = client.enable_pgvector_extension()
            
            assert result is True
            mock_client.rpc.assert_called_once_with("exec_sql", {"query": "CREATE EXTENSION IF NOT EXISTS vector;"})


class TestSchemaManager:
    """Schema manager tesztelése"""
    
    def test_users_table_creation(self):
        """Teszteli a users tábla létrehozását"""
        mock_supabase = Mock()
        schema_manager = SchemaManager(mock_supabase)
        
        result = schema_manager.create_users_table()
        
        assert result is True
        mock_supabase.execute_query.assert_called_once()
    
    def test_products_table_creation(self):
        """Teszteli a products tábla létrehozását"""
        mock_supabase = Mock()
        schema_manager = SchemaManager(mock_supabase)
        
        result = schema_manager.create_products_table()
        
        assert result is True
        mock_supabase.execute_query.assert_called_once()
    
    def test_all_tables_creation(self):
        """Teszteli az összes tábla létrehozását"""
        mock_supabase = Mock()
        schema_manager = SchemaManager(mock_supabase)
        
        # Mock pgvector extension
        mock_supabase.enable_pgvector_extension.return_value = True
        
        results = schema_manager.create_all_tables()
        
        assert isinstance(results, dict)
        assert "users" in results
        assert "products" in results
        assert "orders" in results
        assert "chat_sessions" in results
        assert "audit_logs" in results
        assert "user_consents" in results
    
    def test_schema_validation(self):
        """Teszteli a schema validációt"""
        mock_supabase = Mock()
        mock_supabase.get_table_info.return_value = [
            {"column_name": "id", "data_type": "uuid", "is_nullable": "NO"}
        ]
        mock_supabase.check_rls_enabled.return_value = True
        
        schema_manager = SchemaManager(mock_supabase)
        validation = schema_manager.validate_schema()
        
        assert isinstance(validation, dict)
        assert "users" in validation
        assert validation["users"]["exists"] is True
        assert validation["users"]["rls_enabled"] is True


class TestRLSPolicyManager:
    """RLS policy manager tesztelése"""
    
    def test_users_policies_creation(self):
        """Teszteli a users tábla RLS policy-k létrehozását"""
        mock_supabase = Mock()
        rls_manager = RLSPolicyManager(mock_supabase)
        
        result = rls_manager.create_users_policies()
        
        assert result is True
        # Ellenőrizzük, hogy több policy-t hozott létre
        assert mock_supabase.execute_query.call_count > 1
    
    def test_gdpr_compliance_policies(self):
        """Teszteli a GDPR compliance policy-k létrehozását"""
        mock_supabase = Mock()
        rls_manager = RLSPolicyManager(mock_supabase)
        
        result = rls_manager.create_gdpr_compliance_policies()
        
        assert result is True
        mock_supabase.execute_query.assert_called_once()
    
    def test_audit_trail_policies(self):
        """Teszteli az audit trail policy-k létrehozását"""
        mock_supabase = Mock()
        rls_manager = RLSPolicyManager(mock_supabase)
        
        result = rls_manager.create_audit_trail_policies()
        
        assert result is True
        mock_supabase.execute_query.assert_called_once()
    
    def test_all_policies_creation(self):
        """Teszteli az összes RLS policy létrehozását"""
        mock_supabase = Mock()
        rls_manager = RLSPolicyManager(mock_supabase)
        
        results = rls_manager.create_all_policies()
        
        assert isinstance(results, dict)
        assert "users" in results
        assert "products" in results
        assert "orders" in results
        assert "chat_sessions" in results
        assert "audit_logs" in results
        assert "user_consents" in results
        assert "gdpr_compliance" in results
        assert "audit_trail" in results


class TestVectorOperations:
    """Vector operations tesztelése"""
    
    @pytest.mark.asyncio
    async def test_embedding_generation(self):
        """Teszteli az embedding generálását"""
        mock_supabase = Mock()
        vector_ops = VectorOperations(mock_supabase)
        
        embedding = await vector_ops.generate_embedding("test text")
        
        assert embedding is not None
        assert len(embedding) == 1536  # OpenAI text-embedding-ada-002 dimenzió
        assert all(isinstance(x, float) for x in embedding)
    
    @pytest.mark.asyncio
    async def test_product_embedding_generation(self):
        """Teszteli a termék embedding generálását"""
        mock_supabase = Mock()
        vector_ops = VectorOperations(mock_supabase)
        
        product_data = {
            "name": "Test Product",
            "description": "Test description",
            "brand": "Test Brand",
            "tags": ["test", "product"]
        }
        
        embedding = await vector_ops.generate_product_embedding(product_data)
        
        assert embedding is not None
        assert len(embedding) == 1536
    
    @pytest.mark.asyncio
    async def test_similarity_search(self):
        """Teszteli a similarity search-t"""
        mock_supabase = Mock()
        mock_supabase.execute_query.return_value = [
            {
                "id": "test-id",
                "name": "Test Product",
                "similarity": 0.1
            }
        ]
        
        vector_ops = VectorOperations(mock_supabase)
        
        results = await vector_ops.search_similar_products("test query")
        
        assert isinstance(results, list)
        assert len(results) > 0
        assert "similarity_score" in results[0]
    
    @pytest.mark.asyncio
    async def test_hybrid_search(self):
        """Teszteli a hibrid keresést"""
        mock_supabase = Mock()
        mock_supabase.execute_query.return_value = [
            {
                "id": "test-id",
                "name": "Test Product",
                "similarity": 0.1
            }
        ]
        
        vector_ops = VectorOperations(mock_supabase)
        
        filters = {
            "category_id": "test-category",
            "min_price": 1000,
            "max_price": 5000
        }
        
        results = await vector_ops.hybrid_search("test query", filters)
        
        assert isinstance(results, list)
        assert len(results) > 0
    
    @pytest.mark.asyncio
    async def test_vector_statistics(self):
        """Teszteli a vector statisztikák lekérdezését"""
        mock_supabase = Mock()
        mock_supabase.execute_query.side_effect = [
            [{"total_products": 100, "products_with_embedding": 80, "products_without_embedding": 20}],
            [{"index_size": "1 MB"}],
            [{"dimensions": 1536}]
        ]
        
        vector_ops = VectorOperations(mock_supabase)
        
        stats = await vector_ops.get_vector_statistics()
        
        assert isinstance(stats, dict)
        assert "total_products" in stats
        assert "products_with_embedding" in stats
        assert "index_size" in stats
        assert "embedding_dimensions" in stats


class TestDatabaseSetup:
    """Database setup tesztelése"""
    
    @pytest.mark.asyncio
    async def test_complete_database_setup(self):
        """Teszteli a teljes adatbázis setup-ot"""
        config = SupabaseConfig(
            url='https://test.supabase.co',
            key='test-key'
        )
        
        with patch('src.integrations.database.setup_database.SupabaseClient') as mock_client_class:
            mock_client = Mock()
            mock_client.test_connection.return_value = True
            mock_client_class.return_value = mock_client
            
            with patch('src.integrations.database.setup_database.SchemaManager') as mock_schema_class:
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
                
                with patch('src.integrations.database.setup_database.RLSPolicyManager') as mock_rls_class:
                    mock_rls = Mock()
                    mock_rls.create_all_policies.return_value = {
                        "users": True,
                        "products": True
                    }
                    mock_rls.validate_policies.return_value = {
                        "users": {"policies_count": 3}
                    }
                    mock_rls_class.return_value = mock_rls
                    
                    with patch('src.integrations.database.setup_database.VectorOperations') as mock_vector_class:
                        mock_vector = Mock()
                        mock_vector.get_vector_statistics.return_value = {
                            "total_products": 100
                        }
                        mock_vector_class.return_value = mock_vector
                        
                        setup = DatabaseSetup(config)
                        results = await setup.setup_complete_database()
                        
                        assert isinstance(results, dict)
                        assert results["connection_test"] is True
                        assert results["tables_created"] is True
                        assert results["policies_created"] is True
                        assert results["vector_setup"] is True
                        assert results["validation"] is True
    
    def test_schema_documentation_export(self):
        """Teszteli a schema dokumentáció exportálását"""
        config = SupabaseConfig(
            url='https://test.supabase.co',
            key='test-key'
        )
        
        with patch('src.integrations.database.setup_database.SupabaseClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            with patch('src.integrations.database.setup_database.SchemaManager') as mock_schema_class:
                mock_schema = Mock()
                mock_schema.validate_schema.return_value = {
                    "users": {
                        "exists": True,
                        "columns": 5,
                        "rls_enabled": True,
                        "columns_info": [
                            {"column_name": "id", "data_type": "uuid", "is_nullable": "NO", "column_default": None}
                        ]
                    }
                }
                mock_schema_class.return_value = mock_schema
                
                with patch('builtins.open', create=True) as mock_open:
                    mock_file = Mock()
                    mock_open.return_value.__enter__.return_value = mock_file
                    
                    setup = DatabaseSetup(config)
                    result = setup.export_schema_documentation("test_schema.md")
                    
                    assert result is True
                    mock_file.write.assert_called_once()


class TestDatabaseIntegration:
    """Integrációs tesztek"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Teszteli a teljes workflow-t"""
        config = SupabaseConfig(
            url='https://test.supabase.co',
            key='test-key'
        )
        
        # Mock minden komponenst
        with patch('src.integrations.database.supabase_client.create_client') as mock_create:
            mock_client = Mock()
            mock_table = Mock()
            mock_response = Mock()
            mock_response.data = []
            
            mock_table.select.return_value.limit.return_value.execute.return_value = mock_response
            mock_client.table.return_value = mock_table
            mock_client.rpc.return_value.execute.return_value.data = []
            mock_create.return_value = mock_client
            
            # Supabase kliens tesztelése
            supabase = SupabaseClient(config)
            assert supabase.test_connection() is True
            
            # Schema manager tesztelése
            schema_manager = SchemaManager(supabase)
            table_results = schema_manager.create_all_tables()
            assert isinstance(table_results, dict)
            
            # RLS policy manager tesztelése
            rls_manager = RLSPolicyManager(supabase)
            policy_results = rls_manager.create_all_policies()
            assert isinstance(policy_results, dict)
            
            # Vector operations tesztelése
            vector_ops = VectorOperations(supabase)
            embedding = await vector_ops.generate_embedding("test")
            assert embedding is not None
    
    def test_error_handling(self):
        """Teszteli a hibakezelést"""
        config = SupabaseConfig(
            url='https://test.supabase.co',
            key='test-key'
        )
        
        with patch('src.integrations.database.supabase_client.create_client') as mock_create:
            mock_create.side_effect = Exception("Connection failed")
            
            with pytest.raises(Exception):
                SupabaseClient(config)


if __name__ == "__main__":
    pytest.main([__file__]) 