"""
fs_tools — Async file-system utilities for SideloadOS.

Writes approved artifact content to /app/workspaces/{workspace}/{filename}.
"""

import os
import re

import aiofiles


def _sanitize(name: str) -> str:
    """Lowercase, replace spaces with underscores, strip non-alphanum chars."""
    name = name.strip().lower().replace(" ", "_")
    name = re.sub(r"[^a-z0-9_\-]", "", name)
    return name or "untitled"


_EXT_MAP = {
    "code": ".py",
    "text": ".md",
}


async def write_artifact_to_disk(
    workspace_name: str,
    title: str,
    content: str,
    content_type: str,
) -> str:
    """Write content to /app/workspaces/<workspace>/<title>.<ext>.

    Returns the absolute file path of the written file.
    """
    safe_ws = _sanitize(workspace_name)
    safe_title = _sanitize(title)
    extension = _EXT_MAP.get(content_type, ".txt")

    dir_path = f"/app/workspaces/{safe_ws}"
    os.makedirs(dir_path, exist_ok=True)

    file_path = f"{dir_path}/{safe_title}{extension}"

    async with aiofiles.open(file_path, mode="w", encoding="utf-8") as f:
        await f.write(content)

    return file_path
