"""Add challenges table

Revision ID: 004_add_challenges
Revises: 003_user_flag_salt
Create Date: 2026-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = '004_add_challenges'
down_revision = '003_user_flag_salt'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create challenges table
    op.create_table(
        'challenges',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('case_id', UUID(as_uuid=True), sa.ForeignKey('cases.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('semantic_truth', sa.Text(), nullable=False),
        sa.Column('semantic_truth_hash', sa.String(64), nullable=False),
        sa.Column('points', sa.Integer(), nullable=False),
        sa.Column('difficulty', sa.String(50), nullable=False),
        sa.Column('display_order', sa.Integer(), nullable=False),
        sa.Column('hints', JSONB(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Index('ix_challenges_case_id', 'case_id'),
        sa.Index('ix_challenges_display_order', 'case_id', 'display_order'),
    )
    
    # Create user_challenge_submissions table
    op.create_table(
        'user_challenge_submissions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('challenge_id', UUID(as_uuid=True), sa.ForeignKey('challenges.id', ondelete='CASCADE'), nullable=False),
        sa.Column('submitted_flag', sa.Text(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.Column('points_awarded', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Index('ix_user_challenge_submissions_user', 'user_id'),
        sa.Index('ix_user_challenge_submissions_challenge', 'challenge_id'),
        sa.Index('ix_user_challenge_submissions_user_challenge', 'user_id', 'challenge_id'),
    )


def downgrade() -> None:
    op.drop_table('user_challenge_submissions')
    op.drop_table('challenges')
