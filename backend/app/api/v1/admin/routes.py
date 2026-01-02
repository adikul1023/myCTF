"""
Admin API endpoints.

Endpoints:
- POST /cases - Create a new case
- PUT /cases/{case_id} - Update a case
- DELETE /cases/{case_id} - Delete a case
- POST /cases/{case_id}/artifacts - Upload artifact
- DELETE /cases/{case_id}/artifacts/{artifact_id} - Delete artifact
- POST /invite-codes - Generate invite code
- GET /invite-codes - List invite codes
- GET /stats - Get platform statistics
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.dependencies import get_current_admin
from ....core.security import security_service
from ....db.session import get_db
from ....db.models import User, Case, Artifact, InviteCode, Submission, ArtifactType
from ....schemas.case import CaseCreate, CaseUpdate, CaseResponse, CaseStatistics
from ....schemas.artifact import (
    ArtifactCreate,
    ArtifactResponse,
    ArtifactUploadRequest,
    ArtifactUploadResponse,
)
from ....schemas.invite import InviteCodeCreate, InviteCodeResponse, InviteCodeListResponse
from ....schemas.common import MessageResponse
from ....services.case_engine import case_engine
from ....utils.storage import storage_client


router = APIRouter(prefix="/admin", tags=["Admin"])


# ============== Case Management ==============

@router.post(
    "/cases",
    response_model=CaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new case",
    description="Create a new forensic case (admin only).",
)
async def create_case(
    case_data: CaseCreate,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new forensic case.
    
    The semantic_truth (answer) will be hashed immediately.
    It is NEVER stored in plaintext.
    
    Admin only.
    """
    case = await case_engine.create_case(
        db=db,
        case_data=case_data,
        created_by=current_admin,
    )
    
    await db.commit()
    await db.refresh(case)
    
    return CaseResponse.model_validate(case)


@router.put(
    "/cases/{case_id}",
    response_model=CaseResponse,
    summary="Update a case",
    description="Update an existing case (admin only).",
)
async def update_case(
    case_id: uuid.UUID,
    case_data: CaseUpdate,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a forensic case.
    
    Note: This endpoint does NOT allow changing the semantic_truth.
    Use the dedicated endpoint for that as it invalidates all user flags.
    
    Admin only.
    """
    case = await case_engine.update_case(
        db=db,
        case_id=case_id,
        case_data=case_data,
    )
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )
    
    await db.commit()
    await db.refresh(case)
    
    return CaseResponse.model_validate(case)


@router.put(
    "/cases/{case_id}/semantic-truth",
    response_model=MessageResponse,
    summary="Update case semantic truth",
    description="Update the answer for a case. WARNING: Invalidates all existing flags.",
)
async def update_case_semantic_truth(
    case_id: uuid.UUID,
    semantic_truth: str = Form(..., min_length=1),
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Update the semantic truth (answer) for a case.
    
    WARNING: This invalidates ALL existing user flags for this case.
    Users who already solved it will need to solve it again to get new flags.
    
    Admin only.
    """
    case = await case_engine.update_semantic_truth(
        db=db,
        case_id=case_id,
        new_semantic_truth=semantic_truth,
    )
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )
    
    await db.commit()
    
    return MessageResponse(
        message="Semantic truth updated. All existing flags have been invalidated.",
        success=True,
    )


@router.delete(
    "/cases/{case_id}",
    response_model=MessageResponse,
    summary="Delete a case",
    description="Delete a case and all associated data (admin only).",
)
async def delete_case(
    case_id: uuid.UUID,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a forensic case.
    
    WARNING: This is permanent and deletes all associated:
    - Artifacts
    - Submissions
    
    Admin only.
    """
    deleted = await case_engine.delete_case(db, case_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )
    
    await db.commit()
    
    return MessageResponse(
        message="Case deleted successfully",
        success=True,
    )


@router.get(
    "/cases/{case_id}/stats",
    response_model=CaseStatistics,
    summary="Get case statistics",
    description="Get detailed statistics for a case (admin only).",
)
async def get_case_stats(
    case_id: uuid.UUID,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed statistics for a case.
    
    Admin only.
    """
    case = await case_engine.get_case_by_id(db, case_id)
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )
    
    stats = await case_engine.get_case_statistics(db, case_id)
    
    return CaseStatistics(**stats)


# ============== Artifact Management ==============

@router.post(
    "/cases/{case_id}/artifacts/upload-url",
    response_model=ArtifactUploadResponse,
    summary="Get artifact upload URL",
    description="Get a presigned URL for uploading an artifact (admin only).",
)
async def get_artifact_upload_url(
    case_id: uuid.UUID,
    upload_request: ArtifactUploadRequest,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a presigned URL for uploading an artifact.
    
    Use this URL to upload the file directly to storage.
    After upload, call the create artifact endpoint.
    
    Admin only.
    """
    # Verify case exists
    case = await case_engine.get_case_by_id(db, case_id)
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )
    
    # Generate artifact ID and storage path
    artifact_id = uuid.uuid4()
    object_name = f"cases/{case_id}/artifacts/{artifact_id}/{upload_request.filename}"
    
    try:
        upload_url = await storage_client.get_presigned_upload_url(
            object_name=object_name,
            expires=timedelta(hours=1),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate upload URL",
        )
    
    return ArtifactUploadResponse(
        upload_url=upload_url,
        artifact_id=artifact_id,
        expires_in=3600,
    )


@router.post(
    "/cases/{case_id}/artifacts",
    response_model=ArtifactResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create artifact record",
    description="Create an artifact record after uploading the file (admin only).",
)
async def create_artifact(
    case_id: uuid.UUID,
    artifact_id: uuid.UUID = Form(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    artifact_type: ArtifactType = Form(ArtifactType.OTHER),
    filename: str = Form(...),
    file_size: int = Form(...),
    file_hash_sha256: str = Form(...),
    mime_type: Optional[str] = Form(None),
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Create an artifact record after uploading.
    
    Call this after successfully uploading the file using the presigned URL.
    
    Admin only.
    """
    # Verify case exists
    case = await case_engine.get_case_by_id(db, case_id)
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )
    
    # Create artifact record
    storage_path = f"cases/{case_id}/artifacts/{artifact_id}/{filename}"
    
    artifact = Artifact(
        id=artifact_id,
        case_id=case_id,
        name=name,
        description=description,
        artifact_type=artifact_type,
        storage_path=storage_path,
        file_size=file_size,
        file_hash_sha256=file_hash_sha256,
        mime_type=mime_type,
        extra_metadata=None,
    )
    
    db.add(artifact)
    await db.commit()
    await db.refresh(artifact)
    
    return ArtifactResponse.model_validate(artifact)


@router.delete(
    "/cases/{case_id}/artifacts/{artifact_id}",
    response_model=MessageResponse,
    summary="Delete an artifact",
    description="Delete an artifact from a case (admin only).",
)
async def delete_artifact(
    case_id: uuid.UUID,
    artifact_id: uuid.UUID,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete an artifact.
    
    Removes both the database record and the file from storage.
    
    Admin only.
    """
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
    
    # Delete from storage
    try:
        object_name = artifact.storage_path.split("/", 1)[-1] if "/" in artifact.storage_path else artifact.storage_path
        await storage_client.delete_file(object_name)
    except Exception:
        pass  # Continue even if storage delete fails
    
    # Delete from database
    await db.delete(artifact)
    await db.commit()
    
    return MessageResponse(
        message="Artifact deleted successfully",
        success=True,
    )


# ============== Invite Code Management ==============

@router.post(
    "/invite-codes",
    response_model=InviteCodeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate invite code",
    description="Generate a new invite code (admin only).",
)
async def generate_invite_code(
    invite_data: InviteCodeCreate,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a new invite code.
    
    Admin only.
    """
    code = security_service.generate_invite_code()
    
    expires_at = None
    if invite_data.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=invite_data.expires_in_days)
    
    invite_code = InviteCode(
        code=code,
        max_uses=invite_data.max_uses,
        expires_at=expires_at,
        created_by_id=current_admin.id,
    )
    
    db.add(invite_code)
    await db.commit()
    await db.refresh(invite_code)
    
    return InviteCodeResponse.model_validate(invite_code)


@router.get(
    "/invite-codes",
    response_model=InviteCodeListResponse,
    summary="List invite codes",
    description="List all invite codes (admin only).",
)
async def list_invite_codes(
    include_used: bool = Query(False, description="Include used codes"),
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    List all invite codes.
    
    Admin only.
    """
    query = select(InviteCode).order_by(InviteCode.created_at.desc())
    
    if not include_used:
        query = query.where(InviteCode.is_used == False)
    
    result = await db.execute(query)
    codes = result.scalars().all()
    
    return InviteCodeListResponse(
        codes=[InviteCodeResponse.model_validate(c) for c in codes],
        total=len(codes),
    )


@router.delete(
    "/invite-codes/{code_id}",
    response_model=MessageResponse,
    summary="Delete invite code",
    description="Delete an invite code (admin only).",
)
async def delete_invite_code(
    code_id: uuid.UUID,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete an invite code.
    
    Admin only.
    """
    result = await db.execute(
        select(InviteCode).where(InviteCode.id == code_id)
    )
    invite_code = result.scalar_one_or_none()
    
    if not invite_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite code not found",
        )
    
    await db.delete(invite_code)
    await db.commit()
    
    return MessageResponse(
        message="Invite code deleted successfully",
        success=True,
    )


# ============== Platform Statistics ==============

@router.get(
    "/stats",
    summary="Get platform statistics",
    description="Get overall platform statistics (admin only).",
)
async def get_platform_stats(
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get overall platform statistics.
    
    Admin only.
    """
    # Total users
    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar() or 0
    
    # Active users
    active_users_result = await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )
    active_users = active_users_result.scalar() or 0
    
    # Total cases
    total_cases_result = await db.execute(select(func.count(Case.id)))
    total_cases = total_cases_result.scalar() or 0
    
    # Active cases
    active_cases_result = await db.execute(
        select(func.count(Case.id)).where(Case.is_active == True)
    )
    active_cases = active_cases_result.scalar() or 0
    
    # Total submissions
    total_submissions_result = await db.execute(select(func.count(Submission.id)))
    total_submissions = total_submissions_result.scalar() or 0
    
    # Correct submissions
    correct_submissions_result = await db.execute(
        select(func.count(Submission.id)).where(Submission.is_correct == True)
    )
    correct_submissions = correct_submissions_result.scalar() or 0
    
    # Total artifacts
    total_artifacts_result = await db.execute(select(func.count(Artifact.id)))
    total_artifacts = total_artifacts_result.scalar() or 0
    
    return {
        "users": {
            "total": total_users,
            "active": active_users,
        },
        "cases": {
            "total": total_cases,
            "active": active_cases,
        },
        "submissions": {
            "total": total_submissions,
            "correct": correct_submissions,
            "success_rate": round(
                (correct_submissions / total_submissions * 100) if total_submissions > 0 else 0.0,
                2,
            ),
        },
        "artifacts": {
            "total": total_artifacts,
        },
    }
