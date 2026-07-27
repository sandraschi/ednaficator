# MCP registry (how Ednaficator finds tools)

Ednaficator is an **MCP orchestrator**: the local LLM picks a `server` + `tool`, and Edna spawns that MCP process over stdio.

## Source of truth

| What | Where |
|------|--------|
| **Registered servers** | `mcpServers` in Claude Desktop config |
| **Default path** | `%AppData%\Claude\claude_desktop_config.json` |
| **Override** | `CLAUDE_DESKTOP_CONFIG` env var |

Ednaficator does **not** scan `D:\Dev\repos` or `mcp-central-docs` fleet manifests. A fleet repo is usable only if your Claude config already points at it (typical: `uv run --directory D:\Dev\repos\plex-mcp ...`).

Keys prefixed with `_` in Claude config are disabled (Desktop convention).

## Lifecycle

1. **Load registry** at EdnaCore startup — parse JSON, apply optional allowlist.
2. **Eager start** — only `fileops` (if present) starts immediately.
3. **Lazy start** — other servers spawn on first tool call to that name.
4. **LLM manifest** — lists tools for ready servers; idle servers appear as `(registered — lazy-start on first tool call)`.

## Family safety allowlist (Track B)

Set before starting the API:

```powershell
$env:EDNA_MCP_ALLOWLIST = "plex-mcp,tapo-camera-mcp,mywienerlinien-mcp"
uv run python -m ednaficator
```

Only those names from Claude config are loaded. Omit the variable to mirror the full Claude registry.

## API / UI

- `GET /api/servers` — registry metadata + per-server `ready` / `tool_count` / `error`
- UI sidebar: **ready/total** = started vs registered, not “fleet discovery”

## Plex concierge REST (Track B slice 1)

Direct Plex tools (no MCP stdio) live under `/api/concierge/*`. Set in `.env`:

- `EDNA_PLEX_URL`, `EDNA_PLEX_TOKEN`, `EDNA_PLEX_DEFAULT_CLIENT`
- `EDNA_MODE=concierge` — chat/WebSocket use `ConciergeRouter` (plex/email/news adapters, not MCP stdio)

| Route | Purpose |
|-------|---------|
| `GET /api/concierge/status` | Plex configured + server reachable |
| `GET /api/concierge/clients` | Plex client names |
| `POST /api/concierge/resolve_and_play` | Fuzzy match + play |
| `POST /api/concierge/browse` | Short choice list |
| `POST /api/concierge/play_music` | Artist/era/mood playback |
| `POST /api/concierge/chat` | LLM concierge loop (always adapter mode) |
| `POST /api/concierge/email/*` | Unread summaries, send |
| `POST /api/concierge/news/*` | Digest text + read-aloud WAV |

Also: `EDNA_CONCIERGE_TOOLS=plex,email,news` filters enabled adapters.

Tests: `uv run pytest tests/test_concierge_*.py tests/test_email_tools.py tests/test_news_tools.py -q`

## Product direction vs current code

| Layer | Status |
|-------|--------|
| **Running code** | Orchestrator + Plex concierge REST (`/api/concierge/*`) |
| **PRD pivot (2026-07)** | Narrow “Edna Media Concierge” (Plex/Telegram, 3 tools) |
| **Track B** | `EDNA_MODE=concierge`, `/api/concierge/chat`, Telegram bot (`uv run ednaficator-bot`); live TV test still human |

See `README.md`, `STATUS.md`, `TODO.md` for the product decision gate.

## Verify

```powershell
uv run python tests/smoke_test.py
uv run pytest tests/test_registry.py -q
```

Smoke test requires Claude config with at least one enabled server unless you point `CLAUDE_DESKTOP_CONFIG` at a test fixture.
