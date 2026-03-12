"""
Artifact management router.

Prefix: /api/artifacts
Provides retrieval and HITL approval endpoints.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Artifact

router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])


# ── Pydantic Schemas ────────────────────────────────────────────────────────

class ArtifactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    content_type: str
    content: str
    human_edits: Optional[str]
    status: str
    thread_id: Optional[str]
    file_path: Optional[str] = None
    blueprint_path: str


class ApproveRequest(BaseModel):
    human_edits: str


# ── Background Task — isolated resume wrapper (Amendment 4) ─────────────────

async def resume_workflow(checkpointer, thread_id: str, blueprint_path: str = "default.yaml"):
    """Resume a paused LangGraph thread in the background.

    This function is invoked via FastAPI BackgroundTasks so the HTTP
    response returns instantly while the graph continues executing.
    """
    import os
    from engine.blueprint_parser import compile_blueprint

    # Amendment 2: Ghost Cartridge guard — fallback if file was deleted
    safe_blueprint = os.path.basename(blueprint_path)
    target_path = f"/app/blueprints/{safe_blueprint}"
    if not os.path.exists(target_path):
        target_path = "/app/blueprints/default.yaml"
        safe_blueprint = "default.yaml"

    graph = compile_blueprint(target_path, checkpointer)
    # Amendment 3: Inject blueprint_path into configurable dict for future nodes
    await graph.ainvoke(None, {"configurable": {"thread_id": thread_id, "blueprint_path": safe_blueprint}})


# ── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/{artifact_id}", response_model=ArtifactOut)
async def get_artifact(
    artifact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return a single artifact by ID."""
    result = await db.execute(
        select(Artifact).where(Artifact.id == artifact_id)
    )
    artifact = result.scalar_one_or_none()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact


@router.post("/{artifact_id}/approve")
async def approve_artifact(
    artifact_id: uuid.UUID,
    body: ApproveRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Approve an artifact and resume the paused LangGraph thread."""
    # 1. Fetch artifact
    result = await db.execute(
        select(Artifact).where(Artifact.id == artifact_id)
    )
    artifact = result.scalar_one_or_none()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # 2. Apply human edits and update status
    artifact.human_edits = body.human_edits
    artifact.status = "approved"
    await db.commit()

    # 3. Resume the graph in the background (Amendment 4 — no HTTP hang)
    if artifact.thread_id:
        checkpointer = request.app.state.checkpointer
        background_tasks.add_task(
            resume_workflow, checkpointer, artifact.thread_id, artifact.blueprint_path
        )

    return {"status": "resumed"}
