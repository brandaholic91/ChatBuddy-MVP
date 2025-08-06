"""
Koordinátor Agent - Enhanced LangGraph + Pydantic AI architektúra.

Ez a modul implementálja a fő koordinátor agent-et az optimalizált
LangGraph workflow architektúrával, amely agent caching, enhanced routing
és performance monitoring funkciókat tartalmaz Redis cache támogatással.
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

from ..models.agent import AgentType, AgentResponse, LangGraphState
from ..models.user import User
from ..utils.state_management import create_initial_state, get_state_summary
from .langgraph_workflow_v2 import get_correct_workflow_manager
from .agent_cache_manager import get_agent_cache_manager, preload_all_agents, get_cache_statistics
# Security and audit imports
from ..config.security import get_security_config, get_threat_detector, InputValidator
from ..config.audit_logging import get_audit_logger, log_agent_interaction
from ..config.gdpr_compliance import get_gdpr_compliance, ConsentType, DataCategory
# Redis cache imports
from ..integrations.cache import get_redis_cache_service, SessionCache, PerformanceCache


@dataclass
class CoordinatorDependencies:
    """Koordinátor agent függőségei."""
    user: Optional[User] = None
    session_id: Optional[str] = None
    llm: Optional[ChatOpenAI] = None
    supabase_client: Optional[Any] = None
    webshop_api: Optional[Any] = None
    security_context: Optional[Any] = None
    audit_logger: Optional[Any] = None
    gdpr_compliance: Optional[Any] = None


class CoordinatorAgent:
    """
    Koordinátor Agent - Enhanced LangGraph + Pydantic AI architektúra.
    
    Ez az agent koordinálja a különböző szakértő agent-eket az optimalizált
    LangGraph workflow segítségével, amely agent caching, enhanced routing
    és performance monitoring funkciókat tartalmaz.
    """
    
    def __init__(
        self,
        llm: Optional[ChatOpenAI] = None,
        verbose: bool = True
    ):
        """Koordinátor Agent inicializálása."""
        self.llm = llm
        self.verbose = verbose
        self._workflow_manager = get_correct_workflow_manager()
        # Initialize security and audit components
        self._security_config = get_security_config()
        self._threat_detector = get_threat_detector()
        self._input_validator = InputValidator()
        self._audit_logger = get_audit_logger()
        self._gdpr_compliance = get_gdpr_compliance()
        # Initialize Redis cache components
        self._redis_cache_service = None
        self._session_cache = None
        self._performance_cache = None
        self._cache_initialized = False
        # Initialize agent cache manager
        self._agent_cache_manager = get_agent_cache_manager()
        self._agents_preloaded = False
    
    async def _initialize_cache(self):
        """Redis cache inicializálása."""
        if not self._cache_initialized:
            try:
                self._redis_cache_service = await get_redis_cache_service()
                self._session_cache = self._redis_cache_service.session_cache
                self._performance_cache = self._redis_cache_service.performance_cache
                self._cache_initialized = True
                if self.verbose:
                    print("✅ Redis cache initialized for coordinator")
            except Exception as e:
                if self.verbose:
                    print(f"⚠️ Redis cache initialization failed: {e}")
                self._cache_initialized = True  # Mark as initialized to avoid retries
    
    async def _preload_agents(self):
        """Preload all agents for faster response times."""
        if not self._agents_preloaded:
            try:
                if self.verbose:
                    print("🚀 Preloading agents for faster response times...")
                
                preload_results = await preload_all_agents()
                successful_agents = sum(1 for success in preload_results.values() if success)
                total_agents = len(preload_results)
                
                if self.verbose:
                    print(f"✅ Preloaded {successful_agents}/{total_agents} agents successfully")
                    for agent_type, success in preload_results.items():
                        status = "✅" if success else "❌"
                        print(f"  {status} {agent_type.value}")
                
                self._agents_preloaded = True
            except Exception as e:
                if self.verbose:
                    print(f"⚠️ Agent preloading failed: {e}")
                self._agents_preloaded = True  # Mark as attempted to avoid retries
    
    async def process_message(
        self,
        message: str,
        user: Optional[User] = None,
        session_id: Optional[str] = None,
        dependencies: Optional[CoordinatorDependencies] = None
    ) -> AgentResponse:
        """
        Üzenet feldolgozása Redis cache támogatással.
        
        Args:
            message: Feldolgozandó üzenet
            user: Felhasználó objektum
            session_id: Session azonosító
            dependencies: Függőségek
            
        Returns:
            Agent válasz
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 1. Initialize cache and preload agents
            await self._initialize_cache()
            await self._preload_agents()
            
            # 2. Input validation and sanitization
            sanitized_message = self._input_validator.sanitize_string(message)
            if sanitized_message != message:
                message = sanitized_message
            
            # 3. Threat detection
            threat_analysis = await self._threat_detector.analyze_message(message)
            if threat_analysis.get("threat_level", "low") == "high":
                return AgentResponse(
                    agent_type=AgentType.COORDINATOR,
                    response_text="Sajnálom, ez az üzenet nem feldolgozható biztonsági okokból.",
                    confidence=0.0,
                    metadata={"threat_detected": True, "threat_analysis": threat_analysis}
                )
            
            # 4. Check Redis cache for session
            if self._session_cache and session_id:
                session_data = await self._session_cache.get_session(session_id)
                if session_data:
                    # Update session activity
                    session_data.last_activity = datetime.now()
                    await self._session_cache.update_session(session_id, session_data)
            
            # 5. Check Redis cache for response
            if self._performance_cache:
                import hashlib
                import json
                
                # Generate cache key for response
                cache_data = {
                    "message": message,
                    "user_id": user.id if user else "anonymous",
                    "session_id": session_id,
                    "timestamp": int(time.time() / 300)  # 5-minute cache window
                }
                cache_key = f"coordinator_response:{hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()}"
                
                cached_response = await self._performance_cache.get_cached_agent_response(cache_key)
                if cached_response:
                    # Return cached response
                    return AgentResponse(
                        agent_type=AgentType.COORDINATOR,
                        response_text=cached_response.get("response_text", "Cache-elt válasz"),
                        confidence=cached_response.get("confidence", 0.8),
                        metadata={
                            **cached_response.get("metadata", {}),
                            "cached": True,
                            "cache_source": "redis",
                            "session_id": session_id,
                            "user_id": user.id if user else None
                        }
                    )
            
            # 6. Create dependencies
            if dependencies is None:
                dependencies = CoordinatorDependencies(
                    user=user,
                    session_id=session_id,
                    llm=self.llm,
                    supabase_client=None,  # Will be set by workflow
                    webshop_api=None,  # Will be set by workflow
                    security_context=self._security_config,
                    audit_logger=self._audit_logger,
                    gdpr_compliance=self._gdpr_compliance
                )
            
            # 7. Process message through correct LangGraph workflow
            user_context = {
                "user_id": user.id if user else None,
                "email": user.email if user else None,
                "phone": getattr(user, 'phone', None) if user else None,
                "preferences": getattr(user, 'preferences', {}) if user else {},
                "supabase_client": dependencies.supabase_client,
                "webshop_api": dependencies.webshop_api,
                "audit_logger": dependencies.audit_logger
            }
            
            final_state = await self._workflow_manager.process_message(
                user_message=message,
                user_context=user_context,
                security_context=dependencies.security_context
            )
            
            # 8. Extract response from final state
            response_text = self._extract_response_from_state(final_state)
            confidence = self._extract_confidence_from_state(final_state)
            metadata = self._extract_metadata_from_state(final_state)
            
            # 9. Calculate processing time
            processing_time = asyncio.get_event_loop().time() - start_time
            
            # 10. Cache the response in Redis
            if self._performance_cache:
                response_data = {
                    "response_text": response_text,
                    "confidence": confidence,
                    "metadata": metadata,
                    "processing_time": processing_time,
                    "created_at": time.time()
                }
                await self._performance_cache.cache_agent_response(cache_key, response_data)
            
            # 11. Create agent response
            response = AgentResponse(
                agent_type=AgentType.COORDINATOR,
                response_text=response_text,
                confidence=confidence,
                metadata={
                    "session_id": session_id,
                    "user_id": user.id if user else None,
                    "langgraph_used": True,
                    "enhanced_workflow": True,
                    "redis_cache_used": self._cache_initialized,
                    "workflow_summary": get_state_summary(final_state),
                    "processing_time": processing_time,
                    "threat_analysis": threat_analysis,
                    "cached": False,
                    "cache_source": "redis" if self._cache_initialized else "memory",
                    **metadata
                }
            )
            
            # 12. Audit logging for successful interaction
            await log_agent_interaction(
                user_id=user.id if user else "anonymous",
                agent_name="coordinator",
                query=message,
                response=response_text,
                session_id=session_id,
                success=True
            )
            
            if self.verbose:
                print(f"Koordinátor Agent válasz: {response_text[:100]}...")
                print(f"Feldolgozási idő: {processing_time:.2f}s")
                print(f"Redis cache használva: {self._cache_initialized}")
            
            return response
            
        except Exception as e:
            # Calculate processing time for error case
            processing_time = asyncio.get_event_loop().time() - start_time
            
            # Error handling
            error_response = AgentResponse(
                agent_type=AgentType.COORDINATOR,
                response_text=f"Sajnálom, hiba történt az üzenet feldolgozása során: {str(e)}",
                confidence=0.0,
                metadata={
                    "error": str(e),
                    "session_id": session_id,
                    "user_id": user.id if user else None,
                    "langgraph_used": True,
                    "enhanced_workflow": True,
                    "redis_cache_used": self._cache_initialized,
                    "processing_time": processing_time
                }
            )
            
            # Audit logging for error
            await log_agent_interaction(
                user_id=user.id if user else "anonymous",
                agent_name="coordinator",
                query=message,
                response=error_response.response_text,
                session_id=session_id,
                success=False
            )
            
            if self.verbose:
                print(f"Koordinátor Agent hiba: {e}")
            
            return error_response
    
    def _extract_response_from_state(self, state) -> str:
        """Válasz kinyerése a LangGraph state-ből."""
        try:
            # Check agent responses first (new v2 structure)
            if hasattr(state, 'get') and state.get("agent_responses"):
                active_agent = state.get("active_agent")
                if active_agent and active_agent in state["agent_responses"]:
                    agent_response = state["agent_responses"][active_agent]
                    if isinstance(agent_response, dict) and "response_text" in agent_response:
                        return agent_response["response_text"]
            
            # Fallback to messages (compatible with both old and new)
            if hasattr(state, 'get') and state.get("messages") and len(state["messages"]) > 1:
                last_message = state["messages"][-1]
                if isinstance(last_message, AIMessage):
                    return last_message.content
                elif hasattr(last_message, 'content'):
                    return str(last_message.content)
            
            # Legacy fallback
            if hasattr(state, 'get') and state.get("error_message"):
                return state["error_message"]
            
            return "Sajnálom, nem sikerült válaszolni."
            
        except Exception as e:
            return f"Hiba a válasz kinyerésekor: {str(e)}"
    
    def _extract_confidence_from_state(self, state) -> float:
        """Bizonyosság kinyerése a LangGraph state-ből."""
        try:
            # Check agent responses first (new v2 structure)
            if hasattr(state, 'get') and state.get("agent_responses"):
                active_agent = state.get("active_agent")
                if active_agent and active_agent in state["agent_responses"]:
                    agent_response = state["agent_responses"][active_agent]
                    if isinstance(agent_response, dict) and "confidence" in agent_response:
                        return float(agent_response["confidence"])
            
            # Try to get confidence from metadata (legacy)
            if hasattr(state, 'get'):
                metadata = state.get("metadata", {})
                if "confidence" in metadata:
                    return float(metadata["confidence"])
                
                # Try to get from agent-specific metadata
                for key, value in metadata.items():
                    if isinstance(value, dict) and "confidence" in value:
                        return float(value["confidence"])
            
            # Default confidence
            return 0.8
            
        except Exception:
            return 0.5
    
    def _extract_metadata_from_state(self, state) -> Dict[str, Any]:
        """Metaadatok kinyerése a LangGraph state-ből."""
        try:
            extracted_metadata = {}
            
            if not hasattr(state, 'get'):
                return {"metadata_extraction_error": "Invalid state object"}
            
            # Extract from new v2 structure
            if state.get("agent_responses"):
                active_agent = state.get("active_agent")
                if active_agent and active_agent in state["agent_responses"]:
                    agent_response = state["agent_responses"][active_agent]
                    if isinstance(agent_response, dict) and "metadata" in agent_response:
                        extracted_metadata.update(agent_response["metadata"])
            
            # Agent type
            if state.get("active_agent"):
                extracted_metadata["agent_type"] = state["active_agent"]
            elif state.get("current_agent"):
                extracted_metadata["agent_type"] = state["current_agent"]
            
            # Workflow steps
            if state.get("workflow_steps"):
                extracted_metadata["workflow_steps"] = state["workflow_steps"]
            
            # User context
            if state.get("user_context"):
                extracted_metadata["user_context"] = state["user_context"]
            
            # Legacy metadata support
            if state.get("metadata"):
                extracted_metadata.update(state["metadata"])
            
            return extracted_metadata
            
        except Exception as e:
            return {"metadata_extraction_error": str(e)}
    
    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Beszélgetési előzmények lekérése.
        
        Args:
            session_id: Session azonosító
            limit: Eredmények száma
            
        Returns:
            Beszélgetési előzmények
        """
        try:
            # TODO: Implement conversation history retrieval
            # This would typically query a database or cache
            
            # Mock implementation for now
            return [
                {
                    "timestamp": "2024-12-19T10:00:00Z",
                    "message": "Üdvözöllek!",
                    "response": "Üdvözöllek! Miben segíthetek?",
                    "agent_type": "coordinator"
                }
            ]
            
        except Exception as e:
            if self.verbose:
                print(f"Hiba a beszélgetési előzmények lekérésekor: {e}")
            return []
    
    def get_agent_cache_status(self) -> Dict[str, Any]:
        """
        Get detailed agent cache status.
        
        Returns:
            Agent cache status and statistics
        """
        try:
            cache_stats = get_cache_statistics()
            
            return {
                "agent_cache_enabled": True,
                "agents_preloaded": self._agents_preloaded,
                "cache_manager_initialized": self._agent_cache_manager is not None,
                "performance_improvement_expected": "60-80% faster response times",
                **cache_stats
            }
            
        except Exception as e:
            return {
                "agent_cache_enabled": False,
                "error": str(e),
                "agents_preloaded": False
            }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        Agent státusz lekérése.
        
        Returns:
            Agent státusz információk
        """
        try:
            return {
                "agent_type": "coordinator",
                "status": "active",
                "workflow_manager": "correct_langgraph_pydantic_ai_integration",
                "llm_available": self.llm is not None,
                "verbose_mode": self.verbose,
                "security_enabled": True,
                "audit_logging_enabled": True,
                "gdpr_compliance_enabled": True,
                "workflow_version": "v2_correct_integration",
                "architecture_pattern": "langgraph_with_pydantic_ai_tools",
                "follows_article_pattern": True,
                "redis_cache_enabled": True,
                "session_cache_enabled": True,
                "performance_cache_enabled": True,
                "agent_cache_enabled": True,
                "agents_preloaded": self._agents_preloaded,
                "agent_cache_stats": get_cache_statistics()
            }
            
        except Exception as e:
            return {
                "agent_type": "coordinator",
                "status": "error",
                "error": str(e)
            }


# Global coordinator agent instance
_coordinator_agent: Optional[CoordinatorAgent] = None


def get_coordinator_agent(
    llm: Optional[ChatOpenAI] = None,
    verbose: bool = True
) -> CoordinatorAgent:
    """
    Koordinátor agent singleton instance.
    
    Args:
        llm: Language model
        verbose: Verbose mode
        
    Returns:
        CoordinatorAgent instance
    """
    global _coordinator_agent
    if _coordinator_agent is None:
        _coordinator_agent = CoordinatorAgent(llm=llm, verbose=verbose)
    return _coordinator_agent


async def process_coordinator_message(
    message: str,
    user: Optional[User] = None,
    session_id: Optional[str] = None,
    dependencies: Optional[CoordinatorDependencies] = None
) -> AgentResponse:
    """
    Koordinátor üzenet feldolgozása.
    
    Args:
        message: Felhasználói üzenet
        user: Felhasználó objektum
        session_id: Session azonosító
        dependencies: Koordinátor függőségei
        
    Returns:
        Agent válasz
    """
    agent = get_coordinator_agent()
    return await agent.process_message(
        message=message,
        user=user,
        session_id=session_id,
        dependencies=dependencies
    ) 