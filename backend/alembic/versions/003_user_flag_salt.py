"""Add time-variant flag salt to users

Revision ID: 003_user_flag_salt
Revises: 002_unlock_and_telemetry
Create Date: 2025-01-01 00:00:03.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import secrets
from datetime import datetime, timezone


# revision identifiers, used by Alembic.
revision = '003_user_flag_salt'
down_revision = '002_unlock_and_telemetry'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure pgcrypto extension exists for random bytes generation
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    
    # Add flag_salt column with a default value
    op.add_column(
        'users',
        sa.Column(
            'flag_salt',
            sa.String(64),
            nullable=True,  # Temporarily nullable for migration
        )
    )
    
    # Add flag_salt_rotated_at column
    op.add_column(
        'users',
        sa.Column(
            'flag_salt_rotated_at',
            sa.DateTime(timezone=True),
            nullable=True,  # Temporarily nullable for migration
        )
    )
    
    # Update existing rows with random salts and current timestamp
    # Using raw SQL for bulk update with random values
    op.execute("""
        UPDATE users 
        SET 
            flag_salt = encode(gen_random_bytes(32), 'hex'),
            flag_salt_rotated_at = NOW()
        WHERE flag_salt IS NULL
    """)
    
    # Now make columns non-nullable
    op.alter_column('users', 'flag_salt', nullable=False)
    op.alter_column('users', 'flag_salt_rotated_at', nullable=False)


def downgrade() -> None:
    op.drop_column('users', 'flag_salt_rotated_at')
    op.drop_column('users', 'flag_salt')
