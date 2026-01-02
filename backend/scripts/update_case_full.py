"""Update Case 001 with full story content and seed artifacts."""

import sys
import os
import uuid
import secrets

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import get_sync_session

# The actual full narrative from case_metadata.json
BACKGROUND = """Marcus Chen, a senior software engineer at Nexus Dynamics, failed to appear for work on November 15th, 2024. His access badge wasn't used, his phone went straight to voicemail, and his apartment was found empty.

HR initially assumed a family emergency, but when they couldn't reach him for 48 hours, they escalated to Security. A preliminary review of access logs showed unusual patterns in the days leading up to his disappearance.

You've been brought in to investigate."""

BRIEFING = """Your task is to analyze the digital artifacts recovered from Marcus Chen's work accounts and devices. Security has already preserved:
- A GitHub organization export
- His Telegram backup  
- Photos from his device
- Network captures from his workstation
- A forensic image of his laptop

Your primary objective is to determine if data was exfiltrated and identify any external contacts involved."""

OBJECTIVES = """1. Analyze all provided artifacts for signs of data exfiltration
2. Identify any external contacts Marcus may have communicated with
3. Determine the method and timing of any data transfer
4. Recover the external contact email used for coordination"""

# Artifacts to seed - using actual column names from migration
ARTIFACTS = [
    {
        "name": "GitHub Organization Export",
        "description": "Complete export of the nexus-dynamics-org GitHub organization, including all repositories Marcus had access to, commit histories, and organization metadata.",
        "artifact_type": "archive",
        "storage_path": "cases/001-the-disappearance/github_export.tar.gz",
        "mime_type": "application/gzip",
    },
    {
        "name": "Telegram Chat Export",
        "description": "Export of Marcus's Telegram activity from a tech industry group chat he participated in.",
        "artifact_type": "document",
        "storage_path": "cases/001-the-disappearance/telegram_export/",
        "mime_type": "application/json",
    },
    {
        "name": "Device Photo Library",
        "description": "312 images recovered from Marcus's iPhone backup. Most appear to be screenshots, memes, and wallpapers.",
        "artifact_type": "archive",
        "storage_path": "cases/001-the-disappearance/images/",
        "mime_type": "image/png",
    },
    {
        "name": "Network Traffic Capture",
        "description": "48-hour PCAP capture from Marcus's workstation network port, spanning November 13-15, 2024.",
        "artifact_type": "pcap",
        "storage_path": "cases/001-the-disappearance/network_capture.pcap",
        "mime_type": "application/vnd.tcpdump.pcap",
    },
    {
        "name": "Laptop Forensic Image",
        "description": "Forensic image of Marcus's MacBook Pro. Contains browser history, shell history, and potentially deleted files.",
        "artifact_type": "disk_image",
        "storage_path": "cases/001-the-disappearance/disk_image.dd.gz",
        "mime_type": "application/gzip",
    },
]


def update_case():
    """Update the case with full story and add artifacts."""
    session = get_sync_session()
    
    try:
        # Get case ID
        result = session.execute(text("SELECT id, title FROM cases WHERE slug = 'the-disappearance'"))
        case_row = result.first()
        
        if not case_row:
            print("Case not found!")
            return
        
        case_id = str(case_row[0])
        print(f"Updating case: {case_row[1]} (ID: {case_id})")
        
        # Update case with full story
        session.execute(text("""
            UPDATE cases SET 
                description = :description,
                story_background = :story_background,
                investigation_objectives = :investigation_objectives
            WHERE id = :case_id
        """), {
            "case_id": case_id,
            "description": BRIEFING,
            "story_background": BACKGROUND,
            "investigation_objectives": OBJECTIVES,
        })
        session.commit()
        print("✓ Updated case story content")
        
        # Check if artifacts already exist
        result = session.execute(text("SELECT COUNT(*) FROM artifacts WHERE case_id = :case_id"), {"case_id": case_id})
        artifact_count = result.scalar()
        
        if artifact_count > 0:
            print(f"Found {artifact_count} existing artifacts, deleting...")
            session.execute(text("DELETE FROM artifacts WHERE case_id = :case_id"), {"case_id": case_id})
            session.commit()
        
        # Insert artifacts using actual column names from migration
        for artifact in ARTIFACTS:
            artifact_id = str(uuid.uuid4())
            session.execute(text("""
                INSERT INTO artifacts 
                (id, case_id, name, description, artifact_type, storage_path, file_size, file_hash_sha256, mime_type, created_at, updated_at)
                VALUES 
                (:id, :case_id, :name, :description, :artifact_type, :storage_path, :file_size, :file_hash_sha256, :mime_type, NOW(), NOW())
            """), {
                "id": artifact_id,
                "case_id": case_id,
                "name": artifact["name"],
                "description": artifact["description"],
                "artifact_type": artifact["artifact_type"],
                "storage_path": artifact["storage_path"],
                "file_size": 0,
                "file_hash_sha256": secrets.token_hex(32),  # Placeholder hash
                "mime_type": artifact["mime_type"],
            })
            print(f"✓ Added artifact: {artifact['name']}")
        
        session.commit()
        print(f"\n✅ Successfully updated case with full story and {len(ARTIFACTS)} artifacts!")
        
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    update_case()
