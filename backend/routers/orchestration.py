"""
Orchestration router — SSE streaming endpoint for the LangGraph agentic loop.

POST /api/orchestrate accepts a workspace_id, prompt, and thread_id.
It streams graph execution events as Server-Sent Events and yields
a "paused" event when the HITL interrupt fires.
"""

import json

from fastapi import APIRouter, Request
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from engine.graph import get_compiled_graph

router = APIRouter(prefix="/api", tags=["orchestration"])


class OrchestrateRequest(BaseModel):
    workspace_id: str
    prompt: str
    thread_id: str
    model_alias: str = "gpt-4o"


@router.post("/orchestrate")
async def orchestrate(body: OrchestrateRequest, request: Request):
    """Stream LangGraph execution as SSE, pausing at HITL interrupt."""
    checkpointer = request.app.state.checkpointer
    graph = get_compiled_graph(checkpointer)
    config = {"configurable": {"thread_id": body.thread_id, "model_alias": body.model_alias}}

    async def event_generator():
        try:
            async for event in graph.astream_events(
                {
                    "messages": [("user", body.prompt)],
                    "workspace_id": body.workspace_id,
                },
                config=config,
                version="v2",
            ):
                kind = event.get("event", "")
                name = event.get("name", "")
                yield {
                    "event": "status",
                    "data": json.dumps({"step": f"{kind}: {name}"}),
                }

            # Check if graph is paused at the HITL interrupt
            state = await graph.aget_state(config)
            next_nodes = state.next  # tuple of next node names
            if next_nodes and "action_node" in next_nodes:
                artifact_id = state.values.get("draft_artifact_id", "")
                yield {
                    "event": "paused",
                    "data": json.dumps({
                        "message": "Awaiting human approval",
                        "artifact_id": artifact_id,
                    }),
                }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"message": str(e)}),
            }

        yield {"event": "done", "data": json.dumps({"message": "Stream complete"})}

    return EventSourceResponse(event_generator())
