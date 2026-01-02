"""
Flag Engine - Core service for dynamic flag generation and verification.

This implements the anti-writeup, per-user flag system.
NO static flags are ever used in this platform.

Security Model:
1. Each case has a "semantic truth" - the actual answer
2. Semantic truth is NEVER stored in plaintext (only hash)
3. Flags are computed: HMAC(secret, user_id + case_id + semantic_truth_hash + case_salt + user_flag_salt + time_window)
4. Each user gets a unique flag for each case
5. Flags cannot be shared - submitting another user's flag won't work
6. Flags automatically expire after configurable time window
7. User salts rotate periodically, invalidating old leaked flags
8. All verifications use constant-time comparison

Anti-Leak Features:
- Time-variant user salt: Each user has a rotating salt
- Time-windowed flags: Flags expire after FLAG_EXPIRY_MINUTES
- Cross-user replay protection: Flags include user-specific data
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.crypto import CryptoService, crypto_service
from ..db.models import Case, User, Submission


class FlagEngine:
    """
    Engine for generating and verifying flags.
    
    Key principles:
    - Flags are never static
    - Flags are user-specific AND time-limited
    - Verification is timing-attack resistant
    - No hints on incorrect submissions
    - Old/leaked flags automatically expire
    - Replayed flags from other users always fail
    """
    
    def __init__(self, crypto: Optional[CryptoService] = None):
        """
        Initialize the flag engine.
        
        Args:
            crypto: CryptoService instance (defaults to global instance).
        """
        self._crypto = crypto or crypto_service
    
    async def maybe_rotate_user_salt(
        self,
        db: AsyncSession,
        user: User,
    ) -> User:
        """
        Check if user's flag salt needs rotation and rotate if necessary.
        
        Salt is rotated every FLAG_SALT_ROTATION_HOURS.
        This ensures that even if a flag is leaked, it becomes
        invalid after the rotation period.
        
        Args:
            db: Database session.
            user: The user to check.
        
        Returns:
            The user (potentially with updated salt).
        """
        import secrets
        
        rotation_hours = settings.FLAG_SALT_ROTATION_HOURS
        rotation_threshold = datetime.now(timezone.utc) - timedelta(hours=rotation_hours)
        
        if user.flag_salt_rotated_at < rotation_threshold:
            # Time to rotate the salt
            user.flag_salt = secrets.token_hex(32)
            user.flag_salt_rotated_at = datetime.now(timezone.utc)
            await db.flush()
            await db.refresh(user)
        
        return user
    
    def generate_flag_for_user(
        self,
        user_id: UUID,
        case_id: UUID,
        semantic_truth_hash: str,
        case_salt: str,
        user_flag_salt: str,
    ) -> str:
        """
        Generate a unique, time-limited flag for a specific user and case.
        
        Args:
            user_id: The user's unique identifier.
            case_id: The case's unique identifier.
            semantic_truth_hash: The hashed semantic truth for the case.
            case_salt: Additional case-level salt for entropy.
            user_flag_salt: The user's time-variant salt.
        
        Returns:
            The unique flag string for this user/case combination.
            This flag will expire after FLAG_EXPIRY_MINUTES.
        """
        # Combine user_id, case_id, and case_salt for uniqueness
        combined_case_id = f"{case_id}:{case_salt}"
        
        return self._crypto.generate_flag(
            user_id=str(user_id),
            case_id=combined_case_id,
            semantic_truth_hash=semantic_truth_hash,
            user_flag_salt=user_flag_salt,
        )
    
    def verify_answer(
        self,
        submitted_answer: str,
        stored_semantic_truth_hash: str,
    ) -> bool:
        """
        Verify if a submitted answer is correct.
        
        This checks if the user's answer matches the semantic truth
        by comparing hashes in constant time.
        
        Args:
            submitted_answer: The answer submitted by the user.
            stored_semantic_truth_hash: The stored hash of the semantic truth.
        
        Returns:
            True if the answer is correct, False otherwise.
        """
        return self._crypto.verify_answer(
            submitted_answer=submitted_answer,
            stored_semantic_truth_hash=stored_semantic_truth_hash,
        )
    
    def verify_flag(
        self,
        submitted_flag: str,
        user_id: UUID,
        case_id: UUID,
        semantic_truth_hash: str,
        case_salt: str,
        user_flag_salt: str,
    ) -> Tuple[bool, str]:
        """
        Verify if a submitted flag is correct for this user/case.
        
        Checks current and previous time windows for boundary tolerance.
        A flag from another user will ALWAYS fail (different user_flag_salt).
        An expired flag (outside time window) will ALWAYS fail.
        
        Args:
            submitted_flag: The flag submitted by the user.
            user_id: The user's unique identifier.
            case_id: The case's unique identifier.
            semantic_truth_hash: The stored hash of the semantic truth.
            case_salt: Additional case-level salt.
            user_flag_salt: The user's time-variant salt.
        
        Returns:
            Tuple of (is_valid, reason).
            Reasons: "valid", "invalid_or_expired"
        """
        combined_case_id = f"{case_id}:{case_salt}"
        
        return self._crypto.verify_flag(
            submitted_flag=submitted_flag,
            user_id=str(user_id),
            case_id=combined_case_id,
            semantic_truth_hash=semantic_truth_hash,
            user_flag_salt=user_flag_salt,
        )
    
    async def process_submission(
        self,
        db: AsyncSession,
        user: User,
        case: Case,
        submitted_answer: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        time_spent_seconds: Optional[int] = None,
    ) -> Tuple[bool, str, Optional[str], Optional[int]]:
        """
        Process a user's submission for a case.
        
        This is the main entry point for handling submissions.
        It verifies the answer, records the submission, and generates
        the flag if correct.
        
        Security features:
        - User salt is rotated if needed (invalidates old leaked flags)
        - Generated flags include time window (auto-expire)
        - Flags are bound to user's unique salt (replay from others fails)
        
        Args:
            db: Database session.
            user: The submitting user.
            case: The case being submitted to.
            submitted_answer: The user's answer.
            ip_address: Client IP for audit logging.
            user_agent: Client user agent for audit logging.
            time_spent_seconds: Self-reported time spent.
        
        Returns:
            Tuple of (is_correct, message, flag_or_none, points_or_none)
        """
        # Rotate user salt if needed (anti-leak: old flags expire)
        user = await self.maybe_rotate_user_salt(db, user)
        
        # Check if user already solved this case
        already_solved = await self._check_already_solved(db, user.id, case.id)
        
        # Verify the answer
        is_correct = self.verify_answer(
            submitted_answer=submitted_answer,
            stored_semantic_truth_hash=case.semantic_truth_hash,
        )
        
        # Hash the submitted answer for storage (privacy - never store plaintext)
        submitted_answer_hash = self._crypto.hash_semantic_truth(submitted_answer)
        
        # Create submission record
        submission = Submission(
            user_id=user.id,
            case_id=case.id,
            submitted_answer_hash=submitted_answer_hash,  # Store hash, not plaintext
            is_correct=is_correct,
            ip_address=ip_address,
            user_agent=user_agent,
            time_spent_seconds=time_spent_seconds,
        )
        db.add(submission)
        await db.flush()
        
        if is_correct:
            # Generate unique, time-limited flag for this user
            flag = self.generate_flag_for_user(
                user_id=user.id,
                case_id=case.id,
                semantic_truth_hash=case.semantic_truth_hash,
                case_salt=case.case_salt,
                user_flag_salt=user.flag_salt,
            )
            
            expiry_minutes = settings.FLAG_EXPIRY_MINUTES
            
            if already_solved:
                return (
                    True,
                    f"Correct! You've already solved this case. Flag expires in {expiry_minutes} minutes.",
                    flag,
                    0,  # No additional points
                )
            else:
                return (
                    True,
                    f"Correct! Here is your unique flag. It expires in {expiry_minutes} minutes.",
                    flag,
                    case.points,
                )
        else:
            # Generic failure message - no hints (anti-writeup)
            return (
                False,
                "Incorrect. Continue your investigation.",
                None,
                None,
            )
    
    async def _check_already_solved(
        self,
        db: AsyncSession,
        user_id: UUID,
        case_id: UUID,
    ) -> bool:
        """Check if a user has already solved a case."""
        result = await db.execute(
            select(Submission)
            .where(
                Submission.user_id == user_id,
                Submission.case_id == case_id,
                Submission.is_correct == True,
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None
    
    async def get_user_attempts_count(
        self,
        db: AsyncSession,
        user_id: UUID,
        case_id: UUID,
    ) -> int:
        """Get the number of attempts a user has made on a case."""
        result = await db.execute(
            select(func.count(Submission.id))
            .where(
                Submission.user_id == user_id,
                Submission.case_id == case_id,
            )
        )
        return result.scalar() or 0


# Global flag engine instance
flag_engine = FlagEngine()
