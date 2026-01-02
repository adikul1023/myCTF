"""
Submission-related Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class SubmissionCreate(BaseModel):
    """Schema for submitting an answer to a case."""
    case_id: UUID = Field(..., description="The case ID to submit answer for")
    answer: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="The user's answer/analysis result",
    )
    
    # Optional metadata for analytics
    time_spent_seconds: Optional[int] = Field(
        None,
        ge=0,
        description="Time spent on the case (client-reported)",
    )


class SubmissionResponse(BaseModel):
    """Schema for submission response."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    id: UUID
    case_id: UUID
    is_correct: bool
    submitted_at: datetime = Field(alias="created_at")


class SubmissionVerifyResponse(BaseModel):
    """
    Schema for submission verification response.
    
    If correct, includes the user's unique flag.
    If incorrect, provides no hints (anti-writeup design).
    """
    is_correct: bool
    message: str
    
    # Only populated if correct
    flag: Optional[str] = None
    points_earned: Optional[int] = None
    
    # For rate limiting feedback
    attempts_remaining: Optional[int] = None


class SubmissionHistoryResponse(BaseModel):
    """Schema for user's submission history on a case."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    case_id: UUID
    case_title: str
    is_correct: bool
    submitted_at: datetime
    
    # Don't expose the submitted answer to prevent answer sharing


class UserSubmissionStats(BaseModel):
    """Schema for user's overall submission statistics."""
    total_submissions: int
    correct_submissions: int
    unique_cases_attempted: int
    unique_cases_solved: int
    total_points: int
    success_rate: float  # percentage


class SubmissionListResponse(BaseModel):
    """Schema for paginated submission list."""
    submissions: List[SubmissionHistoryResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class FlagSubmissionCreate(BaseModel):
    """
    Schema for flag submission (alternative verification method).
    
    Some cases might want users to submit the flag directly
    instead of the answer. This is less common but supported.
    """
    case_id: UUID = Field(..., description="The case ID")
    flag: str = Field(
        ...,
        min_length=10,
        max_length=100,
        description="The flag in format FORENSIC{...}",
    )


class LeaderboardEntry(BaseModel):
    """Schema for leaderboard entry."""
    rank: int
    user_id: UUID
    username: str
    total_points: int
    cases_solved: int
    last_solve_at: Optional[datetime]


class LeaderboardResponse(BaseModel):
    """Schema for leaderboard response."""
    entries: List[LeaderboardEntry]
    total_users: int
    last_updated: datetime
