"""Create admin user directly without interactive input."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.security import SecurityService
from app.db.session import get_sync_session


def create_admin(email: str, password: str, username: str = "admin"):
    """Create admin user with provided credentials."""
    
    security_service = SecurityService()
    session = get_sync_session()
    
    try:
        # Delete in correct order due to foreign key constraints
        session.execute(text("DELETE FROM invite_codes"))
        session.execute(text("DELETE FROM users"))
        session.commit()
        print("Deleted all existing users and invite codes")
        
        password_hash = security_service.hash_password(password)
        
        # Insert admin user
        session.execute(text("""
            INSERT INTO users (email, username, password_hash, is_active, is_admin, invite_code_used, created_at, updated_at)
            VALUES (:email, :username, :password_hash, true, true, 'ADMIN_DIRECT', NOW(), NOW())
        """), {
            "email": email,
            "username": username,
            "password_hash": password_hash
        })
        
        session.commit()
        
        print("=" * 50)
        print("Admin user created successfully!")
        print("=" * 50)
        print(f"Email: {email}")
        print(f"Username: {username}")
        print("=" * 50)
        
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_admin_direct.py <email> <password> [username]")
        print("Example: python create_admin_direct.py admin@example.com MySecurePass123! admin")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    username = sys.argv[3] if len(sys.argv) > 3 else "admin"
    
    create_admin(email, password, username)
