"""add_thread_id_to_artifacts

Revision ID: 6cfd3da45f49
Revises: 89505e02b013
Create Date: 2026-03-10 14:13:51.480463

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6cfd3da45f49'
down_revision: Union[str, Sequence[str], None] = '89505e02b013'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('artifacts', sa.Column('thread_id', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('artifacts', 'thread_id')

