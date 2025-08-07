"""
LangGraph SDK Authentication Configuration

Ez a modul kezeli a LangGraph Cloud szolgáltatáshoz való kapcsolódást
és authentikációt a LangGraph SDK használatával.
"""

import os
from typing import Optional, Dict, Any
from langgraph_sdk import get_client
from langgraph_sdk.client import LangGraphClient
from src.config.logging import get_logger
from src.config.security import get_security_config

logger = get_logger(__name__)


class LangGraphAuthManager:
    """LangGraph SDK authentikáció kezelő"""
    
    def __init__(self):
        self.client: Optional[LangGraphClient] = None
        self.is_authenticated: bool = False
        self.auth_config = self._load_auth_config()
    
    def _load_auth_config(self) -> Dict[str, Any]:
        """LangGraph authentikációs konfiguráció betöltése"""
        return {
            "api_key": os.getenv("LANGGRAPH_API_KEY"),
            "project_id": os.getenv("LANGGRAPH_PROJECT_ID"),
            "environment": os.getenv("LANGGRAPH_ENVIRONMENT", "development"),
            "timeout": int(os.getenv("LANGGRAPH_TIMEOUT", "30")),
        }
    
    async def authenticate(self) -> bool:
        """LangGraph SDK authentikáció"""
        try:
            if not self.auth_config["api_key"]:
                logger.warning("LANGGRAPH_API_KEY nincs beállítva - LangGraph SDK nem használható")
                return False
            
            # LangGraph kliens inicializálása a get_client függvénnyel
            self.client = get_client(
                api_key=self.auth_config["api_key"],
                timeout=self.auth_config["timeout"]
            )
            
            # Kapcsolat tesztelése
            await self._test_connection()
            
            self.is_authenticated = True
            logger.info("✅ LangGraph SDK authentikáció sikeres")
            return True
            
        except Exception as e:
            logger.error(f"❌ LangGraph SDK authentikáció sikertelen: {e}")
            self.is_authenticated = False
            return False
    
    async def _test_connection(self):
        """LangGraph kapcsolat tesztelése"""
        if not self.client:
            raise ValueError("LangGraph kliens nincs inicializálva")
        
        # Egyszerű API hívás a kapcsolat tesztelésére
        # TODO: Implementálni a konkrét API hívást
        pass
    
    def get_client(self) -> Optional[LangGraphClient]:
        """LangGraph kliens visszaadása"""
        if not self.is_authenticated or not self.client:
            logger.warning("LangGraph kliens nem elérhető - nincs authentikálva")
            return None
        return self.client
    
    async def disconnect(self):
        """LangGraph kapcsolat lezárása"""
        if self.client:
            # LangGraph kliens cleanup
            self.client = None
            self.is_authenticated = False
            logger.info("LangGraph SDK kapcsolat lezárva")


# Globális LangGraph auth manager instance
langgraph_auth_manager = LangGraphAuthManager()


async def get_langgraph_client() -> Optional[LangGraphClient]:
    """LangGraph kliens lekérése"""
    if not langgraph_auth_manager.is_authenticated:
        await langgraph_auth_manager.authenticate()
    
    return langgraph_auth_manager.get_client()


async def initialize_langgraph_auth():
    """LangGraph authentikáció inicializálása"""
    logger.info("🔐 LangGraph SDK authentikáció inicializálása...")
    success = await langgraph_auth_manager.authenticate()
    
    if success:
        logger.info("✅ LangGraph SDK authentikáció sikeresen inicializálva")
    else:
        logger.warning("⚠️ LangGraph SDK authentikáció nem sikerült - LangGraph funkciók nem lesznek elérhetők")
    
    return success


async def shutdown_langgraph_auth():
    """LangGraph authentikáció leállítása"""
    await langgraph_auth_manager.disconnect()
    logger.info("LangGraph SDK authentikáció leállítva") 