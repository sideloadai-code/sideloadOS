# UI/UX Specification: The 3-Pane Antigravity Layout

The entire application runs on a single `100vh` non-scrolling page using Zustand state to manipulate three panes via `react-resizable-panels`.

---

## Pane Layout

| Pane | Position | Default Width | Role |
|------|----------|:---:|------|
| **Command Center** | Left | 20% | Workspace tree, Blueprint Switcher, Settings |
| **Action Stream** | Center | 80% | Live execution cards, SSE streaming, Omnibar |
| **Artifact Workbench** | Right | 0% → 40% | Monaco/Tiptap editors with approval controls |

### Resize Behavior

- **Default state:** Panes 1 + 2 visible (20/80). Pane 3 is hidden (`rightPaneWidth: 0`).
- **Artifact review:** When `[Review Artifact]` is clicked, layout transitions to **20/40/40**.
- **Close workbench:** Returns to 20/80/0.
- Managed by `useLayoutStore` (Zustand) with `openWorkbench()` / `closeWorkbench()` actions.

---

## Pane 1: Command Center

- **Start Conversation** button (top)
- **Blueprint Switcher** — `<select>` dropdown that:
  - Fetches cartridges from `GET /api/blueprints/`
  - Displays blueprint name and description
  - Persists selection to `localStorage` (`sideload_active_blueprint`)
  - Selection is passed as `blueprint_path` to the orchestration API
- **Workspace Tree** — Zustand-driven list of workspaces using `lucide-react` icons. Active workspace highlighted with emerald accent.
- **Settings** — Opens `<SettingsModal>` for API key management and provider configuration.

---

## Pane 2: Action Stream

- **WalkthroughCard** — Renders execution steps as an animated card with:
  - Node labels mapped to human-readable descriptions (e.g., `🧭 Analyzing request...`)
  - Swarm-specific labels: `📐 Architect designing spec...`, `💻 Developer writing code...`, `🔎 QA testing code...`
  - `[Review Artifact]` button that opens Pane 3
  - Error display with `❌` prefix
  - Chat response display with `🤖` prefix
- **Omnibar** (absolute bottom footer):
  - **Model dropdown** — Dynamically populated from `GET /api/models/available`
  - **Agent dropdown** — Currently static ("System Orchestrator")
  - **Text input** — Disabled until workspace + model selected
  - **Send button** — Triggers `POST /api/orchestrate` via `useAgentStream` hook

---

## Pane 3: Artifact Workbench

- Hidden by default. Opens only when `[Review Artifact]` card is clicked.
- **Code artifacts** → `@monaco-editor/react` with syntax highlighting
- **Text artifacts** → `@tiptap/react` rich text editor (RichTextEditor component)
- **Header controls:**
  - ✅ `Approve & Execute` button (green) — calls `POST /api/artifacts/{id}/approve`
  - ✏️ Edit toggle
  - ❌ Close button — collapses Pane 3

---

## Real-Time Communication

| Channel | Hook | Purpose |
|---------|------|---------|
| WebSocket | `useGlobalSocket` | System events (workspace creation, etc.) |
| SSE | `useAgentStream` | Agent execution streaming with cross-platform delimiter handling |

---

## State Management

| Store | File | Responsibilities |
|-------|------|-----------------|
| `useLayoutStore` | `store/layoutStore.ts` | Pane widths, workbench open/close, active artifact ID |
| `useWorkspaceStore` | `store/workspaceStore.ts` | Workspace list, active workspace selection |
