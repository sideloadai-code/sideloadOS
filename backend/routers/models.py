"""
Model discovery router.

Prefix: /api/models
Returns available cloud + local (Ollama) models.
"""

from typing import List, Optional

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Setting

router = APIRouter(prefix="/api/models", tags=["models"])

# Ollama endpoint — uses host.docker.internal for Docker container networking
OLLAMA_API_BASE = "http://host.docker.internal:11434"
OLLAMA_TAGS_URL = f"{OLLAMA_API_BASE}/api/tags"
OLLAMA_TIMEOUT = 1.5  # seconds


# ── Known cloud models per provider ─────────────────────────────────────────

PROVIDER_MODELS: dict[str, list[str]] = {
    "openai": [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-3.5-turbo",
        "o1-preview",
        "o1-mini",
    ],
    "anthropic": [
        "claude-sonnet-4-20250514",
        "claude-3-5-sonnet-20241022",
        "claude-3-haiku-20240307",
        "claude-3-opus-20240229",
    ],
    "gemini": [
        "gemini/gemini-3.1-pro-preview",
        "gemini/gemini-3-flash-preview",
        "gemini/gemini-3.1-flash-lite-preview",
        "gemini/gemini-2.5-pro",
        "gemini/gemini-2.5-flash",
        "gemini/gemini-2.5-flash-lite",
    ],
}


# ── Pydantic Schemas ────────────────────────────────────────────────────────

class AvailableModel(BaseModel):
    model_alias: str
    provider: str
    source: str  # "cloud" or "ollama"
    size: Optional[str] = None  # populated for Ollama models


# ── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/available", response_model=List[AvailableModel])
async def list_available_models(db: AsyncSession = Depends(get_db)):
    """
    Return a merged list of:
    1. Cloud models from providers that have keys configured in the DB
    2. Local Ollama models (auto-discovered via /api/tags with 1.5s timeout)
    """
    models: list[AvailableModel] = []

    # ── Cloud models from configured providers ──────────────────────────
    result = await db.execute(select(Setting.provider_name))
    configured_providers = {row[0].lower() for row in result.all()}

    for provider, model_list in PROVIDER_MODELS.items():
        if provider in configured_providers:
            for alias in model_list:
                models.append(
                    AvailableModel(
                        model_alias=alias,
                        provider=provider,
                        source="cloud",
                    )
                )

    # ── Local Ollama models (graceful timeout) ──────────────────────────
    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            resp = await client.get(OLLAMA_TAGS_URL)
            resp.raise_for_status()
            data = resp.json()

            for m in data.get("models", []):
                name = m.get("name", "")
                size_bytes = m.get("size")
                size_label = None
                if size_bytes:
                    size_gb = size_bytes / (1024**3)
                    size_label = f"{size_gb:.1f}GB"

                models.append(
                    AvailableModel(
                        model_alias=f"ollama/{name}",
                        provider="ollama",
                        source="ollama",
                        size=size_label,
                    )
                )
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError):
        # Ollama not running or unreachable — gracefully skip
        pass

    return models
