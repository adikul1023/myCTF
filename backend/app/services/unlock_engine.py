"""
Unlock Engine - Service for managing case and artifact unlock conditions.

Handles:
- Case dependency checks
- Artifact unlock condition validation
- Manual unlock management
- User progress tracking for unlocks
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import (
    Case,
    Artifact,
    Submission,
    CaseDependency,
    ArtifactUnlockCondition,
    UserArtifactDownload,
    ManualUnlock,
    UnlockConditionType,
)
from .telemetry_service import telemetry_service


class UnlockEngine:
    """
    Engine for managing unlock conditions and dependencies.
    
    Provides methods for:
    - Checking if a case is accessible to a user
    - Checking if an artifact is accessible to a user
    - Managing manual unlocks
    - Creating and updating dependencies
    """
    
    # ===== Case Dependency Methods =====
    
    async def check_case_accessible(
        self,
        db: AsyncSession,
        user_id: UUID,
        case_id: UUID,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a case is accessible to a user.
        
        A case is accessible if:
        1. It has no dependencies, OR
        2. All dependency conditions are met, OR
        3. The user has a manual unlock for this case
        
        Args:
            db: Database session
            user_id: The user to check
            case_id: The case to check
        
        Returns:
            Tuple of (is_accessible, lock_reason_if_locked)
        """
        # Check for manual unlock first (fastest path)
        manual_unlock = await db.execute(
            select(ManualUnlock).where(
                ManualUnlock.user_id == user_id,
                ManualUnlock.case_id == case_id,
            )
        )
        if manual_unlock.scalar_one_or_none():
            return (True, None)
        
        # Get all dependencies for this case
        deps_result = await db.execute(
            select(CaseDependency).where(CaseDependency.case_id == case_id)
        )
        dependencies = list(deps_result.scalars().all())
        
        # No dependencies = accessible
        if not dependencies:
            return (True, None)
        
        # Check each dependency
        for dep in dependencies:
            # Check if user has solved the required case
            solved_result = await db.execute(
                select(Submission).where(
                    Submission.user_id == user_id,
                    Submission.case_id == dep.required_case_id,
                    Submission.is_correct == True,
                ).limit(1)
            )
            
            if solved_result.scalar_one_or_none() is None:
                # Get the required case title for the lock reason
                required_case = await db.execute(
                    select(Case.title).where(Case.id == dep.required_case_id)
                )
                required_title = required_case.scalar() or "another case"
                
                reason = dep.lock_reason or f"You must solve '{required_title}' first."
                return (False, reason)
            
            # If dependency also requires a specific artifact to be downloaded
            if dep.required_artifact_id:
                download_result = await db.execute(
                    select(UserArtifactDownload).where(
                        UserArtifactDownload.user_id == user_id,
                        UserArtifactDownload.artifact_id == dep.required_artifact_id,
                    )
                )
                
                if download_result.scalar_one_or_none() is None:
                    reason = dep.lock_reason or "You must download a required artifact first."
                    return (False, reason)
        
        return (True, None)
    
    async def get_case_dependencies(
        self,
        db: AsyncSession,
        case_id: UUID,
    ) -> List[Dict[str, Any]]:
        """
        Get all dependencies for a case with details.
        
        Returns:
            List of dependency details including required case info
        """
        deps_result = await db.execute(
            select(CaseDependency).where(CaseDependency.case_id == case_id)
        )
        dependencies = list(deps_result.scalars().all())
        
        result = []
        for dep in dependencies:
            # Get required case info
            case_result = await db.execute(
                select(Case).where(Case.id == dep.required_case_id)
            )
            required_case = case_result.scalar_one_or_none()
            
            result.append({
                "dependency_id": str(dep.id),
                "required_case_id": str(dep.required_case_id),
                "required_case_title": required_case.title if required_case else None,
                "required_artifact_id": str(dep.required_artifact_id) if dep.required_artifact_id else None,
                "lock_reason": dep.lock_reason,
            })
        
        return result
    
    async def add_case_dependency(
        self,
        db: AsyncSession,
        case_id: UUID,
        required_case_id: UUID,
        required_artifact_id: Optional[UUID] = None,
        lock_reason: Optional[str] = None,
    ) -> CaseDependency:
        """
        Add a dependency to a case.
        
        Args:
            db: Database session
            case_id: The case that will have the dependency
            required_case_id: The case that must be solved first
            required_artifact_id: Optional artifact that must be downloaded
            lock_reason: Custom message shown when locked
        
        Returns:
            The created CaseDependency
        """
        dependency = CaseDependency(
            case_id=case_id,
            required_case_id=required_case_id,
            required_artifact_id=required_artifact_id,
            lock_reason=lock_reason,
        )
        
        db.add(dependency)
        await db.flush()
        await db.refresh(dependency)
        
        return dependency
    
    async def remove_case_dependency(
        self,
        db: AsyncSession,
        dependency_id: UUID,
    ) -> bool:
        """Remove a case dependency."""
        result = await db.execute(
            select(CaseDependency).where(CaseDependency.id == dependency_id)
        )
        dep = result.scalar_one_or_none()
        
        if not dep:
            return False
        
        await db.delete(dep)
        await db.flush()
        return True
    
    # ===== Artifact Unlock Methods =====
    
    async def check_artifact_accessible(
        self,
        db: AsyncSession,
        user_id: UUID,
        artifact_id: UUID,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if an artifact is accessible to a user.
        
        An artifact is accessible if:
        1. It has no unlock conditions, OR
        2. ALL unlock conditions are met, OR
        3. The user has a manual unlock for this artifact
        
        Args:
            db: Database session
            user_id: The user to check
            artifact_id: The artifact to check
        
        Returns:
            Tuple of (is_accessible, lock_reason_if_locked)
        """
        # Check for manual unlock first
        manual_unlock = await db.execute(
            select(ManualUnlock).where(
                ManualUnlock.user_id == user_id,
                ManualUnlock.artifact_id == artifact_id,
            )
        )
        if manual_unlock.scalar_one_or_none():
            return (True, None)
        
        # Get all unlock conditions for this artifact
        conditions_result = await db.execute(
            select(ArtifactUnlockCondition).where(
                ArtifactUnlockCondition.artifact_id == artifact_id
            )
        )
        conditions = list(conditions_result.scalars().all())
        
        # No conditions = accessible
        if not conditions:
            return (True, None)
        
        # Check each condition
        for condition in conditions:
            is_met, reason = await self._check_unlock_condition(
                db, user_id, condition
            )
            
            if not is_met:
                return (False, reason or condition.description or "Artifact is locked.")
        
        return (True, None)
    
    async def _check_unlock_condition(
        self,
        db: AsyncSession,
        user_id: UUID,
        condition: ArtifactUnlockCondition,
    ) -> Tuple[bool, Optional[str]]:
        """Check if a single unlock condition is met."""
        
        if condition.condition_type == UnlockConditionType.CASE_SOLVED:
            if not condition.required_case_id:
                return (True, None)  # Invalid condition, allow access
            
            result = await db.execute(
                select(Submission).where(
                    Submission.user_id == user_id,
                    Submission.case_id == condition.required_case_id,
                    Submission.is_correct == True,
                ).limit(1)
            )
            
            if result.scalar_one_or_none():
                return (True, None)
            
            # Get case title for reason
            case_result = await db.execute(
                select(Case.title).where(Case.id == condition.required_case_id)
            )
            case_title = case_result.scalar() or "the required case"
            return (False, f"Solve '{case_title}' to unlock this artifact.")
        
        elif condition.condition_type == UnlockConditionType.ARTIFACT_DOWNLOADED:
            if not condition.required_artifact_id:
                return (True, None)
            
            result = await db.execute(
                select(UserArtifactDownload).where(
                    UserArtifactDownload.user_id == user_id,
                    UserArtifactDownload.artifact_id == condition.required_artifact_id,
                )
            )
            
            if result.scalar_one_or_none():
                return (True, None)
            
            return (False, "Download a required artifact first to unlock this.")
        
        elif condition.condition_type == UnlockConditionType.TIME_BASED:
            if not condition.unlock_at:
                return (True, None)
            
            now = datetime.now(timezone.utc)
            if now >= condition.unlock_at:
                return (True, None)
            
            return (False, f"This artifact unlocks at {condition.unlock_at.isoformat()}.")
        
        elif condition.condition_type == UnlockConditionType.POINTS_THRESHOLD:
            if not condition.required_points:
                return (True, None)
            
            # Calculate user's total points
            result = await db.execute(
                select(func.sum(Case.points)).select_from(
                    Submission
                ).join(
                    Case, Submission.case_id == Case.id
                ).where(
                    Submission.user_id == user_id,
                    Submission.is_correct == True,
                )
            )
            total_points = result.scalar() or 0
            
            if total_points >= condition.required_points:
                return (True, None)
            
            return (
                False,
                f"You need {condition.required_points} points to unlock. You have {total_points}."
            )
        
        elif condition.condition_type == UnlockConditionType.MANUAL:
            # Manual unlocks are handled by the ManualUnlock table
            # If we're here, the user doesn't have a manual unlock
            return (False, condition.description or "This artifact requires admin approval.")
        
        # Unknown condition type - allow access (fail open for unknown)
        return (True, None)
    
    async def get_artifact_unlock_conditions(
        self,
        db: AsyncSession,
        artifact_id: UUID,
    ) -> List[Dict[str, Any]]:
        """Get all unlock conditions for an artifact."""
        result = await db.execute(
            select(ArtifactUnlockCondition).where(
                ArtifactUnlockCondition.artifact_id == artifact_id
            )
        )
        conditions = list(result.scalars().all())
        
        return [
            {
                "condition_id": str(c.id),
                "condition_type": c.condition_type.value,
                "required_case_id": str(c.required_case_id) if c.required_case_id else None,
                "required_artifact_id": str(c.required_artifact_id) if c.required_artifact_id else None,
                "unlock_at": c.unlock_at.isoformat() if c.unlock_at else None,
                "required_points": c.required_points,
                "description": c.description,
            }
            for c in conditions
        ]
    
    async def add_artifact_unlock_condition(
        self,
        db: AsyncSession,
        artifact_id: UUID,
        condition_type: UnlockConditionType,
        required_case_id: Optional[UUID] = None,
        required_artifact_id: Optional[UUID] = None,
        unlock_at: Optional[datetime] = None,
        required_points: Optional[int] = None,
        description: Optional[str] = None,
    ) -> ArtifactUnlockCondition:
        """Add an unlock condition to an artifact."""
        condition = ArtifactUnlockCondition(
            artifact_id=artifact_id,
            condition_type=condition_type,
            required_case_id=required_case_id,
            required_artifact_id=required_artifact_id,
            unlock_at=unlock_at,
            required_points=required_points,
            description=description,
        )
        
        db.add(condition)
        await db.flush()
        await db.refresh(condition)
        
        return condition
    
    async def remove_artifact_unlock_condition(
        self,
        db: AsyncSession,
        condition_id: UUID,
    ) -> bool:
        """Remove an artifact unlock condition."""
        result = await db.execute(
            select(ArtifactUnlockCondition).where(
                ArtifactUnlockCondition.id == condition_id
            )
        )
        condition = result.scalar_one_or_none()
        
        if not condition:
            return False
        
        await db.delete(condition)
        await db.flush()
        return True
    
    # ===== Manual Unlock Methods =====
    
    async def grant_manual_unlock(
        self,
        db: AsyncSession,
        user_id: UUID,
        granted_by: UUID,
        artifact_id: Optional[UUID] = None,
        case_id: Optional[UUID] = None,
        reason: Optional[str] = None,
    ) -> ManualUnlock:
        """
        Grant a manual unlock to a user.
        
        Either artifact_id OR case_id must be provided (not both).
        """
        if not artifact_id and not case_id:
            raise ValueError("Either artifact_id or case_id must be provided")
        
        unlock = ManualUnlock(
            user_id=user_id,
            artifact_id=artifact_id,
            case_id=case_id,
            granted_by=granted_by,
            reason=reason,
        )
        
        db.add(unlock)
        await db.flush()
        await db.refresh(unlock)
        
        # Fire telemetry hook
        if artifact_id:
            await telemetry_service.on_artifact_unlocked(
                db, user_id, artifact_id, case_id
            )
        elif case_id:
            await telemetry_service.on_case_unlocked(db, user_id, case_id)
        
        return unlock
    
    async def revoke_manual_unlock(
        self,
        db: AsyncSession,
        unlock_id: UUID,
    ) -> bool:
        """Revoke a manual unlock."""
        result = await db.execute(
            select(ManualUnlock).where(ManualUnlock.id == unlock_id)
        )
        unlock = result.scalar_one_or_none()
        
        if not unlock:
            return False
        
        await db.delete(unlock)
        await db.flush()
        return True
    
    async def get_user_manual_unlocks(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> List[Dict[str, Any]]:
        """Get all manual unlocks for a user."""
        result = await db.execute(
            select(ManualUnlock).where(ManualUnlock.user_id == user_id)
        )
        unlocks = list(result.scalars().all())
        
        return [
            {
                "unlock_id": str(u.id),
                "artifact_id": str(u.artifact_id) if u.artifact_id else None,
                "case_id": str(u.case_id) if u.case_id else None,
                "granted_by": str(u.granted_by) if u.granted_by else None,
                "reason": u.reason,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in unlocks
        ]
    
    # ===== User Progress Methods =====
    
    async def get_user_accessible_cases(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> List[Dict[str, Any]]:
        """
        Get all cases with their accessibility status for a user.
        
        Returns a list of cases with is_accessible and lock_reason fields.
        """
        # Get all active cases
        cases_result = await db.execute(
            select(Case).where(Case.is_active == True).order_by(Case.created_at)
        )
        cases = list(cases_result.scalars().all())
        
        result = []
        for case in cases:
            is_accessible, lock_reason = await self.check_case_accessible(
                db, user_id, case.id
            )
            
            # Check if user has solved this case
            solved_result = await db.execute(
                select(Submission).where(
                    Submission.user_id == user_id,
                    Submission.case_id == case.id,
                    Submission.is_correct == True,
                ).limit(1)
            )
            is_solved = solved_result.scalar_one_or_none() is not None
            
            result.append({
                "case_id": str(case.id),
                "title": case.title,
                "slug": case.slug,
                "difficulty": case.difficulty.value,
                "points": case.points,
                "is_accessible": is_accessible,
                "is_solved": is_solved,
                "lock_reason": lock_reason,
            })
        
        return result
    
    async def get_case_artifact_access(
        self,
        db: AsyncSession,
        user_id: UUID,
        case_id: UUID,
    ) -> List[Dict[str, Any]]:
        """
        Get all artifacts for a case with their accessibility status.
        """
        # First check if case itself is accessible
        case_accessible, case_lock_reason = await self.check_case_accessible(
            db, user_id, case_id
        )
        
        if not case_accessible:
            return [{
                "error": "Case is locked",
                "lock_reason": case_lock_reason,
            }]
        
        # Get artifacts for this case
        artifacts_result = await db.execute(
            select(Artifact).where(Artifact.case_id == case_id)
        )
        artifacts = list(artifacts_result.scalars().all())
        
        result = []
        for artifact in artifacts:
            is_accessible, lock_reason = await self.check_artifact_accessible(
                db, user_id, artifact.id
            )
            
            # Check if user has downloaded this artifact
            download_result = await db.execute(
                select(UserArtifactDownload).where(
                    UserArtifactDownload.user_id == user_id,
                    UserArtifactDownload.artifact_id == artifact.id,
                )
            )
            download = download_result.scalar_one_or_none()
            
            result.append({
                "artifact_id": str(artifact.id),
                "name": artifact.name,
                "description": artifact.description,
                "artifact_type": artifact.artifact_type.value,
                "file_size": artifact.file_size,
                "is_accessible": is_accessible,
                "is_downloaded": download is not None,
                "download_count": download.download_count if download else 0,
                "lock_reason": lock_reason,
            })
        
        return result


# Global singleton instance
unlock_engine = UnlockEngine()
