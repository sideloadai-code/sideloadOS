"""
Execution Sandbox — secure, air-gapped Docker container for running AI-generated code.

Uses the sibling container pattern: the FastAPI container talks to the *host*
Docker daemon via the mounted socket.  Sandbox containers run alongside it,
not inside it.

Security features:
  - network_mode="none"  → blocks all internet access (air-gapped)
  - mem_limit="128m"     → prevents fork bombs / memory exhaustion
  - timeout=10           → kills runaway loops
  - environment variable code injection → avoids shell-escaping traps

Amendment 1: try/finally guarantees container cleanup even on SDK errors.
Amendment 3: log truncation caps output at 2000 chars to protect LLM context.
"""

import asyncio
import logging

import docker

logger = logging.getLogger(__name__)

_MAX_LOG_CHARS = 2000


def _run_in_docker(code: str) -> str:
    """Synchronous helper — runs code inside a disposable Python container."""
    client = docker.from_env()
    container = None

    try:
        container = client.containers.run(
            "python:3.12-slim",
            command=["python", "-c", "import os\nexec(os.environ.get('CODE', ''))"],
            environment={"CODE": code},
            network_mode="none",
            mem_limit="128m",
            detach=True,
        )

        try:
            result = container.wait(timeout=10)
        except Exception:
            container.kill()
            logs = container.logs(stdout=True, stderr=True).decode(
                "utf-8", errors="replace"
            )
            # Amendment 3: truncate before returning
            if len(logs) > _MAX_LOG_CHARS:
                logs = "...[TRUNCATED]...\n" + logs[-_MAX_LOG_CHARS:]
            return (
                f"Execution Failed: Code timed out after 10 seconds.\n"
                f"Partial Logs:\n{logs}"
            )

        logs = container.logs(stdout=True, stderr=True).decode(
            "utf-8", errors="replace"
        )
        # Amendment 3: truncate before returning
        if len(logs) > _MAX_LOG_CHARS:
            logs = "...[TRUNCATED]...\n" + logs[-_MAX_LOG_CHARS:]

        if result.get("StatusCode", 0) != 0:
            return (
                f"Execution Failed (Exit Code {result.get('StatusCode')}):\n"
                f"Terminal Output:\n{logs}"
            )
        return f"Execution Success.\nTerminal Output:\n{logs}"

    except Exception as e:
        return f"Sandbox Infrastructure Error: {str(e)}"

    finally:
        # Amendment 1: GUARANTEE container destruction
        if container:
            try:
                container.remove(force=True)
            except Exception:
                pass


async def run_in_sandbox(code: str) -> str:
    """Async wrapper — prevents the synchronous Docker SDK from blocking
    the FastAPI event loop by offloading to a thread."""
    return await asyncio.to_thread(_run_in_docker, code)
