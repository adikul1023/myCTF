"""
FastAPI dependencies for authentication, authorization, and rate limiting.
"""

import ipaddress
from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .security import security_service, TokenPayload
from ..db.session import get_db
from ..db.models import User
from ..utils.rate_limiter import RateLimiter


# HTTP Bearer token scheme
bearer_scheme = HTTPBearer(auto_error=False)

# Rate limiters
submission_rate_limiter = RateLimiter(
    requests_per_minute=10,
    key_prefix="submission",
)

auth_rate_limiter = RateLimiter(
    requests_per_minute=5,
    key_prefix="auth",
)

# Account lockout - stricter than general auth rate limit
login_attempt_limiter = RateLimiter(
    requests_per_minute=settings.MAX_LOGIN_ATTEMPTS,
    key_prefix="login_attempt",
)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Get the current user if a valid token is provided.
    Returns None if no token or invalid token.
    """
    if not credentials:
        return None
    
    token_payload = security_service.decode_token(credentials.credentials)
    if not token_payload:
        return None
    
    from sqlalchemy import select
    
    result = await db.execute(
        select(User).where(User.id == token_payload.sub)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        return None
    
    return user


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get the current authenticated user.
    Raises 401 if not authenticated or invalid token.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_payload = security_service.decode_token(credentials.credentials)
    if not token_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    from sqlalchemy import select
    
    result = await db.execute(
        select(User).where(User.id == token_payload.sub)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )
    
    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current user and verify they have admin privileges.
    Raises 403 if not an admin.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to require admin privileges.
    Alias for get_current_admin for cleaner usage in route definitions.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


def _is_trusted_proxy(ip: str) -> bool:
    """
    Check if an IP address is in the trusted proxy list.
    """
    try:
        client_ip = ipaddress.ip_address(ip)
        for proxy in settings.TRUSTED_PROXIES:
            if '/' in proxy:
                # It's a network
                if client_ip in ipaddress.ip_network(proxy, strict=False):
                    return True
            else:
                # It's a single IP
                if client_ip == ipaddress.ip_address(proxy):
                    return True
        return False
    except ValueError:
        return False


def get_client_ip(request: Request) -> str:
    """
    Extract the client IP address from the request.
    
    Only trusts X-Forwarded-For header from trusted proxies.
    This prevents IP spoofing attacks.
    """
    # Get the direct client IP
    direct_ip = request.client.host if request.client else "unknown"
    
    # Only trust proxy headers from known proxies
    if _is_trusted_proxy(direct_ip):
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain (original client)
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
    
    return direct_ip


async def check_submission_rate_limit(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Check rate limit for flag submissions.
    Uses user ID as the rate limit key.
    """
    key = f"user:{current_user.id}"
    
    if not await submission_rate_limiter.is_allowed(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please wait before submitting again.",
        )
    
    return current_user


async def check_auth_rate_limit(request: Request) -> str:
    """
    Check rate limit for authentication endpoints.
    Uses client IP as the rate limit key.
    """
    client_ip = get_client_ip(request)
    
    if not await auth_rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Please try again later.",
        )
    
    return client_ip
