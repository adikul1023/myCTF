"""Simple sync version to reset admin user."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.security import SecurityService
from app.db.session import get_sync_session


def reset_admin():
    """Delete all users and create a new admin user."""
    
    security_service = SecurityService()
    
    # Create session
    session = get_sync_session()
    
    try:
        # Delete in correct order due to foreign key constraints
        session.execute(text("DELETE FROM invite_codes"))
        session.execute(text("DELETE FROM users"))
        session.commit()
        print("Deleted all existing users and invite codes")
        
        # Get admin credentials from user
        print("\nEnter admin credentials:")
        email = input("Email: ").strip()
        username = input("Username (default: admin): ").strip() or "admin"
        password = input("Password: ").strip()
        
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
        print("Admin user created!")
        print("=" * 50)
        print(f"Email: {email}")
        print(f"Password: {password}")
        print("=" * 50)
        
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    reset_admin()
