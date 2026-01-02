"""
Case-related Pydantic schemas for request/response validation.
"""

import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict

from ..db.models import DifficultyLevel


class CaseBase(BaseModel):
    """Base case schema with common fields."""
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    points: int = Field(default=100, ge=0, le=10000)


class CaseCreate(CaseBase):
    """Schema for creating a new case (admin only)."""
    slug: Optional[str] = Field(
        None,
        min_length=3,
        max_length=255,
        description="URL-friendly identifier (auto-generated if not provided)",
    )
    story_background: str = Field(
        ...,
        min_length=50,
        description="The narrative/story background for the case",
    )
    investigation_objectives: str = Field(
        ...,
        min_length=20,
        description="What the investigator needs to find",
    )
    semantic_truth: str = Field(
        ...,
        min_length=1,
        description="The actual answer (will be hashed, NEVER stored plaintext)",
    )
    extra_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata (tools needed, estimated time, etc.)",
    )
    
    @field_validator("slug", mode="before")
    @classmethod
    def generate_slug(cls, v: Optional[str], info) -> str:
        if v:
            # Validate provided slug
            if not re.match(r"^[a-z0-9-]+$", v):
                raise ValueError("Slug must contain only lowercase alphanumeric characters and hyphens")
            return v
        return None  # Will be auto-generated from title
    
    @field_validator("semantic_truth")
    @classmethod
    def validate_semantic_truth(cls, v: str) -> str:
        """Ensure semantic truth is not empty after stripping."""
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Semantic truth cannot be empty")
        return cleaned


class CaseUpdate(BaseModel):
    """Schema for updating a case (admin only)."""
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    story_background: Optional[str] = Field(None, min_length=50)
    investigation_objectives: Optional[str] = Field(None, min_length=20)
    difficulty: Optional[DifficultyLevel] = None
    points: Optional[int] = Field(None, ge=0, le=10000)
    extra_metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    # NOTE: semantic_truth cannot be updated through this endpoint
    # A separate admin endpoint should be used for that


class CaseResponse(BaseModel):
    """Schema for case list response (minimal data)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    title: str
    slug: str
    description: str
    difficulty: DifficultyLevel
    points: int
    is_active: bool
    created_at: datetime


class CaseListResponse(BaseModel):
    """Schema for paginated case list."""
    cases: List[CaseResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class CaseDetailResponse(CaseResponse):
    """
    Schema for detailed case view.
    
    NOTE: This does NOT include:
    - semantic_truth_hash (would allow brute force)
    - Any hints that could spoil the investigation
    """
    story_background: str
    investigation_objectives: str
    extra_metadata: Optional[Dict[str, Any]]
    artifact_count: int = 0
    solve_count: int = 0  # Number of users who solved this case
    
    # User-specific data (only if authenticated)
    user_solved: bool = False
    user_attempts: int = 0


class CaseStatistics(BaseModel):
    """Schema for case statistics (admin view)."""
    model_config = ConfigDict(from_attributes=True)
    
    case_id: UUID
    total_attempts: int
    unique_users: int
    solve_count: int
    solve_rate: float  # percentage
    average_attempts_to_solve: float
    first_blood_user_id: Optional[UUID]
    first_blood_at: Optional[datetime]
