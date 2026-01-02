"""
Authentication API endpoints.

Endpoints:
- POST /register - Register new user (invite-only)
- POST /login - Authenticate user
- GET /me - Get current user profile
- POST /validate-invite - Check if invite code is valid
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.config import settings
from ....core.dependencies import (
    get_current_user,
    check_auth_rate_limit,
    get_client_ip,
    login_attempt_limiter,
)
from ....core.security import security_service
from ....db.session import get_db
from ....db.models import User, InviteCode
from ....schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserProfileResponse,
    TokenResponse,
)
from ....schemas.invite import InviteCodeValidate, InviteCodeValidateResponse
from ....services.user_service import user_service

from sqlalchemy import select


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Register a new user with an invite code. Invite codes are required.",
)
async def register(
    user_data: UserCreate,
    request: Request,
    _: str = Depends(check_auth_rate_limit),
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user account.
    
    Requires a valid invite code. Each invite code can only be used once
    (or up to max_uses times for multi-use codes).
    
    Password requirements:
    - Minimum 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    user, error = await user_service.register_user(db, user_data)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )
    
    await db.commit()
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user",
    description="Login with email and password to receive an access token.",
)
async def login(
    credentials: UserLogin,
    request: Request,
    _: str = Depends(check_auth_rate_limit),
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate a user and return an access token.
    
    The token should be included in subsequent requests as:
    `Authorization: Bearer <token>`
    """
    client_ip = get_client_ip(request)
    
    # Check account lockout by email (prevents brute force on specific accounts)
    lockout_key = f"email:{credentials.email.lower()}"
    if not await login_attempt_limiter.is_allowed(lockout_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account temporarily locked due to too many failed attempts. Please try again later.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user, error = await user_service.authenticate_user(
        db,
        credentials.email,
        credentials.password,
    )
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",  # Generic message
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Reset lockout on successful login
    await login_attempt_limiter.reset(lockout_key)
    
    access_token = security_service.create_access_token(user_id=str(user.id))
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get current user profile",
    description="Get the profile and statistics of the currently authenticated user.",
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the current user's profile with statistics.
    
    Requires authentication.
    """
    stats = await user_service.get_user_statistics(db, current_user.id)
    
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        is_active=current_user.is_active,
        is_admin=current_user.is_admin,
        created_at=current_user.created_at,
        total_submissions=stats["total_submissions"],
        correct_submissions=stats["correct_submissions"],
        total_points=stats["total_points"],
    )


@router.post(
    "/validate-invite",
    response_model=InviteCodeValidateResponse,
    summary="Validate an invite code",
    description="Check if an invite code is valid before registration.",
)
async def validate_invite_code(
    data: InviteCodeValidate,
    _: str = Depends(check_auth_rate_limit),  # Rate limit to prevent enumeration
    db: AsyncSession = Depends(get_db),
):
    """
    Check if an invite code is valid.
    
    This does not consume the invite code, just checks validity.
    Rate limited to prevent invite code enumeration.
    """
    result = await db.execute(
        select(InviteCode).where(InviteCode.code == data.code)
    )
    invite_code = result.scalar_one_or_none()
    
    if not invite_code:
        return InviteCodeValidateResponse(
            is_valid=False,
            message="Invalid or expired invite code",  # Generic message
        )
    
    if not invite_code.is_valid:
        return InviteCodeValidateResponse(
            is_valid=False,
            message="Invalid or expired invite code",  # Generic message
        )
    
    return InviteCodeValidateResponse(
        is_valid=True,
        message="Invite code is valid",
    )
