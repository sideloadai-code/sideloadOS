\# SYSTEM ARCHITECTURE \& DATA FLOW

SideloadOS is a decoupled, event-driven React/FastAPI application. 



\## 1. Real-Time Comms

\- \*\*WebSockets (`ws://`):\*\* Used for System Actions. When the Python LangGraph agent manipulates the DB (e.g., creates a Workspace folder), FastAPI broadcasts a WS event. The Next.js Zustand store catches it and re-renders the UI instantly without polling.

\- \*\*Server-Sent Events (SSE):\*\* Used for Agent Execution. LangGraph yields SSE JSON chunks (`{"type": "status", "step": "Scraping..."}`). Next.js parses this to render live UI cards in the Center Pane.



\## 2. Autonomy Layer

\- \*\*MCP (Model Context Protocol):\*\* SideloadOS is an MCP Client. We dynamically load external MCP tools into LangChain `@tool` objects.

\- \*\*Chrono Engine:\*\* Background tasks run via Celery + Redis.

