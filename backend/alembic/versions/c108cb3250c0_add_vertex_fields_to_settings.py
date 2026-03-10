"""add_vertex_fields_to_settings

Revision ID: c108cb3250c0
Revises: 6cfd3da45f49
Create Date: 2026-03-10 21:26:50.902108

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c108cb3250c0'
down_revision: Union[str, Sequence[str], None] = '6cfd3da45f49'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add vertex_project and vertex_location columns to settings table."""
    op.add_column('settings', sa.Column('vertex_project', sa.String(length=255), nullable=True))
    op.add_column('settings', sa.Column('vertex_location', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Remove vertex columns from settings table."""
    op.drop_column('settings', 'vertex_location')
    op.drop_column('settings', 'vertex_project')
