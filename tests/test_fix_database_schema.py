import pytest
from unittest.mock import Mock, patch
from src.integrations.database.fix_database_schema import DatabaseSchemaFixer, main
import os
import asyncio
from typing import List, Dict, Any

@pytest.fixture
def mock_supabase_client():
    """Mock SupabaseClient fixture"""
    with patch('src.integrations.database.fix_database_schema.SupabaseClient') as mock:
        client = Mock()
        mock.return_value = client
        yield client

@pytest.fixture
def schema_fixer(mock_supabase_client):
    """DatabaseSchemaFixer fixture"""
    return DatabaseSchemaFixer()

class TestDatabaseSchemaFixer:
    """DatabaseSchemaFixer tesztek"""

    def test_initialization(self, schema_fixer, mock_supabase_client):
        """Teszteli az osztály inicializálását"""
        assert schema_fixer is not None
        assert schema_fixer.supabase_client == mock_supabase_client

    def test_fix_products_table_success(self, schema_fixer, mock_supabase_client):
        """Teszteli a products tábla sikeres javítását"""
        # Mock a sikeres SQL végrehajtást
        mock_supabase_client.execute_query.return_value = {"success": True}

        result = schema_fixer.fix_products_table()
        assert result is True

        # Ellenőrizzük, hogy minden SQL parancs végrehajtásra került
        expected_calls = 17  # A fix_commands lista hossza
        assert mock_supabase_client.execute_query.call_count == expected_calls

    def test_fix_products_table_partial_success(self, schema_fixer, mock_supabase_client):
        """Teszteli a products tábla részleges javítását"""
        # Az első 10 hívás sikeres, a többi sikertelen
        mock_supabase_client.execute_query.side_effect = [
            {"success": True} for _ in range(10)
        ] + [None for _ in range(7)]

        result = schema_fixer.fix_products_table()
        assert result is False

    def test_fix_products_table_with_json_error(self, schema_fixer, mock_supabase_client):
        """Teszteli a JSON parsing hibák kezelését"""
        # Mock egy JSON parsing hibát
        class JSONError(Exception):
            def __str__(self):
                return "JSON could not be generated but success"

        mock_supabase_client.execute_query.side_effect = JSONError()
        
        result = schema_fixer.fix_products_table()
        assert result is True  # Még mindig sikeresnek tekintjük

    def test_fix_products_table_failure(self, schema_fixer, mock_supabase_client):
        """Teszteli a products tábla javításának hibáját"""
        # Mock egy kritikus hibát
        mock_supabase_client.execute_query.side_effect = Exception("Critical error")

        result = schema_fixer.fix_products_table()
        assert result is False

    def test_verify_fix_success(self, schema_fixer, mock_supabase_client):
        """Teszteli a sikeres javítás ellenőrzését"""
        # Mock a sikeres ellenőrzést
        mock_columns = [
            {"column_name": "id", "data_type": "uuid", "is_nullable": "NO"},
            {"column_name": "name", "data_type": "text", "is_nullable": "NO"},
            {"column_name": "brand", "data_type": "text", "is_nullable": "YES"},
            {"column_name": "embedding", "data_type": "vector", "is_nullable": "YES"}
        ]
        mock_supabase_client.execute_query.return_value = mock_columns

        result = schema_fixer.verify_fix()
        assert result is True

    def test_verify_fix_failure(self, schema_fixer, mock_supabase_client):
        """Teszteli a sikertelen javítás ellenőrzését"""
        # Mock egy üres eredményt
        mock_supabase_client.execute_query.return_value = None

        result = schema_fixer.verify_fix()
        assert result is False

    def test_verify_fix_error(self, schema_fixer, mock_supabase_client):
        """Teszteli az ellenőrzés hibáját"""
        # Mock egy hibát
        mock_supabase_client.execute_query.side_effect = Exception("Verification error")

        result = schema_fixer.verify_fix()
        assert result is False

@pytest.mark.asyncio
async def test_main_success(mock_supabase_client):
    """Teszteli a main függvény sikeres futását"""
    # Mock környezeti változókat
    env_vars = {
        "SUPABASE_URL": "http://test.com",
        "SUPABASE_ANON_KEY": "test_anon_key",
        "SUPABASE_SERVICE_KEY": "test_service_key"
    }
    
    with patch.dict(os.environ, env_vars):
        # Mock a sikeres javítást és ellenőrzést
        mock_supabase_client.execute_query.return_value = {"success": True}
        
        # Futtatjuk a main függvényt
        await main()
        
        # Ellenőrizzük a hívásokat
        assert mock_supabase_client.execute_query.called

@pytest.mark.asyncio
async def test_main_missing_env_vars():
    """Teszteli a main függvényt hiányzó környezeti változókkal"""
    # Töröljük a környezeti változókat
    with patch.dict(os.environ, {}, clear=True):
        # Futtatjuk a main függvényt
        await main()
        # Nem kellene hibát dobnia, csak logolnia

@pytest.mark.asyncio
async def test_main_critical_error(mock_supabase_client):
    """Teszteli a main függvény kritikus hibáját"""
    # Mock környezeti változókat
    env_vars = {
        "SUPABASE_URL": "http://test.com",
        "SUPABASE_ANON_KEY": "test_anon_key",
        "SUPABASE_SERVICE_KEY": "test_service_key"
    }
    
    with patch.dict(os.environ, env_vars):
        # Mock egy kritikus hibát
        mock_supabase_client.execute_query.side_effect = Exception("Critical error")
        
        # Futtatjuk a main függvényt és ellenőrizzük a hibát
        # A sys.exit() nem dob SystemExit kivételt a tesztben, ezért mock-oljuk
        with patch('sys.exit') as mock_exit:
            await main()
            mock_exit.assert_called_once_with(1)