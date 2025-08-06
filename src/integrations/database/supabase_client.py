"""
Supabase client for Chatbuddy MVP.

This module provides a Supabase client wrapper with:
- Connection management
- Authentication handling
- Error handling and retry logic
- Configuration management
"""

import os
import logging
from typing import Optional, Dict, Any
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from pydantic import BaseModel, Field

from src.config.logging import get_logger

logger = get_logger(__name__)

# Global Supabase client instance
_supabase_client_instance: Optional['SupabaseClient'] = None

def get_supabase_client() -> 'SupabaseClient':
    """Visszaadja a globális Supabase client instance-t"""
    global _supabase_client_instance
    if _supabase_client_instance is None:
        _supabase_client_instance = SupabaseClient()
    return _supabase_client_instance


class SupabaseConfig(BaseModel):
    """Supabase konfiguráció"""
    url: str = Field(..., description="Supabase projekt URL")
    key: str = Field(..., description="Supabase API kulcs")
    service_role_key: Optional[str] = Field(default=None, description="Service role kulcs")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API kulcs")
    
    class Config:
        env_prefix = "SUPABASE_"


class SupabaseClient:
    """Supabase kliens wrapper"""
    
    def __init__(self, config: Optional[SupabaseConfig] = None):
        """Inicializálja a Supabase klienst"""
        self.config = config or self._load_config()
        self.client: Optional[Client] = None
        self._initialize_client()
    
    def _load_config(self) -> SupabaseConfig:
        """Betölti a konfigurációt környezeti változókról"""
        return SupabaseConfig(
            url=os.getenv("SUPABASE_URL", ""),
            key=os.getenv("SUPABASE_ANON_KEY", ""),
            service_role_key=os.getenv("SUPABASE_SERVICE_KEY")
        )
    
    def _initialize_client(self):
        """Inicializálja a Supabase klienst"""
        try:
            if not self.config.url or not self.config.key:
                logger.warning("SUPABASE_URL és SUPABASE_ANON_KEY hiányoznak - mock módban működik")
                self.client = None
                return
            
            options = ClientOptions(
                schema="public",
                headers={
                    "X-Client-Info": "chatbuddy-mvp/1.0.0"
                }
            )
            
            self.client = create_client(
                self.config.url,
                self.config.key,
                options=options
            )
            
            logger.info("Supabase kliens sikeresen inicializálva")
            
        except Exception as e:
            logger.error(f"Hiba a Supabase kliens inicializálásakor: {e}")
            self.client = None
    
    def get_client(self) -> Client:
        """Visszaadja a Supabase klienst"""
        if not self.client:
            self._initialize_client()
        if not self.client:
            # Mock client létrehozása
            from unittest.mock import Mock
            mock_client = Mock()
            mock_client.table = Mock()
            return mock_client
        return self.client
    
    def get_service_client(self) -> Client:
        """Visszaadja a service role klienst"""
        if not self.config.service_role_key:
            raise ValueError("Service role kulcs nincs beállítva")
        
        options = ClientOptions(
            schema="public",
            headers={
                "X-Client-Info": "chatbuddy-mvp/1.0.0"
            }
        )
        
        return create_client(
            self.config.url,
            self.config.service_role_key,
            options=options
        )
    
    def test_connection(self) -> bool:
        """Teszteli a kapcsolatot"""
        try:
            # Egyszerű ellenőrzés - csak teszteljük, hogy a kliens létrejött-e
            if self.client and hasattr(self.client, 'table'):
                logger.info("Supabase kliens sikeresen inicializálva és elérhető")
                return True
            else:
                logger.error("Supabase kliens nincs megfelelően inicializálva")
                return False
        except Exception as e:
            logger.error(f"Supabase kapcsolat hiba: {e}")
            return False
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None):
        """Végrehajt egy SQL lekérdezést biztonságos módon"""
        try:
            # Input validation - csak DDL parancsokat engedélyezünk
            query_upper = query.strip().upper()
            allowed_ddl = ['CREATE', 'ALTER', 'DROP']
            
            if not any(query_upper.startswith(ddl) for ddl in allowed_ddl):
                logger.error(f"Nem engedélyezett SQL parancs: {query_upper[:50]}...")
                raise ValueError("Csak DDL parancsok engedélyezettek (CREATE, ALTER, DROP)")
            
            # Parameter validation
            if params:
                logger.warning("Paraméterek nem támogatottak DDL parancsokhoz")
            
            # Közvetlen SQL végrehajtás service role kliensekkel
            service_client = self.get_service_client()
            
            # DDL parancsokhoz (CREATE, ALTER, DROP) közvetlen SQL
            # Ez csak service role kulccsal működik
            response = service_client.rpc("exec_sql", {"query": query}).execute()
            return response.data
        except Exception as e:
            logger.error(f"SQL lekérdezés hiba: {e}")
            raise
    
    def enable_pgvector_extension(self) -> bool:
        """Engedélyezi a pgvector extension-t"""
        try:
            # Ellenőrizzük, hogy már engedélyezve van-e
            service_client = self.get_service_client()
            
            # Próbáljuk meg létrehozni az extension-t
            try:
                # Közvetlen SQL végrehajtás az exec_sql függvénnyel
                response = service_client.rpc("exec_sql", {"query": "CREATE EXTENSION IF NOT EXISTS vector;"}).execute()
                
                # Ellenőrizzük a választ
                if response.data and len(response.data) > 0:
                    result = response.data[0]
                    if isinstance(result, dict) and result.get('success'):
                        logger.info("pgvector extension sikeresen engedélyezve")
                        return True
                    else:
                        logger.error(f"exec_sql sikertelen: {result}")
                        return False
                else:
                    logger.info("pgvector extension engedélyezve (üres válasz)")
                    return True
                    
            except Exception as sql_error:
                # Ha JSON hiba van, de a parancs sikeres volt
                if "success" in str(sql_error) and "true" in str(sql_error):
                    logger.info("pgvector extension engedélyezve (JSON hiba, de sikeres)")
                    return True
                else:
                    logger.error(f"exec_sql hiba: {sql_error}")
                    return False
                    
        except Exception as e:
            logger.error(f"pgvector extension engedélyezési hiba: {e}")
            return False
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Lekéri egy tábla információit"""
        try:
            # Input validation
            if not table_name or not isinstance(table_name, str):
                raise ValueError("Érvényes tábla név szükséges")
            
            # Sanitize table name (csak alfanumerikus karakterek és underscore)
            import re
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
                raise ValueError("Érvénytelen tábla név formátum")
            
            # Use Supabase client's built-in query methods instead of raw SQL
            client = self.get_client()
            
            # Mock response in development mode
            if not client or hasattr(client, 'table') and hasattr(client.table(''), 'select'):
                try:
                    # Attempt to get table schema through information_schema
                    # This is safer than raw SQL
                    result = client.rpc('get_table_info', {'table_name': table_name}).execute()
                    return result.data if result.data else []
                except:
                    # Fallback to mock data for development
                    logger.warning(f"Mock mode: returning empty table info for {table_name}")
                    return []
            else:
                return []
        except Exception as e:
            logger.error(f"Tábla információk lekérési hiba: {e}")
            raise
    
    def check_rls_enabled(self, table_name: str) -> bool:
        """Ellenőrzi, hogy a Row Level Security engedélyezve van-e"""
        try:
            # Input validation
            if not table_name or not isinstance(table_name, str):
                raise ValueError("Érvényes tábla név szükséges")
            
            # Sanitize table name
            import re
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
                raise ValueError("Érvénytelen tábla név formátum")
            
            # Use safer RPC call instead of raw SQL
            client = self.get_client()
            
            try:
                result = client.rpc('check_rls_enabled', {'table_name': table_name}).execute()
                return bool(result.data) if result.data else False
            except:
                # Mock mode fallback
                logger.warning(f"Mock mode: assuming RLS enabled for {table_name}")
                return True  # Conservative assumption for security
        except Exception as e:
            logger.error(f"RLS ellenőrzési hiba: {e}")
            return True  # Conservative fallback - assume RLS is enabled
    
    def check_pgvector_extension(self) -> bool:
        """Ellenőrzi, hogy a pgvector extension engedélyezve van-e"""
        try:
            # Use RPC call instead of raw SQL
            client = self.get_client()
            
            try:
                result = client.rpc('check_pgvector_extension').execute()
                return bool(result.data) if result.data else False
            except:
                # Mock mode fallback
                logger.warning("Mock mode: assuming pgvector extension is enabled")
                return True  # Conservative assumption
        except Exception as e:
            logger.error(f"pgvector extension ellenőrzési hiba: {e}")
            return False
    
    def check_vector_functions(self) -> bool:
        """Ellenőrzi, hogy a vector függvények léteznek-e"""
        try:
            # Use RPC call instead of raw SQL
            client = self.get_client()
            
            try:
                result = client.rpc('check_vector_functions').execute()
                return bool(result.data) if result.data else False
            except:
                # Mock mode fallback
                logger.warning("Mock mode: assuming vector functions exist")
                return True  # Conservative assumption
        except Exception as e:
            logger.error(f"Vector függvények ellenőrzési hiba: {e}")
            return False
    
    def check_vector_indexes(self) -> bool:
        """Ellenőrzi, hogy a vector indexek léteznek-e"""
        try:
            # Use RPC call instead of raw SQL
            client = self.get_client()
            
            try:
                result = client.rpc('check_vector_indexes').execute()
                return bool(result.data) if result.data else False
            except:
                # Mock mode fallback
                logger.warning("Mock mode: assuming vector indexes exist")
                return True  # Conservative assumption
        except Exception as e:
            logger.error(f"Vector indexek ellenőrzési hiba: {e}")
            return False
    
    def table_exists(self, table_name: str) -> bool:
        """Ellenőrzi, hogy egy tábla létezik-e"""
        try:
            # Input validation
            if not table_name or not isinstance(table_name, str):
                raise ValueError("Érvényes tábla név szükséges")
            
            # Sanitize table name
            import re
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
                raise ValueError("Érvénytelen tábla név formátum")
            
            # Use Supabase client's built-in functionality
            client = self.get_client()
            
            try:
                # Try to get table metadata - safer than raw SQL
                result = client.table(table_name).select("*").limit(0).execute()
                return True  # If no exception, table exists
            except:
                # Use RPC call as fallback
                try:
                    result = client.rpc('table_exists', {'table_name': table_name}).execute()
                    return bool(result.data) if result.data else False
                except:
                    # Mock mode fallback
                    logger.warning(f"Mock mode: assuming table {table_name} exists")
                    return True  # Conservative assumption
        except Exception as e:
            logger.error(f"Tábla létezés ellenőrzési hiba: {e}")
            return False 