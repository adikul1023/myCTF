"""
Telemetry Service - Non-sensitive event tracking.

PRIVACY-FIRST DESIGN:
- NO submitted answers or flags stored
- NO personally identifiable information beyond user_id
- NO IP addresses stored
- Minimal data for analytics only

This service provides hooks for tracking user activity
without compromising user privacy or leaking sensitive data.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import (
    TelemetryEvent,
    TelemetryEventType,
    UserArtifactDownload,
)


logger = logging.getLogger(__name__)


class TelemetryService:
    """
    Service for recording telemetry events.
    
    All methods are designed to be non-blocking and fail-safe.
    Telemetry failures should never impact user experience.
    """
    
    @staticmethod
    def _sanitize_extra_data(data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Sanitize extra data to ensure no sensitive information is stored.
        
        Removes any fields that could contain PII or sensitive data.
        """
        if data is None:
            return None
        
        # Whitelist of allowed fields
        ALLOWED_FIELDS = {
            "time_spent_seconds",
            "attempt_number",
            "difficulty",
            "artifact_type",
            "file_size",
            "client_type",  # e.g., "web", "api"
        }
        
        # Blacklist of forbidden fields (extra safety)
        FORBIDDEN_PATTERNS = [
            "answer", "flag", "password", "token", "secret",
            "email", "ip", "address", "phone", "name",
            "cookie", "session", "auth", "credential",
        ]
        
        sanitized = {}
        for key, value in data.items():
            # Check against blacklist
            key_lower = key.lower()
            if any(pattern in key_lower for pattern in FORBIDDEN_PATTERNS):
                logger.warning(
                    f"Telemetry: Blocked sensitive field '{key}' from being recorded"
                )
                continue
            
            # Check against whitelist
            if key in ALLOWED_FIELDS:
                sanitized[key] = value
        
        return sanitized if sanitized else None
    
    async def record_event(
        self,
        db: AsyncSession,
        event_type: TelemetryEventType,
        user_id: Optional[UUID] = None,
        case_id: Optional[UUID] = None,
        artifact_id: Optional[UUID] = None,
        was_successful: Optional[bool] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[TelemetryEvent]:
        """
        Record a telemetry event.
        
        This method is designed to be fail-safe - errors are logged
        but do not propagate to the caller.
        
        Args:
            db: Database session
            event_type: Type of event
            user_id: User who triggered the event (optional for anonymous)
            case_id: Related case (if applicable)
            artifact_id: Related artifact (if applicable)
            was_successful: For submission events, whether it was correct
            extra_data: Additional non-sensitive data
        
        Returns:
            The created TelemetryEvent or None if failed
        """
        try:
            sanitized_data = self._sanitize_extra_data(extra_data)
            
            event = TelemetryEvent(
                event_type=event_type,
                user_id=user_id,
                case_id=case_id,
                artifact_id=artifact_id,
                was_successful=was_successful,
                created_at=datetime.now(timezone.utc),
                extra_data=sanitized_data,
            )
            
            db.add(event)
            await db.flush()
            
            logger.debug(
                f"Telemetry: Recorded {event_type.value} "
                f"user={user_id} case={case_id} artifact={artifact_id}"
            )
            
            return event
            
        except Exception as e:
            # Log but don't propagate - telemetry should never break the app
            logger.error(f"Telemetry: Failed to record event: {e}")
            return None
    
    # ===== Convenience Methods (Telemetry Hooks) =====
    
    async def on_case_viewed(
        self,
        db: AsyncSession,
        user_id: UUID,
        case_id: UUID,
    ) -> None:
        """Hook: User viewed a case details page."""
        await self.record_event(
            db=db,
            event_type=TelemetryEventType.CASE_VIEWED,
            user_id=user_id,
            case_id=case_id,
        )
    
    async def on_case_started(
        self,
        db: AsyncSession,
        user_id: UUID,
        case_id: UUID,
    ) -> None:
        """Hook: User started working on a case (first artifact download)."""
        await self.record_event(
            db=db,
            event_type=TelemetryEventType.CASE_STARTED,
            user_id=user_id,
            case_id=case_id,
        )
    
    async def on_artifact_downloaded(
        self,
        db: AsyncSession,
        user_id: UUID,
        artifact_id: UUID,
        case_id: Optional[UUID] = None,
        file_size: Optional[int] = None,
    ) -> None:
        """
        Hook: User downloaded an artifact.
        
        Also updates the UserArtifactDownload tracking table.
        """
        extra = {}
        if file_size is not None:
            extra["file_size"] = file_size
        
        await self.record_event(
            db=db,
            event_type=TelemetryEventType.ARTIFACT_DOWNLOADED,
            user_id=user_id,
            case_id=case_id,
            artifact_id=artifact_id,
            extra_data=extra if extra else None,
        )
        
        # Also track in UserArtifactDownload for unlock conditions
        await self._track_artifact_download(db, user_id, artifact_id)
    
    async def _track_artifact_download(
        self,
        db: AsyncSession,
        user_id: UUID,
        artifact_id: UUID,
    ) -> None:
        """Track artifact download for unlock condition checks."""
        try:
            # Check if already downloaded
            result = await db.execute(
                select(UserArtifactDownload).where(
                    UserArtifactDownload.user_id == user_id,
                    UserArtifactDownload.artifact_id == artifact_id,
                )
            )
            download = result.scalar_one_or_none()
            
            if download:
                # Increment download count
                download.download_count += 1
            else:
                # First download
                download = UserArtifactDownload(
                    user_id=user_id,
                    artifact_id=artifact_id,
                    download_count=1,
                )
                db.add(download)
            
            await db.flush()
            
        except Exception as e:
            logger.error(f"Telemetry: Failed to track artifact download: {e}")
    
    async def on_submission_attempt(
        self,
        db: AsyncSession,
        user_id: UUID,
        case_id: UUID,
        was_correct: bool,
        attempt_number: Optional[int] = None,
        time_spent_seconds: Optional[int] = None,
    ) -> None:
        """
        Hook: User submitted an answer.
        
        IMPORTANT: Does NOT record the submitted answer itself.
        Only records success/failure for analytics.
        """
        extra = {}
        if attempt_number is not None:
            extra["attempt_number"] = attempt_number
        if time_spent_seconds is not None:
            extra["time_spent_seconds"] = time_spent_seconds
        
        await self.record_event(
            db=db,
            event_type=TelemetryEventType.SUBMISSION_ATTEMPT,
            user_id=user_id,
            case_id=case_id,
            was_successful=was_correct,
            extra_data=extra if extra else None,
        )
    
    async def on_case_solved(
        self,
        db: AsyncSession,
        user_id: UUID,
        case_id: UUID,
        time_spent_seconds: Optional[int] = None,
    ) -> None:
        """Hook: User solved a case (first correct submission)."""
        extra = {}
        if time_spent_seconds is not None:
            extra["time_spent_seconds"] = time_spent_seconds
        
        await self.record_event(
            db=db,
            event_type=TelemetryEventType.CASE_SOLVED,
            user_id=user_id,
            case_id=case_id,
            was_successful=True,
            extra_data=extra if extra else None,
        )
    
    async def on_artifact_unlocked(
        self,
        db: AsyncSession,
        user_id: UUID,
        artifact_id: UUID,
        case_id: Optional[UUID] = None,
    ) -> None:
        """Hook: An artifact was unlocked for a user."""
        await self.record_event(
            db=db,
            event_type=TelemetryEventType.ARTIFACT_UNLOCKED,
            user_id=user_id,
            artifact_id=artifact_id,
            case_id=case_id,
        )
    
    async def on_case_unlocked(
        self,
        db: AsyncSession,
        user_id: UUID,
        case_id: UUID,
    ) -> None:
        """Hook: A case was unlocked for a user."""
        await self.record_event(
            db=db,
            event_type=TelemetryEventType.CASE_UNLOCKED,
            user_id=user_id,
            case_id=case_id,
        )
    
    # ===== Analytics Queries =====
    
    async def get_case_analytics(
        self,
        db: AsyncSession,
        case_id: UUID,
    ) -> Dict[str, Any]:
        """
        Get analytics for a specific case.
        
        Returns view counts, download counts, solve rates, etc.
        """
        try:
            # Views count
            views_result = await db.execute(
                select(func.count(TelemetryEvent.id)).where(
                    TelemetryEvent.case_id == case_id,
                    TelemetryEvent.event_type == TelemetryEventType.CASE_VIEWED,
                )
            )
            views = views_result.scalar() or 0
            
            # Unique users who viewed
            unique_views_result = await db.execute(
                select(func.count(func.distinct(TelemetryEvent.user_id))).where(
                    TelemetryEvent.case_id == case_id,
                    TelemetryEvent.event_type == TelemetryEventType.CASE_VIEWED,
                )
            )
            unique_views = unique_views_result.scalar() or 0
            
            # Submission attempts
            attempts_result = await db.execute(
                select(func.count(TelemetryEvent.id)).where(
                    TelemetryEvent.case_id == case_id,
                    TelemetryEvent.event_type == TelemetryEventType.SUBMISSION_ATTEMPT,
                )
            )
            attempts = attempts_result.scalar() or 0
            
            # Successful solves
            solves_result = await db.execute(
                select(func.count(TelemetryEvent.id)).where(
                    TelemetryEvent.case_id == case_id,
                    TelemetryEvent.event_type == TelemetryEventType.CASE_SOLVED,
                )
            )
            solves = solves_result.scalar() or 0
            
            return {
                "case_id": str(case_id),
                "total_views": views,
                "unique_viewers": unique_views,
                "total_attempts": attempts,
                "total_solves": solves,
                "solve_rate": round((solves / unique_views * 100), 2) if unique_views > 0 else 0.0,
            }
            
        except Exception as e:
            logger.error(f"Telemetry: Failed to get case analytics: {e}")
            return {"error": "Failed to retrieve analytics"}
    
    async def get_user_activity_summary(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> Dict[str, Any]:
        """
        Get activity summary for a user (for their profile).
        
        Does NOT expose sensitive data - only aggregate counts.
        """
        try:
            # Cases viewed
            cases_viewed_result = await db.execute(
                select(func.count(func.distinct(TelemetryEvent.case_id))).where(
                    TelemetryEvent.user_id == user_id,
                    TelemetryEvent.event_type == TelemetryEventType.CASE_VIEWED,
                )
            )
            cases_viewed = cases_viewed_result.scalar() or 0
            
            # Cases solved
            cases_solved_result = await db.execute(
                select(func.count(func.distinct(TelemetryEvent.case_id))).where(
                    TelemetryEvent.user_id == user_id,
                    TelemetryEvent.event_type == TelemetryEventType.CASE_SOLVED,
                )
            )
            cases_solved = cases_solved_result.scalar() or 0
            
            # Artifacts downloaded
            artifacts_downloaded_result = await db.execute(
                select(func.count(UserArtifactDownload.id)).where(
                    UserArtifactDownload.user_id == user_id,
                )
            )
            artifacts_downloaded = artifacts_downloaded_result.scalar() or 0
            
            return {
                "user_id": str(user_id),
                "cases_viewed": cases_viewed,
                "cases_solved": cases_solved,
                "artifacts_downloaded": artifacts_downloaded,
            }
            
        except Exception as e:
            logger.error(f"Telemetry: Failed to get user activity: {e}")
            return {"error": "Failed to retrieve activity"}


# Global singleton instance
telemetry_service = TelemetryService()
