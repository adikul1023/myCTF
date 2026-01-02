"""Update artifact storage paths to match R2."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import get_sync_session

# Map artifact names to their actual R2 storage paths
# Based on what we uploaded earlier
ARTIFACT_PATHS = {
    "GitHub Organization Export": "cases/001-the-disappearance/github_export/",
    "Telegram Chat Export": "cases/001-the-disappearance/telegram_export/result.json",
    "Device Photo Library": "cases/001-the-disappearance/images/",
    "Network Traffic Capture": "cases/001-the-disappearance/network_capture/",
    "Laptop Forensic Image": "cases/001-the-disappearance/disk_image/",
}


def update_artifact_paths():
    """Update artifact storage paths to match R2."""
    session = get_sync_session()
    
    try:
        # Get all artifacts for the case
        result = session.execute(text("""
            SELECT id, name, storage_path
            FROM artifacts
            WHERE case_id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
        """))
        
        artifacts = result.fetchall()
        print(f"Found {len(artifacts)} artifacts\n")
        
        for artifact_id, name, current_path in artifacts:
            print(f"Artifact: {name}")
            print(f"  Current path: {current_path}")
            
            if name in ARTIFACT_PATHS:
                new_path = ARTIFACT_PATHS[name]
                print(f"  New path: {new_path}")
                
                session.execute(text("""
                    UPDATE artifacts
                    SET storage_path = :new_path,
                        file_size = 1048576
                    WHERE id = :artifact_id
                """), {
                    "artifact_id": str(artifact_id),
                    "new_path": new_path
                })
                print("  ✓ Updated")
            else:
                print("  ⚠ No mapping found")
            print()
        
        session.commit()
        print("\n✅ All artifact paths updated!")
        
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    update_artifact_paths()
