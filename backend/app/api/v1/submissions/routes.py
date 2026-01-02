"""
Submissions API endpoints.

Endpoints:
- POST /submit - Submit an answer to a case
- GET /history - Get user's submission history
- GET /leaderboard - Get the platform leaderboard
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.dependencies import (
    get_current_user,
    check_submission_rate_limit,
    get_client_ip,
    submission_rate_limiter,
)
from ....db.session import get_db
from ....db.models import User, Case, Submission
from ....schemas.submission import (
    SubmissionCreate,
    SubmissionResponse,
    SubmissionVerifyResponse,
    SubmissionHistoryResponse,
    SubmissionListResponse,
    LeaderboardEntry,
    LeaderboardResponse,
    UserSubmissionStats,
)
from ....services.flag_engine import flag_engine
from ....services.case_engine import case_engine
from ....services.user_service import user_service

from datetime import datetime, timezone


router = APIRouter(prefix="/submissions", tags=["Submissions"])


@router.post(
    "/submit",
    response_model=SubmissionVerifyResponse,
    summary="Submit an answer",
    description="Submit your answer for a forensic case. Rate-limited.",
)
async def submit_answer(
    submission: SubmissionCreate,
    request: Request,
    current_user: User = Depends(check_submission_rate_limit),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit an answer to a forensic case.
    
    If the answer is correct, you will receive your unique flag.
    Each user gets a different flag for the same case (anti-writeup).
    
    Rate limited to prevent brute force attempts.
    """
    # Get the case
    case = await case_engine.get_case_by_id(db, submission.case_id)
    
    if not case or not case.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )
    
    # Get client info for audit
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "")[:512]
    
    # Process the submission
    is_correct, message, flag, points = await flag_engine.process_submission(
        db=db,
        user=current_user,
        case=case,
        submitted_answer=submission.answer,
        ip_address=client_ip,
        user_agent=user_agent,
        time_spent_seconds=submission.time_spent_seconds,
    )
    
    await db.commit()
    
    # Get remaining rate limit
    remaining, _ = await submission_rate_limiter.get_remaining(
        f"user:{current_user.id}"
    )
    
    return SubmissionVerifyResponse(
        is_correct=is_correct,
        message=message,
        flag=flag,
        points_earned=points,
        attempts_remaining=remaining,
    )


@router.get(
    "/history",
    response_model=SubmissionListResponse,
    summary="Get submission history",
    description="Get your submission history across all cases.",
)
async def get_submission_history(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=50, description="Items per page"),
    case_id: Optional[UUID] = Query(None, description="Filter by case"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get your submission history.
    
    Shows all your submission attempts with timestamps and correctness.
    Does NOT show the submitted answers to prevent answer sharing.
    """
    # Build query
    query = (
        select(Submission, Case.title)
        .join(Case, Submission.case_id == Case.id)
        .where(Submission.user_id == current_user.id)
    )
    
    count_query = (
        select(func.count(Submission.id))
        .where(Submission.user_id == current_user.id)
    )
    
    if case_id:
        query = query.where(Submission.case_id == case_id)
        count_query = count_query.where(Submission.case_id == case_id)
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page).order_by(Submission.created_at.desc())
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    submissions = [
        SubmissionHistoryResponse(
            id=row[0].id,
            case_id=row[0].case_id,
            case_title=row[1],
            is_correct=row[0].is_correct,
            submitted_at=row[0].created_at,
        )
        for row in rows
    ]
    
    total_pages = (total + per_page - 1) // per_page
    
    return SubmissionListResponse(
        submissions=submissions,
        total=total,
        page=page,
        per_page=per_page,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@router.get(
    "/stats",
    response_model=UserSubmissionStats,
    summary="Get your statistics",
    description="Get your overall submission statistics.",
)
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get your overall statistics.
    
    Includes total submissions, solve rate, and points.
    """
    stats = await user_service.get_user_statistics(db, current_user.id)
    
    return UserSubmissionStats(**stats)


@router.get(
    "/leaderboard",
    response_model=LeaderboardResponse,
    summary="Get leaderboard",
    description="Get the platform leaderboard.",
)
async def get_leaderboard(
    limit: int = Query(50, ge=1, le=100, description="Number of entries"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the platform leaderboard.
    
    Shows top users by total points earned.
    """
    # Complex query to calculate points per user
    # Only count first solve per case per user
    
    # Subquery to get first correct submission per user per case
    first_solve_subquery = (
        select(
            Submission.user_id,
            Submission.case_id,
            func.min(Submission.created_at).label("first_solve_at"),
        )
        .where(Submission.is_correct == True)
        .group_by(Submission.user_id, Submission.case_id)
        .subquery()
    )
    
    # Main query to calculate total points
    leaderboard_query = (
        select(
            User.id,
            User.username,
            func.sum(Case.points).label("total_points"),
            func.count(Case.id).label("cases_solved"),
            func.max(first_solve_subquery.c.first_solve_at).label("last_solve_at"),
        )
        .join(first_solve_subquery, User.id == first_solve_subquery.c.user_id)
        .join(Case, first_solve_subquery.c.case_id == Case.id)
        .where(User.is_active == True)
        .group_by(User.id, User.username)
        .order_by(desc("total_points"), desc("cases_solved"))
        .limit(limit)
    )
    
    result = await db.execute(leaderboard_query)
    rows = result.fetchall()
    
    # Count total users with at least one solve
    total_users_result = await db.execute(
        select(func.count(func.distinct(Submission.user_id)))
        .where(Submission.is_correct == True)
    )
    total_users = total_users_result.scalar() or 0
    
    entries = [
        LeaderboardEntry(
            rank=idx + 1,
            user_id=row[0],
            username=row[1],
            total_points=row[2] or 0,
            cases_solved=row[3] or 0,
            last_solve_at=row[4],
        )
        for idx, row in enumerate(rows)
    ]
    
    return LeaderboardResponse(
        entries=entries,
        total_users=total_users,
        last_updated=datetime.now(timezone.utc),
    )


@router.get(
    "/case/{case_id}/my-status",
    summary="Get your status for a case",
    description="Get your submission status for a specific case.",
)
async def get_case_status(
    case_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get your status for a specific case.
    
    Shows if you've solved it and how many attempts you've made.
    """
    # Verify case exists
    case = await case_engine.get_case_by_id(db, case_id)
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )
    
    status = await case_engine.get_user_case_status(
        db, current_user.id, case_id
    )
    
    return status
