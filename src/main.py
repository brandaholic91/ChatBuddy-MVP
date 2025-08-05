"""
Chatbuddy MVP - Main FastAPI application.
"""

import os
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from src.config.logging import setup_logging
from src.config.security import setup_security_middleware, get_security_headers
from src.workflows.coordinator import process_coordinator_message
from src.models.chat import ChatRequest, ChatResponse
from src.models.user import User
from src.config.audit_logging import get_audit_logger, AuditSeverity
from src.config.gdpr_compliance import get_gdpr_compliance
from src.integrations.cache import get_redis_cache_service, shutdown_redis_cache_service
from src.integrations.websocket_manager import websocket_manager, chat_handler
from src.config.logging import get_logger

# Load environment variables from .env file
load_dotenv()

# Set test environment for pytest
import sys
if "pytest" in sys.modules:
    os.environ["ENVIRONMENT"] = "test"

# Environment security validation - KRITIKUS
from src.config.environment_security import validate_environment_on_startup

# Validate environment on startup (skip during testing)
if "pytest" not in sys.modules:
    print("🔒 Környezeti változók biztonsági validálása...")
    if not validate_environment_on_startup():
        print("❌ Alkalmazás indítása megszakítva - környezeti változók hiányoznak vagy érvénytelenek")
        exit(1)

# Setup logging
setup_logging()

# Get logger for WebSocket endpoint
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Chatbuddy MVP",
    description="Magyar nyelvű omnichannel ügyfélszolgálati chatbot",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lambda app: lifespan_context(app)
)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan_context(app):
    print("🚀 Chatbuddy MVP starting up...")
    print(f"📅 Started at: {datetime.now(timezone.utc).isoformat()}")
    print(f"🔧 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    try:
        audit_logger = get_audit_logger()
        await audit_logger.start_processing()
        print("✅ Security audit logger started")
        gdpr_compliance = get_gdpr_compliance()
        print("✅ GDPR compliance layer initialized")
        await setup_rate_limiting()
        print("✅ Rate limiting initialized")
        
        # Redis cache inicializálása
        try:
            redis_cache_service = await get_redis_cache_service()
            print("✅ Redis cache service initialized")
        except Exception as e:
            print(f"⚠️ Redis cache service initialization failed: {e}")
        
        # WebSocket handler inicializálása
        try:
            await chat_handler.initialize()
            print("✅ WebSocket chat handler initialized")
        except Exception as e:
            print(f"⚠️ WebSocket chat handler initialization failed: {e}")
        
        print("🔒 Security systems initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing security systems: {e}")
    yield
    print("🛑 Chatbuddy MVP shutting down...")
    print(f"📅 Stopped at: {datetime.now(timezone.utc).isoformat()}")
    try:
        audit_logger = get_audit_logger()
        await audit_logger.stop_processing()
        print("✅ Security audit logger stopped")
        
        # Redis cache leállítása
        try:
            await shutdown_redis_cache_service()
            print("✅ Redis cache service stopped")
        except Exception as e:
            print(f"⚠️ Redis cache service shutdown failed: {e}")
            
    except Exception as e:
        print(f"❌ Error shutting down security systems: {e}")

# Setup security middleware
setup_security_middleware(app)

# Initialize rate limiting (simplified for now)
from src.config.rate_limiting import get_rate_limiter
import asyncio

async def setup_rate_limiting():
    """Rate limiting setup."""
    rate_limiter = get_rate_limiter()
    print("✅ Rate limiting initialized")
    return rate_limiter

# Add security headers to all responses
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    for header, value in get_security_headers().items():
        response.headers[header] = value
    return response


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Chatbuddy MVP API",
        "version": "0.1.0",
        "status": "running",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
        Health status of all services
    """
    try:
        # Check environment variables
        required_env_vars = [
            "OPENAI_API_KEY",
            "SUPABASE_URL", 
            "SUPABASE_ANON_KEY",
            "SECRET_KEY"
        ]
        
        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        # Check services
        services_status = {
            "database": "connected",  # Will be implemented
            "ai_models": "available"   # Will be implemented
        }
        
        # Redis cache health check
        try:
            redis_cache_service = await get_redis_cache_service()
            redis_health = await redis_cache_service.health_check()
            services_status["redis"] = "connected" if redis_health["redis_connection"] else "disconnected"
        except Exception as e:
            services_status["redis"] = "error"
            print(f"Redis health check error: {e}")
        
        # Overall status
        if missing_vars:
            status = "degraded"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "0.1.0",
            "services": services_status,
            "missing_env_vars": missing_vars if missing_vars else None
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }
        )


@app.get("/api/v1/status")
async def api_status():
    """
    API status endpoint.
    
    Returns:
        API status information
    """
    return {
        "api_version": "v1",
        "status": "operational",
        "features": {
            "chat": "available",
            "products": "available", 
            "orders": "available",
            "agents": "available"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/v1/info")
async def api_info():
    """
    API information endpoint.
    
    Returns:
        Detailed API information
    """
    return {
        "name": "Chatbuddy MVP",
        "description": "Magyar nyelvű omnichannel ügyfélszolgálati chatbot",
        "version": "0.1.0",
        "author": "Chatbuddy Team",
        "technologies": [
            "FastAPI",
            "LangGraph", 
            "Pydantic AI",
            "Supabase",
            "Redis",
            "OpenAI",
            "Anthropic"
        ],
        "endpoints": {
            "chat": "/api/v1/chat",
            "products": "/api/v1/products",
            "orders": "/api/v1/orders",
            "agents": "/api/v1/agents"
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        }
    }


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "not_found",
            "message": "Endpoint not found",
            "path": str(request.url.path)
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


# Startup and shutdown events
# @app.on_event("startup")
# async def startup_event():
#     """Application startup event."""
#     print("🚀 Chatbuddy MVP starting up...")
#     print(f"📅 Started at: {datetime.utcnow().isoformat()}")
#     print(f"🔧 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    
#     # Initialize security systems
#     try:
#         # Start audit logger
#         audit_logger = get_security_audit_logger()
#         await audit_logger.start()
#         print("✅ Security audit logger started")
        
#         # Initialize GDPR compliance
#         gdpr_compliance = get_gdpr_compliance()
#         print("✅ GDPR compliance layer initialized")
        
#         # Setup rate limiting
#         await setup_rate_limiting()
#         print("✅ Rate limiting initialized")
        
#         print("🔒 Security systems initialized successfully")
        
#     except Exception as e:
#         print(f"❌ Error initializing security systems: {e}")


# @app.on_event("shutdown")
# async def shutdown_event():
#     """Application shutdown event."""
#     print("🛑 Chatbuddy MVP shutting down...")
#     print(f"📅 Stopped at: {datetime.utcnow().isoformat()}")
    
#     # Shutdown security systems
#     try:
#         audit_logger = get_security_audit_logger()
#         await audit_logger.stop()
#         print("✅ Security audit logger stopped")
        
#     except Exception as e:
#         print(f"❌ Error shutting down security systems: {e}")


# Chat endpoints
@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, request_obj: Request):
    """
    Chat endpoint - Koordinátor Agent használatával biztonsági fókusszal.
    
    Args:
        request: Chat kérés
        request_obj: FastAPI request objektum
        
    Returns:
        Chat válasz
    """
    try:
        # Extract security information
        source_ip = request_obj.client.host if request_obj.client else None
        user_agent = request_obj.headers.get("user-agent")
        
        # Input validation
        if not request.message or len(request.message.strip()) == 0:
            raise HTTPException(
                status_code=400,
                detail="Üres üzenet"
            )
        
        if len(request.message) > 1000:
            raise HTTPException(
                status_code=400,
                detail="Túl hosszú üzenet (max 1000 karakter)"
            )
        
        # Security audit logging
        audit_logger = get_audit_logger()
        await audit_logger.log_security_event(
            event_type="chat_request",
            user_id=request.user_id or "anonymous",
            details={"message_length": len(request.message)},
            ip_address=source_ip
        )
        
        # Felhasználó objektum létrehozása (placeholder)
        user = None
        if request.user_id:
            # Note: ChatRequest nem tartalmaz user_email mezőt
            user = User(id=request.user_id, email="user@example.com")  # Placeholder email
        
        # Koordinátor agent hívása biztonsági paraméterekkel
        agent_response = await process_coordinator_message(
            message=request.message,
            user=user,
            session_id=request.session_id
        )
        
        # ChatResponse létrehozása
        response = ChatResponse(
            message=agent_response.response_text,
            session_id=request.session_id,
            timestamp=datetime.now(timezone.utc),
            agent_used=agent_response.agent_type.value,
            metadata=agent_response.metadata
        )
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log security event for errors
        audit_logger = get_audit_logger()
        await audit_logger.log_security_event(
            event_type="chat_error",
            user_id=request.user_id or "anonymous",
            details={"error": str(e)},
            ip_address=source_ip if 'source_ip' in locals() else None
        )
        
        raise HTTPException(
            status_code=500,
            detail="Chat feldolgozási hiba"
        )


# WebSocket endpoints
@app.websocket("/ws/chat/{session_id}")
async def websocket_chat_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint a real-time chat kommunikációhoz.
    
    Args:
        websocket: WebSocket objektum
        session_id: Session azonosító
    """
    try:
        # WebSocket kapcsolat elfogadása
        await websocket.accept()
        
        # Query paraméterek kinyerése
        user_id = websocket.query_params.get("user_id")
        
        # Kapcsolat hozzáadása a manager-hez
        connection_id = await websocket_manager.connect(websocket, session_id, user_id)
        
        # Kapcsolat visszajelzés küldése
        await websocket.send_json({
            "type": "connection_established",
            "data": {
                "connection_id": connection_id,
                "session_id": session_id,
                "user_id": user_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        })
        
        # Üzenetek feldolgozása
        try:
            while True:
                # Üzenet fogadása
                message_data = await websocket.receive_json()
                
                # Üzenet feldolgozása
                response = await chat_handler.handle_message(websocket, connection_id, message_data)
                
                # Válasz küldése
                await websocket.send_json(response)
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket kapcsolat lezárva: {connection_id}")
        except Exception as e:
            logger.error(f"Hiba a WebSocket kommunikációban: {e}")
            try:
                await websocket.send_json({
                    "type": "error",
                    "data": {
                        "error_type": "communication_error",
                        "error_message": "Kommunikációs hiba történt",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                })
            except:
                pass
        finally:
            # Kapcsolat eltávolítása
            await websocket_manager.disconnect(connection_id)
            
    except Exception as e:
        logger.error(f"Hiba a WebSocket endpoint-ban: {e}")
        try:
            await websocket.close(code=1011, reason="Internal error")
        except:
            pass


@app.get("/api/v1/websocket/stats")
async def websocket_stats():
    """
    WebSocket statisztikák lekérése.
    
    Returns:
        WebSocket manager statisztikák
    """
    try:
        stats = websocket_manager.get_stats()
        return {
            "websocket_stats": stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Hiba a WebSocket statisztikák lekérésekor: {e}")
        raise HTTPException(
            status_code=500,
            detail="Hiba a WebSocket statisztikák lekérésekor"
        )


@app.get("/api/v1/workflow/performance")
async def workflow_performance():
    """
    Workflow teljesítmény metrikák lekérése.
    
    Returns:
        Workflow performance metrikák
    """
    try:
        from src.workflows.langgraph_workflow import get_workflow_manager
        
        workflow_manager = get_workflow_manager()
        metrics = workflow_manager.get_performance_metrics()
        
        return {
            "workflow_performance": {
                "metrics": metrics,
                "optimization_status": "enhanced",
                "framework": "LangGraph + Pydantic AI",
                "features": [
                    "Agent Caching",
                    "Enhanced Routing", 
                    "Performance Monitoring",
                    "Error Recovery"
                ]
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Hiba a workflow performance lekérésekor: {e}")
        raise HTTPException(
            status_code=500,
            detail="Hiba a workflow performance lekérésekor"
        )


@app.get("/api/v1/cache/stats")
async def cache_stats():
    """
    Cache statisztikák és állapot lekérése.
    
    Returns:
        Cache performance és állapot információk
    """
    try:
        from src.integrations.cache import get_redis_cache_service
        
        redis_cache_service = await get_redis_cache_service()
        stats = await redis_cache_service.get_stats()
        health = await redis_cache_service.health_check()
        
        return {
            "cache_performance": {
                "stats": stats,
                "health": health,
                "cache_type": "Redis",
                "features": [
                    "Session Caching",
                    "Performance Caching", 
                    "Rate Limiting",
                    "Distributed Caching"
                ]
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Hiba a cache statisztikák lekérésekor: {e}")
        raise HTTPException(
            status_code=500,
            detail="Hiba a cache statisztikák lekérésekor"
        )


@app.post("/api/v1/cache/invalidate")
async def invalidate_cache(pattern: str = None):
    """
    Cache érvénytelenítése.
    
    Args:
        pattern: Opcionális pattern a szelektív érvénytelenítéshez
        
    Returns:
        Érvénytelenítés eredménye
    """
    try:
        from src.workflows.langgraph_workflow import get_enhanced_workflow_manager
        
        workflow_manager = get_enhanced_workflow_manager()
        await workflow_manager.invalidate_cache(pattern)
        
        return {
            "cache_invalidation": {
                "status": "success",
                "pattern": pattern,
                "message": f"Cache érvénytelenítve: {pattern if pattern else 'all'}"
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Hiba a cache érvénytelenítésekor: {e}")
        raise HTTPException(
            status_code=500,
            detail="Hiba a cache érvénytelenítésekor"
        )


# Development only endpoints
if os.getenv("ENVIRONMENT") == "development":
    @app.get("/debug/env")
    async def debug_env():
        """Debug endpoint to check environment variables (development only)."""
        return {
            "environment": os.getenv("ENVIRONMENT", "development"),
            "python_version": os.getenv("PYTHON_VERSION", "unknown"),
            "available_env_vars": {
                "OPENAI_API_KEY": "***" if os.getenv("OPENAI_API_KEY") else None,
                "SUPABASE_URL": os.getenv("SUPABASE_URL"),
                "SECRET_KEY": "***" if os.getenv("SECRET_KEY") else None,
                "REDIS_URL": os.getenv("REDIS_URL")
            }
        } 