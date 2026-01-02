#!/usr/bin/env python3
"""
Upload Case 001 artifacts to MinIO and update database records.

This script:
1. Creates ZIP archives of artifact folders
2. Uploads them to MinIO
3. Updates the database artifact records with correct hashes and sizes
"""

import asyncio
import hashlib
import io
import os
import sys
import zipfile
from pathlib import Path
from uuid import UUID

# Add parent directory to path for imports
backend_path = str(Path(__file__).parent.parent)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

os.chdir(backend_path)

from minio import Minio
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.models import Artifact

# Case 001 ID
CASE_ID = UUID("03a9a67b-5be9-41a7-8927-d14d49183166")

# Artifacts base path
ARTIFACTS_BASE = Path(__file__).parent.parent.parent / "cases" / "001-the-disappearance" / "artifacts"

# Artifact folder mappings (folder_name -> artifact_name in DB)
ARTIFACT_MAPPINGS = {
    "github_export": "GitHub Organization Export",
    "telegram_export": "Telegram Chat Export", 
    "images": "Device Photo Library",
    "network_capture": "Network Traffic Capture",
    "disk_image": "Laptop Forensic Image",
}


def create_zip_from_folder(folder_path: Path) -> tuple[bytes, int, str]:
    """
    Create a ZIP archive from a folder.
    
    Returns:
        Tuple of (zip_bytes, file_size, sha256_hash)
    """
    buffer = io.BytesIO()
    
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(folder_path)
                zf.write(file_path, arcname)
    
    buffer.seek(0)
    zip_bytes = buffer.read()
    file_size = len(zip_bytes)
    
    # Calculate SHA256
    sha256_hash = hashlib.sha256(zip_bytes).hexdigest()
    
    return zip_bytes, file_size, sha256_hash


async def main():
    print("Uploading Case 001 artifacts to MinIO...\n")
    
    # Check artifacts folder exists
    if not ARTIFACTS_BASE.exists():
        print(f"Error: Artifacts folder not found: {ARTIFACTS_BASE}")
        return
    
    # Initialize MinIO client
    minio_client = Minio(
        endpoint=settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_USE_SSL,
    )
    
    # Ensure bucket exists
    bucket_name = settings.MINIO_BUCKET_NAME
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)
        print(f"Created bucket: {bucket_name}")
    else:
        print(f"Bucket exists: {bucket_name}")
    
    # Database connection
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Get existing artifacts for this case
        result = await db.execute(
            select(Artifact).where(Artifact.case_id == CASE_ID)
        )
        artifacts = {a.name: a for a in result.scalars().all()}
        
        if not artifacts:
            print("No artifacts found in database for Case 001")
            print("   Run seed_artifacts_001.py first!")
            return
        
        print(f"Found {len(artifacts)} artifacts in database\n")
        
        # Process each artifact folder
        for folder_name, artifact_name in ARTIFACT_MAPPINGS.items():
            folder_path = ARTIFACTS_BASE / folder_name
            
            if not folder_path.exists():
                print(f"Warning: Folder not found: {folder_name}")
                continue
            
            if artifact_name not in artifacts:
                print(f"Warning: Artifact not in DB: {artifact_name}")
                continue
            
            artifact = artifacts[artifact_name]
            print(f"Processing: {folder_name}")
            
            # Create ZIP
            print(f"   Zipping folder...")
            zip_bytes, file_size, sha256_hash = create_zip_from_folder(folder_path)
            print(f"   Size: {file_size / (1024*1024):.2f} MB")
            print(f"   SHA256: {sha256_hash[:16]}...")
            
            # Upload to MinIO
            object_name = f"cases/{CASE_ID}/{folder_name}.zip"
            print(f"   Uploading to MinIO...")
            
            minio_client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=io.BytesIO(zip_bytes),
                length=file_size,
                content_type="application/zip",
            )
            print(f"   Uploaded: {object_name}")
            
            # Update database record
            await db.execute(
                update(Artifact)
                .where(Artifact.id == artifact.id)
                .values(
                    storage_path=f"{bucket_name}/{object_name}",
                    file_size=file_size,
                    file_hash_sha256=sha256_hash,
                )
            )
            print(f"   Database updated\n")
        
        await db.commit()
    
    await engine.dispose()
    
    print("=" * 50)
    print("All artifacts uploaded successfully!")
    print(f"   Bucket: {bucket_name}")
    print(f"   Case ID: {CASE_ID}")


if __name__ == "__main__":
    asyncio.run(main())
