<div align="center">

# 🌌 SideloadOS

### The Universal AI Operating System

*A stateful, human-in-the-loop execution engine for declarative AI workflows.*

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![LiteLLM](https://img.shields.io/badge/LiteLLM-FF6F00?style=for-the-badge&logoColor=white)](https://litellm.ai/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

---

**SideloadOS is the console. Blueprints are the cartridges.**

</div>

---

## 🔭 The Vision

Most AI tools are disposable. You type a prompt, get a response, and the context evaporates. **SideloadOS is the opposite.**

SideloadOS is a **stateful, human-in-the-loop (HITL) execution engine** designed to run **Sideload Blueprints** — declarative AI workflow definitions that describe *what* should happen, not *how*. Think of it like a gaming console:

- **SideloadOS** is the hardware — the operating system, the runtime, the memory, and the display.
- **Blueprints** are the cartridges — plug one in and the system executes a complex, multi-step AI workflow with full human oversight at every critical decision point.

The engine doesn't just run prompts. It **orchestrates agents**, **persists memory across reboots**, **pauses for human approval**, and **streams every step** to a rich IDE-like interface in real time.

---

## 🏗️ The Architecture — The 4 Pillars

### 🔌 Pillar 1: The Universal AI Gateway

> *Hot-swap any AI model with zero code changes.*

Powered by **[LiteLLM](https://litellm.ai/)**, SideloadOS provides a unified interface to every major AI provider. Switch between **OpenAI**, **Google Gemini**, **Anthropic Claude**, or a local **Ollama** instance by changing a single dropdown — no code modifications, no redeployment, no vendor lock-in.

```
OpenAI  ──┐
Gemini  ──┤
Claude  ──┼──▶  LiteLLM Gateway  ──▶  LangGraph Agent
Ollama  ──┘
```

---

### 🧠 Pillar 2: Persistent Deep Memory

> *The AI's memory survives server reboots.*

Powered by **[LangGraph](https://langchain-ai.github.io/langgraph/)** with **PostgreSQL Checkpointers**, every conversation thread, agent state, and execution checkpoint is serialized to the database. Restart the server, redeploy the container — the agent picks up exactly where it left off with full conversational context intact.

---

### ⚡ Pillar 3: The God-Tier HITL Engine

> *The system physically pauses execution and waits for human approval.*

This is not a "confirm/cancel" dialog. When a LangGraph agent produces a draft artifact (code, document, plan), the engine:

1. **Pauses** the graph execution at an `interrupt()` checkpoint.
2. **Streams** the draft to a rich editor (Monaco for code, Tiptap for prose) in the Artifact Workbench.
3. **Waits** — the workflow is frozen in the database until the human acts.
4. **Resumes** via an isolated `BackgroundTask` when the user clicks **Approve & Execute**, carrying any human edits forward into the next graph step.

No polling. No timeouts. Full human agency over every AI decision.

---

### 🖥️ Pillar 4: The Antigravity GUI

> *A strict 100vh, non-scrolling, 3-pane IDE layout.*

The frontend is a **Next.js** application that mirrors the look and feel of a professional code editor:

| Pane | Role | Default Width |
|------|------|:---:|
| **Command Center** (Left) | Workspace & task tree navigation | 20% |
| **Action Stream** (Center) | Live execution cards, real-time SSE streaming, Omnibar | 80% |
| **Artifact Workbench** (Right) | Monaco/Tiptap editors with approval controls | 0% → 40% |

Communication is real-time via **WebSockets** (system events) and **Server-Sent Events** (agent execution streaming). The right pane is hidden by default and expands only when a `[Review Artifact]` card is clicked, resizing the layout to 20/40/40.

---

## 🚀 Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- [Node.js](https://nodejs.org/) ≥ 18

### 1. Configure Environment

```bash
cp .env.example .env
# Edit .env and set your actual POSTGRES_PASSWORD and FERNET_KEY
```

### 2. Boot the Backend

```bash
docker compose up -d --build
```

This starts **PostgreSQL** (with pgvector), **Redis**, **Celery**, and the **FastAPI** server.

### 3. Run Database Migrations

```bash
docker compose exec fastapi alembic upgrade head
```

### 4. Boot the Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) — you should see the 3-pane Antigravity IDE.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 15, React, TypeScript, Tailwind CSS, shadcn/ui, Zustand, react-resizable-panels |
| **Editors** | Monaco Editor (code), Tiptap (rich text) |
| **Backend** | FastAPI, Python 3.12, SQLAlchemy 2.0 (asyncpg), Alembic |
| **AI Engine** | LangGraph, LangChain, LiteLLM |
| **Database** | PostgreSQL 16 + pgvector |
| **Task Queue** | Celery + Redis |
| **Real-Time** | WebSockets, Server-Sent Events (SSE) |
| **Infrastructure** | Docker Compose |

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

**Built with 🧠 and ⚡ by the Sideload AI team.**

*SideloadOS is the console. Now go build the cartridges.*

</div>
