"""
Script to create the initial admin user.

Run this after migrations to create the first admin account.

Usage:
    python scripts/create_admin.py
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.core.security import security_service
from app.db.session import SessionLocal
from app.db.models import User, InviteCode


async def create_admin():
    """Create the initial admin user and invite code."""
    
    print("=" * 50)
    print("Forensic CTF Platform - Admin Setup")
    print("=" * 50)
    
    async with SessionLocal() as db:
        # Check if any admin exists
        result = await db.execute(
            select(User).where(User.is_admin == True).limit(1)
        )
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            print(f"\n⚠️  Admin user already exists: {existing_admin.email}")
            print("If you need to create another admin, modify this script.")
            return
        
        print("\nNo admin user found. Creating initial admin...")
        
        # Get admin details
        email = input("\nAdmin email: ").strip()
        if not email:
            print("❌ Email is required")
            return
        
        username = input("Admin username: ").strip()
        if not username:
            print("❌ Username is required")
            return
        
        password = input("Admin password (min 12 chars): ").strip()
        if len(password) < 12:
            print("❌ Password must be at least 12 characters")
            return
        
        # Create a special admin invite code
        admin_invite_code = security_service.generate_invite_code()
        invite_code = InviteCode(
            code=admin_invite_code,
            max_uses=1,
            use_count=1,
            is_used=True,
        )
        db.add(invite_code)
        await db.flush()
        
        # Create admin user
        password_hash = security_service.hash_password(password)
        
        admin_user = User(
            email=email,
            username=username.lower(),
            password_hash=password_hash,
            invite_code_used=admin_invite_code,
            is_active=True,
            is_admin=True,
        )
        
        db.add(admin_user)
        await db.flush()
        
        # Update invite code with user reference
        invite_code.used_by_id = admin_user.id
        
        await db.commit()
        
        print("\n" + "=" * 50)
        print("✅ Admin user created successfully!")
        print("=" * 50)
        print(f"\nEmail: {email}")
        print(f"Username: {username}")
        print("\nYou can now login at /api/v1/auth/login")
        print("\n⚠️  Keep these credentials safe!")
        print("=" * 50)


async def generate_invite_codes(count: int = 5):
    """Generate invite codes for distribution."""
    
    print("\n" + "=" * 50)
    print("Generating Invite Codes")
    print("=" * 50)
    
    async with SessionLocal() as db:
        # Get admin user
        result = await db.execute(
            select(User).where(User.is_admin == True).limit(1)
        )
        admin = result.scalar_one_or_none()
        
        if not admin:
            print("❌ No admin user found. Run create_admin first.")
            return
        
        codes = []
        for _ in range(count):
            code_str = security_service.generate_invite_code()
            invite_code = InviteCode(
                code=code_str,
                max_uses=1,
                created_by_id=admin.id,
            )
            db.add(invite_code)
            codes.append(code_str)
        
        await db.commit()
        
        print(f"\n✅ Generated {count} invite codes:\n")
        for code in codes:
            print(f"  {code}")
        
        print("\n⚠️  Share these codes securely with trusted users.")
        print("=" * 50)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--invite-codes":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        asyncio.run(generate_invite_codes(count))
    else:
        asyncio.run(create_admin())
