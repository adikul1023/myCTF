"""Add case dependencies, artifact unlock conditions, and telemetry

Revision ID: 002_unlock_and_telemetry
Revises: 001_initial
Create Date: 2025-01-01 00:00:02.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = '002_unlock_and_telemetry'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE unlockconditiontype AS ENUM (
                'case_solved',
                'artifact_downloaded',
                'time_based',
                'points_threshold',
                'manual'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE telemetryeventtype AS ENUM (
                'case_viewed',
                'case_started',
                'artifact_downloaded',
                'submission_attempt',
                'case_solved',
                'artifact_unlocked',
                'case_unlocked'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create case_dependencies table
    op.create_table(
        'case_dependencies',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('case_id', UUID(as_uuid=True), sa.ForeignKey('cases.id', ondelete='CASCADE'), nullable=False),
        sa.Column('required_case_id', UUID(as_uuid=True), sa.ForeignKey('cases.id', ondelete='CASCADE'), nullable=False),
        sa.Column('required_artifact_id', UUID(as_uuid=True), sa.ForeignKey('artifacts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('lock_reason', sa.String(512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint('case_id', 'required_case_id', name='uq_case_dependency'),
    )
    
    op.create_index('ix_case_dependencies_case', 'case_dependencies', ['case_id'])
    op.create_index('ix_case_dependencies_required', 'case_dependencies', ['required_case_id'])
    
    # Create artifact_unlock_conditions table using raw SQL to avoid enum conflicts
    op.execute("""
        CREATE TABLE artifact_unlock_conditions (
            id UUID PRIMARY KEY,
            artifact_id UUID NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,
            condition_type unlockconditiontype NOT NULL,
            required_case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
            required_artifact_id UUID REFERENCES artifacts(id) ON DELETE CASCADE,
            unlock_at TIMESTAMP WITH TIME ZONE,
            required_points INTEGER,
            description VARCHAR(512),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
        )
    """)
    
    op.create_index('ix_artifact_unlock_artifact', 'artifact_unlock_conditions', ['artifact_id'])
    op.create_index('ix_artifact_unlock_type', 'artifact_unlock_conditions', ['condition_type'])
    
    # Create user_artifact_downloads table
    op.create_table(
        'user_artifact_downloads',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('artifact_id', UUID(as_uuid=True), sa.ForeignKey('artifacts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('first_downloaded_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('download_count', sa.Integer, default=1, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint('user_id', 'artifact_id', name='uq_user_artifact_download'),
    )
    
    op.create_index('ix_user_artifact_downloads_user', 'user_artifact_downloads', ['user_id'])
    op.create_index('ix_user_artifact_downloads_artifact', 'user_artifact_downloads', ['artifact_id'])
    
    # Create telemetry_events table using raw SQL to avoid enum conflicts
    op.execute("""
        CREATE TABLE telemetry_events (
            id UUID PRIMARY KEY,
            event_type telemetryeventtype NOT NULL,
            user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            case_id UUID REFERENCES cases(id) ON DELETE SET NULL,
            artifact_id UUID REFERENCES artifacts(id) ON DELETE SET NULL,
            was_successful BOOLEAN,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            extra_data JSONB
        )
    """)
    
    op.create_index('ix_telemetry_events_event_type', 'telemetry_events', ['event_type'])
    op.create_index('ix_telemetry_events_user_id', 'telemetry_events', ['user_id'])
    op.create_index('ix_telemetry_events_case_id', 'telemetry_events', ['case_id'])
    op.create_index('ix_telemetry_events_artifact_id', 'telemetry_events', ['artifact_id'])
    op.create_index('ix_telemetry_events_created_at', 'telemetry_events', ['created_at'])
    op.create_index('ix_telemetry_type_created', 'telemetry_events', ['event_type', 'created_at'])
    op.create_index('ix_telemetry_case_type', 'telemetry_events', ['case_id', 'event_type'])
    
    # Create manual_unlocks table
    op.create_table(
        'manual_unlocks',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('artifact_id', UUID(as_uuid=True), sa.ForeignKey('artifacts.id', ondelete='CASCADE'), nullable=True),
        sa.Column('case_id', UUID(as_uuid=True), sa.ForeignKey('cases.id', ondelete='CASCADE'), nullable=True),
        sa.Column('granted_by', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reason', sa.String(512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    op.create_index('ix_manual_unlocks_user', 'manual_unlocks', ['user_id'])
    op.create_index('ix_manual_unlocks_artifact', 'manual_unlocks', ['artifact_id'])
    op.create_index('ix_manual_unlocks_case', 'manual_unlocks', ['case_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('manual_unlocks')
    op.drop_table('telemetry_events')
    op.drop_table('user_artifact_downloads')
    op.drop_table('artifact_unlock_conditions')
    op.drop_table('case_dependencies')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS telemetryeventtype')
    op.execute('DROP TYPE IF EXISTS unlockconditiontype')
