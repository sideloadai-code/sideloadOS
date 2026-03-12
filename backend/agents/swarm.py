"""
Multi-Agent Swarm — Architect → Developer → QA autonomous coding pipeline.

This module defines three LangGraph async nodes and a conditional router
for the Software Engineering Swarm cartridge. The swarm autonomously
debates code quality before surfacing a draft artifact for human approval.

The nodes reuse SideloadOS infrastructure (AsyncSessionLocal, get_llm,
Artifact model) and are wired into a graph topology via the
software_engineer.yaml blueprint.
"""

import re
import uuid
import json

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables.config import RunnableConfig

from database import AsyncSessionLocal
from models import Artifact
from gateway import get_llm
from engine.state import SideloadState
from engine.graph import _extract_json
from engine.sandbox import run_in_sandbox


# ── System prompts (static — never interpolated with user data) ─────────────

_ARCHITECT_PROMPT = (
    "You are the Principal Architect. Analyze the user request. "
    "Write a strict technical specification and step-by-step implementation plan. "
    "Output only the spec."
)

_DEVELOPER_PROMPT = (
    "You are the Lead Developer. Write the complete code based exactly on "
    "the provided specification. Output ONLY raw code (no markdown backticks). "
    "If QA provided feedback, incorporate all fixes."
)

_QA_PROMPT = (
    "You are the QA Tester. Review the provided Code against the Spec AND the "
    "Sandbox Terminal Output. If the Sandbox Terminal Output shows a Traceback, "
    "Exception, SyntaxError, or failed execution, you MUST fail the code "
    "(pass: false) and explain the error to the Developer so they can fix it. "
    'Respond ONLY in raw JSON: {"pass": true/false, "feedback": "explain why", '
    '"title": "A short 3-5 word title for this file"}. '
    "Do NOT include any text before or after the JSON object."
)


# ── Swarm Nodes ─────────────────────────────────────────────────────────────

async def architect_node(state: SideloadState, config: RunnableConfig) -> dict:
    """Principal Architect — reads user messages, outputs a technical spec."""
    model_alias = config.get("configurable", {}).get("model_alias", "openai")

    # SESSION: fetch LLM — then RELEASE before network call
    async with AsyncSessionLocal() as session:
        llm = await get_llm(model_alias, session)

    # Invoke with full conversation context
    messages = [SystemMessage(content=_ARCHITECT_PROMPT)] + state["messages"]
    ai_message = await llm.ainvoke(messages)

    raw_text = ai_message.content if hasattr(ai_message, "content") else str(ai_message)

    # Amendment 1: RESET all swarm state to prevent Residual State Loop Trap
    return {
        "tech_spec": raw_text,
        "swarm_iterations": 0,
        "code_draft": None,
        "qa_feedback": None,
        "draft_artifact_id": None,
        "execution_logs": None,
    }


async def developer_node(state: SideloadState, config: RunnableConfig) -> dict:
    """Lead Developer — writes code from spec, incorporates QA feedback."""
    model_alias = config.get("configurable", {}).get("model_alias", "openai")

    # SESSION: fetch LLM — then RELEASE before network call
    async with AsyncSessionLocal() as session:
        llm = await get_llm(model_alias, session)

    # Amendment 2: NO f-strings — inject data via HumanMessage concatenation
    # Amendment 4: Include state["messages"] for full conversation context
    data_message = HumanMessage(
        content="Spec:\n" + str(state.get("tech_spec"))
        + "\n\nQA Feedback:\n" + str(state.get("qa_feedback", "None"))
    )
    messages = [SystemMessage(content=_DEVELOPER_PROMPT)] + state["messages"] + [data_message]
    ai_message = await llm.ainvoke(messages)

    raw_text = ai_message.content if hasattr(ai_message, "content") else str(ai_message)
    return {"code_draft": raw_text}


async def execution_node(state: SideloadState, config: RunnableConfig) -> dict:
    """Execution Sandbox — runs the Developer's code in a secure Docker container."""
    code = state.get("code_draft")
    if not code:
        return {"execution_logs": "No code provided."}

    # Amendment 2: Strip markdown backticks before execution
    clean_code = code.strip()
    if clean_code.startswith("```"):
        clean_code = re.sub(r"^```[a-zA-Z]*\n", "", clean_code)
        clean_code = re.sub(r"\n```$", "", clean_code)

    logs = await run_in_sandbox(clean_code)
    return {"execution_logs": logs}


async def qa_node(state: SideloadState, config: RunnableConfig) -> dict:
    """QA Tester — reviews code against spec, returns pass/fail JSON."""
    model_alias = config.get("configurable", {}).get("model_alias", "openai")
    thread_id = config.get("configurable", {}).get("thread_id")
    blueprint_path = config.get("configurable", {}).get("blueprint_path", "software_engineer.yaml")

    # SESSION: fetch LLM — then RELEASE before network call
    async with AsyncSessionLocal() as session:
        llm = await get_llm(model_alias, session)

    # Amendment 2: NO f-strings — inject data via HumanMessage concatenation
    # Amendment 4: Include state["messages"] for full conversation context
    data_message = HumanMessage(
        content="Code:\n" + str(state.get("code_draft"))
        + "\n\nSpec:\n" + str(state.get("tech_spec"))
        + "\n\nSandbox Terminal Output:\n" + str(state.get("execution_logs"))
    )
    messages = [SystemMessage(content=_QA_PROMPT)] + state["messages"] + [data_message]
    ai_message = await llm.ainvoke(messages)

    raw_text = ai_message.content if hasattr(ai_message, "content") else str(ai_message)

    # Parse the JSON response safely
    try:
        json_str = _extract_json(raw_text)
        parsed_json = json.loads(json_str)
    except Exception:
        # Amendment 3: FAIL CLOSED — force rejection on parse failure
        parsed_json = {
            "pass": False,
            "title": "Generated Script",
            "feedback": "CRITICAL: QA Node failed to output valid JSON. "
                        "Please fix the code and I will evaluate again.",
        }

    iterations = state.get("swarm_iterations", 0) + 1

    # CRITICAL LOOP GUARD: force approval after 3 iterations
    if iterations >= 3:
        parsed_json["pass"] = True
        feedback = parsed_json.get("feedback", "")
        parsed_json["feedback"] = feedback + " Max iterations reached."

    qa_pass = parsed_json.get("pass", False)
    feedback = parsed_json.get("feedback", "")
    title = parsed_json.get("title", "Generated Script")

    if qa_pass:
        # Create the draft artifact in the database
        new_id = uuid.uuid4()

        # Amendment 4: proper context manager — no DB connection leaks
        async with AsyncSessionLocal() as session:
            artifact = Artifact(
                id=new_id,
                task_id=None,
                title=title,
                content_type="code",
                content=state.get("code_draft", ""),
                status="draft",
                thread_id=thread_id,
                blueprint_path=blueprint_path,
            )
            session.add(artifact)
            await session.commit()

        return {
            "qa_feedback": feedback,
            "swarm_iterations": iterations,
            "draft_artifact_id": str(new_id),
        }

    # QA rejected — loop back to developer
    return {
        "qa_feedback": feedback,
        "swarm_iterations": iterations,
    }


# ── Conditional edge router ────────────────────────────────────────────────

def route_qa(state: SideloadState) -> str:
    """Route to action_node on QA pass, or back to developer_node on rejection."""
    return "action_node" if state.get("draft_artifact_id") else "developer_node"
