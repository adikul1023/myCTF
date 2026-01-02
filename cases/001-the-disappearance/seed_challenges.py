#!/usr/bin/env python3
"""
Seed challenges for Case 001: The Disappearance
"""
import asyncio
import hashlib
import sys
import json
from pathlib import Path
from uuid import UUID

backend_path = str(Path(__file__).parent.parent.parent / "backend")
sys.path.insert(0, backend_path)

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

CASE_ID = UUID("03a9a67b-5be9-41a7-8927-d14d49183166")

CHALLENGES = [
    {
        "title": "Challenge 1: Initial Assessment",
        "question": "Which repository contains evidence of credential cleanup?",
        "semantic_truth": "internal-tools",
        "points": 75,
        "difficulty": "EASY",
        "display_order": 1,
        "hints": [
            {"cost": 10, "text": "Look for commits that delete .bak files"},
            {"cost": 15, "text": "Check bash_history.txt for failed git commands"},
            {"cost": 20, "text": "The repository name contains the word 'internal'"}
        ]
    },
    {
        "title": "Challenge 2: Timeline Analysis",
        "question": "What was the exact UTC timestamp of the suspicious network burst to paste.sh? (Format: YYYY-MM-DD HH:MM:SS)",
        "semantic_truth": "2024-11-14 23:48:12",
        "points": 125,
        "difficulty": "MEDIUM",
        "display_order": 2,
        "hints": [
            {"cost": 15, "text": "Use Wireshark filter: ip.addr == 104.21.67.185"},
            {"cost": 20, "text": "Look for TLS connections with SNI extension containing 'paste'"},
            {"cost": 30, "text": "The timestamp is 72 seconds after the Telegram forward"}
        ]
    },
    {
        "title": "Challenge 3: Hidden in Plain Sight",
        "question": "What is the password hidden in the steganographic payload?",
        "semantic_truth": "nexus2024!",
        "points": 150,
        "difficulty": "MEDIUM",
        "display_order": 3,
        "hints": [
            {"cost": 20, "text": "Check wallpaper_abstract_*.png files for embedded data"},
            {"cost": 30, "text": "Use steghide tool to detect and extract"},
            {"cost": 40, "text": "The file number contains digits 0, 4, 7"}
        ]
    },
    {
        "title": "Challenge 4: External Contact",
        "question": "Identify the Telegram handle of the external contact who coordinated the extraction.",
        "semantic_truth": "DataHaven",
        "points": 100,
        "difficulty": "MEDIUM",
        "display_order": 4,
        "hints": [
            {"cost": 15, "text": "Look for forwarded messages in Telegram export"},
            {"cost": 20, "text": "Correlate message timestamp with network traffic"},
            {"cost": 25, "text": "The message mentions 'Package ready' and has message ID 4847"}
        ]
    },
    {
        "title": "Challenge 5: The Dead Drop",
        "question": "What external email address was Marcus using to coordinate the data exfiltration? (Include hash prefix: email:hash)",
        "semantic_truth": "d4ta.ex7ract@protonmail.ch:acb10e",
        "points": 300,
        "difficulty": "HARD",
        "display_order": 5,
        "hints": [
            {"cost": 40, "text": "Check auth.yaml.bak file in internal-tools/config/"},
            {"cost": 50, "text": "The third test_recipients entry is encrypted with password from Challenge 3"},
            {"cost": 75, "text": "Decrypt with: echo '<string>' | openssl enc -aes-256-cbc -a -d -pbkdf2 -k 'nexus2024!'"},
            {"cost": 100, "text": "After decryption, apply ROT13 to get the email address"}
        ]
    }
]


async def seed_challenges():
    """Seed the 5 challenges into the database."""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Verify case exists
        result = await db.execute(text("SELECT id, title FROM cases WHERE id = :case_id"), {"case_id": str(CASE_ID)})
        row = result.first()
        
        if not row:
            print(f"Error: Case {CASE_ID} not found!")
            return
        
        print(f"Seeding challenges for: {row[1]}\n")
        
        for challenge_data in CHALLENGES:
            # Calculate semantic truth hash
            semantic_truth_hash = hashlib.sha256(
                challenge_data["semantic_truth"].encode()
            ).hexdigest()
            
            # Insert challenge
            await db.execute(
                text("""
                INSERT INTO challenges 
                (case_id, title, question, semantic_truth, semantic_truth_hash, 
                 points, difficulty, display_order, hints, is_active)
                VALUES 
                (:case_id, :title, :question, :semantic_truth, :semantic_truth_hash, 
                 :points, :difficulty, :display_order, :hints::jsonb, :is_active)
                """),
                {
                    "case_id": str(CASE_ID),
                    "title": challenge_data["title"],
                    "question": challenge_data["question"],
                    "semantic_truth": challenge_data["semantic_truth"],
                    "semantic_truth_hash": semantic_truth_hash,
                    "points": challenge_data["points"],
                    "difficulty": challenge_data["difficulty"],
                    "display_order": challenge_data["display_order"],
                    "hints": json.dumps(challenge_data["hints"]),
                    "is_active": True
                }
            )
            
            print(f"✓ Added: {challenge_data['title']} ({challenge_data['points']} points)")
        
        await db.commit()
        print(f"\n✓ Successfully seeded {len(CHALLENGES)} challenges!")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_challenges())
