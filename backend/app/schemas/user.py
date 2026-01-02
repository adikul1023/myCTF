"""
User-related Pydantic schemas for request/response validation.
"""

import re
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    username: str = Field(
        ...,
        min_length=3,
        max_length=64,
        description="Username (alphanumeric and underscores only)",
    )
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username must contain only alphanumeric characters and underscores")
        return v.lower()


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(
        ...,
        min_length=12,
        max_length=128,
        description="Password (minimum 12 characters)",
    )
    invite_code: str = Field(
        ...,
        min_length=8,
        max_length=64,
        description="Invite code for registration",
    )
    
    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate password strength.
        Requirements:
        - At least 12 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        """
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    """Schema for user response (public data only)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    email: EmailStr
    username: str
    is_active: bool
    is_admin: bool
    created_at: datetime


class UserProfileResponse(UserResponse):
    """Extended user profile with statistics."""
    total_submissions: int = 0
    correct_submissions: int = 0
    total_points: int = 0


class TokenResponse(BaseModel):
    """Schema for authentication token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenPayloadSchema(BaseModel):
    """Schema for decoded JWT token payload."""
    sub: str
    exp: datetime
    iat: datetime
    type: str = "access"
