"""Fix case difficulty enum value in database."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import get_sync_session


def fix_difficulty():
    """Check PostgreSQL enum values and case data."""
    session = get_sync_session()
    
    try:
        # Check PostgreSQL enum values
        result = session.execute(text("SELECT unnest(enum_range(NULL::difficultylevel))"))
        enum_vals = [row[0] for row in result]
        print(f"PostgreSQL enum values: {enum_vals}")
        
        # Check current values
        result = session.execute(text("SELECT id, title, difficulty FROM cases"))
        rows = result.fetchall()
        print("\nCurrent cases:")
        for row in rows:
            print(f"  {row}")
        
        # Check what the Python enum expects
        from app.db.models import DifficultyLevel
        print("\nPython DifficultyLevel enum:")
        for level in DifficultyLevel:
            print(f"  {level.name} = '{level.value}'")
            
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    fix_difficulty()
