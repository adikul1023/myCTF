"""
Forensic CTF Platform - Main Application Entry Point

A production-grade, story-driven forensic simulation CTF platform.

Key Features:
- No static flags (HMAC-based, per-user, per-case)
- Anti-writeup by design
- Noise-heavy, realism-first
- Invite-only registration
- Rate-limited submissions
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.middleware import (
    SecurityHeadersMiddleware,
    RequestIDMiddleware,
    AuditLoggingMiddleware,
)
from app.api.v1 import api_router
from app.db.session import init_db, close_db, engine
from app.utils.storage import storage_client


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events:
    - Database initialization
    - Storage bucket creation
    - Resource cleanup
    """
    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Initialize database (dev only - use Alembic in production)
    if settings.DEBUG:
        await init_db()
        print("Database tables initialized")
    
    # Ensure storage bucket exists
    try:
        await storage_client.ensure_bucket_exists()
        print(f"Storage bucket '{settings.MINIO_BUCKET_NAME}' ready")
    except Exception as e:
        print(f"Warning: Could not initialize storage: {e}")
    
    yield
    
    # Shutdown
    print("Shutting down...")
    await close_db()
    print("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="""
## Forensic Simulation CTF Platform

A production-grade CTF platform designed for **serious cybersecurity practitioners**.

### Philosophy

This is NOT a casual CTF platform. It's a forensic simulation environment where:

- **Story-driven cases**: Each challenge is a complete forensic scenario with narrative
- **No static flags**: Flags are generated per-user, per-case using HMAC
- **Anti-writeup by design**: Sharing flags is useless - each user gets unique flags
- **Realism-first**: Cases include noise, red herrings, and realistic artifacts
- **Rate-limited**: Brute force is not an option

### Flag System

Flags are computed as:
```
flag = HMAC(secret, user_id + case_id + semantic_truth_hash)
```

This means:
- Your flag won't work for anyone else
- You can't use someone else's flag
- Write-ups are learning resources, not cheat sheets

### Getting Started

1. Obtain an invite code
2. Register your account
3. Browse available cases
4. Download artifacts and investigate
5. Submit your findings

Good luck, investigator.
    """,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)


# Add security middlewares (order matters - first added = last executed)
app.add_middleware(AuditLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)

# CORS middleware - restrict methods and headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)


# Include API routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with clean error messages."""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"][1:])  # Skip 'body'
        errors.append({
            "field": field,
            "message": error["msg"],
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": errors,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    if settings.DEBUG:
        raise exc
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
    }


@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """
    Readiness check - verifies all dependencies are available.
    """
    status_response = {
        "status": "ready",
        "version": settings.APP_VERSION,
        "database": "unknown",
        "storage": "unknown",
    }
    
    # Check database
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        status_response["database"] = "connected"
    except Exception as e:
        status_response["database"] = f"error: {str(e)}"
        status_response["status"] = "not ready"
    
    # Check storage
    try:
        # Simple check - just verify client can be created
        _ = storage_client.client
        status_response["storage"] = "configured"
    except Exception as e:
        status_response["storage"] = f"error: {str(e)}"
        status_response["status"] = "not ready"
    
    return status_response


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with platform info."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Forensic Simulation CTF Platform",
        "docs": f"{settings.API_V1_PREFIX}/docs" if settings.DEBUG else None,
        "message": "Welcome, investigator. Obtain an invite code to begin.",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else 4,
    )
