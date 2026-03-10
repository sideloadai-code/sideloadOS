"""add_file_path

Revision ID: bdef0ebd81c8
Revises: c108cb3250c0
Create Date: 2026-03-10 22:30:17.264776

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bdef0ebd81c8'
down_revision: Union[str, Sequence[str], None] = 'c108cb3250c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('artifacts', sa.Column('file_path', sa.String(length=512), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('artifacts', 'file_path')
