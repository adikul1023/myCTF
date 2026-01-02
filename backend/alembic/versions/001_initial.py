"""Initial migration - create all tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types using raw SQL with IF NOT EXISTS
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE difficultylevel AS ENUM ('beginner', 'intermediate', 'advanced', 'expert', 'insane');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE artifacttype AS ENUM ('disk_image', 'memory_dump', 'pcap', 'log_file', 'registry_hive', 'email_archive', 'document', 'executable', 'archive', 'other');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('username', sa.String(64), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('invite_code_used', sa.String(64), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_admin', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)

    # Create invite_codes table
    op.create_table(
        'invite_codes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(64), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False, default=False),
        sa.Column('used_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('max_uses', sa.Integer(), nullable=False, default=1),
        sa.Column('use_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['used_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_invite_codes_code', 'invite_codes', ['code'], unique=True)

    # Create cases table
    op.create_table(
        'cases',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('story_background', sa.Text(), nullable=False),
        sa.Column('investigation_objectives', sa.Text(), nullable=False),
        sa.Column('difficulty', postgresql.ENUM('beginner', 'intermediate', 'advanced', 'expert', 'insane', name='difficultylevel', create_type=False), nullable=False),
        sa.Column('semantic_truth_hash', sa.String(64), nullable=False),
        sa.Column('case_salt', sa.String(64), nullable=False),
        sa.Column('points', sa.Integer(), nullable=False, default=100),
        sa.Column('extra_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_cases_slug', 'cases', ['slug'], unique=True)

    # Create artifacts table
    op.create_table(
        'artifacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('artifact_type', postgresql.ENUM('disk_image', 'memory_dump', 'pcap', 'log_file', 'registry_hive', 'email_archive', 'document', 'executable', 'archive', 'other', name='artifacttype', create_type=False), nullable=False),
        sa.Column('storage_path', sa.String(512), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_hash_sha256', sa.String(64), nullable=False),
        sa.Column('mime_type', sa.String(128), nullable=True),
        sa.Column('extra_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_artifacts_case_id', 'artifacts', ['case_id'])

    # Create submissions table
    op.create_table(
        'submissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('submitted_answer_hash', sa.String(64), nullable=False),  # SHA-256 hash for privacy
        sa.Column('is_correct', sa.Boolean(), nullable=False, default=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(512), nullable=True),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_submissions_user_id', 'submissions', ['user_id'])
    op.create_index('ix_submissions_case_id', 'submissions', ['case_id'])
    op.create_index('ix_submissions_user_case', 'submissions', ['user_id', 'case_id'])
    op.create_index('ix_submissions_correct', 'submissions', ['is_correct'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('submissions')
    op.drop_table('artifacts')
    op.drop_table('cases')
    op.drop_table('invite_codes')
    op.drop_table('users')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS artifacttype')
    op.execute('DROP TYPE IF EXISTS difficultylevel')
