"""
Case 001: The Disappearance - Backend Integration

This module provides database seeding and case registration for Case 001.
Run this after artifact generation to register the case in the platform.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

# Import from the main backend
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session_factory
from app.db.models import (
    Case, CaseStatus, Artifact, ArtifactType, 
    Challenge, ChallengeType, Hint,
    CaseDependency, DependencyType,
    ArtifactUnlockCondition, UnlockConditionType
)


CASE_DIR = Path(__file__).parent


async def load_case_metadata() -> dict:
    """Load case metadata from JSON file."""
    metadata_file = CASE_DIR / "case_metadata.json"
    with open(metadata_file, 'r') as f:
        return json.load(f)


async def seed_case_001(db: AsyncSession) -> Case:
    """Seed Case 001 into the database."""
    
    metadata = await load_case_metadata()
    
    # Create the case
    case = Case(
        slug=metadata["slug"],
        title=metadata["title"],
        subtitle=metadata["subtitle"],
        description=metadata["narrative"]["background"],
        briefing=metadata["narrative"]["briefing"],
        difficulty=metadata["difficulty"],
        points_total=metadata["points_total"],
        estimated_time_minutes=metadata["metadata"]["estimated_time_minutes"],
        status=CaseStatus.DRAFT,  # Start as draft until artifacts uploaded
        author=metadata["metadata"]["author"],
        version=metadata["metadata"]["version"],
    )
    
    db.add(case)
    await db.flush()  # Get case.id
    
    # Create artifacts
    artifact_map = {}  # id -> Artifact object
    
    for art_data in metadata["artifacts"]:
        artifact_type = ArtifactType.ARCHIVE
        if art_data["type"] == "json":
            artifact_type = ArtifactType.DOCUMENT
        elif art_data["type"] == "pcap":
            artifact_type = ArtifactType.NETWORK_CAPTURE
        elif art_data["type"] == "forensic-image":
            artifact_type = ArtifactType.DISK_IMAGE
        
        artifact = Artifact(
            case_id=case.id,
            name=art_data["name"],
            description=art_data["description"],
            artifact_type=artifact_type,
            filename=art_data["filename"],
            # storage_path will be set when uploaded to MinIO
            storage_path=f"cases/{case.slug}/artifacts/{art_data['filename']}",
            size_bytes=0,  # Will be updated on upload
            sha256_hash="",  # Will be computed on upload
            unlock_order=art_data["unlock_order"],
        )
        
        db.add(artifact)
        await db.flush()
        
        artifact_map[art_data["id"]] = artifact
        
        # Create hints for this artifact
        for i, hint_data in enumerate(art_data.get("hints", [])):
            hint = Hint(
                artifact_id=artifact.id,
                hint_order=i + 1,
                cost=hint_data["cost"],
                content=hint_data["text"],
            )
            db.add(hint)
    
    # Create unlock conditions for artifacts
    for art_data in metadata["artifacts"]:
        if "unlock_condition" in art_data:
            artifact = artifact_map[art_data["id"]]
            condition = art_data["unlock_condition"]
            
            if condition["type"] == "artifact_downloaded":
                # Requires downloading another artifact first
                required_artifact = artifact_map[condition["artifact_id"]]
                unlock_condition = ArtifactUnlockCondition(
                    artifact_id=artifact.id,
                    condition_type=UnlockConditionType.ARTIFACT_DOWNLOADED,
                    required_artifact_id=required_artifact.id,
                )
                db.add(unlock_condition)
            
            elif condition["type"] == "submission_correct":
                # Requires solving a specific challenge
                unlock_condition = ArtifactUnlockCondition(
                    artifact_id=artifact.id,
                    condition_type=UnlockConditionType.SUBMISSION_CORRECT,
                    required_challenge_id=condition["challenge_id"],
                )
                db.add(unlock_condition)
    
    # Create challenges
    for chal_data in metadata["challenges"]:
        challenge_type = ChallengeType.TEXT
        if chal_data["type"] == "flag":
            challenge_type = ChallengeType.FLAG
        elif chal_data["type"] == "multiple_choice":
            challenge_type = ChallengeType.MULTIPLE_CHOICE
        
        challenge = Challenge(
            case_id=case.id,
            slug=chal_data["id"],
            title=chal_data["title"],
            description=chal_data["description"],
            challenge_type=challenge_type,
            points=chal_data["points"],
            answer_format=chal_data["answer_format"],
            # For non-flag challenges, store the answer hash
            # For flag challenges, the flag is generated dynamically per-user
            correct_answer_hash="" if chal_data["type"] == "flag" else 
                _hash_answer(chal_data["validation"]["value"]),
            challenge_order=chal_data["order"],
            is_final=chal_data.get("is_final", False),
        )
        
        db.add(challenge)
    
    await db.commit()
    
    print(f"✅ Case 001 '{case.title}' seeded successfully!")
    print(f"   ID: {case.id}")
    print(f"   Artifacts: {len(metadata['artifacts'])}")
    print(f"   Challenges: {len(metadata['challenges'])}")
    
    return case


def _hash_answer(answer: str) -> str:
    """Hash an answer for storage."""
    import hashlib
    # Normalize: lowercase, strip whitespace
    normalized = answer.lower().strip()
    return hashlib.sha256(normalized.encode()).hexdigest()


async def register_semantic_truth(db: AsyncSession, case_id: int):
    """
    Register the semantic truth for flag generation.
    
    The semantic truth for Case 001 is: d4ta.ex7ract@protonmail.ch
    
    This is stored separately and used for HMAC flag generation.
    """
    from app.db.models import CaseSemanticTruth
    
    truth = CaseSemanticTruth(
        case_id=case_id,
        challenge_id="final",
        semantic_truth="d4ta.ex7ract@protonmail.ch",
        # The flag is generated as: HMAC(user_salt || case_id || challenge_id, semantic_truth)
    )
    
    db.add(truth)
    await db.commit()
    
    print(f"✅ Semantic truth registered for Case {case_id}")


async def update_artifact_storage(
    db: AsyncSession, 
    case_slug: str, 
    artifact_filename: str,
    storage_path: str,
    size_bytes: int,
    sha256_hash: str
):
    """Update artifact with actual storage information after upload."""
    from sqlalchemy import select
    
    result = await db.execute(
        select(Artifact)
        .join(Case)
        .where(Case.slug == case_slug)
        .where(Artifact.filename == artifact_filename)
    )
    artifact = result.scalar_one_or_none()
    
    if artifact:
        artifact.storage_path = storage_path
        artifact.size_bytes = size_bytes
        artifact.sha256_hash = sha256_hash
        await db.commit()
        print(f"✅ Updated artifact: {artifact_filename}")
    else:
        print(f"❌ Artifact not found: {artifact_filename}")


async def activate_case(db: AsyncSession, case_slug: str):
    """Activate the case (make it available to players)."""
    from sqlalchemy import select
    
    result = await db.execute(
        select(Case).where(Case.slug == case_slug)
    )
    case = result.scalar_one_or_none()
    
    if case:
        case.status = CaseStatus.ACTIVE
        case.released_at = datetime.now(timezone.utc)
        await db.commit()
        print(f"✅ Case '{case.title}' is now ACTIVE!")
    else:
        print(f"❌ Case not found: {case_slug}")


# ============================================================================
# CLI COMMANDS
# ============================================================================

async def main():
    """Main CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Case 001 Backend Integration")
    parser.add_argument("command", choices=["seed", "activate", "status"])
    
    args = parser.parse_args()
    
    async with async_session_factory() as db:
        if args.command == "seed":
            case = await seed_case_001(db)
            await register_semantic_truth(db, case.id)
            
        elif args.command == "activate":
            await activate_case(db, "the-disappearance")
            
        elif args.command == "status":
            from sqlalchemy import select
            result = await db.execute(
                select(Case).where(Case.slug == "the-disappearance")
            )
            case = result.scalar_one_or_none()
            if case:
                print(f"Case: {case.title}")
                print(f"Status: {case.status.value}")
                print(f"Points: {case.points_total}")
            else:
                print("Case 001 not found in database")


if __name__ == "__main__":
    asyncio.run(main())
