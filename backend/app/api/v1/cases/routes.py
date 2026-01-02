"""
Cases API endpoints.

Endpoints:
- GET /cases - List all active cases
- GET /cases/{case_id} - Get case details
- GET /cases/{case_id}/artifacts - List case artifacts
- GET /cases/{case_id}/artifacts/{artifact_id}/download - Download artifact
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.dependencies import get_current_user, get_current_user_optional
from ....db.session import get_db
from ....db.models import User, Case, Artifact, DifficultyLevel
from ....schemas.case import (
    CaseResponse,
    CaseListResponse,
    CaseDetailResponse,
)
from ....schemas.artifact import ArtifactResponse, ArtifactDownloadResponse, ArtifactListResponse
from ....services.case_engine import case_engine
from ....utils.storage import storage_client

from datetime import timedelta


router = APIRouter(prefix="/cases", tags=["Cases"])


@router.get(
    "",
    response_model=CaseListResponse,
    summary="List all cases",
    description="Get a paginated list of active forensic cases.",
)
async def list_cases(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=50, description="Items per page"),
    difficulty: Optional[DifficultyLevel] = Query(None, description="Filter by difficulty"),
    search: Optional[str] = Query(None, max_length=100, description="Search term"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    List all active forensic cases.
    
    Cases can be filtered by difficulty level and searched by title/description.
    Authentication is optional but provides user-specific data.
    """
    cases, total = await case_engine.list_cases(
        db=db,
        page=page,
        per_page=per_page,
        difficulty=difficulty,
        active_only=True,
        search=search,
    )
    
    total_pages = (total + per_page - 1) // per_page
    
    return CaseListResponse(
        cases=[CaseResponse.model_validate(case) for case in cases],
        total=total,
        page=page,
        per_page=per_page,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@router.get(
    "/{case_id}",
    response_model=CaseDetailResponse,
    summary="Get case details",
    description="Get detailed information about a specific case.",
)
async def get_case_details(
    case_id: UUID,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed information about a forensic case.
    
    Returns the case story, investigation objectives, and metadata.
    Does NOT reveal the answer or any spoilers.
    
    If authenticated, also returns user-specific data like solve status.
    """
    case = await case_engine.get_case_by_id(
        db=db,
        case_id=case_id,
        include_artifacts=True,
    )
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )
    
    if not case.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )
    
    # Get statistics
    stats = await case_engine.get_case_statistics(db, case.id)
    
    # Get user-specific data if authenticated
    user_solved = False
    user_attempts = 0
    
    if current_user:
        user_status = await case_engine.get_user_case_status(
            db, current_user.id, case.id
        )
        user_solved = user_status["is_solved"]
        user_attempts = user_status["attempts"]
    
    return CaseDetailResponse(
        id=case.id,
        title=case.title,
        slug=case.slug,
        description=case.description,
        story_background=case.story_background,
        investigation_objectives=case.investigation_objectives,
        difficulty=case.difficulty,
        points=case.points,
        is_active=case.is_active,
        created_at=case.created_at,
        extra_metadata=case.extra_metadata,
        artifact_count=len(case.artifacts),
        solve_count=stats["solve_count"],
        user_solved=user_solved,
        user_attempts=user_attempts,
    )


@router.get(
    "/{case_id}/artifacts",
    response_model=ArtifactListResponse,
    summary="List case artifacts",
    description="Get all artifacts (evidence files) for a case.",
)
async def list_case_artifacts(
    case_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all artifacts for a forensic case.
    
    Requires authentication to prevent unauthorized access to evidence files.
    """
    case = await case_engine.get_case_by_id(
        db=db,
        case_id=case_id,
        include_artifacts=True,
    )
    
    if not case or not case.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )
    
    return ArtifactListResponse(
        artifacts=[ArtifactResponse.model_validate(a) for a in case.artifacts],
        total=len(case.artifacts),
    )


@router.get(
    "/{case_id}/artifacts/{artifact_id}/download",
    summary="Download artifact file",
    description="Download a forensic artifact file directly.",
)
async def download_artifact(
    case_id: UUID,
    artifact_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Download a forensic artifact file.
    
    Generates a presigned URL from R2 and redirects to it.
    This avoids streaming through the backend, reducing memory usage.
    Requires authentication.
    """
    # Verify case exists and is active
    case = await case_engine.get_case_by_id(db=db, case_id=case_id)
    
    if not case or not case.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )
    
    # Get artifact
    result = await db.execute(
        select(Artifact).where(
            Artifact.id == artifact_id,
            Artifact.case_id == case_id,
        )
    )
    artifact = result.scalar_one_or_none()
    
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found",
        )
    
    # Use storage path directly (bucket name already removed)
    object_name = artifact.storage_path
    
    # Determine filename for download
    safe_name = artifact.name.replace(" ", "_").replace("/", "_")
    if not safe_name.endswith(".zip"):
        safe_name += ".zip"
    
    # Generate presigned URL valid for 1 hour
    try:
        presigned_url = storage_client.client.presigned_get_object(
            bucket_name=storage_client.bucket_name,
            object_name=object_name,
            expires=timedelta(hours=1),
            response_headers={
                "response-content-disposition": f'attachment; filename="{safe_name}"',
                "response-content-type": artifact.mime_type or "application/zip",
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate download URL: {str(e)}",
        )
    
    # Redirect to the presigned URL
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=presigned_url, status_code=307)


@router.get(
    "/slug/{slug}",
    response_model=CaseDetailResponse,
    summary="Get case by slug",
    description="Get case details using the URL-friendly slug.",
)
async def get_case_by_slug(
    slug: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Get case details using the slug.
    
    Alternative to using the UUID.
    """
    case = await case_engine.get_case_by_slug(
        db=db,
        slug=slug,
        include_artifacts=True,
    )
    
    if not case or not case.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )
    
    # Get statistics
    stats = await case_engine.get_case_statistics(db, case.id)
    
    # Get user-specific data if authenticated
    user_solved = False
    user_attempts = 0
    
    if current_user:
        user_status = await case_engine.get_user_case_status(
            db, current_user.id, case.id
        )
        user_solved = user_status["is_solved"]
        user_attempts = user_status["attempts"]
    
    return CaseDetailResponse(
        id=case.id,
        title=case.title,
        slug=case.slug,
        description=case.description,
        story_background=case.story_background,
        investigation_objectives=case.investigation_objectives,
        difficulty=case.difficulty,
        points=case.points,
        is_active=case.is_active,
        created_at=case.created_at,
        extra_metadata=case.extra_metadata,
        artifact_count=len(case.artifacts),
        solve_count=stats["solve_count"],
        user_solved=user_solved,
        user_attempts=user_attempts,
    )


@router.get(
    '/{case_id}/challenges',
    summary='Get challenges for a case',
)
async def get_case_challenges(
    case_id: UUID,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import text
    result = await db.execute(text('SELECT id FROM cases WHERE id = :case_id AND is_active = true'), {'case_id': str(case_id)})
    if not result.first():
        raise HTTPException(status_code=404, detail='Case not found')
    result = await db.execute(text('SELECT id, title, question, points, difficulty, display_order, hints FROM challenges WHERE case_id = :case_id AND is_active = true ORDER BY display_order'), {'case_id': str(case_id)})
    challenges = []
    for row in result:
        c = {'id': str(row[0]), 'title': row[1], 'question': row[2], 'points': row[3], 'difficulty': row[4], 'display_order': row[5], 'hints': row[6] if row[6] else [], 'is_solved': False, 'user_attempts': 0}
        if current_user:
            s = await db.execute(text('SELECT COUNT(*), MAX(CASE WHEN is_correct THEN 1 ELSE 0 END) FROM user_challenge_submissions WHERE user_id = :uid AND challenge_id = :cid'), {'uid': str(current_user.id), 'cid': str(row[0])})
            sr = s.first()
            if sr:
                c['user_attempts'] = sr[0]
                c['is_solved'] = bool(sr[1])
        challenges.append(c)
    return {'challenges': challenges}

