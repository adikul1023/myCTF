"""Reset/create admin with valid email."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, update
from app.core.security import security_service
from app.db.session import SessionLocal
from app.db.models import User, InviteCode


async def reset_admin():
    """Update admin user with valid email."""
    
    async with SessionLocal() as db:
        # Get existing admin
        result = await db.execute(
            select(User).where(User.is_admin == True).limit(1)
        )
        admin = result.scalar_one_or_none()
        
        if admin:
            # Update existing admin
            new_email = "admin@forensic-ctf.com"
            new_password = "adminpassword123!"
            password_hash = security_service.hash_password(new_password)
            
            admin.email = new_email
            admin.password_hash = password_hash
            
            await db.commit()
            
            print("=" * 50)
            print("Admin user updated!")
            print("=" * 50)
            print(f"Email: {new_email}")
            print(f"Password: {new_password}")
            print("=" * 50)
        else:
            # Create new admin
            admin_invite_code = security_service.generate_invite_code()
            invite_code = InviteCode(
                code=admin_invite_code,
                max_uses=1,
                use_count=1,
                is_used=True,
            )
            db.add(invite_code)
            await db.flush()
            
            email = "admin@forensic-ctf.com"
            username = "admin"
            password = "adminpassword123!"
            
            password_hash = security_service.hash_password(password)
            
            admin_user = User(
                email=email,
                username=username,
                password_hash=password_hash,
                invite_code_used=admin_invite_code,
                is_active=True,
                is_admin=True,
            )
            
            db.add(admin_user)
            await db.flush()
            
            invite_code.used_by_id = admin_user.id
            await db.commit()
            
            print("=" * 50)
            print("Admin user created!")
            print("=" * 50)
            print(f"Email: {email}")
            print(f"Password: {password}")
            print("=" * 50)


if __name__ == "__main__":
    asyncio.run(reset_admin())
