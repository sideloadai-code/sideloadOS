"""
SideloadState — the LangGraph state schema for the SideloadOS agentic loop.

This TypedDict defines the shape of data flowing through every node in the
StateGraph. The `messages` field uses LangGraph's `add_messages` reducer
for automatic accumulation.
"""

from typing import Annotated, Optional

from typing_extensions import TypedDict

from langgraph.graph.message import AnyMessage, add_messages


class SideloadState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    workspace_id: str
    current_task_id: Optional[str]
    draft_artifact_id: Optional[str]
