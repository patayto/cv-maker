"""add pdf_path to generated_cover_letters

Revision ID: 4f8b717c4bcc
Revises: f1d96c156609
Create Date: 2026-07-05 21:14:25.882140

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f8b717c4bcc'
down_revision: Union[str, Sequence[str], None] = 'f1d96c156609'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('generated_cover_letters', sa.Column('pdf_path', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('generated_cover_letters', 'pdf_path')
