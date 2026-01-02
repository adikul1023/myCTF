"""
Artifact-related Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from ..db.models import ArtifactType


class ArtifactBase(BaseModel):
    """Base artifact schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    artifact_type: ArtifactType = ArtifactType.OTHER


class ArtifactCreate(ArtifactBase):
    """Schema for creating an artifact (admin only)."""
    case_id: UUID = Field(..., description="The case this artifact belongs to")
    extra_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata (compression, encryption hints, etc.)",
    )


class ArtifactUpdate(BaseModel):
    """Schema for updating an artifact (admin only)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    artifact_type: Optional[ArtifactType] = None
    extra_metadata: Optional[Dict[str, Any]] = None


class ArtifactResponse(BaseModel):
    """Schema for artifact response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    case_id: UUID
    name: str
    description: Optional[str]
    artifact_type: ArtifactType
    file_size: int
    file_hash_sha256: str
    mime_type: Optional[str]
    extra_metadata: Optional[Dict[str, Any]]
    created_at: datetime


class ArtifactDownloadResponse(BaseModel):
    """Schema for artifact download response (presigned URL)."""
    artifact_id: UUID
    download_url: str
    expires_in: int  # seconds
    filename: str
    file_size: int


class ArtifactUploadRequest(BaseModel):
    """Schema for requesting artifact upload (admin only)."""
    case_id: UUID
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: Optional[str] = None
    file_size: int = Field(..., gt=0)


class ArtifactUploadResponse(BaseModel):
    """Schema for artifact upload response (presigned URL)."""
    upload_url: str
    artifact_id: UUID
    expires_in: int  # seconds
    fields: Optional[Dict[str, str]] = None  # For form-based uploads


class ArtifactListResponse(BaseModel):
    """Schema for artifact list response."""
    artifacts: List[ArtifactResponse]
    total: int
