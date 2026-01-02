"""Fix case difficulty enum value in database."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import get_sync_session


def fix_difficulty():
    """Fix the difficulty enum value to uppercase."""
    session = get_sync_session()
    
    try:
        # Check current values
        result = session.execute(text("SELECT id, title, difficulty FROM cases"))
        rows = result.fetchall()
        print("Current cases:")
        for row in rows:
            print(f"  {row}")
        
        # The enum column might need to be updated
        # First, let's see the column type
        result = session.execute(text("""
            SELECT column_name, data_type, udt_name 
            FROM information_schema.columns 
            WHERE table_name = 'cases' AND column_name = 'difficulty'
        """))
        col_info = result.fetchone()
        print(f"\nColumn info: {col_info}")
        
        # Update difficulty to uppercase ADVANCED if it's lowercase
        session.execute(text("""
            UPDATE cases 
            SET difficulty = 'ADVANCED' 
            WHERE difficulty = 'advanced' OR difficulty = 'Advanced'
        """))
        session.commit()
        print("\nUpdated difficulty to ADVANCED")
        
        # Verify
        result = session.execute(text("SELECT id, title, difficulty FROM cases"))
        rows = result.fetchall()
        print("\nAfter fix:")
        for row in rows:
            print(f"  {row}")
            
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    fix_difficulty()
