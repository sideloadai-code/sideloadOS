"""
System tools for the SideloadOS System Orchestrator.

These LangChain @tool functions are designed to run inside the Uvicorn
event loop so they share the global ConnectionManager instance.
"""

import uuid

from langchain_core.tools import tool

from database import AsyncSessionLocal
from models import Workspace
from ws_manager import manager


@tool
async def create_workspace(name: str) -> str:
    """Create a new workspace with the given name."""
    new_id = uuid.uuid4()

    async with AsyncSessionLocal() as session:
        workspace = Workspace(id=new_id, name=name)
        session.add(workspace)
        await session.commit()

    await manager.broadcast({
        "event": "workspace_created",
        "payload": {"id": str(new_id), "name": name},
    })

    return f"Workspace '{name}' created with id {str(new_id)}"
