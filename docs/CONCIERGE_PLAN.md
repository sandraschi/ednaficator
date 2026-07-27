# Edna Concierge Plan — widened family front door

Edna is a **family concierge**, not a dev assistant. This plan widens beyond Plex (Track B slice 1) into comms and news, while keeping orchestrator/dev tools separate.

## Tier model

| Tier | Domain | Status | Mechanism |
|------|--------|--------|-----------|
| **0** | Plex media (TV, music) | Done (REST slice) | `concierge/plex_tools.py`, `/api/concierge/*` |
| **1** | Family comms (email) | Planned | Direct Python adapter to email-mcp APIs (send, read summaries) |
| **2** | News digest + TTS | Planned | aiwatcher-mcp digest read aloud (no full MCP stdio on hot path) |
| **3** | Calendar / reminders | Optional later | Lightweight adapter; not V1 |

## Explicit exclusions

Edna concierge must **not** expose:

- KiCad, winops, fileops, git-github, docker/fileops dev tooling
- Full MCP fleet stdio from family chat paths
- Code review, repo ops, or agentic dev workflows

Those remain under `EDNA_MCP_ALLOWLIST` + orchestrator mode for Sandra's dev sessions only.

## Configuration

Two parallel allowlists:

| Env | Purpose |
|-----|---------|
| `EDNA_MCP_ALLOWLIST` | Orchestrator dev mode — which MCP servers load via stdio |
| `EDNA_CONCIERGE_TOOLS` | Concierge tiers/tools enabled for family (e.g. `plex,email,news`) |
| `EDNA_MODE` | `orchestrator` (default) or `concierge` — chat routing |

Concierge uses **direct Python adapters** (like `plex_tools.py`) for latency and simplicity, not spawning MCP stdio subprocesses on family Telegram/voice paths.

## Implementation phases

### Phase 1 — Plex REST (exists)

- `ednaficator/concierge/plex_tools.py` — plexapi resolve/play
- `ednaficator/concierge/tools.py` — `PlexConcierge` PRD verbs
- `api_bridge.py` — `/api/concierge/{status,clients,resolve_and_play,browse,play_music}`
- Tests: `tests/test_plex_tools.py`, `tests/test_concierge_tools.py`

### Phase 2 — Email adapter

- [x] `concierge/email_tools.py` — HTTP client to email-mcp (`10813`)
- [x] `concierge/email_concierge.py` — German copy verbs
- [x] REST: `/api/concierge/email/{status,unread,send}`
- [x] Tests: `tests/test_email_tools.py`
- [x] Wire into `EDNA_MODE=concierge` chat routing (Phase 4)

### Phase 3 — News digest + TTS

- [x] `concierge/news_tools.py` — aiwatcher `/api/digest/preview`
- [x] `concierge/speech_tools.py` — speech-mcp `/api/v1/tts/wav`
- [x] `concierge/news_concierge.py` — German copy + read aloud
- [x] REST: `/api/concierge/news/{status,digest,read-aloud}`
- [x] Tests: `tests/test_news_tools.py`
- [ ] Telegram voice reply wiring (Phase 4)

### Phase 4 — Concierge chat routing

- [x] `concierge/router.py` — LLM tool manifest + adapter execution
- [x] `EDNA_MODE=concierge` wired in `EdnaCore.process_request`
- [x] `POST /api/concierge/chat` — always concierge (Telegram/testing)
- [x] Chat + WebSocket return `choices` for inline buttons
- [x] `ednaficator/bot.py` — Telegram long-poll, allowlist, Plex choice buttons
- [x] Tests: `tests/test_concierge_router.py`
- [x] Voice notes via faster-whisper (RECIPE Step 5) — `concierge/voice_tools.py`, bot voice handler

## Reference code

| Path | Role |
|------|------|
| `ednaficator/concierge/plex_tools.py` | Deterministic Plex layer |
| `ednaficator/concierge/tools.py` | Concierge class → dict responses |
| `ednaficator/mcp/registry.py` | Orchestrator MCP stdio registry (not concierge) |
| `api_bridge.py` | FastAPI routes + `Settings.mode` |
| `tests/test_concierge_tools.py` | Unit tests with monkeypatched plex |

## Related docs

- [PRD.md](../PRD.md) — product definition
- [MCP_REGISTRY.md](MCP_REGISTRY.md) — orchestrator vs concierge REST
- [TODO.md](../TODO.md) — gated task list
