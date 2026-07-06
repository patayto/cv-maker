"""add job_fit_evaluations table

Revision ID: f1d96c156609
Revises:
Create Date: 2026-07-05 21:05:23.156546

Baseline migration. Tables that predate Alembic are created by
Base.metadata.create_all() at app startup; this migration adds the
job_fit_evaluations table for databases that already existed before it.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

# revision identifiers, used by Alembic.
revision: str = 'f1d96c156609'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'job_fit_evaluations',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('job_id', sa.Integer(), sa.ForeignKey('jobs.id'), nullable=False),
        sa.Column('technical_skills', sa.Integer(), nullable=False),
        sa.Column('experience_match', sa.Integer(), nullable=False),
        sa.Column('behavioral_fit', sa.Integer(), nullable=False),
        sa.Column('career_alignment', sa.Integer(), nullable=False),
        sa.Column('location_pass', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('overall_score', sa.Integer(), nullable=False),
        sa.Column('verdict', sa.String(length=50), nullable=False),
        sa.Column('key_strengths', ARRAY(sa.String())),
        sa.Column('gaps', ARRAY(sa.String())),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        if_not_exists=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('job_fit_evaluations')
