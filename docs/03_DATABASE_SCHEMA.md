\# DATABASE SCHEMA (POSTGRESQL + PGVECTOR)

All tables use `UUID` (asyncpg).



\- \*\*workspaces:\*\* id, name, cron\_schedule, created\_at

\- \*\*agent\_configs:\*\* id, workspace\_id, role, system\_prompt, model\_alias, mcp\_tools (JSONB)

\- \*\*tasks:\*\* id, workspace\_id, assigned\_agent\_id, instruction, status (pending, running, awaiting\_approval, completed)

\- \*\*artifacts:\*\* id, task\_id, title, content\_type, content, human\_edits, status, thread\_id, file\_path, blueprint\_path

\- \*\*settings:\*\* id, provider\_name, encrypted\_api\_key (AES-256 via cryptography.fernet)

