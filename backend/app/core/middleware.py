"""
Security middleware for the application.

Implements:
- Security headers (CSP, HSTS, X-Frame-Options, etc.)
- Request ID tracking
- Audit logging
"""

import uuid
import time
import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings


# Configure audit logger
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)

# Create handler if not exists
if not audit_logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - AUDIT - %(message)s'
    ))
    audit_logger.addHandler(handler)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    
    Headers added:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Referrer-Policy: strict-origin-when-cross-origin
    - Cache-Control: no-store (for API responses)
    - Strict-Transport-Security (in production)
    - Content-Security-Policy
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Always add these headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # API responses should not be cached
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
        
        # HSTS in production (HTTPS required)
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content Security Policy
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",  # For Swagger UI
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
            "img-src 'self' data: https://fastapi.tiangolo.com",
            "font-src 'self'",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "form-action 'self'",
            "base-uri 'self'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add a unique request ID to each request.
    
    This helps with:
    - Request tracing across logs
    - Debugging issues
    - Audit trails
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or use existing request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Store in request state for use in logging
        request.state.request_id = request_id
        
        response = await call_next(request)
        
        # Add to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for security audit logging.
    
    Logs:
    - Authentication attempts
    - Authorization failures
    - Sensitive operations
    - Rate limit hits
    """
    
    # Paths that should be audit logged
    AUDIT_PATHS = [
        "/api/v1/auth/",
        "/api/v1/admin/",
        "/api/v1/submissions/submit",
    ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if this path should be audited
        should_audit = any(
            request.url.path.startswith(path) for path in self.AUDIT_PATHS
        )
        
        if not should_audit:
            return await call_next(request)
        
        # Get request info
        client_ip = self._get_client_ip(request)
        request_id = getattr(request.state, "request_id", "unknown")
        user_agent = request.headers.get("User-Agent", "unknown")[:256]
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Log the request
            duration_ms = (time.time() - start_time) * 1000
            
            audit_logger.info(
                f"request_id={request_id} "
                f"method={request.method} "
                f"path={request.url.path} "
                f"status={response.status_code} "
                f"duration_ms={duration_ms:.2f} "
                f"client_ip={client_ip} "
                f"user_agent={user_agent}"
            )
            
            # Log security events
            if response.status_code == 401:
                audit_logger.warning(
                    f"AUTH_FAILURE request_id={request_id} "
                    f"path={request.url.path} client_ip={client_ip}"
                )
            elif response.status_code == 403:
                audit_logger.warning(
                    f"AUTHZ_FAILURE request_id={request_id} "
                    f"path={request.url.path} client_ip={client_ip}"
                )
            elif response.status_code == 429:
                audit_logger.warning(
                    f"RATE_LIMITED request_id={request_id} "
                    f"path={request.url.path} client_ip={client_ip}"
                )
            
            return response
            
        except Exception as e:
            audit_logger.error(
                f"REQUEST_ERROR request_id={request_id} "
                f"path={request.url.path} client_ip={client_ip} "
                f"error={str(e)}"
            )
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check trusted proxy headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        if request.client:
            return request.client.host
        
        return "unknown"
