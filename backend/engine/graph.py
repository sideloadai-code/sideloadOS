"""
SideloadOS LangGraph workflow — the core agentic loop with Master Router.

Graph flow:
              ┌──► workspace_node ──► END
              │
START ──► supervisor_node ──┼──► draft_node ──► [INTERRUPT] ──► action_node ──► END
              │
              └──► chat_node ──► END

The supervisor_node uses JSON-in-prompt to route requests. The graph is
compiled with interrupt_before=["action_node"] so that draft_node triggers
a HITL pause, while workspace_node and chat_node complete autonomously.
"""

import uuid
import json as json_mod
import re
from typing import Literal, Optional


from sqlalchemy import select
from pydantic import BaseModel, Field

from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables.config import RunnableConfig

from database import AsyncSessionLocal
from models import Artifact, Workspace
from engine.fs_tools import write_artifact_to_disk
from engine.state import SideloadState
from engine.rag import ingest_workspace, search_workspace
from gateway import get_llm
from agents.tools import create_workspace


# ── Pydantic schemas for structured LLM output ─────────────────────────────

class DraftOutput(BaseModel):
    title: str = Field(description="A short 3-5 word title for the artifact")
    content_type: Literal["text", "code"] = Field(
        description="Must be exactly 'text' or 'code'"
    )
    content: str = Field(
        description="The actual generated text or code. "
        "Do not wrap in markdown blocks if it is code."
    )


class SupervisorDecision(BaseModel):
    decision: Literal["create_workspace", "draft_artifact", "chat", "ingest_workspace", "rag_search"]
    tool_kwargs: Optional[dict] = Field(default_factory=dict)
    chat_response: Optional[str] = None


# ── JSON extraction helper ──────────────────────────────────────────────────

def _extract_json(text: str) -> str:
    """Extract a JSON object from LLM text, stripping markdown fences if present."""
    # Try to find a ```json ... ``` block first
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Otherwise try to find a raw { ... } block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0).strip()
    return text.strip()


# ── System prompts ──────────────────────────────────────────────────────────

_DRAFT_PROMPT = (
    "You are an expert AI orchestrator. Draft the requested artifact.\n"
    "You MUST respond with ONLY a valid JSON object (no markdown, no extra text) "
    "matching this exact schema:\n"
    "{\n"
    '  "title": "A short 3-5 word title",\n'
    '  "content_type": "text" or "code",\n'
    '  "content": "The actual generated text or code"\n'
    "}\n"
    "For code, output raw code in the content field without markdown backticks.\n"
    "Do NOT include any text before or after the JSON object."
)

_SUPERVISOR_PROMPT = (
    "You are the SideloadOS Master Router. Analyze the user's request.\n"
    "Output ONLY raw JSON matching this schema:\n"
    "{\n"
    '  "decision": "create_workspace" | "draft_artifact" | "chat" | "ingest_workspace" | "rag_search",\n'
    '  "tool_kwargs": { ... } or null,\n'
    '  "chat_response": "..." or null\n'
    "}\n"
    "Rules:\n"
    "- If the user wants to create a workspace, select 'create_workspace' "
    "and set tool_kwargs to {\"name\": \"<workspace_name>\"}.\n"
    "- If the user asks to write code, a document, or any artifact, "
    "select 'draft_artifact'. Leave tool_kwargs and chat_response null.\n"
    "- If the user asks you to read, memorize, sync, or ingest the workspace, "
    "select 'ingest_workspace'. Leave tool_kwargs and chat_response null.\n"
    "- If the user asks a question about existing files or code in the workspace, "
    "select 'rag_search' and set tool_kwargs to {\"query\": \"their specific search query\"}.\n"
    "- Otherwise, select 'chat' and write a friendly response in chat_response.\n"
    "Do NOT include any text before or after the JSON object."
)


# ── Graph Nodes ─────────────────────────────────────────────────────────────

async def supervisor_node(state: SideloadState, config: RunnableConfig) -> dict:
    """Route the user's request to the appropriate execution path."""
    model_alias = config.get("configurable", {}).get("model_alias", "openai")

    # SESSION: fetch LLM — then RELEASE before network call
    async with AsyncSessionLocal() as session:
        llm = await get_llm(model_alias, session)

    # Invoke with supervisor prompt + user messages
    messages = [SystemMessage(content=_SUPERVISOR_PROMPT)] + state["messages"]
    ai_message = await llm.ainvoke(messages)

    raw_text = ai_message.content if hasattr(ai_message, "content") else str(ai_message)
    json_str = _extract_json(raw_text)

    try:
        parsed = SupervisorDecision.model_validate_json(json_str)
    except Exception:
        # Amendment 3: graceful fallback on LLM parse failure
        return {
            "next_route": "chat",
            "chat_response": "I encountered an internal error routing your request. Please try again.",
            "tool_kwargs": {},
        }

    return {
        "next_route": parsed.decision,
        "tool_kwargs": parsed.tool_kwargs,
        "chat_response": parsed.chat_response,
    }


async def draft_node(state: SideloadState, config: RunnableConfig) -> dict:
    """Use LLM with JSON-in-prompt to draft a real artifact."""
    new_id = uuid.uuid4()
    thread_id = config.get("configurable", {}).get("thread_id")
    model_alias = config.get("configurable", {}).get("model_alias", "openai")
    blueprint_path = config.get("configurable", {}).get("blueprint_path", "default.yaml")

    # SESSION 1: Fetch the LLM instance (quick DB read) — then RELEASE
    async with AsyncSessionLocal() as session:
        llm = await get_llm(model_alias, session)

    # OUTSIDE any session: Call the LLM (15-30s network request)
    messages = [SystemMessage(content=_DRAFT_PROMPT)] + state["messages"]
    ai_message = await llm.ainvoke(messages)

    # Parse the JSON response into our Pydantic schema
    raw_text = ai_message.content if hasattr(ai_message, "content") else str(ai_message)
    json_str = _extract_json(raw_text)
    response = DraftOutput.model_validate_json(json_str)

    # SESSION 2: Persist the real generated artifact — then RELEASE
    async with AsyncSessionLocal() as session:
        artifact = Artifact(
            id=new_id,
            task_id=None,
            title=response.title,
            content_type=response.content_type,
            content=response.content,
            status="draft",
            thread_id=thread_id,
            blueprint_path=blueprint_path,
        )
        session.add(artifact)
        await session.commit()

    return {"draft_artifact_id": str(new_id)}


async def workspace_node(state: SideloadState) -> dict:
    """Execute the create_workspace tool autonomously."""
    # Amendment 1: guard against None — .get() returns None if key exists with None value
    kwargs = state.get("tool_kwargs") or {}
    result = await create_workspace.ainvoke(kwargs)
    return {"messages": [AIMessage(content=str(result))]}


async def chat_node(state: SideloadState) -> dict:
    """Surface the supervisor's pre-generated chat response."""
    return {"messages": [AIMessage(content=state.get("chat_response") or "Acknowledged.")]}


async def action_node(state: SideloadState) -> dict:
    """Act on the approved draft — write artifact to disk and update status."""
    artifact_id = state.get("draft_artifact_id")
    workspace_id = state.get("workspace_id")

    # Amendment 2: return error message instead of silent {}
    if not artifact_id or not workspace_id:
        return {
            "messages": [
                AIMessage(content="Error: Could not write to disk. Missing workspace or artifact context.")
            ]
        }

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Artifact).where(Artifact.id == uuid.UUID(artifact_id))
        )
        artifact = result.scalar_one_or_none()

        result = await session.execute(
            select(Workspace).where(Workspace.id == uuid.UUID(workspace_id))
        )
        workspace = result.scalar_one_or_none()

        # Amendment 2: return error message instead of silent {}
        if not artifact or not workspace:
            return {
                "messages": [
                    AIMessage(content="Error: Could not write to disk. Artifact or workspace not found in database.")
                ]
            }

        # Amendment 1: explicit None check — empty string "" is a valid user intent
        final_content = artifact.human_edits if artifact.human_edits is not None else artifact.content

        file_path = await write_artifact_to_disk(
            workspace.name, artifact.title, final_content, artifact.content_type
        )

        artifact.status = "applied"
        artifact.file_path = file_path
        await session.commit()

    return {
        "messages": [
            AIMessage(content=f"Successfully wrote {artifact.title} to disk at {file_path}")
        ]
    }


async def ingest_node(state: SideloadState) -> dict:
    """Ingest all workspace files into pgvector for semantic search."""
    workspace_id = state.get("workspace_id")
    if not workspace_id:
        return {"chat_response": "Error: No workspace selected."}
    result = await ingest_workspace(workspace_id)
    return {"chat_response": result}


async def rag_node(state: SideloadState, config: RunnableConfig) -> dict:
    """Retrieve relevant workspace context via cosine similarity and answer with LLM."""
    workspace_id = state.get("workspace_id")
    if not workspace_id:
        return {"chat_response": "Error: No workspace selected."}

    # Extract query from tool_kwargs (set by supervisor) or fall back to last message
    query = (state.get("tool_kwargs") or {}).get(
        "query", state["messages"][-1].content
    )

    context = await search_workspace(workspace_id, query)

    model_alias = config.get("configurable", {}).get("model_alias", "openai")

    # SESSION: fetch LLM — then RELEASE before network call
    async with AsyncSessionLocal() as session:
        llm = await get_llm(model_alias, session)

    system_msg = SystemMessage(
        content=(
            "You are SideloadOS. Answer the user's query using ONLY this "
            "workspace context:\n\n"
            f"{context}\n\n"
            "If the answer isn't in the context, say so."
        )
    )
    ai_message = await llm.ainvoke([system_msg] + state["messages"])

    raw = ai_message.content if hasattr(ai_message, "content") else str(ai_message)
    return {"chat_response": raw}


def route_from_supervisor(state: SideloadState) -> str:
    """Return the next node name based on the supervisor's decision."""
    return state.get("next_route") or "chat"
