"""
LangGraph async Postgres checkpointer for SideloadOS.

Provides `get_checkpointer()` which:
  1. Reads DATABASE_URL from the environment.
  2. Strips the `+asyncpg` driver prefix (psycopg requires plain postgresql://).
  3. Creates an AsyncConnectionPool via psycopg_pool.
  4. Returns an (AsyncPostgresSaver, AsyncConnectionPool) tuple.

The caller (main.py lifespan) is responsible for calling
`await checkpointer.setup()` and closing the pool on shutdown.
"""

import os

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


async def get_checkpointer() -> tuple[AsyncPostgresSaver, AsyncConnectionPool]:
    """Initialise and return the LangGraph checkpointer + its connection pool."""
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://sideload:sideload_password@localhost:5434/sideload_db",
    )
    # psycopg requires standard postgresql:// — strip SQLAlchemy's +asyncpg driver
    conninfo = db_url.replace("+asyncpg", "")

    pool = AsyncConnectionPool(
        conninfo=conninfo,
        open=False,
        kwargs={"autocommit": True, "row_factory": dict_row},
    )
    await pool.open()

    checkpointer = AsyncPostgresSaver(pool)
    return checkpointer, pool
