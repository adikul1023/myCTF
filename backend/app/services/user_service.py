"""
User Service - Business logic for user management.
"""

from typing import Optional, Tuple
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import security_service
from ..db.models import User, InviteCode, Submission, Case
from ..schemas.user import UserCreate


class UserService:
    """
    Service for user management operations.
    
    Handles:
    - User registration (invite-only)
    - User authentication
    - User statistics
    """
    
    async def register_user(
        self,
        db: AsyncSession,
        user_data: UserCreate,
    ) -> Tuple[Optional[User], str]:
        """
        Register a new user with an invite code.
        
        Args:
            db: Database session.
            user_data: User registration data.
        
        Returns:
            Tuple of (User or None, error message or empty string)
        """
        # Check if email already exists
        email_exists = await db.execute(
            select(User).where(User.email == user_data.email).limit(1)
        )
        if email_exists.scalar_one_or_none():
            # Generic message to prevent email enumeration
            return None, "Registration failed. Please check your details."
        
        # Check if username already exists
        username_exists = await db.execute(
            select(User).where(User.username == user_data.username.lower()).limit(1)
        )
        if username_exists.scalar_one_or_none():
            # Generic message to prevent username enumeration
            return None, "Registration failed. Please check your details."
        
        # Validate invite code
        invite_result = await db.execute(
            select(InviteCode).where(InviteCode.code == user_data.invite_code)
        )
        invite_code = invite_result.scalar_one_or_none()
        
        if not invite_code:
            return None, "Invalid invite code"
        
        if not invite_code.is_valid:
            return None, "Invite code has expired or been used"
        
        # Hash the password
        password_hash = security_service.hash_password(user_data.password)
        
        # Create user
        user = User(
            email=user_data.email,
            username=user_data.username.lower(),
            password_hash=password_hash,
            invite_code_used=user_data.invite_code,
            is_active=True,
            is_admin=False,
        )
        
        db.add(user)
        await db.flush()
        
        # Mark invite code as used
        invite_code.use_count += 1
        if invite_code.use_count >= invite_code.max_uses:
            invite_code.is_used = True
        invite_code.used_by_id = user.id
        invite_code.used_at = datetime.now(timezone.utc)
        
        await db.flush()
        await db.refresh(user)
        
        return user, ""
    
    async def authenticate_user(
        self,
        db: AsyncSession,
        email: str,
        password: str,
    ) -> Tuple[Optional[User], str]:
        """
        Authenticate a user by email and password.
        
        Args:
            db: Database session.
            email: User's email.
            password: User's password.
        
        Returns:
            Tuple of (User or None, error message or empty string)
        """
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Perform a dummy hash to prevent timing attacks
            security_service.hash_password("dummy_password_for_timing")
            return None, "Invalid email or password"
        
        if not user.is_active:
            return None, "Account is deactivated"
        
        if not security_service.verify_password(password, user.password_hash):
            return None, "Invalid email or password"
        
        # Check if password needs rehashing (parameters changed)
        if security_service.needs_rehash(user.password_hash):
            user.password_hash = security_service.hash_password(password)
            await db.flush()
        
        return user, ""
    
    async def get_user_by_id(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> Optional[User]:
        """Get a user by their ID."""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_statistics(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> dict:
        """
        Get statistics for a user.
        
        Args:
            db: Database session.
            user_id: The user ID.
        
        Returns:
            Dictionary with user statistics.
        """
        # Total submissions
        total_submissions_result = await db.execute(
            select(func.count(Submission.id))
            .where(Submission.user_id == user_id)
        )
        total_submissions = total_submissions_result.scalar() or 0
        
        # Correct submissions
        correct_submissions_result = await db.execute(
            select(func.count(Submission.id))
            .where(
                Submission.user_id == user_id,
                Submission.is_correct == True,
            )
        )
        correct_submissions = correct_submissions_result.scalar() or 0
        
        # Unique cases attempted
        cases_attempted_result = await db.execute(
            select(func.count(func.distinct(Submission.case_id)))
            .where(Submission.user_id == user_id)
        )
        cases_attempted = cases_attempted_result.scalar() or 0
        
        # Unique cases solved
        cases_solved_result = await db.execute(
            select(func.count(func.distinct(Submission.case_id)))
            .where(
                Submission.user_id == user_id,
                Submission.is_correct == True,
            )
        )
        cases_solved = cases_solved_result.scalar() or 0
        
        # Total points
        # Need to get points from solved cases (only counting first solve)
        solved_cases_result = await db.execute(
            select(Case.points)
            .join(Submission, Submission.case_id == Case.id)
            .where(
                Submission.user_id == user_id,
                Submission.is_correct == True,
            )
            .distinct(Submission.case_id)
        )
        total_points = sum(row[0] for row in solved_cases_result.fetchall())
        
        return {
            "total_submissions": total_submissions,
            "correct_submissions": correct_submissions,
            "unique_cases_attempted": cases_attempted,
            "unique_cases_solved": cases_solved,
            "total_points": total_points,
            "success_rate": round(
                (correct_submissions / total_submissions * 100) if total_submissions > 0 else 0.0,
                2,
            ),
        }


# Global user service instance
user_service = UserService()
