#!/usr/bin/env python3
"""
Update artifact database records after MinIO upload.
Run this from inside the Docker backend container.
"""

import asyncio
import sys
from pathlib import Path
from uuid import UUID

# Add parent directory to path
backend_path = str(Path(__file__).parent.parent)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.models import Artifact

# Case 001 ID
CASE_ID = UUID("03a9a67b-5be9-41a7-8927-d14d49183166")

# Artifact data from MinIO upload
ARTIFACT_DATA = {
    "GitHub Organization Export": {
        "storage_path": "forensic-artifacts/cases/03a9a67b-5be9-41a7-8927-d14d49183166/github_export.zip",
        "file_size": 30908,  # 0.03 MB
        "file_hash_sha256": "32caee6f9db157f4",  # Partial, will update with full hash
    },
    "Telegram Chat Export": {
        "storage_path": "forensic-artifacts/cases/03a9a67b-5be9-41a7-8927-d14d49183166/telegram_export.zip",
        "file_size": 10240,  # 0.01 MB
        "file_hash_sha256": "e7cbb5c88dd616ff",
    },
    "Network Traffic Capture": {
        "storage_path": "forensic-artifacts/cases/03a9a67b-5be9-41a7-8927-d14d49183166/network_capture.zip",
        "file_size": 3177472,  # 3.03 MB
        "file_hash_sha256": "9404ee2d90a59969",
    },
}


async def main():
    print("Updating artifact database records...\n")
    
    # Database connection
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Get artifacts for this case
        result = await db.execute(
            select(Artifact).where(Artifact.case_id == CASE_ID)
        )
        artifacts = {a.name: a for a in result.scalars().all()}
        
        if not artifacts:
            print("No artifacts found in database!")
            return
        
        print(f"Found {len(artifacts)} artifacts in database")
        
        # Update each artifact
        for artifact_name, data in ARTIFACT_DATA.items():
            if artifact_name not in artifacts:
                print(f"Warning: {artifact_name} not found in DB")
                continue
            
            print(f"\nUpdating: {artifact_name}")
            print(f"   Storage: {data['storage_path']}")
            print(f"   Size: {data['file_size']} bytes")
            
            await db.execute(
                update(Artifact)
                .where(Artifact.id == artifacts[artifact_name].id)
                .values(
                    storage_path=data["storage_path"],
                    file_size=data["file_size"],
                )
            )
        
        await db.commit()
    
    await engine.dispose()
    
    print("\n" + "=" * 50)
    print("Database updated successfully!")


if __name__ == "__main__":
    asyncio.run(main())
