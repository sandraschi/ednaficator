# ednaficator Agent Context

Conversational MCP orchestrator (FastAPI + React UI). **Not** fleet auto-discovery — see `docs/MCP_REGISTRY.md`.

## Architecture

| Piece | Role |
|-------|------|
| `api_bridge.py` | FastAPI app (:10942), lifespan starts `EdnaCore` |
| `ednaficator/mcp/registry.py` | Loads `mcpServers` from Claude Desktop JSON |
| `ednaficator/mcp/orchestrator.py` | Lazy stdio MCP pool; eager `fileops` only |
| `ui/` | Vite frontend (:10943) |
| `fleet-start.config.ps1` | Unified fleet launcher (uvicorn `api_bridge:app`) |

## Env

- `CLAUDE_DESKTOP_CONFIG` — MCP registry path
- `EDNA_MCP_ALLOWLIST` — optional comma-separated server name filter
- `EDNA_LLM_PROVIDER`, `EDNA_*` — see `.env.example`

## Commands

```powershell
Set-Location D:\Dev\repos\ednaficator
just run                    # API only
uv run python start_all.py  # API + UI
uv run pytest tests/ -q
uv run python tests/smoke_test.py
```

## Product note

README describes a **media concierge pivot** (Plex/Telegram). Code still runs the **full orchestrator** until Track B whitelist work lands in `TODO.md`.
