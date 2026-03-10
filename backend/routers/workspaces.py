"""
Workspace management router.

Prefix: /api/workspaces
"""

import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Workspace

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


# ── Pydantic Schemas ────────────────────────────────────────────────────────

class WorkspaceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    created_at: datetime


# ── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/", response_model=List[WorkspaceOut])
async def list_workspaces(db: AsyncSession = Depends(get_db)):
    """Return all workspaces ordered by creation date."""
    result = await db.execute(select(Workspace).order_by(Workspace.created_at))
    return result.scalars().all()

