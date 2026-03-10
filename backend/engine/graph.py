"""
SideloadOS LangGraph workflow — the core agentic loop with HITL interrupt.

Graph flow:  START → draft_node → [INTERRUPT] → action_node → END

The graph is compiled with `interrupt_before=["action_node"]` so that
after draft_node produces a draft artifact, execution freezes. The state
is checkpointed to Postgres and a "paused" SSE event is emitted. The
graph waits for a human approval signal (Step 7) to resume into action_node.
"""

import uuid
from typing import Literal

from langgraph.graph import END, START, StateGraph
from sqlalchemy import select
from pydantic import BaseModel, Field

from langchain_core.messages import SystemMessage
from langchain_core.runnables.config import RunnableConfig

from database import AsyncSessionLocal
from models import Artifact
from engine.state import SideloadState
from gateway import get_llm


# ── Pydantic schema for structured LLM output ──────────────────────────────

class DraftOutput(BaseModel):
    title: str = Field(description="A short 3-5 word title for the artifact")
    content_type: Literal["text", "code"] = Field(
        description="Must be exactly 'text' or 'code'"
    )
    content: str = Field(
        description="The actual generated text or code. "
        "Do not wrap in markdown blocks if it is code."
    )
import json as json_mod
import re


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


# ── System prompt that forces JSON output ────────────────────────────────────

_SYSTEM_PROMPT = (
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


async def draft_node(state: SideloadState, config: RunnableConfig) -> dict:
    """Use LLM with JSON-in-prompt to draft a real artifact."""
    new_id = uuid.uuid4()
    thread_id = config.get("configurable", {}).get("thread_id")
    model_alias = config.get("configurable", {}).get("model_alias", "gpt-4o")

    # SESSION 1: Fetch the LLM instance (quick DB read) — then RELEASE
    async with AsyncSessionLocal() as session:
        llm = await get_llm(model_alias, session)

    # OUTSIDE any session: Call the LLM (15-30s network request)
    messages = [SystemMessage(content=_SYSTEM_PROMPT)] + state["messages"]
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
        )
        session.add(artifact)
        await session.commit()

    return {"draft_artifact_id": str(new_id)}


async def action_node(state: SideloadState) -> dict:
    """Act on the approved draft — updates artifact status to 'approved'."""
    artifact_id = state.get("draft_artifact_id")
    if artifact_id:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Artifact).where(Artifact.id == uuid.UUID(artifact_id))
            )
            artifact = result.scalar_one_or_none()
            if artifact:
                artifact.status = "approved"
                await session.commit()
    return {}


def get_compiled_graph(checkpointer):
    """Build and compile the StateGraph with HITL interrupt before action_node."""
    graph = StateGraph(SideloadState)
    graph.add_node("draft_node", draft_node)
    graph.add_node("action_node", action_node)
    graph.add_edge(START, "draft_node")
    graph.add_edge("draft_node", "action_node")
    graph.add_edge("action_node", END)
    return graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["action_node"],
    )
