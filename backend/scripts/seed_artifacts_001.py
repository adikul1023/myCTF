"""
Seed artifacts for Case 001: The Disappearance
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.models import Case, Artifact, ArtifactType


async def seed_artifacts():
    """Seed artifacts for Case 001."""
    
    async with SessionLocal() as db:
        # Get Case 001
        result = await db.execute(
            select(Case).where(Case.slug == "the-disappearance")
        )
        case = result.scalar_one_or_none()
        
        if not case:
            print("❌ Case 001 not found. Run seed_case_001.py first.")
            return
        
        # Check if artifacts already exist
        result = await db.execute(
            select(Artifact).where(Artifact.case_id == case.id)
        )
        existing = result.scalars().all()
        
        if existing:
            print(f"⚠️  Case 001 already has {len(existing)} artifacts")
            for art in existing:
                print(f"   - {art.name}")
            return
        
        # Define artifacts (matching case_metadata.json)
        artifacts_data = [
            {
                "name": "GitHub Organization Export",
                "description": "Complete export of the nexus-dynamics-org GitHub organization, including all repositories Marcus had access to, commit histories, and organization metadata.",
                "artifact_type": ArtifactType.ARCHIVE,
                "storage_path": "cases/the-disappearance/github_export.tar.gz",
                "file_size": 45000000,  # ~45 MB
                "file_hash_sha256": "placeholder",
                "mime_type": "application/gzip",
            },
            {
                "name": "Telegram Chat Export",
                "description": "Export of Marcus's Telegram activity from a tech industry group chat he participated in.",
                "artifact_type": ArtifactType.DOCUMENT,
                "storage_path": "cases/the-disappearance/telegram_export.tar.gz",
                "file_size": 12000000,  # ~12 MB
                "file_hash_sha256": "placeholder",
                "mime_type": "application/gzip",
            },
            {
                "name": "Device Photo Library",
                "description": "312 images recovered from Marcus's iPhone backup. Most appear to be screenshots, memes, and wallpapers.",
                "artifact_type": ArtifactType.ARCHIVE,
                "storage_path": "cases/the-disappearance/image_dump.tar.gz",
                "file_size": 890000000,  # ~890 MB
                "file_hash_sha256": "placeholder",
                "mime_type": "application/gzip",
            },
            {
                "name": "Network Traffic Capture",
                "description": "48-hour PCAP capture from Marcus's workstation network port, spanning November 13-15, 2024.",
                "artifact_type": ArtifactType.PCAP,
                "storage_path": "cases/the-disappearance/network_capture.pcap",
                "file_size": 2100000000,  # ~2.1 GB
                "file_hash_sha256": "placeholder",
                "mime_type": "application/vnd.tcpdump.pcap",
            },
            {
                "name": "Laptop Forensic Image",
                "description": "Forensic image of Marcus's MacBook Pro. Contains browser history, shell history, and potentially deleted files.",
                "artifact_type": ArtifactType.DISK_IMAGE,
                "storage_path": "cases/the-disappearance/disk_image.dd.gz",
                "file_size": 512000000,  # ~512 MB
                "file_hash_sha256": "placeholder",
                "mime_type": "application/gzip",
            },
        ]
        
        for art_data in artifacts_data:
            artifact = Artifact(
                case_id=case.id,
                **art_data
            )
            db.add(artifact)
        
        await db.commit()
        
        print("=" * 50)
        print("✅ Artifacts seeded for Case 001!")
        print("=" * 50)
        print(f"Total artifacts: {len(artifacts_data)}")
        for art in artifacts_data:
            print(f"  • {art['name']}")
        print("=" * 50)
        print("\n⚠️  NOTE: These are placeholder entries.")
        print("   Actual files need to be uploaded to MinIO.")
        print("   Files are located in: cases/001-the-disappearance/artifacts/")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(seed_artifacts())
