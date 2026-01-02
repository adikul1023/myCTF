"""
Seed Case 001: The Disappearance into the database.
"""

import asyncio
import sys
import os
import hashlib
import secrets

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.models import Case, DifficultyLevel


async def seed_case_001():
    """Seed Case 001 into the database."""
    
    async with SessionLocal() as db:
        # Check if case already exists
        result = await db.execute(
            select(Case).where(Case.slug == "the-disappearance")
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"⚠️  Case 001 already exists: {existing.title}")
            print(f"   ID: {existing.id}")
            return existing
        
        # The semantic truth (the answer)
        semantic_truth = "d4ta.ex7ract@protonmail.ch"
        semantic_truth_hash = hashlib.sha256(
            semantic_truth.lower().strip().encode()
        ).hexdigest()
        
        # Generate case salt for flag generation
        case_salt = secrets.token_hex(32)
        
        case = Case(
            title="The Disappearance",
            slug="the-disappearance",
            description="Marcus Chen, a senior software engineer at Nexus Dynamics, failed to appear for work on November 15th, 2024. His access badge wasn't used, his phone went straight to voicemail, and his apartment was found empty. HR initially assumed a family emergency, but when they couldn't reach him for 48 hours, they escalated to Security. A preliminary review of access logs showed unusual patterns in the days leading up to his disappearance. You've been brought in to investigate.",
            story_background="""Marcus Chen was a senior software engineer at Nexus Dynamics, a defense contractor specializing in autonomous systems. He had been with the company for 4 years and had access to several classified projects.

On November 15th, 2024, Marcus failed to appear for work. His access badge wasn't used, his phone went straight to voicemail, and his apartment was found empty. Initial investigation revealed unusual patterns in the days leading up to his disappearance.

Security has preserved several digital artifacts from Marcus's work accounts and devices for your analysis.""",
            investigation_objectives="""Your task is to analyze the digital artifacts recovered from Marcus Chen's work accounts and devices. Security has already preserved:

1. A GitHub organization export
2. His Telegram backup
3. Photos from his device
4. Network captures from his workstation
5. A forensic image of his laptop

Your primary objectives:
- Analyze all provided artifacts for signs of data exfiltration
- Identify any external contacts Marcus may have communicated with
- Determine the method and timing of any data transfer
- Recover the external contact email used for coordination

The semantic truth you must discover is an email address.""",
            difficulty=DifficultyLevel.INTERMEDIATE,
            semantic_truth_hash=semantic_truth_hash,
            case_salt=case_salt,
            points=500,
            extra_metadata={
                "subtitle": "A Data Security Incident Investigation",
                "estimated_time_minutes": 120,
                "author": "CTF Platform",
                "version": "1.0.0",
                "skills_tested": [
                    "Git forensics",
                    "Metadata analysis",
                    "Network traffic analysis",
                    "Steganography detection",
                    "File carving",
                    "Timeline correlation"
                ],
                "tools_recommended": [
                    "Wireshark",
                    "ExifTool",
                    "steghide",
                    "photorec/scalpel",
                    "jq",
                    "Git"
                ]
            },
            is_active=True,
        )
        
        db.add(case)
        await db.commit()
        await db.refresh(case)
        
        print("=" * 50)
        print("✅ Case 001 'The Disappearance' seeded!")
        print("=" * 50)
        print(f"ID: {case.id}")
        print(f"Title: {case.title}")
        print(f"Difficulty: {case.difficulty.value}")
        print(f"Points: {case.points}")
        print(f"Active: {case.is_active}")
        print("=" * 50)
        print(f"\n🔑 Semantic Truth: {semantic_truth}")
        print("   (Users must discover this email address)")
        print("=" * 50)
        
        return case


if __name__ == "__main__":
    asyncio.run(seed_case_001())
