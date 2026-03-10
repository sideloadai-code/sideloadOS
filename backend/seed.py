"""
Seed script — inserts a single test workspace to unblock UI verification.

Usage: python seed.py  (inside the backend container or venv)
"""

import asyncio

from database import AsyncSessionLocal
from models import Workspace


async def seed():
    async with AsyncSessionLocal() as session:
        ws = Workspace(name="Test Workspace")
        session.add(ws)
        await session.commit()
        print(f"Seeded workspace: {ws.id}")


if __name__ == "__main__":
    asyncio.run(seed())
