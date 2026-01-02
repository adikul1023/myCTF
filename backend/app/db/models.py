"""
SQLAlchemy ORM models for the forensic CTF platform.

Models:
- User: Platform users with invite-code based registration
- Case: Forensic investigation cases/challenges
- Artifact: Evidence files associated with cases
- Submission: User answer submissions for cases
- InviteCode: Registration invite codes
"""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .base import Base, TimestampMixin


class DifficultyLevel(str, PyEnum):
    """Case difficulty levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    INSANE = "insane"


class ArtifactType(str, PyEnum):
    """Types of forensic artifacts."""
    DISK_IMAGE = "disk_image"
    MEMORY_DUMP = "memory_dump"
    PCAP = "pcap"
    LOG_FILE = "log_file"
    REGISTRY_HIVE = "registry_hive"
    EMAIL_ARCHIVE = "email_archive"
    DOCUMENT = "document"
    EXECUTABLE = "executable"
    ARCHIVE = "archive"
    OTHER = "other"


class UnlockConditionType(str, PyEnum):
    """Types of unlock conditions for artifacts and cases."""
    CASE_SOLVED = "case_solved"           # Must solve a specific case
    ARTIFACT_DOWNLOADED = "artifact_downloaded"  # Must download specific artifact
    TIME_BASED = "time_based"             # Unlocks after specific time
    POINTS_THRESHOLD = "points_threshold"  # User must have X total points
    MANUAL = "manual"                     # Admin manually unlocks


class TelemetryEventType(str, PyEnum):
    """Types of telemetry events (no sensitive data logged)."""
    CASE_VIEWED = "case_viewed"
    CASE_STARTED = "case_started"
    ARTIFACT_DOWNLOADED = "artifact_downloaded"
    SUBMISSION_ATTEMPT = "submission_attempt"  # Only success/fail, no answer
    CASE_SOLVED = "case_solved"
    ARTIFACT_UNLOCKED = "artifact_unlocked"
    CASE_UNLOCKED = "case_unlocked"


class User(Base, TimestampMixin):
    """
    User model for platform authentication.
    
    Registration is invite-only - users must provide a valid invite code.
    Passwords are hashed using Argon2.
    """
    
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    
    username: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )
    
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    invite_code_used: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    
    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    # Time-variant flag salt for anti-replay protection
    flag_salt: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default=lambda: __import__('secrets').token_hex(32),
    )
    
    flag_salt_rotated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    
    # Relationships
    submissions: Mapped[List["Submission"]] = relationship(
        "Submission",
        back_populates="user",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<User {self.username} ({self.email})>"


class InviteCode(Base, TimestampMixin):
    """
    Invite codes for registration.
    
    Each code can only be used once.
    Codes can have an optional expiration date.
    """
    
    __tablename__ = "invite_codes"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    code: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )
    
    is_used: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    used_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    
    used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    
    max_uses: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    
    use_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    
    def __repr__(self) -> str:
        return f"<InviteCode {self.code[:8]}... used={self.is_used}>"
    
    @property
    def is_valid(self) -> bool:
        """Check if the invite code is still valid."""
        if self.is_used and self.use_count >= self.max_uses:
            return False
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        return True


class Case(Base, TimestampMixin):
    """
    Forensic investigation case/challenge.
    
    Each case represents a complete forensic scenario with:
    - Story/narrative background
    - Multiple artifacts to analyze
    - A semantic truth (the actual answer, stored as hash)
    - Difficulty rating
    
    The semantic_truth_hash stores the hashed version of the answer.
    This is NEVER stored in plaintext.
    """
    
    __tablename__ = "cases"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    slug: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    
    # The story/narrative - this is what makes it forensic simulation
    story_background: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    
    # Investigation questions/objectives (what the user needs to find)
    investigation_objectives: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    
    difficulty: Mapped[DifficultyLevel] = mapped_column(
        Enum(
            DifficultyLevel,
            values_callable=lambda x: [e.value for e in x],
            create_constraint=False,
            native_enum=True,
        ),
        default=DifficultyLevel.INTERMEDIATE,
        nullable=False,
    )
    
    # The answer hash - NEVER store plaintext
    # This is the hash of the semantic truth
    semantic_truth_hash: Mapped[str] = mapped_column(
        String(64),  # SHA-256 hex
        nullable=False,
    )
    
    # Additional salt for extra entropy in flag generation
    case_salt: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    
    # Points awarded for solving
    points: Mapped[int] = mapped_column(
        Integer,
        default=100,
        nullable=False,
    )
    
    # Case metadata (tools needed, estimated time, etc.)
    extra_metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    
    # Relationships
    artifacts: Mapped[List["Artifact"]] = relationship(
        "Artifact",
        back_populates="case",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    
    submissions: Mapped[List["Submission"]] = relationship(
        "Submission",
        back_populates="case",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<Case {self.title} ({self.difficulty.value})>"


class Artifact(Base, TimestampMixin):
    """
    Forensic artifact/evidence file.
    
    Artifacts are the actual files that users analyze:
    - Disk images
    - Memory dumps
    - Network captures
    - Log files
    - etc.
    
    Files are stored in S3-compatible storage (MinIO).
    """
    
    __tablename__ = "artifacts"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    artifact_type: Mapped[ArtifactType] = mapped_column(
        Enum(
            ArtifactType,
            values_callable=lambda x: [e.value for e in x],
            create_constraint=False,
            native_enum=True,
        ),
        default=ArtifactType.OTHER,
        nullable=False,
    )
    
    # S3/MinIO storage path
    storage_path: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )
    
    # File metadata
    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    
    file_hash_sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    
    mime_type: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
    )
    
    # Additional metadata (compression, encryption, etc.)
    extra_metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )
    
    # Relationships
    case: Mapped["Case"] = relationship(
        "Case",
        back_populates="artifacts",
    )
    
    def __repr__(self) -> str:
        return f"<Artifact {self.name} ({self.artifact_type.value})>"


class Submission(Base, TimestampMixin):
    """
    User submission for a case.
    
    Tracks all submission attempts for:
    - Auditing
    - Anti-cheat detection
    - Statistics
    
    Submissions can be either:
    - Answer submissions (user submits their analysis result)
    - Flag submissions (user submits the generated flag)
    """
    
    __tablename__ = "submissions"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Hash of what the user submitted (NOT plaintext for privacy)
    submitted_answer_hash: Mapped[str] = mapped_column(
        String(64),  # SHA-256 hash
        nullable=False,
    )
    
    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    # For analytics and anti-cheat
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True,
    )
    
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
    )
    
    # Time tracking for suspiciously fast solves
    time_spent_seconds: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="submissions",
    )
    
    case: Mapped["Case"] = relationship(
        "Case",
        back_populates="submissions",
    )
    
    # Indexes for common queries
    __table_args__ = (
        Index("ix_submissions_user_case", "user_id", "case_id"),
        Index("ix_submissions_correct", "is_correct"),
    )
    
    def __repr__(self) -> str:
        return f"<Submission user={self.user_id} case={self.case_id} correct={self.is_correct}>"


class CaseDependency(Base, TimestampMixin):
    """
    Case-to-case dependency relationship.
    
    A case can require other cases to be solved before it becomes accessible.
    This enables progressive, story-driven investigations.
    """
    
    __tablename__ = "case_dependencies"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    # The case that has the dependency (the "child")
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # The case that must be solved first (the "parent/prerequisite")
    required_case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Optional: requires a specific artifact from the required case to be downloaded
    required_artifact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("artifacts.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Description shown to user about why this is locked
    lock_reason: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
    )
    
    __table_args__ = (
        UniqueConstraint("case_id", "required_case_id", name="uq_case_dependency"),
        Index("ix_case_dependencies_case", "case_id"),
        Index("ix_case_dependencies_required", "required_case_id"),
    )
    
    def __repr__(self) -> str:
        return f"<CaseDependency case={self.case_id} requires={self.required_case_id}>"


class ArtifactUnlockCondition(Base, TimestampMixin):
    """
    Unlock condition for an artifact.
    
    Artifacts can be locked until specific conditions are met:
    - Another case is solved
    - Another artifact is downloaded
    - Time-based (unlocks at specific datetime)
    - Points threshold (user has X total points)
    - Manual (admin unlocks for specific users)
    """
    
    __tablename__ = "artifact_unlock_conditions"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    # The artifact this condition applies to
    artifact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("artifacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    condition_type: Mapped[UnlockConditionType] = mapped_column(
        Enum(
            UnlockConditionType,
            values_callable=lambda x: [e.value for e in x],
            create_constraint=False,
            native_enum=True,
        ),
        nullable=False,
    )
    
    # For CASE_SOLVED: the case that must be solved
    required_case_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=True,
    )
    
    # For ARTIFACT_DOWNLOADED: the artifact that must be downloaded
    required_artifact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("artifacts.id", ondelete="CASCADE"),
        nullable=True,
    )
    
    # For TIME_BASED: when the artifact unlocks
    unlock_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # For POINTS_THRESHOLD: minimum points required
    required_points: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    
    # Description shown to user about unlock requirements
    description: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
    )
    
    __table_args__ = (
        Index("ix_artifact_unlock_artifact", "artifact_id"),
        Index("ix_artifact_unlock_type", "condition_type"),
    )
    
    def __repr__(self) -> str:
        return f"<ArtifactUnlockCondition artifact={self.artifact_id} type={self.condition_type.value}>"


class UserArtifactDownload(Base, TimestampMixin):
    """
    Tracks which artifacts a user has downloaded.
    
    Used for:
    - Unlock condition checks (artifact_downloaded)
    - Telemetry (without storing sensitive data)
    - Rate limiting downloads
    """
    
    __tablename__ = "user_artifact_downloads"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    artifact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("artifacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # First download time
    first_downloaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    # Count of downloads (for rate limiting/analytics)
    download_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    
    __table_args__ = (
        UniqueConstraint("user_id", "artifact_id", name="uq_user_artifact_download"),
        Index("ix_user_artifact_downloads_user", "user_id"),
        Index("ix_user_artifact_downloads_artifact", "artifact_id"),
    )
    
    def __repr__(self) -> str:
        return f"<UserArtifactDownload user={self.user_id} artifact={self.artifact_id}>"


class TelemetryEvent(Base):
    """
    Telemetry event for analytics.
    
    PRIVACY-FIRST DESIGN:
    - NO submitted answers or flags stored
    - NO personally identifiable information beyond user_id
    - NO IP addresses stored (only hashed for uniqueness if needed)
    - Minimal data for analytics only
    """
    
    __tablename__ = "telemetry_events"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    event_type: Mapped[TelemetryEventType] = mapped_column(
        Enum(
            TelemetryEventType,
            values_callable=lambda x: [e.value for e in x],
            create_constraint=False,
            native_enum=True,
        ),
        nullable=False,
        index=True,
    )
    
    # User who triggered the event (for per-user analytics)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Related case (if applicable)
    case_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Related artifact (if applicable)
    artifact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("artifacts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # For SUBMISSION_ATTEMPT: only success/fail, NEVER the answer
    was_successful: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
    )
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    
    # Non-sensitive metadata (e.g., time_spent, but NO PII)
    extra_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )
    
    __table_args__ = (
        Index("ix_telemetry_type_created", "event_type", "created_at"),
        Index("ix_telemetry_case_type", "case_id", "event_type"),
    )
    
    def __repr__(self) -> str:
        return f"<TelemetryEvent {self.event_type.value} at {self.created_at}>"


class ManualUnlock(Base, TimestampMixin):
    """
    Manual unlock record for admin-controlled access.
    
    Admins can grant specific users access to locked artifacts
    or cases outside of the normal unlock conditions.
    """
    
    __tablename__ = "manual_unlocks"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Either artifact_id OR case_id should be set, not both
    artifact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("artifacts.id", ondelete="CASCADE"),
        nullable=True,
    )
    
    case_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=True,
    )
    
    # Admin who granted the unlock
    granted_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Reason for manual unlock (for audit trail)
    reason: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
    )
    
    __table_args__ = (
        Index("ix_manual_unlocks_user", "user_id"),
        Index("ix_manual_unlocks_artifact", "artifact_id"),
        Index("ix_manual_unlocks_case", "case_id"),
    )
    
    def __repr__(self) -> str:
        target = f"artifact={self.artifact_id}" if self.artifact_id else f"case={self.case_id}"
        return f"<ManualUnlock user={self.user_id} {target}>"
