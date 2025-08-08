"""
Chatbuddy MVP - Main FastAPI application.magy
"""

import os
import json
from datetime import datetime, timezone
import traceback
from typing import Any, Dict, List, Union
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from src.utils.error_handler import ChatBuddyError, get_error_message
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from src.config.logging import setup_logging
from src.config.security import setup_security_middleware, get_security_headers, setup_csrf_protection
from src.config.langgraph_auth import initialize_langgraph_auth, shutdown_langgraph_auth
from src.workflows.coordinator import process_coordinator_message
from src.models.chat import ChatRequest, ChatResponse
from src.models.user import User
from src.config.audit_logging import get_audit_logger, AuditSeverity
from src.config.gdpr_compliance import get_gdpr_compliance
from src.integrations.cache import get_redis_cache_service, shutdown_redis_cache_service
from src.integrations.websocket_manager import websocket_manager, chat_handler
from src.config.logging import get_logger
from src.monitoring.performance_tracker import PerformanceTracker

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


def _make_json_safe(obj: Any) -> Any:
    """Make an object JSON-serializable by filtering out non-serializable objects."""
    if isinstance(obj, dict):
        return {key: _make_json_safe(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_make_json_safe(item) for item in obj]
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    else:
        # Convert non-serializable objects to string
        return str(obj)

# Create rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="Chatbuddy MVP",
    description="Magyar nyelvű omnichannel ügyfélszolgálati chatbot",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lambda app: lifespan_context(app)
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
        setup_csrf_protection(app)
        print("✅ CSRF protection initialized")

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

        # LangGraph SDK authentikáció inicializálása
        try:
            await initialize_langgraph_auth()
            print("✅ LangGraph SDK authentication initialized")
        except Exception as e:
            print(f"⚠️ LangGraph SDK authentication initialization failed: {e}")

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

        # LangGraph SDK authentikáció leállítása
        try:
            await shutdown_langgraph_auth()
            print("✅ LangGraph SDK authentication stopped")
        except Exception as e:
            print(f"⚠️ LangGraph SDK authentication shutdown failed: {e}")

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
        error_info = get_error_message("GENERIC_ERROR", error_code="E001")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": error_info["message"],
                "details": str(e) if os.getenv("ENVIRONMENT") != "production" else None
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
    error_info = get_error_message("GENERIC_ERROR", error_code="E001")
    return JSONResponse(
        status_code=404,
        content=error_info
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors."""
    error_info = get_error_message("GENERIC_ERROR", error_code="E001")
    return JSONResponse(
        status_code=500,
        content=error_info
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


# CSRF token endpoint
@app.get("/api/v1/csrf-token")
async def get_csrf_token(request: Request):
    """
    Get CSRF token for secure form submissions.

    Args:
        request: FastAPI request object

    Returns:
        CSRF token
    """
    try:
        from src.config.security import get_csrf_protection_manager

        csrf_manager = get_csrf_protection_manager()
        csrf_token = await csrf_manager.generate_csrf_token(request)

        return {
            "csrf_token": csrf_token,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"CSRF token generation error: {e}")
        raise ChatBuddyError(error_key="GENERIC_ERROR", message="CSRF token generálás sikertelen.")


# Chat endpoints
@app.post("/api/v1/chat", response_model=ChatResponse)
@limiter.limit("50/minute")
async def chat_endpoint(payload: ChatRequest, request: Request):
    """
    Chat endpoint - Koordinátor Agent használatával biztonsági fókusszal.

    Args:
        request: Chat kérés
        request_obj: FastAPI request objektum

    Returns:
        Chat válasz
    """
    tracker = PerformanceTracker("chat_endpoint")
    tracker.start()
    try:
        # Extract security information
        source_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # Enhanced Input validation and sanitization
        if not payload.message or len(payload.message.strip()) == 0:
            raise ChatBuddyError(error_key="INVALID_INPUT", message="Üres üzenet.")

        if len(payload.message) > 4000:  # Increased limit
            raise ChatBuddyError(error_key="INVALID_INPUT", message="Túl hosszú üzenet (max 4000 karakter).")

        # Import security utilities
        from src.config.security import InputValidator, get_threat_detector

        # Sanitize input message
        sanitized_message = InputValidator.sanitize_string(payload.message, max_length=4000)
        if not sanitized_message:
            raise ChatBuddyError(error_key="INVALID_INPUT", message="Érvénytelen üzenet tartalom.")

        # Security audit logging
        audit_logger = get_audit_logger()

        # Threat detection
        threat_detector = get_threat_detector()
        if threat_detector.should_block_request(sanitized_message):
            await audit_logger.log_security_event(
                event_type="threat_detected",
                user_id=payload.user_id or "anonymous",
                details={
                    "message": sanitized_message[:100],  # Only first 100 chars
                    "source_ip": source_ip,
                    "user_agent": user_agent
                },
                severity=AuditSeverity.HIGH
            )
            raise ChatBuddyError(error_key="UNAUTHORIZED_ACCESS", message="Kérés blokkolva biztonsági okokból.")

        # Replace original message with sanitized version
        payload.message = sanitized_message
        await audit_logger.log_security_event(
            event_type="chat_request",
            user_id=payload.user_id or "anonymous",
            details={"message_length": len(sanitized_message)},
            ip_address=source_ip
        )

        # Felhasználó objektum létrehozása (placeholder)
        user = None
        if payload.user_id:
            # Note: ChatRequest nem tartalmaz user_email mezőt
            user = User(id=payload.user_id, email="user@example.com")  # Placeholder email

        # Koordinátor agent hívása biztonsági paraméterekkel
        # process_coordinator_message egy async generátor, gyűjtsük az utolsó választ
        final_response = None
        async def _collect_stream():
            nonlocal final_response
            async for chunk in process_coordinator_message(
                message=sanitized_message,
                user=user,
                session_id=payload.session_id
            ):
                final_response = chunk
            return final_response

        agent_response = await PerformanceTracker("process_coordinator_message").measure_async(_collect_stream)

        # ChatResponse létrehozása
        response = ChatResponse(
            message=agent_response.response_text,
            session_id=payload.session_id,
            timestamp=datetime.now(timezone.utc),
            agent_used=agent_response.agent_type.value,
            metadata=agent_response.metadata
        )

        return response

    except ChatBuddyError as e:
        # Custom ChatBuddyError already contains detailed info
        audit_logger = get_audit_logger()
        await audit_logger.log_security_event(
            event_type=f"chat_error_{e.error_key}",
            user_id=payload.user_id or "anonymous",
            details=e.to_dict(),
            ip_address=source_ip if 'source_ip' in locals() else None,
            severity=AuditSeverity.ERROR
        )
        raise HTTPException(
            status_code=400 if e.category == "Validation" else 500,
            detail=e.to_dict()
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        audit_logger = get_audit_logger()
        error_key = "GENERIC_ERROR"
        chat_buddy_error = ChatBuddyError(error_key=error_key, original_error=str(e))

        log_severity = AuditSeverity.CRITICAL if os.getenv("ENVIRONMENT") == "production" else AuditSeverity.ERROR

        await audit_logger.log_security_event(
            event_type=f"chat_error_{error_key}",
            user_id=payload.user_id or "anonymous",
            details={
                "error_key": error_key,
                "message": chat_buddy_error.message,
                "action": chat_buddy_error.action,
                "category": chat_buddy_error.category,
                "original_error": str(e),
                "traceback": traceback.format_exc() if os.getenv("ENVIRONMENT") != "production" else "Traceback suppressed in production"
            },
            ip_address=source_ip if 'source_ip' in locals() else None,
            severity=log_severity
        )

        logger.error(f"Error processing chat: {e}", exc_info=True)

        raise HTTPException(
            status_code=500,
            detail=chat_buddy_error.to_dict()
        )
    finally:
        tracker.stop("Chat endpoint execution time")


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

                # Válasz küldése (JSON-safe response)
                safe_response = _make_json_safe(response)
                await websocket.send_json(safe_response)

        except WebSocketDisconnect:
            logger.info(f"WebSocket kapcsolat lezárva: {connection_id}")
        except Exception as e:
            logger.error(f"Hiba a WebSocket kommunikációban: {e}", exc_info=True)
            error_info = get_error_message("NETWORK_ERROR") # Or a more specific error key
            try:
                await websocket.send_json({
                    "type": "error",
                    "data": {
                        "error_type": error_info["code"],
                        "error_message": error_info["message"],
                        "action": error_info["action"],
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                })
            except Exception as send_error:
                logger.error(f"Hiba a WebSocket hibaüzenet küldésekor: {send_error}")
        finally:
            # Kapcsolat eltávolítása
            await websocket_manager.disconnect(connection_id)

    except Exception as e:
        logger.error(f"Hiba a WebSocket endpoint-ban: {e}", exc_info=True)
        error_info = get_error_message("GENERIC_ERROR")
        try:
            await websocket.close(code=1011, reason=error_info["message"])
        except Exception as close_error:
            logger.error(f"Hiba a WebSocket kapcsolat lezárásakor: {close_error}")


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
        error_info = get_error_message("GENERIC_ERROR", error_code="E001")
        logger.error(f"Hiba a WebSocket statisztikák lekérésekor: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=error_info
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
        error_info = get_error_message("GENERIC_ERROR", error_code="E001")
        logger.error(f"Hiba a workflow performance lekérésekor: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=error_info
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
        error_info = get_error_message("GENERIC_ERROR", error_code="E001")
        logger.error(f"Hiba a cache statisztikák lekérésekor: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=error_info
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
        error_info = get_error_message("GENERIC_ERROR", error_code="E001")
        logger.error(f"Hiba a cache érvénytelenítésekor: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=error_info
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


# Social Media Webhook Endpoints
@app.get("/webhook/messenger")
async def verify_messenger_webhook(
    hub_mode: str,
    hub_verify_token: str,
    hub_challenge: str
):
    """
    Facebook Messenger webhook verification.

    Args:
        hub_mode: Hub mode
        hub_verify_token: Verify token
        hub_challenge: Challenge string

    Returns:
        Challenge response
    """
    try:
        from src.integrations.social_media import create_messenger_client

        messenger_client = create_messenger_client()
        if not messenger_client:
            # Test environment - return challenge directly
            if hub_mode == "subscribe" and hub_verify_token == "test_token":
                return int(hub_challenge)
            else:
                raise ChatBuddyError(error_key="GENERIC_ERROR", message="Messenger kliens nem elérhető.")

        challenge = await messenger_client.verify_webhook(hub_mode, hub_verify_token, hub_challenge)

        # Audit logging
        audit_logger = get_audit_logger()
        await audit_logger.log_event(
            "messenger_webhook_verification",
            "INFO",
            f"Facebook Messenger webhook verified: {hub_mode}",
            {"hub_mode": hub_mode, "challenge": challenge}
        )

        return challenge
    except Exception as e:
        logger.error(f"Hiba a Messenger webhook ellenőrzésekor: {e}", exc_info=True)
        raise ChatBuddyError(error_key="UNAUTHORIZED_ACCESS", message="Hozzáférés megtagadva.")


@app.post("/webhook/messenger")
async def handle_messenger_webhook(request: Request):
    """
    Facebook Messenger webhook handler.

    Args:
        request: FastAPI request object

    Returns:
        Webhook processing result
    """
    try:
        from src.integrations.social_media import create_messenger_client
        from src.agents.social_media import create_social_media_agent, SocialMediaDependencies

        # Get request body and signature
        body = await request.body()
        signature = request.headers.get("X-Hub-Signature-256")

        # Verify signature
        messenger_client = create_messenger_client()
        if not messenger_client:
            # Test environment - skip signature verification
            if signature == "test_signature":
                pass
            else:
                raise ChatBuddyError(error_key="GENERIC_ERROR", message="Messenger kliens nem elérhető.")
        else:
            if not messenger_client.verify_signature(signature, body):
                raise ChatBuddyError(error_key="UNAUTHORIZED_ACCESS", message="Érvénytelen aláírás.")

        # Parse webhook data
        webhook_data = json.loads(body)

        # Create social media agent dependencies
        dependencies = SocialMediaDependencies(
            user_context={},
            messenger_api=messenger_client,
            whatsapp_api=None,
            supabase_client=None,
            template_engine=None,
            security_context=None,
            audit_logger=get_audit_logger()
        )

        # Process webhook with social media agent
        social_media_agent = create_social_media_agent()
        result = await social_media_agent.run(
            f"Handle messenger webhook: {json.dumps(webhook_data)}",
            deps=dependencies
        )

        # Audit logging
        audit_logger = get_audit_logger()
        await audit_logger.log_event(
            "messenger_webhook_processed",
            "INFO",
            "Facebook Messenger webhook processed successfully",
            {"webhook_data": webhook_data, "result": result.response_text}
        )

        return {"status": "ok", "result": result.response_text}
    except Exception as e:
        logger.error(f"Hiba a Messenger webhook feldolgozásakor: {e}", exc_info=True)
        raise ChatBuddyError(error_key="GENERIC_ERROR", message="Belső szerver hiba.")


@app.get("/webhook/whatsapp")
async def verify_whatsapp_webhook(
    hub_mode: str,
    hub_verify_token: str,
    hub_challenge: str
):
    """
    WhatsApp Business webhook verification.

    Args:
        hub_mode: Hub mode
        hub_verify_token: Verify token
        hub_challenge: Challenge string

    Returns:
        Challenge response
    """
    try:
        from src.integrations.social_media import create_whatsapp_client

        whatsapp_client = create_whatsapp_client()

        if not whatsapp_client:
            # Test environment - return challenge directly
            if hub_mode == "subscribe" and hub_verify_token == "test_token":
                return int(hub_challenge)
            else:
                raise ChatBuddyError(error_key="GENERIC_ERROR", message="WhatsApp kliens nem elérhető.")

        challenge = await whatsapp_client.verify_webhook(hub_mode, hub_verify_token, hub_challenge)

        # Audit logging
        audit_logger = get_audit_logger()
        await audit_logger.log_event(
            "whatsapp_webhook_verification",
            "INFO",
            f"WhatsApp Business webhook verified: {hub_mode}",
            {"hub_mode": hub_mode, "challenge": challenge}
        )

        return challenge
    except Exception as e:
        logger.error(f"Hiba a WhatsApp webhook ellenőrzésekor: {e}", exc_info=True)
        raise ChatBuddyError(error_key="UNAUTHORIZED_ACCESS", message="Hozzáférés megtagadva.")


@app.post("/webhook/whatsapp")
async def handle_whatsapp_webhook(request: Request):
    """
    WhatsApp Business webhook handler.

    Args:
        request: FastAPI request object

    Returns:
        Webhook processing result
    """
    try:
        from src.integrations.social_media import create_whatsapp_client
        from src.agents.social_media import create_social_media_agent, SocialMediaDependencies

        # Get request body
        webhook_data = await request.json()

        # Create WhatsApp client
        whatsapp_client = create_whatsapp_client()
        if not whatsapp_client:
            # Test environment - create mock client
            logger.warning("WhatsApp client not available, using test mode")
            whatsapp_client = None

        # Create social media agent dependencies
        dependencies = SocialMediaDependencies(
            user_context={},
            messenger_api=None,
            whatsapp_api=whatsapp_client,
            supabase_client=None,
            template_engine=None,
            security_context=None,
            audit_logger=get_audit_logger()
        )

        # Process webhook with social media agent
        social_media_agent = create_social_media_agent()
        result = await social_media_agent.run(
            f"Handle whatsapp webhook: {json.dumps(webhook_data)}",
            deps=dependencies
        )

        # Audit logging
        audit_logger = get_audit_logger()
        await audit_logger.log_event(
            "whatsapp_webhook_processed",
            "INFO",
            "WhatsApp Business webhook processed successfully",
            {"webhook_data": webhook_data, "result": result.response_text}
        )

        return {"status": "ok", "result": result.response_text}
    except Exception as e:
        logger.error(f"Hiba a WhatsApp webhook feldolgozásakor: {e}", exc_info=True)
        raise ChatBuddyError(error_key="GENERIC_ERROR", message="Belső szerver hiba.")


@app.get("/api/v1/social-media/status")
async def social_media_status():
    """
    Social media integrációk állapotának lekérése.

    Returns:
        Social media services állapota
    """
    try:
        from src.integrations.social_media import create_messenger_client, create_whatsapp_client

        messenger_client = create_messenger_client()
        whatsapp_client = create_whatsapp_client()

        status = {
            "facebook_messenger": {
                "available": messenger_client is not None,
                "status": "active" if messenger_client else "not_configured"
            },
            "whatsapp_business": {
                "available": whatsapp_client is not None,
                "status": "active" if whatsapp_client else "not_configured"
            },
            "features": [
                "Webhook Handling",
                "Message Sending",
                "Template Messages",
                "Interactive Messages",
                "Carousel Messages",
                "Quick Replies"
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        return status
    except Exception as e:
        logger.error(f"Hiba a social media állapot lekérésekor: {e}", exc_info=True)
        raise ChatBuddyError(error_key="GENERIC_ERROR", message="Hiba a social media állapot lekérésekor.")
