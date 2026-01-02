"""
Challenge submission API endpoints.

Endpoints:
- POST /{challenge_id}/submit - Submit an answer to a specific challenge
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.dependencies import (
    get_current_user,
    check_submission_rate_limit,
    submission_rate_limiter,
)
from ....db.session import get_db
from ....db.models import User
from ....schemas.submission import SubmissionVerifyResponse
from ....core.crypto import CryptoService
from pydantic import BaseModel


router = APIRouter(prefix="/challenges", tags=["Challenges"])

# Initialize crypto service
crypto_service = CryptoService()


class ChallengeSubmission(BaseModel):
    answer: str
    time_spent_seconds: int | None = None


@router.post(
    "/{challenge_id}/submit",
    response_model=SubmissionVerifyResponse,
    summary="Submit challenge answer",
    description="Submit your answer for a specific challenge. Rate-limited.",
)
async def submit_challenge_answer(
    challenge_id: UUID,
    submission: ChallengeSubmission,
    request: Request,
    current_user: User = Depends(check_submission_rate_limit),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit an answer to a specific challenge.
    
    Validates against the challenge's semantic truth.
    Rate limited to prevent brute force attempts.
    """
    # Get the challenge
    challenge_query = text("""
        SELECT c.id, c.case_id, c.title, c.semantic_truth, c.semantic_truth_hash, 
               c.points, c.is_active, cs.title as case_title
        FROM challenges c
        JOIN cases cs ON c.case_id = cs.id
        WHERE c.id = :challenge_id
    """)
    
    result = await db.execute(challenge_query, {"challenge_id": str(challenge_id)})
    challenge_row = result.fetchone()
    
    if not challenge_row or not challenge_row.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found",
        )
    
    # Check if user already solved this challenge
    check_query = text("""
        SELECT id, is_correct FROM user_challenge_submissions
        WHERE user_id = :user_id AND challenge_id = :challenge_id
        ORDER BY submitted_at DESC
        LIMIT 1
    """)
    
    existing_result = await db.execute(check_query, {
        "user_id": str(current_user.id),
        "challenge_id": str(challenge_id)
    })
    existing_row = existing_result.fetchone()
    
    already_solved = existing_row and existing_row.is_correct
    
    # Normalize the submitted answer
    submitted_answer = submission.answer.strip()
    
    # Hash the submitted answer
    submitted_hash = crypto_service.hash_semantic_truth(submitted_answer)
    
    # Check if answer is correct
    is_correct = submitted_hash == challenge_row.semantic_truth_hash
    
    # Calculate points
    points_awarded = challenge_row.points if is_correct and not already_solved else 0
    
    # Record the submission
    insert_query = text("""
        INSERT INTO user_challenge_submissions 
        (user_id, challenge_id, submitted_flag, is_correct, points_awarded)
        VALUES 
        (:user_id, :challenge_id, :submitted_flag, :is_correct, :points_awarded)
    """)
    
    await db.execute(insert_query, {
        "user_id": str(current_user.id),
        "challenge_id": str(challenge_id),
        "submitted_flag": submitted_answer,
        "is_correct": is_correct,
        "points_awarded": points_awarded
    })
    
    await db.commit()
    
    # Get remaining rate limit
    remaining, _ = await submission_rate_limiter.get_remaining(
        f"user:{current_user.id}"
    )
    
    # Build response message
    if is_correct:
        if already_solved:
            message = "You already solved this challenge!"
        else:
            message = f"Correct! You earned {points_awarded} points."
    else:
        message = "Incorrect. Try again."
    
    return SubmissionVerifyResponse(
        is_correct=is_correct,
        message=message,
        flag=None,  # Challenges don't use flags
        points_earned=points_awarded,
        attempts_remaining=remaining,
    )
