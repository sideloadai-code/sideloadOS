"""
Provider API key management router.

Prefix: /api/settings
Stores AES-256 (Fernet) encrypted API keys in the settings table.
Vertex AI uses Application Default Credentials (ADC) — no key stored.
"""

import os
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Setting
from security import encrypt_api_key, decrypt_api_key

router = APIRouter(prefix="/api/settings", tags=["settings"])


# ── Pydantic Schemas ────────────────────────────────────────────────────────

class ProviderKeyCreate(BaseModel):
    provider_name: str
    api_key: str
    vertex_project: Optional[str] = None
    vertex_location: Optional[str] = None


class ProviderKeyOut(BaseModel):
    id: uuid.UUID
    provider_name: str
    is_configured: bool

    class Config:
        from_attributes = True


# ── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/", response_model=List[ProviderKeyOut])
async def list_providers(db: AsyncSession = Depends(get_db)):
    """List all configured providers. Never exposes raw API keys."""
    result = await db.execute(select(Setting))
    settings = result.scalars().all()
    return [
        ProviderKeyOut(
            id=s.id,
            provider_name=s.provider_name,
            is_configured=bool(s.encrypted_api_key),
        )
        for s in settings
    ]


@router.post("/", response_model=ProviderKeyOut, status_code=200)
async def upsert_provider_key(
    payload: ProviderKeyCreate,
    db: AsyncSession = Depends(get_db),
):
    """Save or update an encrypted provider API key."""
    result = await db.execute(
        select(Setting).where(Setting.provider_name == payload.provider_name)
    )
    setting = result.scalar_one_or_none()

    encrypted = encrypt_api_key(payload.api_key)

    if setting:
        setting.encrypted_api_key = encrypted
        setting.vertex_project = payload.vertex_project
        setting.vertex_location = payload.vertex_location
    else:
        setting = Setting(
            id=uuid.uuid4(),
            provider_name=payload.provider_name,
            encrypted_api_key=encrypted,
            vertex_project=payload.vertex_project,
            vertex_location=payload.vertex_location,
        )
        db.add(setting)

    await db.commit()
    await db.refresh(setting)

    return ProviderKeyOut(
        id=setting.id,
        provider_name=setting.provider_name,
        is_configured=True,
    )


@router.delete("/{provider_name}", status_code=200)
async def delete_provider_key(
    provider_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Remove a provider's stored API key."""
    result = await db.execute(
        select(Setting).where(Setting.provider_name == provider_name)
    )
    setting = result.scalar_one_or_none()
    if not setting:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")

    await db.execute(
        delete(Setting).where(Setting.provider_name == provider_name)
    )
    await db.commit()
    return {"detail": f"Provider '{provider_name}' deleted"}


@router.post("/{provider_name}/test", status_code=200)
async def test_provider_key(
    provider_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Decrypt the stored key and make a lightweight litellm ping to verify it works."""
    import litellm

    # Map provider → a cheap model for the ping
    test_models = {
        "openai": "gpt-4o-mini",
        "anthropic": "claude-3-haiku-20240307",
        "vertex_ai": "vertex_ai/gemini-2.0-flash",
    }
    model = test_models.get(provider_name)

    # ── Vertex AI uses ADC (no DB key needed) ───────────────────────────
    if provider_name == "vertex_ai":
        if not model:
            return {"detail": "No test model for vertex_ai"}
        try:
            response = await litellm.acompletion(
                model=model,
                messages=[{"role": "user", "content": "Say 'ok'"}],
                vertex_project=os.getenv("VERTEXAI_PROJECT"),
                vertex_location=os.getenv("VERTEXAI_LOCATION", "global"),
                max_tokens=5,
            )
            return {"detail": "ADC credentials are valid", "model_tested": model}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Vertex AI test failed: {str(e)}")

    # ── Standard providers (key from DB) ────────────────────────────────
    result = await db.execute(
        select(Setting).where(Setting.provider_name == provider_name)
    )
    setting = result.scalar_one_or_none()
    if not setting:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")

    decrypted_key = decrypt_api_key(setting.encrypted_api_key)

    if not model:
        return {"detail": f"No test model configured for provider '{provider_name}', but key decrypted successfully"}

    try:
        response = await litellm.acompletion(
            model=model,
            messages=[{"role": "user", "content": "Say 'ok'"}],
            api_key=decrypted_key,
            max_tokens=5,
        )
        return {"detail": "Key is valid", "model_tested": model}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Key test failed: {str(e)}")
