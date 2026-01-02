"""
Case Engine - Service for managing forensic cases.

Handles:
- Case CRUD operations
- Artifact management
- Case statistics
- User progress tracking
"""

import re
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.crypto import crypto_service
from ..db.models import Case, Artifact, Submission, User, DifficultyLevel
from ..schemas.case import CaseCreate, CaseUpdate


class CaseEngine:
    """
    Engine for managing forensic cases.
    
    Handles all business logic related to cases including:
    - Creating and updating cases
    - Listing and filtering cases
    - Generating case statistics
    - Managing user progress
    """
    
    @staticmethod
    def generate_slug(title: str) -> str:
        """
        Generate a URL-friendly slug from a title.
        
        Args:
            title: The case title.
        
        Returns:
            A lowercase, hyphen-separated slug.
        """
        # Convert to lowercase and replace spaces with hyphens
        slug = title.lower().strip()
        # Remove special characters
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        # Replace spaces with hyphens
        slug = re.sub(r'[\s_]+', '-', slug)
        # Remove consecutive hyphens
        slug = re.sub(r'-+', '-', slug)
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        return slug
    
    async def create_case(
        self,
        db: AsyncSession,
        case_data: CaseCreate,
        created_by: Optional[User] = None,
    ) -> Case:
        """
        Create a new forensic case.
        
        The semantic_truth is immediately hashed and never stored plaintext.
        
        Args:
            db: Database session.
            case_data: Case creation data.
            created_by: The admin user creating the case.
        
        Returns:
            The created Case object.
        """
        # Generate slug if not provided
        slug = case_data.slug or self.generate_slug(case_data.title)
        
        # Ensure slug is unique
        slug = await self._ensure_unique_slug(db, slug)
        
        # Hash the semantic truth - NEVER store plaintext
        semantic_truth_hash = crypto_service.hash_semantic_truth(
            case_data.semantic_truth
        )
        
        # Generate case salt for additional entropy
        case_salt = crypto_service.generate_case_salt()
        
        case = Case(
            title=case_data.title,
            slug=slug,
            description=case_data.description,
            story_background=case_data.story_background,
            investigation_objectives=case_data.investigation_objectives,
            difficulty=case_data.difficulty,
            semantic_truth_hash=semantic_truth_hash,
            case_salt=case_salt,
            points=case_data.points,
            extra_metadata=case_data.extra_metadata,
            is_active=True,
        )
        
        db.add(case)
        await db.flush()
        await db.refresh(case)
        
        return case
    
    async def _ensure_unique_slug(
        self,
        db: AsyncSession,
        base_slug: str,
    ) -> str:
        """Ensure the slug is unique, appending a number if necessary."""
        slug = base_slug
        counter = 1
        
        while True:
            result = await db.execute(
                select(Case).where(Case.slug == slug).limit(1)
            )
            if result.scalar_one_or_none() is None:
                return slug
            
            slug = f"{base_slug}-{counter}"
            counter += 1
    
    async def update_case(
        self,
        db: AsyncSession,
        case_id: UUID,
        case_data: CaseUpdate,
    ) -> Optional[Case]:
        """
        Update an existing case.
        
        NOTE: This does not allow updating the semantic_truth.
        Use update_semantic_truth for that.
        
        Args:
            db: Database session.
            case_id: The case ID to update.
            case_data: Update data.
        
        Returns:
            The updated Case or None if not found.
        """
        result = await db.execute(
            select(Case).where(Case.id == case_id)
        )
        case = result.scalar_one_or_none()
        
        if not case:
            return None
        
        update_data = case_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(case, field, value)
        
        await db.flush()
        await db.refresh(case)
        
        return case
    
    async def update_semantic_truth(
        self,
        db: AsyncSession,
        case_id: UUID,
        new_semantic_truth: str,
    ) -> Optional[Case]:
        """
        Update a case's semantic truth.
        
        WARNING: This invalidates all existing user flags for this case.
        Should be used with extreme caution.
        
        Args:
            db: Database session.
            case_id: The case ID.
            new_semantic_truth: The new answer (will be hashed).
        
        Returns:
            The updated Case or None if not found.
        """
        result = await db.execute(
            select(Case).where(Case.id == case_id)
        )
        case = result.scalar_one_or_none()
        
        if not case:
            return None
        
        # Hash the new semantic truth
        case.semantic_truth_hash = crypto_service.hash_semantic_truth(
            new_semantic_truth
        )
        
        # Regenerate case salt to invalidate old flags
        case.case_salt = crypto_service.generate_case_salt()
        
        await db.flush()
        await db.refresh(case)
        
        return case
    
    async def get_case_by_id(
        self,
        db: AsyncSession,
        case_id: UUID,
        include_artifacts: bool = False,
    ) -> Optional[Case]:
        """
        Get a case by its ID.
        
        Args:
            db: Database session.
            case_id: The case ID.
            include_artifacts: Whether to eagerly load artifacts.
        
        Returns:
            The Case or None if not found.
        """
        query = select(Case).where(Case.id == case_id)
        
        if include_artifacts:
            query = query.options(selectinload(Case.artifacts))
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_case_by_slug(
        self,
        db: AsyncSession,
        slug: str,
        include_artifacts: bool = False,
    ) -> Optional[Case]:
        """
        Get a case by its slug.
        
        Args:
            db: Database session.
            slug: The case slug.
            include_artifacts: Whether to eagerly load artifacts.
        
        Returns:
            The Case or None if not found.
        """
        query = select(Case).where(Case.slug == slug)
        
        if include_artifacts:
            query = query.options(selectinload(Case.artifacts))
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def list_cases(
        self,
        db: AsyncSession,
        page: int = 1,
        per_page: int = 20,
        difficulty: Optional[DifficultyLevel] = None,
        active_only: bool = True,
        search: Optional[str] = None,
    ) -> Tuple[List[Case], int]:
        """
        List cases with optional filtering.
        
        Args:
            db: Database session.
            page: Page number (1-indexed).
            per_page: Items per page.
            difficulty: Filter by difficulty level.
            active_only: Only show active cases.
            search: Search term for title/description.
        
        Returns:
            Tuple of (list of cases, total count).
        """
        # Base query
        query = select(Case)
        count_query = select(func.count(Case.id))
        
        # Apply filters
        filters = []
        
        if active_only:
            filters.append(Case.is_active == True)
        
        if difficulty:
            filters.append(Case.difficulty == difficulty)
        
        if search:
            search_term = f"%{search}%"
            filters.append(
                or_(
                    Case.title.ilike(search_term),
                    Case.description.ilike(search_term),
                )
            )
        
        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))
        
        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page).order_by(Case.created_at.desc())
        
        result = await db.execute(query)
        cases = list(result.scalars().all())
        
        return cases, total
    
    async def get_case_statistics(
        self,
        db: AsyncSession,
        case_id: UUID,
    ) -> dict:
        """
        Get statistics for a case.
        
        Args:
            db: Database session.
            case_id: The case ID.
        
        Returns:
            Dictionary with case statistics.
        """
        # Total attempts
        total_attempts_result = await db.execute(
            select(func.count(Submission.id))
            .where(Submission.case_id == case_id)
        )
        total_attempts = total_attempts_result.scalar() or 0
        
        # Unique users
        unique_users_result = await db.execute(
            select(func.count(func.distinct(Submission.user_id)))
            .where(Submission.case_id == case_id)
        )
        unique_users = unique_users_result.scalar() or 0
        
        # Solve count (unique users who solved)
        solve_count_result = await db.execute(
            select(func.count(func.distinct(Submission.user_id)))
            .where(
                Submission.case_id == case_id,
                Submission.is_correct == True,
            )
        )
        solve_count = solve_count_result.scalar() or 0
        
        # Calculate solve rate
        solve_rate = (solve_count / unique_users * 100) if unique_users > 0 else 0.0
        
        # First blood
        first_blood_result = await db.execute(
            select(Submission)
            .where(
                Submission.case_id == case_id,
                Submission.is_correct == True,
            )
            .order_by(Submission.created_at.asc())
            .limit(1)
        )
        first_blood = first_blood_result.scalar_one_or_none()
        
        return {
            "case_id": case_id,
            "total_attempts": total_attempts,
            "unique_users": unique_users,
            "solve_count": solve_count,
            "solve_rate": round(solve_rate, 2),
            "first_blood_user_id": first_blood.user_id if first_blood else None,
            "first_blood_at": first_blood.created_at if first_blood else None,
        }
    
    async def get_user_case_status(
        self,
        db: AsyncSession,
        user_id: UUID,
        case_id: UUID,
    ) -> dict:
        """
        Get a user's status for a specific case.
        
        Args:
            db: Database session.
            user_id: The user ID.
            case_id: The case ID.
        
        Returns:
            Dictionary with user's case status.
        """
        # Check if solved
        solved_result = await db.execute(
            select(Submission)
            .where(
                Submission.user_id == user_id,
                Submission.case_id == case_id,
                Submission.is_correct == True,
            )
            .limit(1)
        )
        is_solved = solved_result.scalar_one_or_none() is not None
        
        # Count attempts
        attempts_result = await db.execute(
            select(func.count(Submission.id))
            .where(
                Submission.user_id == user_id,
                Submission.case_id == case_id,
            )
        )
        attempts = attempts_result.scalar() or 0
        
        return {
            "user_id": user_id,
            "case_id": case_id,
            "is_solved": is_solved,
            "attempts": attempts,
        }
    
    async def delete_case(
        self,
        db: AsyncSession,
        case_id: UUID,
    ) -> bool:
        """
        Delete a case and all associated data.
        
        WARNING: This is destructive and permanent.
        
        Args:
            db: Database session.
            case_id: The case ID.
        
        Returns:
            True if deleted, False if not found.
        """
        result = await db.execute(
            select(Case).where(Case.id == case_id)
        )
        case = result.scalar_one_or_none()
        
        if not case:
            return False
        
        await db.delete(case)
        await db.flush()
        
        return True


# Global case engine instance
case_engine = CaseEngine()
