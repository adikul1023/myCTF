"""
Invite code Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class InviteCodeCreate(BaseModel):
    """Schema for creating an invite code (admin only)."""
    max_uses: int = Field(
        default=1,
        ge=1,
        le=100,
        description="Maximum number of times this code can be used",
    )
    expires_in_days: Optional[int] = Field(
        None,
        ge=1,
        le=365,
        description="Number of days until the code expires (None = never)",
    )


class InviteCodeResponse(BaseModel):
    """Schema for invite code response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    code: str
    is_used: bool
    max_uses: int
    use_count: int
    expires_at: Optional[datetime]
    created_at: datetime
    created_by_id: Optional[UUID]


class InviteCodeListResponse(BaseModel):
    """Schema for invite code list response."""
    codes: list[InviteCodeResponse]
    total: int


class InviteCodeValidate(BaseModel):
    """Schema for validating an invite code."""
    code: str = Field(
        ...,
        min_length=8,
        max_length=64,
        description="The invite code to validate",
    )


class InviteCodeValidateResponse(BaseModel):
    """Schema for invite code validation response."""
    is_valid: bool
    message: str
