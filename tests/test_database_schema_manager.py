"""
Database Schema Manager Tests - Chatbuddy MVP.

Ez a modul teszteli a database schema manager funkcionalitását,
beleértve a táblák létrehozását, migrációkat és schema validációt.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any, List

from src.integrations.database.schema_manager import (
    SchemaManager, ColumnDefinition, TableDefinition, IndexDefinition, 
    ConstraintDefinition, Migration, MigrationStatus
)


class TestSchemaManager:
    """Tests for schema manager."""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Create a mock Supabase client for testing."""
        with patch('src.integrations.database.schema_manager.SupabaseClient') as mock_client:
            mock_client.return_value = Mock()
            yield mock_client.return_value
    
    def test_schema_manager_initialization(self, mock_supabase_client):
        """Test schema manager initialization."""
        manager = SchemaManager(mock_supabase_client)
        
        assert manager is not None
        assert manager.supabase == mock_supabase_client
    
    def test_setup_pgvector_extension_success(self, mock_supabase_client):
        """Test successful pgvector extension setup."""
        mock_supabase_client.enable_pgvector_extension.return_value = True
        
        manager = SchemaManager(mock_supabase_client)
        result = manager.setup_pgvector_extension()
        
        assert result is True
        mock_supabase_client.enable_pgvector_extension.assert_called_once()
    
    def test_setup_pgvector_extension_failure(self, mock_supabase_client):
        """Test failed pgvector extension setup."""
        mock_supabase_client.enable_pgvector_extension.return_value = False
        
        manager = SchemaManager(mock_supabase_client)
        result = manager.setup_pgvector_extension()
        
        assert result is False
        mock_supabase_client.enable_pgvector_extension.assert_called_once()
    
    def test_table_definition_validation(self):
        """Test table definition validation."""
        # Valid table definition
        columns = [ColumnDefinition("id", "UUID", primary_key=True)]
        table_def = TableDefinition("valid_table", columns)
        assert table_def is not None
        
        # Invalid table name
        with pytest.raises(ValueError):
            TableDefinition("", columns)
        
        # No columns
        with pytest.raises(ValueError):
            TableDefinition("empty_table", [])
        
        # Duplicate column names
        columns = [
            ColumnDefinition("id", "UUID"),
            ColumnDefinition("id", "INTEGER")  # Duplicate name
        ]
        with pytest.raises(ValueError):
            TableDefinition("duplicate_columns", columns)


class TestColumnDefinition:
    """Tests for column definition."""
    
    def test_column_definition_creation(self):
        """Test column definition creation."""
        col_def = ColumnDefinition(
            name="test_column",
            data_type="VARCHAR(255)",
            nullable=False,
            primary_key=True,
            unique=True,
            default="'default_value'",
            check_constraint="LENGTH(test_column) > 0"
        )
        
        assert col_def.name == "test_column"
        assert col_def.data_type == "VARCHAR(255)"
        assert col_def.nullable is False
        assert col_def.primary_key is True
        assert col_def.unique is True
        assert col_def.default == "'default_value'"
        assert col_def.check_constraint == "LENGTH(test_column) > 0"
    
    def test_column_definition_validation(self):
        """Test column definition validation."""
        # Valid column
        col_def = ColumnDefinition("valid_column", "TEXT")
        assert col_def is not None
        
        # Invalid column name
        with pytest.raises(ValueError):
            ColumnDefinition("", "TEXT")
        
        # Invalid data type
        with pytest.raises(ValueError):
            ColumnDefinition("test", "")
        
        # Invalid default value format
        with pytest.raises(ValueError):
            ColumnDefinition("test", "TEXT", default="invalid_default")
    
    def test_column_definition_sql_generation(self):
        """Test SQL generation for column definition."""
        col_def = ColumnDefinition(
            name="test_column",
            data_type="VARCHAR(255)",
            nullable=False,
            primary_key=True,
            default="'test'"
        )
        
        sql = col_def.to_sql()
        expected = "test_column VARCHAR(255) NOT NULL PRIMARY KEY DEFAULT 'test'"
        assert sql == expected
    
    def test_column_definition_with_check_constraint(self):
        """Test column definition with check constraint."""
        col_def = ColumnDefinition(
            name="age",
            data_type="INTEGER",
            check_constraint="age >= 0 AND age <= 150"
        )
        
        sql = col_def.to_sql()
        expected = "age INTEGER CHECK (age >= 0 AND age <= 150)"
        assert sql == expected


class TestIndexDefinition:
    """Tests for index definition."""
    
    def test_index_definition_creation(self):
        """Test index definition creation."""
        index_def = IndexDefinition(
            name="idx_test",
            columns=["column1", "column2"],
            unique=True,
            method="btree",
            where_clause="column1 IS NOT NULL"
        )
        
        assert index_def.name == "idx_test"
        assert index_def.columns == ["column1", "column2"]
        assert index_def.unique is True
        assert index_def.method == "btree"
        assert index_def.where_clause == "column1 IS NOT NULL"
    
    def test_index_definition_validation(self):
        """Test index definition validation."""
        # Valid index
        index_def = IndexDefinition("valid_index", ["column1"])
        assert index_def is not None
        
        # Invalid index name
        with pytest.raises(ValueError):
            IndexDefinition("", ["column1"])
        
        # No columns
        with pytest.raises(ValueError):
            IndexDefinition("empty_index", [])
        
        # Invalid method
        with pytest.raises(ValueError):
            IndexDefinition("test", ["column1"], method="invalid_method")
    
    def test_index_definition_sql_generation(self):
        """Test SQL generation for index definition."""
        index_def = IndexDefinition(
            name="idx_test",
            columns=["column1", "column2"],
            unique=True,
            method="btree"
        )
        
        sql = index_def.to_sql("test_table")
        expected = "CREATE UNIQUE INDEX idx_test ON test_table (column1, column2)"
        assert sql == expected
    
    def test_index_definition_with_where_clause(self):
        """Test index definition with WHERE clause."""
        index_def = IndexDefinition(
            name="idx_partial",
            columns=["column1"],
            where_clause="column1 > 0"
        )
        
        sql = index_def.to_sql("test_table")
        expected = "CREATE INDEX idx_partial ON test_table (column1) WHERE column1 > 0"
        assert sql == expected


class TestConstraintDefinition:
    """Tests for constraint definition."""
    
    def test_constraint_definition_creation(self):
        """Test constraint definition creation."""
        constraint_def = ConstraintDefinition(
            name="check_positive",
            definition="CHECK (value > 0)",
            deferrable=True,
            initially_deferred=True
        )
        
        assert constraint_def.name == "check_positive"
        assert constraint_def.definition == "CHECK (value > 0)"
        assert constraint_def.deferrable is True
        assert constraint_def.initially_deferred is True
    
    def test_constraint_definition_validation(self):
        """Test constraint definition validation."""
        # Valid constraint
        constraint_def = ConstraintDefinition("valid_constraint", "CHECK (value > 0)")
        assert constraint_def is not None
        
        # Invalid constraint name
        with pytest.raises(ValueError):
            ConstraintDefinition("", "CHECK (value > 0)")
        
        # Invalid definition
        with pytest.raises(ValueError):
            ConstraintDefinition("test", "")
    
    def test_constraint_definition_sql_generation(self):
        """Test SQL generation for constraint definition."""
        constraint_def = ConstraintDefinition(
            name="check_positive",
            definition="CHECK (value > 0)",
            deferrable=True,
            initially_deferred=True
        )
        
        sql = constraint_def.to_sql()
        expected = "CONSTRAINT check_positive CHECK (value > 0) DEFERRABLE INITIALLY DEFERRED"
        assert sql == expected


class TestSchemaManagerAsync:
    """Tests for schema manager async methods."""
    
    @pytest.fixture
    async def mock_schema_manager(self):
        """Create a mock schema manager for testing."""
        with patch('src.integrations.database.schema_manager.SupabaseClient') as mock_client:
            mock_client.return_value = AsyncMock()
            
            manager = SchemaManager(mock_client.return_value)
            yield manager, mock_client.return_value
    
    @pytest.mark.asyncio
    async def test_schema_manager_initialization(self, mock_schema_manager):
        """Test schema manager initialization."""
        manager, mock_client = mock_schema_manager
        
        assert manager is not None
        assert hasattr(manager, 'supabase')
        assert hasattr(manager, 'tables')
    
    @pytest.mark.asyncio
    async def test_create_table_success(self, mock_schema_manager):
        """Test successful table creation."""
        manager, mock_client = mock_schema_manager
        
        # Mock successful table creation
        mock_client.execute_sql.return_value = {"success": True}
        
        columns = [
            ColumnDefinition("id", "UUID", primary_key=True, default="gen_random_uuid()"),
            ColumnDefinition("name", "VARCHAR(255)", nullable=False)
        ]
        
        table_def = TableDefinition("test_table", columns)
        
        result = await manager.create_table(table_def)
        
        assert result is True
        mock_client.execute_sql.assert_called_once()
        
        # Verify SQL contains table creation
        call_args = mock_client.execute_sql.call_args[0][0]
        assert "CREATE TABLE test_table" in call_args
        assert "id UUID PRIMARY KEY" in call_args
        assert "name VARCHAR(255) NOT NULL" in call_args
    
    @pytest.mark.asyncio
    async def test_create_table_with_indexes(self, mock_schema_manager):
        """Test table creation with indexes."""
        manager, mock_client = mock_schema_manager
        
        mock_client.execute_sql.return_value = {"success": True}
        
        columns = [ColumnDefinition("id", "UUID", primary_key=True)]
        indexes = [IndexDefinition("idx_name", ["name"], unique=True)]
        
        table_def = TableDefinition("test_table", columns, indexes=indexes)
        
        result = await manager.create_table(table_def)
        
        assert result is True
        # Should have multiple SQL calls: table creation + index creation
        assert mock_client.execute_sql.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_create_table_with_constraints(self, mock_schema_manager):
        """Test table creation with constraints."""
        manager, mock_client = mock_schema_manager
        
        mock_client.execute_sql.return_value = {"success": True}
        
        columns = [ColumnDefinition("id", "UUID", primary_key=True)]
        constraints = [ConstraintDefinition("check_positive", "CHECK (value > 0)")]
        
        table_def = TableDefinition("test_table", columns, constraints=constraints)
        
        result = await manager.create_table(table_def)
        
        assert result is True
        call_args = mock_client.execute_sql.call_args[0][0]
        assert "CONSTRAINT check_positive CHECK (value > 0)" in call_args
    
    @pytest.mark.asyncio
    async def test_create_table_failure(self, mock_schema_manager):
        """Test table creation failure."""
        manager, mock_client = mock_schema_manager
        
        mock_client.execute_sql.side_effect = Exception("Database error")
        
        columns = [ColumnDefinition("id", "UUID", primary_key=True)]
        table_def = TableDefinition("test_table", columns)
        
        result = await manager.create_table(table_def)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_drop_table_success(self, mock_schema_manager):
        """Test successful table drop."""
        manager, mock_client = mock_schema_manager
        
        mock_client.execute_sql.return_value = {"success": True}
        
        result = await manager.drop_table("test_table")
        
        assert result is True
        mock_client.execute_sql.assert_called_once_with("DROP TABLE IF EXISTS test_table CASCADE")
    
    @pytest.mark.asyncio
    async def test_drop_table_failure(self, mock_schema_manager):
        """Test table drop failure."""
        manager, mock_client = mock_schema_manager
        
        mock_client.execute_sql.side_effect = Exception("Drop failed")
        
        with pytest.raises(Exception, match="Drop failed"):
            await manager.drop_table("test_table")
    
    @pytest.mark.asyncio
    async def test_table_exists_true(self, mock_schema_manager):
        """Test table exists check when table exists."""
        manager, mock_client = mock_schema_manager
        
        mock_client.execute_sql.return_value = {"data": [{"exists": True}]}
        
        exists = await manager.table_exists("test_table")
        
        assert exists is True
        mock_client.execute_sql.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_table_exists_false(self, mock_schema_manager):
        """Test table exists check when table doesn't exist."""
        manager, mock_client = mock_schema_manager
        
        mock_client.execute_sql.return_value = {"data": [{"exists": False}]}
        
        exists = await manager.table_exists("test_table")
        
        assert exists is False
    
    @pytest.mark.asyncio
    async def test_get_table_schema(self, mock_schema_manager):
        """Test getting table schema."""
        manager, mock_client = mock_schema_manager
        
        mock_schema = {
            "columns": [
                {"name": "id", "type": "uuid", "nullable": False, "primary_key": True},
                {"name": "name", "type": "varchar", "nullable": False}
            ],
            "indexes": [
                {"name": "idx_name", "columns": ["name"], "unique": True}
            ]
        }
        
        mock_client.execute_sql.return_value = {"data": mock_schema}
        
        schema = await manager.get_table_schema("test_table")
        
        assert schema is not None
        assert "columns" in schema
        assert "indexes" in schema
        assert len(schema["columns"]) == 2
    
    @pytest.mark.asyncio
    async def test_add_column_success(self, mock_schema_manager):
        """Test successful column addition."""
        manager, mock_client = mock_schema_manager
        
        mock_client.execute_sql.return_value = {"success": True}
        
        column_def = ColumnDefinition("new_column", "TEXT", nullable=True)
        
        result = await manager.add_column("test_table", column_def)
        
        assert result is True
        call_args = mock_client.execute_sql.call_args[0][0]
        assert "ALTER TABLE test_table ADD COLUMN new_column TEXT" in call_args
    
    @pytest.mark.asyncio
    async def test_drop_column_success(self, mock_schema_manager):
        """Test successful column drop."""
        manager, mock_client = mock_schema_manager
        
        mock_client.execute_sql.return_value = {"success": True}
        
        result = await manager.drop_column("test_table", "old_column")
        
        assert result is True
        mock_client.execute_sql.assert_called_once_with(
            "ALTER TABLE test_table DROP COLUMN old_column"
        )
    
    @pytest.mark.asyncio
    async def test_create_index_success(self, mock_schema_manager):
        """Test successful index creation."""
        manager, mock_client = mock_schema_manager
        
        mock_client.execute_sql.return_value = {"success": True}
        
        index_def = IndexDefinition("idx_test", ["column1", "column2"], unique=True)
        
        result = await manager.create_index("test_table", index_def)
        
        assert result is True
        call_args = mock_client.execute_sql.call_args[0][0]
        assert "CREATE UNIQUE INDEX idx_test ON test_table" in call_args
    
    @pytest.mark.asyncio
    async def test_drop_index_success(self, mock_schema_manager):
        """Test successful index drop."""
        manager, mock_client = mock_schema_manager
        
        mock_client.execute_sql.return_value = {"success": True}
        
        result = await manager.drop_index("idx_test")
        
        assert result is True
        mock_client.execute_sql.assert_called_once_with("DROP INDEX IF EXISTS idx_test")
    
    @pytest.mark.asyncio
    async def test_add_constraint_success(self, mock_schema_manager):
        """Test successful constraint addition."""
        manager, mock_client = mock_schema_manager
        
        mock_client.execute_sql.return_value = {"success": True}
        
        constraint_def = ConstraintDefinition("check_positive", "CHECK (value > 0)")
        
        result = await manager.add_constraint("test_table", constraint_def)
        
        assert result is True
        call_args = mock_client.execute_sql.call_args[0][0]
        assert "ALTER TABLE test_table ADD CONSTRAINT check_positive CHECK (value > 0)" in call_args
    
    @pytest.mark.asyncio
    async def test_drop_constraint_success(self, mock_schema_manager):
        """Test successful constraint drop."""
        manager, mock_client = mock_schema_manager
        
        mock_client.execute_sql.return_value = {"success": True}
        
        result = await manager.drop_constraint("test_table", "check_positive")
        
        assert result is True
        mock_client.execute_sql.assert_called_once_with(
            "ALTER TABLE test_table DROP CONSTRAINT check_positive"
        )


class TestMigration:
    """Tests for migration functionality."""
    
    def test_migration_creation(self):
        """Test migration creation."""
        migration = Migration(
            id="001_create_users_table",
            name="Create users table",
            sql="CREATE TABLE users (id UUID PRIMARY KEY)",
            dependencies=[],
            status=MigrationStatus.PENDING
        )
        
        assert migration.id == "001_create_users_table"
        assert migration.name == "Create users table"
        assert migration.sql == "CREATE TABLE users (id UUID PRIMARY KEY)"
        assert migration.dependencies == []
        assert migration.status == MigrationStatus.PENDING
    
    def test_migration_with_dependencies(self):
        """Test migration with dependencies."""
        migration = Migration(
            id="002_add_user_profile",
            name="Add user profile table",
            sql="CREATE TABLE user_profiles (user_id UUID REFERENCES users(id))",
            dependencies=["001_create_users_table"],
            status=MigrationStatus.PENDING
        )
        
        assert len(migration.dependencies) == 1
        assert "001_create_users_table" in migration.dependencies
    
    def test_migration_validation(self):
        """Test migration validation."""
        # Valid migration
        migration = Migration("001", "Test", "SELECT 1")
        assert migration is not None
        
        # Invalid migration ID
        with pytest.raises(ValueError):
            Migration("", "Test", "SELECT 1")
        
        # Invalid SQL
        with pytest.raises(ValueError):
            Migration("001", "Test", "")


class TestSchemaManagerMigrations:
    """Tests for schema manager migration functionality."""
    
    @pytest.fixture
    async def mock_schema_manager(self):
        """Create a mock schema manager for testing."""
        with patch('src.integrations.database.schema_manager.SupabaseClient') as mock_client:
            mock_client.return_value = AsyncMock()
            
            manager = SchemaManager(mock_client.return_value)
            yield manager, mock_client.return_value
    
    @pytest.mark.asyncio
    async def test_create_migration_table(self, mock_schema_manager):
        """Test migration table creation."""
        manager, mock_client = mock_schema_manager
        
        mock_client.execute_sql.return_value = {"success": True}
        
        result = await manager.create_migration_table()
        
        assert result is True
        call_args = mock_client.execute_sql.call_args[0][0]
        assert "CREATE TABLE IF NOT EXISTS migrations" in call_args
    
    @pytest.mark.asyncio
    async def test_register_migration(self, mock_schema_manager):
        """Test migration registration."""
        manager, mock_client = mock_schema_manager
        
        mock_client.execute_sql.return_value = {"success": True}
        
        migration = Migration("001", "Test migration", "SELECT 1")
        
        result = await manager.register_migration(migration)
        
        assert result is True
        call_args = mock_client.execute_sql.call_args[0][0]
        assert "INSERT INTO migrations" in call_args
    
    @pytest.mark.asyncio
    async def test_get_applied_migrations(self, mock_schema_manager):
        """Test getting applied migrations."""
        manager, mock_client = mock_schema_manager
        
        mock_data = [
            {"id": "001", "name": "First migration", "applied_at": "2024-01-01"},
            {"id": "002", "name": "Second migration", "applied_at": "2024-01-02"}
        ]
        
        mock_client.execute_sql.return_value = {"data": mock_data}
        
        migrations = await manager.get_applied_migrations()
        
        assert len(migrations) == 2
        assert migrations[0]["id"] == "001"
        assert migrations[1]["id"] == "002"
    
    @pytest.mark.asyncio
    async def test_apply_migration_success(self, mock_schema_manager):
        """Test successful migration application."""
        manager, mock_client = mock_schema_manager
        
        mock_client.execute_sql.return_value = {"success": True}
        
        migration = Migration("001", "Test migration", "CREATE TABLE test (id INT)")
        
        result = await manager.apply_migration(migration)
        
        assert result is True
        # Should have multiple calls: migration SQL + registration
        assert mock_client.execute_sql.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_apply_migration_failure(self, mock_schema_manager):
        """Test migration application failure."""
        manager, mock_client = mock_schema_manager
        
        mock_client.execute_sql.side_effect = Exception("Migration failed")
        
        migration = Migration("001", "Test migration", "INVALID SQL")
        
        with pytest.raises(Exception, match="Migration failed"):
            await manager.apply_migration(migration)
    
    @pytest.mark.asyncio
    async def test_migrate_all_pending(self, mock_schema_manager):
        """Test migrating all pending migrations."""
        manager, mock_client = mock_schema_manager
        
        # Mock applied migrations
        mock_client.execute_sql.side_effect = [
            {"data": [{"id": "001"}]},  # Applied migrations
            {"success": True},  # Migration 002 SQL
            {"success": True},  # Migration 002 registration
            {"success": True},  # Migration 003 SQL
            {"success": True}   # Migration 003 registration
        ]
        
        pending_migrations = [
            Migration("002", "Second migration", "CREATE TABLE table2 (id INT)"),
            Migration("003", "Third migration", "CREATE TABLE table3 (id INT)")
        ]
        
        result = await manager.migrate_all(pending_migrations)
        
        assert result is True
        assert mock_client.execute_sql.call_count >= 5
    
    @pytest.mark.asyncio
    async def test_migrate_with_dependencies(self, mock_schema_manager):
        """Test migration with dependencies."""
        manager, mock_client = mock_schema_manager

        # Mock applied migrations - only 001 is applied
        mock_client.execute_sql.side_effect = [
            {"data": [{"id": "001"}]},  # Applied migrations
            {"success": True},  # Migration 002 SQL
            {"success": True},  # Migration 002 registration
            {"success": True},  # Migration 003 SQL
            {"success": True}   # Migration 003 registration
        ]

        migrations = [
            Migration("001", "First", "CREATE TABLE table1 (id INT)"),
            Migration("002", "Second", "CREATE TABLE table2 (id INT)", dependencies=["001"]),
            Migration("003", "Third", "CREATE TABLE table3 (id INT)", dependencies=["002"])
        ]

        result = await manager.migrate_all(migrations)

        assert result is True
        # Should apply migrations in dependency order


class TestSchemaValidation:
    """Tests for schema validation."""
    
    @pytest.fixture
    async def mock_schema_manager(self):
        """Create a mock schema manager for testing."""
        with patch('src.integrations.database.schema_manager.SupabaseClient') as mock_client:
            mock_client.return_value = AsyncMock()
            
            manager = SchemaManager(mock_client.return_value)
            yield manager, mock_client.return_value
    
    @pytest.mark.asyncio
    async def test_validate_table_schema(self, mock_schema_manager):
        """Test table schema validation."""
        manager, mock_client = mock_schema_manager
        
        # Mock current schema - get_table_schema returns the data directly
        current_schema = [
            {"column_name": "id", "data_type": "UUID", "is_nullable": "NO"},
            {"column_name": "name", "data_type": "VARCHAR(255)", "is_nullable": "NO"}
        ]
        
        mock_client.execute_sql.return_value = {"data": current_schema}
        
        # Define expected schema
        expected_columns = [
            ColumnDefinition("id", "UUID", primary_key=True),
            ColumnDefinition("name", "VARCHAR(255)", nullable=False)
        ]
        expected_table = TableDefinition("test_table", expected_columns)
        
        is_valid = await manager.validate_table_schema("test_table", expected_table)
        
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_validate_table_schema_mismatch(self, mock_schema_manager):
        """Test table schema validation with mismatch."""
        manager, mock_client = mock_schema_manager
        
        # Mock current schema (different from expected) - get_table_schema returns the data directly
        current_schema = [
            {"column_name": "id", "data_type": "UUID", "is_nullable": "NO"},
            {"column_name": "old_name", "data_type": "VARCHAR(255)", "is_nullable": "NO"}  # Different column
        ]
        
        mock_client.execute_sql.return_value = {"data": current_schema}
        
        # Define expected schema
        expected_columns = [
            ColumnDefinition("id", "UUID", primary_key=True),
            ColumnDefinition("name", "VARCHAR(255)", nullable=False)  # Different column name
        ]
        expected_table = TableDefinition("test_table", expected_columns)
        
        is_valid = await manager.validate_table_schema("test_table", expected_table)
        
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_get_schema_differences(self, mock_schema_manager):
        """Test getting schema differences."""
        manager, mock_client = mock_schema_manager
        
        # Mock current schema - get_table_schema returns the data directly
        current_schema = [
            {"column_name": "id", "data_type": "UUID", "is_nullable": "NO"},
            {"column_name": "name", "data_type": "VARCHAR(255)", "is_nullable": "NO"}
        ]
        
        mock_client.execute_sql.return_value = {"data": current_schema}
        
        # Define expected schema with differences
        expected_columns = [
            ColumnDefinition("id", "UUID", primary_key=True),
            ColumnDefinition("name", "VARCHAR(255)", nullable=False),
            ColumnDefinition("email", "VARCHAR(255)", nullable=True)  # New column
        ]
        expected_table = TableDefinition("test_table", expected_columns)
        
        differences = await manager.get_schema_differences("test_table", expected_table)
        
        assert len(differences) > 0
        assert "email" in str(differences)  # Should detect missing column


class TestSchemaManagerIntegration:
    """Integration tests for schema manager."""
    
    @pytest.fixture
    async def mock_schema_manager(self):
        """Create a mock schema manager for testing."""
        with patch('src.integrations.database.schema_manager.SupabaseClient') as mock_client:
            mock_client.return_value = AsyncMock()
            
            manager = SchemaManager(mock_client.return_value)
            yield manager, mock_client.return_value
    
    @pytest.mark.asyncio
    async def test_complete_table_lifecycle(self, mock_schema_manager):
        """Test complete table lifecycle."""
        manager, mock_client = mock_schema_manager
        
        # Mock all operations - create_table may make multiple calls
        def mock_execute_sql(sql, params=None):
            if "EXISTS" in sql and "information_schema.tables" in sql:
                return {"data": [{"exists": True}]}
            else:
                return {"success": True}
        
        mock_client.execute_sql.side_effect = mock_execute_sql
        
        # Create table
        columns = [
            ColumnDefinition("id", "UUID", primary_key=True),
            ColumnDefinition("name", "VARCHAR(255)", nullable=False)
        ]
        table_def = TableDefinition("test_table", columns)
        
        # Test table creation
        result = await manager.create_table(table_def)
        assert result is True
        
        # Test table exists
        exists = await manager.table_exists("test_table")
        assert exists is True
        
        # Test add column
        new_column = ColumnDefinition("email", "VARCHAR(255)", nullable=True)
        result = await manager.add_column("test_table", new_column)
        assert result is True
        
        # Test create index
        index_def = IndexDefinition("idx_name", ["name"], unique=True)
        result = await manager.create_index("test_table", index_def)
        assert result is True
        
        # Test drop table
        result = await manager.drop_table("test_table")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_migration_workflow(self, mock_schema_manager):
        """Test complete migration workflow."""
        manager, mock_client = mock_schema_manager
        
        # Mock migration operations
        mock_client.execute_sql.side_effect = [
            {"success": True},  # Create migration table
            {"data": []},  # No applied migrations
            {"success": True},  # Apply migration 001
            {"success": True},  # Register migration 001
            {"success": True},  # Apply migration 002
            {"success": True},  # Register migration 002
            {"data": [{"id": "001"}, {"id": "002"}]}  # Applied migrations
        ]
        
        # Create migration table
        result = await manager.create_migration_table()
        assert result is True
        
        # Define migrations
        migrations = [
            Migration("001", "Create users table", "CREATE TABLE users (id UUID PRIMARY KEY)"),
            Migration("002", "Add user profiles", "CREATE TABLE profiles (user_id UUID REFERENCES users(id))")
        ]
        
        # Apply migrations
        result = await manager.migrate_all(migrations)
        assert result is True
        
        # Check applied migrations
        applied = await manager.get_applied_migrations()
        assert len(applied) == 2
        assert applied[0]["id"] == "001"
        assert applied[1]["id"] == "002" 