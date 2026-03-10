"""make_task_id_nullable

Revision ID: 89505e02b013
Revises: 1b27bc1f9963
Create Date: 2026-03-10 01:46:14.654118

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '89505e02b013'
down_revision: Union[str, Sequence[str], None] = '1b27bc1f9963'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('artifacts', 'task_id',
               existing_type=sa.UUID(),
               nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('artifacts', 'task_id',
               existing_type=sa.UUID(),
               nullable=False)
