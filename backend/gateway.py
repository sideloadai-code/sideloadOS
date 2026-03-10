"""
Universal LLM Gateway for SideloadOS.

Returns instantiated ChatLiteLLM objects (LangChain BaseChatModel)
for direct use in LangGraph nodes.

Supports cloud providers (OpenAI, Anthropic) via encrypted DB keys
and local Ollama models via host.docker.internal:11434.
"""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from langchain_community.chat_models import ChatLiteLLM
import litellm

from models import Setting
from security import decrypt_api_key

# Allow litellm to silently drop unsupported params (e.g. tool_choice for Gemini)
litellm.drop_params = True

# Ollama API base — uses host.docker.internal for Docker container networking
OLLAMA_API_BASE = "http://host.docker.internal:11434"

# ── Provider prefix mappings ────────────────────────────────────────────────

_PREFIX_TO_PROVIDER: dict[str, str] = {
    "gpt": "openai",
    "o1": "openai",
    "o3": "openai",
    "claude": "anthropic",
    "gemini": "gemini",
}


def resolve_provider(model_alias: str) -> str:
    """
    Map a model alias to its provider name.

    Examples:
        "gpt-4o"          → "openai"
        "claude-sonnet-4-20250514" → "anthropic"
        "ollama/llama3"   → "ollama"
    """
    lower = model_alias.lower()

    # Ollama models use explicit prefix
    if lower.startswith("ollama/") or lower.startswith("ollama_chat/"):
        return "ollama"

    # Match by known prefix
    for prefix, provider in _PREFIX_TO_PROVIDER.items():
        if lower.startswith(prefix):
            return provider

    raise ValueError(
        f"Cannot resolve provider for model '{model_alias}'. "
        f"Known prefixes: {list(_PREFIX_TO_PROVIDER.keys())}. "
        f"For local models use the 'ollama/' prefix."
    )


async def get_llm(model_alias: str, db: AsyncSession) -> ChatLiteLLM:
    """
    Resolve a model alias into a ready-to-use ChatLiteLLM instance.

    For LangGraph nodes, call:
        llm = await get_llm("gpt-4o", db)
        result = await llm.ainvoke(messages)

    Args:
        model_alias: The model identifier (e.g. "gpt-4o", "ollama/llama3")
        db: An active async SQLAlchemy session

    Returns:
        An instantiated ChatLiteLLM (LangChain BaseChatModel)
    """
    provider = resolve_provider(model_alias)

    # ── Ollama (local, no key required) ─────────────────────────────────
    if provider == "ollama":
        return ChatLiteLLM(
            model=model_alias,
            api_base=OLLAMA_API_BASE,
        )

    # ── Cloud provider (key from DB) ────────────────────────────────────
    result = await db.execute(
        select(Setting).where(func.lower(Setting.provider_name) == provider)
    )
    setting = result.scalar_one_or_none()

    if not setting:
        raise ValueError(
            f"No API key configured for provider '{provider}'. "
            f"Save one via POST /api/settings/ first."
        )

    decrypted_key = decrypt_api_key(setting.encrypted_api_key)

    return ChatLiteLLM(
        model=model_alias,
        api_key=decrypted_key,
    )
