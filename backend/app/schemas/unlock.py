"""
Unlock-related Pydantic schemas for dependencies and unlock conditions.

Handles:
- Case dependency management
- Artifact unlock conditions
- Manual unlock operations
- Access status responses
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from ..db.models import UnlockConditionType


# ===== Case Dependency Schemas =====

class CaseDependencyCreate(BaseModel):
    """Schema for creating a case dependency."""
    required_case_id: UUID = Field(
        ...,
        description="The case that must be solved before accessing the dependent case",
    )
    required_artifact_id: Optional[UUID] = Field(
        None,
        description="Optional: artifact that must be downloaded from the required case",
    )
    lock_reason: Optional[str] = Field(
        None,
        max_length=512,
        description="Custom message shown to users when this case is locked",
    )


class CaseDependencyResponse(BaseModel):
    """Response schema for a case dependency."""
    model_config = ConfigDict(from_attributes=True)
    
    dependency_id: UUID
    case_id: UUID
    required_case_id: UUID
    required_case_title: Optional[str]
    required_artifact_id: Optional[UUID]
    lock_reason: Optional[str]
    created_at: Optional[datetime]


class CaseDependencyListResponse(BaseModel):
    """List of dependencies for a case."""
    case_id: UUID
    dependencies: List[CaseDependencyResponse]


# ===== Artifact Unlock Condition Schemas =====

class ArtifactUnlockConditionCreate(BaseModel):
    """Schema for creating an artifact unlock condition."""
    condition_type: UnlockConditionType = Field(
        ...,
        description="Type of unlock condition",
    )
    required_case_id: Optional[UUID] = Field(
        None,
        description="For CASE_SOLVED: the case that must be solved",
    )
    required_artifact_id: Optional[UUID] = Field(
        None,
        description="For ARTIFACT_DOWNLOADED: the artifact that must be downloaded",
    )
    unlock_at: Optional[datetime] = Field(
        None,
        description="For TIME_BASED: when the artifact unlocks (UTC)",
    )
    required_points: Optional[int] = Field(
        None,
        ge=0,
        description="For POINTS_THRESHOLD: minimum points required",
    )
    description: Optional[str] = Field(
        None,
        max_length=512,
        description="Custom description shown to users about this condition",
    )


class ArtifactUnlockConditionResponse(BaseModel):
    """Response schema for an artifact unlock condition."""
    model_config = ConfigDict(from_attributes=True)
    
    condition_id: UUID
    artifact_id: UUID
    condition_type: UnlockConditionType
    required_case_id: Optional[UUID]
    required_artifact_id: Optional[UUID]
    unlock_at: Optional[datetime]
    required_points: Optional[int]
    description: Optional[str]


class ArtifactUnlockConditionListResponse(BaseModel):
    """List of unlock conditions for an artifact."""
    artifact_id: UUID
    conditions: List[ArtifactUnlockConditionResponse]


# ===== Manual Unlock Schemas =====

class ManualUnlockCreate(BaseModel):
    """Schema for granting a manual unlock."""
    user_id: UUID = Field(
        ...,
        description="The user to grant the unlock to",
    )
    artifact_id: Optional[UUID] = Field(
        None,
        description="The artifact to unlock (mutually exclusive with case_id)",
    )
    case_id: Optional[UUID] = Field(
        None,
        description="The case to unlock (mutually exclusive with artifact_id)",
    )
    reason: Optional[str] = Field(
        None,
        max_length=512,
        description="Reason for granting the manual unlock (for audit trail)",
    )


class ManualUnlockResponse(BaseModel):
    """Response schema for a manual unlock."""
    model_config = ConfigDict(from_attributes=True)
    
    unlock_id: UUID
    user_id: UUID
    artifact_id: Optional[UUID]
    case_id: Optional[UUID]
    granted_by: Optional[UUID]
    reason: Optional[str]
    created_at: Optional[datetime]


class ManualUnlockListResponse(BaseModel):
    """List of manual unlocks for a user."""
    user_id: UUID
    unlocks: List[ManualUnlockResponse]


# ===== Access Status Schemas =====

class CaseAccessStatus(BaseModel):
    """Access status for a single case."""
    case_id: UUID
    title: str
    slug: str
    difficulty: str
    points: int
    is_accessible: bool
    is_solved: bool
    lock_reason: Optional[str]


class CaseAccessListResponse(BaseModel):
    """List of cases with access status for a user."""
    user_id: UUID
    cases: List[CaseAccessStatus]


class ArtifactAccessStatus(BaseModel):
    """Access status for a single artifact."""
    artifact_id: UUID
    name: str
    description: Optional[str]
    artifact_type: str
    file_size: int
    is_accessible: bool
    is_downloaded: bool
    download_count: int
    lock_reason: Optional[str]


class CaseArtifactAccessResponse(BaseModel):
    """List of artifacts with access status for a case."""
    case_id: UUID
    user_id: UUID
    artifacts: List[ArtifactAccessStatus]


# ===== Telemetry Schemas (Admin Only) =====

class CaseAnalyticsResponse(BaseModel):
    """Analytics data for a case (admin only)."""
    case_id: UUID
    total_views: int
    unique_viewers: int
    total_attempts: int
    total_solves: int
    solve_rate: float


class UserActivitySummary(BaseModel):
    """Activity summary for a user (privacy-safe)."""
    user_id: UUID
    cases_viewed: int
    cases_solved: int
    artifacts_downloaded: int
