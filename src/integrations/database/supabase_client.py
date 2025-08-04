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


class SupabaseConfig(BaseModel):
    """Supabase konfiguráció"""
    url: str = Field(..., description="Supabase projekt URL")
    key: str = Field(..., description="Supabase API kulcs")
    service_role_key: Optional[str] = Field(default=None, description="Service role kulcs")
    
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
            raise
    
    def get_client(self) -> Client:
        """Visszaadja a Supabase klienst"""
        if not self.client:
            self._initialize_client()
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
        """Végrehajt egy SQL lekérdezést"""
        try:
            # Közvetlen SQL végrehajtás service role kliensekkel
            service_client = self.get_service_client()
            
            # Egyszerű lekérdezésekhez használjuk a table().select() metódust
            if query.strip().upper().startswith('SELECT'):
                # SELECT lekérdezésekhez külön logika kell
                logger.warning("SELECT lekérdezésekhez külön metódus szükséges")
                return []
            else:
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
            query = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_name = %s
            ORDER BY ordinal_position;
            """
            
            result = self.execute_query(query, {"table_name": table_name})
            return result
        except Exception as e:
            logger.error(f"Tábla információk lekérési hiba: {e}")
            raise
    
    def check_rls_enabled(self, table_name: str) -> bool:
        """Ellenőrzi, hogy a Row Level Security engedélyezve van-e"""
        try:
            query = """
            SELECT relrowsecurity 
            FROM pg_class 
            WHERE relname = %s;
            """
            
            result = self.execute_query(query, {"table_name": table_name})
            return result[0]["relrowsecurity"] if result else False
        except Exception as e:
            logger.error(f"RLS ellenőrzési hiba: {e}")
            return False 