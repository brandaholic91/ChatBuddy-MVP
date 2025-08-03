"""
Chatbuddy MVP - Main FastAPI application.
"""

import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config.logging import setup_logging
from src.config.security import setup_security_middleware, get_security_headers

# Setup logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    title="Chatbuddy MVP",
    description="Magyar nyelvű omnichannel ügyfélszolgálati chatbot",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup security middleware
setup_security_middleware(app)

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
        "timestamp": datetime.utcnow().isoformat()
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
        
        # Check services (placeholder for now)
        services_status = {
            "database": "connected",  # Will be implemented
            "redis": "connected",      # Will be implemented
            "ai_models": "available"   # Will be implemented
        }
        
        # Overall status
        if missing_vars:
            status = "degraded"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "0.1.0",
            "services": services_status,
            "missing_env_vars": missing_vars if missing_vars else None
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
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
        "timestamp": datetime.utcnow().isoformat()
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
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    print("🚀 Chatbuddy MVP starting up...")
    print(f"📅 Started at: {datetime.utcnow().isoformat()}")
    print(f"🔧 Environment: {os.getenv('ENVIRONMENT', 'development')}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    print("🛑 Chatbuddy MVP shutting down...")
    print(f"📅 Stopped at: {datetime.utcnow().isoformat()}")


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