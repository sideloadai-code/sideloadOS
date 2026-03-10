from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from routers.settings import router as settings_router
from routers.models import router as models_router
from routers.workspaces import router as workspaces_router
from routers.orchestration import router as orchestration_router
from routers.artifacts import router as artifacts_router
from ws_manager import manager
from engine.checkpointer import get_checkpointer


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup: initialise LangGraph checkpointer ──────────────────────────
    checkpointer, pool = await get_checkpointer()
    await checkpointer.setup()  # creates LangGraph's internal checkpoint tables
    app.state.checkpointer = checkpointer
    app.state.checkpointer_pool = pool
    yield
    # ── Shutdown: close the connection pool ──────────────────────────────────
    await pool.close()


app = FastAPI(title="SideloadOS API", lifespan=lifespan)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ─────────────────────────────────────────────────────────────────
app.include_router(settings_router)
app.include_router(models_router)
app.include_router(workspaces_router)
app.include_router(orchestration_router)
app.include_router(artifacts_router)


# ── WebSocket ───────────────────────────────────────────────────────────────
@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
