\- \*\*Database:\*\* Always use `async`/`await` with `asyncpg` and SQLAlchemy 2.0. No synchronous DB calls. All primary keys MUST be UUIDs (`uuid.uuid4`).

\- \*\*AI Engine:\*\* Never import `openai` or `anthropic` SDKs directly. Route all LLM calls through `litellm`. We strictly use `langgraph` for state; do NOT use legacy LangChain `AgentExecutor`.

\- \*\*Frontend:\*\* The Next.js layout must use `100vh` and `overflow-hidden`. Absolutely NO vertical page-level scrolling. All scrolling occurs within `<ScrollArea>` components inside the 3 panes.

\- \*\*Styling:\*\* Strict Dark Mode natively. Typography: Inter. Components: `shadcn/ui`.

