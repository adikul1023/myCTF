"""
Unlock API endpoints for managing case dependencies and artifact access.

Provides:
- Case dependency management (admin)
- Artifact unlock condition management (admin)
- Manual unlock management (admin)
- User access status queries
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.dependencies import (
    get_db,
    get_current_user,
    require_admin,
)
from ....db.models import User, UnlockConditionType
from ....services.unlock_engine import unlock_engine
from ....services.telemetry_service import telemetry_service
from ....schemas.unlock import (
    CaseDependencyCreate,
    CaseDependencyResponse,
    CaseDependencyListResponse,
    ArtifactUnlockConditionCreate,
    ArtifactUnlockConditionResponse,
    ArtifactUnlockConditionListResponse,
    ManualUnlockCreate,
    ManualUnlockResponse,
    ManualUnlockListResponse,
    CaseAccessStatus,
    CaseAccessListResponse,
    ArtifactAccessStatus,
    CaseArtifactAccessResponse,
    CaseAnalyticsResponse,
    UserActivitySummary,
)


router = APIRouter(prefix="/unlock", tags=["unlock"])


# ===== User Access Endpoints =====

@router.get(
    "/cases/accessible",
    response_model=CaseAccessListResponse,
    summary="Get all cases with access status",
)
async def get_accessible_cases(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all cases with their accessibility status for the current user.
    
    Returns which cases are:
    - Accessible (no dependencies or all met)
    - Locked (shows lock reason)
    - Solved
    """
    cases = await unlock_engine.get_user_accessible_cases(db, current_user.id)
    
    return CaseAccessListResponse(
        user_id=current_user.id,
        cases=[
            CaseAccessStatus(
                case_id=UUID(c["case_id"]),
                title=c["title"],
                slug=c["slug"],
                difficulty=c["difficulty"],
                points=c["points"],
                is_accessible=c["is_accessible"],
                is_solved=c["is_solved"],
                lock_reason=c["lock_reason"],
            )
            for c in cases
        ],
    )


@router.get(
    "/cases/{case_id}/artifacts",
    response_model=CaseArtifactAccessResponse,
    summary="Get artifacts with access status for a case",
)
async def get_case_artifacts_access(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all artifacts for a case with their accessibility status.
    
    First checks if the case itself is accessible.
    Then returns each artifact's lock status.
    """
    # Record telemetry
    await telemetry_service.on_case_viewed(db, current_user.id, case_id)
    
    artifacts = await unlock_engine.get_case_artifact_access(
        db, current_user.id, case_id
    )
    
    # Check for error (case locked)
    if artifacts and "error" in artifacts[0]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=artifacts[0]["lock_reason"],
        )
    
    return CaseArtifactAccessResponse(
        case_id=case_id,
        user_id=current_user.id,
        artifacts=[
            ArtifactAccessStatus(
                artifact_id=UUID(a["artifact_id"]),
                name=a["name"],
                description=a.get("description"),
                artifact_type=a["artifact_type"],
                file_size=a["file_size"],
                is_accessible=a["is_accessible"],
                is_downloaded=a["is_downloaded"],
                download_count=a["download_count"],
                lock_reason=a["lock_reason"],
            )
            for a in artifacts
        ],
    )


@router.get(
    "/check/case/{case_id}",
    summary="Check if a case is accessible",
)
async def check_case_access(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check if a specific case is accessible to the current user."""
    is_accessible, lock_reason = await unlock_engine.check_case_accessible(
        db, current_user.id, case_id
    )
    
    return {
        "case_id": str(case_id),
        "is_accessible": is_accessible,
        "lock_reason": lock_reason,
    }


@router.get(
    "/check/artifact/{artifact_id}",
    summary="Check if an artifact is accessible",
)
async def check_artifact_access(
    artifact_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check if a specific artifact is accessible to the current user."""
    is_accessible, lock_reason = await unlock_engine.check_artifact_accessible(
        db, current_user.id, artifact_id
    )
    
    return {
        "artifact_id": str(artifact_id),
        "is_accessible": is_accessible,
        "lock_reason": lock_reason,
    }


# ===== Admin: Case Dependency Management =====

@router.get(
    "/admin/cases/{case_id}/dependencies",
    response_model=CaseDependencyListResponse,
    summary="Get case dependencies (admin)",
    dependencies=[Depends(require_admin)],
)
async def get_case_dependencies(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get all dependencies for a case."""
    deps = await unlock_engine.get_case_dependencies(db, case_id)
    
    return CaseDependencyListResponse(
        case_id=case_id,
        dependencies=[
            CaseDependencyResponse(
                dependency_id=UUID(d["dependency_id"]),
                case_id=case_id,
                required_case_id=UUID(d["required_case_id"]),
                required_case_title=d["required_case_title"],
                required_artifact_id=UUID(d["required_artifact_id"]) if d["required_artifact_id"] else None,
                lock_reason=d["lock_reason"],
                created_at=None,
            )
            for d in deps
        ],
    )


@router.post(
    "/admin/cases/{case_id}/dependencies",
    response_model=CaseDependencyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add case dependency (admin)",
    dependencies=[Depends(require_admin)],
)
async def add_case_dependency(
    case_id: UUID,
    data: CaseDependencyCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Add a dependency to a case.
    
    The case will be locked until the required case is solved.
    """
    if case_id == data.required_case_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A case cannot depend on itself",
        )
    
    dep = await unlock_engine.add_case_dependency(
        db=db,
        case_id=case_id,
        required_case_id=data.required_case_id,
        required_artifact_id=data.required_artifact_id,
        lock_reason=data.lock_reason,
    )
    
    await db.commit()
    
    return CaseDependencyResponse(
        dependency_id=dep.id,
        case_id=case_id,
        required_case_id=dep.required_case_id,
        required_case_title=None,  # Not loaded
        required_artifact_id=dep.required_artifact_id,
        lock_reason=dep.lock_reason,
        created_at=dep.created_at,
    )


@router.delete(
    "/admin/dependencies/{dependency_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove case dependency (admin)",
    dependencies=[Depends(require_admin)],
)
async def remove_case_dependency(
    dependency_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Remove a case dependency."""
    success = await unlock_engine.remove_case_dependency(db, dependency_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dependency not found",
        )
    
    await db.commit()


# ===== Admin: Artifact Unlock Condition Management =====

@router.get(
    "/admin/artifacts/{artifact_id}/conditions",
    response_model=ArtifactUnlockConditionListResponse,
    summary="Get artifact unlock conditions (admin)",
    dependencies=[Depends(require_admin)],
)
async def get_artifact_unlock_conditions(
    artifact_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get all unlock conditions for an artifact."""
    conditions = await unlock_engine.get_artifact_unlock_conditions(db, artifact_id)
    
    return ArtifactUnlockConditionListResponse(
        artifact_id=artifact_id,
        conditions=[
            ArtifactUnlockConditionResponse(
                condition_id=UUID(c["condition_id"]),
                artifact_id=artifact_id,
                condition_type=UnlockConditionType(c["condition_type"]),
                required_case_id=UUID(c["required_case_id"]) if c["required_case_id"] else None,
                required_artifact_id=UUID(c["required_artifact_id"]) if c["required_artifact_id"] else None,
                unlock_at=c["unlock_at"],
                required_points=c["required_points"],
                description=c["description"],
            )
            for c in conditions
        ],
    )


@router.post(
    "/admin/artifacts/{artifact_id}/conditions",
    response_model=ArtifactUnlockConditionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add artifact unlock condition (admin)",
    dependencies=[Depends(require_admin)],
)
async def add_artifact_unlock_condition(
    artifact_id: UUID,
    data: ArtifactUnlockConditionCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Add an unlock condition to an artifact.
    
    The artifact will be locked until the condition is met.
    """
    # Validate condition-specific requirements
    if data.condition_type == UnlockConditionType.CASE_SOLVED and not data.required_case_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CASE_SOLVED condition requires required_case_id",
        )
    
    if data.condition_type == UnlockConditionType.ARTIFACT_DOWNLOADED and not data.required_artifact_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ARTIFACT_DOWNLOADED condition requires required_artifact_id",
        )
    
    if data.condition_type == UnlockConditionType.TIME_BASED and not data.unlock_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TIME_BASED condition requires unlock_at",
        )
    
    if data.condition_type == UnlockConditionType.POINTS_THRESHOLD and data.required_points is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="POINTS_THRESHOLD condition requires required_points",
        )
    
    condition = await unlock_engine.add_artifact_unlock_condition(
        db=db,
        artifact_id=artifact_id,
        condition_type=data.condition_type,
        required_case_id=data.required_case_id,
        required_artifact_id=data.required_artifact_id,
        unlock_at=data.unlock_at,
        required_points=data.required_points,
        description=data.description,
    )
    
    await db.commit()
    
    return ArtifactUnlockConditionResponse(
        condition_id=condition.id,
        artifact_id=artifact_id,
        condition_type=condition.condition_type,
        required_case_id=condition.required_case_id,
        required_artifact_id=condition.required_artifact_id,
        unlock_at=condition.unlock_at,
        required_points=condition.required_points,
        description=condition.description,
    )


@router.delete(
    "/admin/conditions/{condition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove artifact unlock condition (admin)",
    dependencies=[Depends(require_admin)],
)
async def remove_artifact_unlock_condition(
    condition_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Remove an artifact unlock condition."""
    success = await unlock_engine.remove_artifact_unlock_condition(db, condition_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Condition not found",
        )
    
    await db.commit()


# ===== Admin: Manual Unlock Management =====

@router.post(
    "/admin/manual-unlock",
    response_model=ManualUnlockResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Grant manual unlock (admin)",
    dependencies=[Depends(require_admin)],
)
async def grant_manual_unlock(
    data: ManualUnlockCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Grant a manual unlock to a user.
    
    Bypasses all unlock conditions for the specified artifact or case.
    """
    if not data.artifact_id and not data.case_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either artifact_id or case_id must be provided",
        )
    
    if data.artifact_id and data.case_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only one of artifact_id or case_id can be provided",
        )
    
    unlock = await unlock_engine.grant_manual_unlock(
        db=db,
        user_id=data.user_id,
        granted_by=current_user.id,
        artifact_id=data.artifact_id,
        case_id=data.case_id,
        reason=data.reason,
    )
    
    await db.commit()
    
    return ManualUnlockResponse(
        unlock_id=unlock.id,
        user_id=unlock.user_id,
        artifact_id=unlock.artifact_id,
        case_id=unlock.case_id,
        granted_by=unlock.granted_by,
        reason=unlock.reason,
        created_at=unlock.created_at,
    )


@router.get(
    "/admin/users/{user_id}/manual-unlocks",
    response_model=ManualUnlockListResponse,
    summary="Get user's manual unlocks (admin)",
    dependencies=[Depends(require_admin)],
)
async def get_user_manual_unlocks(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get all manual unlocks for a user."""
    unlocks = await unlock_engine.get_user_manual_unlocks(db, user_id)
    
    return ManualUnlockListResponse(
        user_id=user_id,
        unlocks=[
            ManualUnlockResponse(
                unlock_id=UUID(u["unlock_id"]),
                user_id=user_id,
                artifact_id=UUID(u["artifact_id"]) if u["artifact_id"] else None,
                case_id=UUID(u["case_id"]) if u["case_id"] else None,
                granted_by=UUID(u["granted_by"]) if u["granted_by"] else None,
                reason=u["reason"],
                created_at=u["created_at"],
            )
            for u in unlocks
        ],
    )


@router.delete(
    "/admin/manual-unlock/{unlock_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke manual unlock (admin)",
    dependencies=[Depends(require_admin)],
)
async def revoke_manual_unlock(
    unlock_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Revoke a manual unlock."""
    success = await unlock_engine.revoke_manual_unlock(db, unlock_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unlock not found",
        )
    
    await db.commit()


# ===== Admin: Analytics =====

@router.get(
    "/admin/analytics/case/{case_id}",
    response_model=CaseAnalyticsResponse,
    summary="Get case analytics (admin)",
    dependencies=[Depends(require_admin)],
)
async def get_case_analytics(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get telemetry analytics for a case."""
    analytics = await telemetry_service.get_case_analytics(db, case_id)
    
    if "error" in analytics:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=analytics["error"],
        )
    
    return CaseAnalyticsResponse(
        case_id=case_id,
        total_views=analytics["total_views"],
        unique_viewers=analytics["unique_viewers"],
        total_attempts=analytics["total_attempts"],
        total_solves=analytics["total_solves"],
        solve_rate=analytics["solve_rate"],
    )


@router.get(
    "/admin/analytics/user/{user_id}",
    response_model=UserActivitySummary,
    summary="Get user activity summary (admin)",
    dependencies=[Depends(require_admin)],
)
async def get_user_activity_summary(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get activity summary for a user (privacy-safe aggregate data only)."""
    summary = await telemetry_service.get_user_activity_summary(db, user_id)
    
    if "error" in summary:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=summary["error"],
        )
    
    return UserActivitySummary(
        user_id=user_id,
        cases_viewed=summary["cases_viewed"],
        cases_solved=summary["cases_solved"],
        artifacts_downloaded=summary["artifacts_downloaded"],
    )
