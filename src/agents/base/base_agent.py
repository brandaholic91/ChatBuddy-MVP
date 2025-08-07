"""
Base Agent - Közös alaposztály minden ágenshez.

Ez a modul implementálja a közös funkcionalitást, amelyet minden ágens használ.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from ...models.agent import AgentType


@dataclass
class BaseDependencies:
    """Közös ágens függőségek."""
    user_context: Dict[str, Any]
    supabase_client: Optional[Any] = None
    webshop_api: Optional[Any] = None
    security_context: Optional[Any] = None
    audit_logger: Optional[Any] = None


class BaseResponse(BaseModel):
    """Közös válasz struktúra minden ágenshez."""
    response_text: str = Field(description="Agent válasza")
    confidence: float = Field(description="Bizonyosság", ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(description="Metaadatok", default_factory=dict)


class BaseAgent(ABC):
    """
    Közös ágens alaposztály.
    
    Az összes ágens ebből az osztályból örököl, és implementálja 
    a közös funkcionalitásokat.
    """
    
    def __init__(self, model: str = 'openai:gpt-4o'):
        """
        Ágens inicializálása.
        
        Args:
            model: Használandó LLM modell
        """
        self.model = model
        self._agent: Optional[Agent] = None
    
    @property
    @abstractmethod
    def agent_type(self) -> AgentType:
        """Ágens típusa."""
        pass
    
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Rendszer prompt az ágenshez."""
        pass
    
    @property
    @abstractmethod
    def dependencies_type(self) -> type:
        """Függőség típus."""
        pass
    
    @property
    @abstractmethod
    def response_type(self) -> type:
        """Válasz típus."""
        pass
    
    def create_agent(self) -> Agent:
        """
        Pydantic AI ágens létrehozása.
        
        Returns:
            Konfigurált ágens instance
        """
        if self._agent is not None:
            return self._agent
        
        agent = Agent(
            self.model,
            deps_type=self.dependencies_type,
            result_type=self.response_type,
            system_prompt=self.system_prompt
        )
        
        # Regisztráljuk a tool-okat
        self._register_tools(agent)
        
        self._agent = agent
        return agent
    
    @abstractmethod
    def _register_tools(self, agent: Agent) -> None:
        """
        Ágens-specifikus tool-ok regisztrálása.
        
        Args:
            agent: Pydantic AI ágens
        """
        pass
    
    async def run(self, message: str, dependencies: BaseDependencies) -> BaseResponse:
        """
        Ágens futtatása.
        
        Args:
            message: Felhasználói üzenet
            dependencies: Ágens függőségei
            
        Returns:
            Ágens válasza
        """
        try:
            agent = self.create_agent()
            result = await agent.run(message, deps=dependencies)
            return result.data
        except Exception as e:
            return await self._handle_error(e, message, dependencies)
    
    async def _handle_error(self, error: Exception, message: str, dependencies: BaseDependencies) -> BaseResponse:
        """
        Hibakezelés közös implementációja.
        
        Args:
            error: Történt hiba
            message: Eredeti üzenet
            dependencies: Függőségek
            
        Returns:
            Hiba válasz
        """
        error_response = BaseResponse(
            response_text=f"Sajnálom, hiba történt a kérés feldolgozása során: {str(error)}",
            confidence=0.0,
            metadata={
                "error_type": type(error).__name__,
                "original_message": message,
                "agent_type": self.agent_type.value if hasattr(self.agent_type, 'value') else str(self.agent_type),
                "error_message": str(error)
            }
        )
        
        # Audit logging ha elérhető
        if dependencies.audit_logger:
            await dependencies.audit_logger.log_error(
                user_id=dependencies.user_context.get("user_id", "anonymous"),
                agent_type=self.agent_type.value if hasattr(self.agent_type, 'value') else str(self.agent_type),
                error_message=str(error),
                details={"message": message}
            )
        
        return error_response
    
    async def _log_data_access(self, dependencies: BaseDependencies, operation: str, success: bool, details: Dict[str, Any] = None) -> None:
        """
        Adathozzáférés naplózása.
        
        Args:
            dependencies: Ágens függőségek
            operation: Művelet típusa
            success: Sikeres volt-e
            details: További részletek
        """
        if dependencies.audit_logger:
            user_id = dependencies.user_context.get("user_id", "anonymous")
            agent_type_str = self.agent_type.value if hasattr(self.agent_type, 'value') else str(self.agent_type)
            await dependencies.audit_logger.log_data_access(
                user_id=user_id,
                data_type=agent_type_str,
                operation=operation,
                success=success,
                details=details or {}
            )
    
    def _get_user_id(self, dependencies: BaseDependencies) -> str:
        """
        Felhasználó azonosító kinyerése a függőségekből.
        
        Args:
            dependencies: Ágens függőségek
            
        Returns:
            Felhasználó azonosító
        """
        return dependencies.user_context.get("user_id", "anonymous")


def create_base_tool_functions():
    """Közösen használható tool funkciók létrehozása."""
    
    async def log_user_interaction(
        ctx: RunContext[BaseDependencies],
        interaction_type: str,
        details: Dict[str, Any] = None
    ) -> bool:
        """
        Felhasználói interakció naplózása.
        
        Args:
            ctx: RunContext
            interaction_type: Interakció típusa
            details: További részletek
            
        Returns:
            Sikeres volt-e a naplózás
        """
        try:
            if ctx.deps.audit_logger:
                await ctx.deps.audit_logger.log_user_interaction(
                    user_id=ctx.deps.user_context.get("user_id", "anonymous"),
                    interaction_type=interaction_type,
                    details=details or {}
                )
            return True
        except Exception:
            return False
    
    async def check_security_context(ctx: RunContext[BaseDependencies]) -> bool:
        """
        Biztonsági kontextus ellenőrzése.
        
        Args:
            ctx: RunContext
            
        Returns:
            Biztonságos-e a kontextus
        """
        try:
            if not ctx.deps.security_context:
                return True  # Ha nincs beállítva, engedélyezzük
            
            # Itt lennének a biztonsági ellenőrzések
            return True
        except Exception:
            return False
    
    return {
        'log_user_interaction': log_user_interaction,
        'check_security_context': check_security_context
    }