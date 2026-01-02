"""Quick script to create admin user"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.core.security import security_service
from app.db.session import SessionLocal
from app.db.models import User, InviteCode

async def create_admin():
    async with SessionLocal() as db:
        admin_invite_code = security_service.generate_invite_code()
        invite_code = InviteCode(code=admin_invite_code, max_uses=1, use_count=1, is_used=True)
        db.add(invite_code)
        await db.flush()
        
        password_hash = security_service.hash_password('adminpassword123!')
        admin_user = User(
            email='admin@ctf.local', 
            username='admin', 
            password_hash=password_hash, 
            invite_code_used=admin_invite_code, 
            is_active=True, 
            is_admin=True
        )
        db.add(admin_user)
        await db.flush()
        
        invite_code.used_by_id = admin_user.id
        await db.commit()
        print('Admin created: admin@ctf.local / adminpassword123!')

asyncio.run(create_admin())
