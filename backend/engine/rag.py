"""
rag.py — Deep Semantic Memory for SideloadOS.

Provides workspace ingestion (file → vector embeddings) and
semantic search (cosine similarity retrieval) using pgvector
and a locally-hosted HuggingFace embedding model.

The embedder is lazy-loaded to avoid blocking the FastAPI event loop
during server startup.
"""

import os
import uuid
import asyncio

from sqlalchemy import select, delete

from database import AsyncSessionLocal
from models import DocumentChunk, Workspace
from engine.fs_tools import _sanitize

# ── Lazy-loaded Embedder (Amendment 2) ──────────────────────────────────────

_embedder = None


def get_embedder():
    """Lazy-initialize the HuggingFace embedding model on first use."""
    global _embedder
    if _embedder is None:
        from langchain_huggingface import HuggingFaceEmbeddings
        _embedder = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return _embedder


def _embed_docs(chunks: list[str]) -> list[list[float]]:
    """Thread-safe helper: embed a list of document chunks."""
    return get_embedder().embed_documents(chunks)


def _embed_query(query: str) -> list[float]:
    """Thread-safe helper: embed a single search query."""
    return get_embedder().embed_query(query)


# ── Text Splitter (Amendment 4) ─────────────────────────────────────────────

from langchain_text_splitters import RecursiveCharacterTextSplitter

_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

# ── Supported file extensions for ingestion ─────────────────────────────────

_INGEST_EXTENSIONS = {".py", ".md", ".txt"}


# ── Core Functions ──────────────────────────────────────────────────────────

async def ingest_workspace(workspace_id: str) -> str:
    """Walk a workspace directory, chunk files, embed them, and store in pgvector.

    Returns a summary string describing how many chunks were ingested.
    """
    # Fetch workspace name from DB
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Workspace).where(Workspace.id == uuid.UUID(workspace_id))
        )
        workspace = result.scalar_one_or_none()

    if not workspace:
        return "Error: Workspace not found in database."

    safe_name = _sanitize(workspace.name)
    workspace_dir = f"/app/workspaces/{safe_name}"

    if not os.path.isdir(workspace_dir):
        return f"No workspace directory found at {workspace_dir}. Write some files first."

    # Collect text from supported files
    all_chunks: list[str] = []
    all_filenames: list[str] = []
    file_count = 0

    for root, _dirs, files in os.walk(workspace_dir):
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in _INGEST_EXTENSIONS:
                continue

            filepath = os.path.join(root, fname)
            # Amendment 3: Force UTF-8, ignore encoding errors
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

            if not text.strip():
                continue

            file_count += 1
            chunks = _splitter.split_text(text)
            for chunk in chunks:
                all_chunks.append(chunk)
                all_filenames.append(fname)

    # Amendment 4: Guard against empty chunks
    if not all_chunks:
        return "No valid text files found to ingest."

    # Embed all chunks in a background thread (non-blocking)
    embeddings = await asyncio.to_thread(_embed_docs, all_chunks)

    # Persist to database
    async with AsyncSessionLocal() as session:
        # Delete existing chunks for this workspace (dedup)
        await session.execute(
            delete(DocumentChunk).where(
                DocumentChunk.workspace_id == workspace_id
            )
        )

        # Bulk-insert new chunks
        for i, (chunk, filename, embedding) in enumerate(
            zip(all_chunks, all_filenames, embeddings)
        ):
            session.add(DocumentChunk(
                workspace_id=workspace_id,
                filename=filename,
                content=chunk,
                embedding=embedding,
            ))

        await session.commit()

    return (
        f"Successfully ingested {len(all_chunks)} chunks "
        f"from {file_count} files into Deep Memory."
    )


async def search_workspace(workspace_id: str, query: str) -> str:
    """Perform cosine-similarity search on ingested workspace chunks.

    Returns formatted context string of top-5 results.
    """
    # Embed the query in a background thread
    query_embedding = await asyncio.to_thread(_embed_query, query)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(DocumentChunk)
            .where(DocumentChunk.workspace_id == workspace_id)
            .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
            .limit(5)
        )
        rows = result.scalars().all()

    if not rows:
        return "No relevant documents found in memory."

    # Format results for LLM context
    context_parts = []
    for row in rows:
        context_parts.append(f"[{row.filename}]:\n{row.content}")

    return "\n\n---\n\n".join(context_parts)
