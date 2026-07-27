# Ednaficator

**Edna** — local LLM front-end for home automation and (planned) family media concierge.

## Two layers (read this first)

| Layer | What it is today |
|-------|------------------|
| **Running code** | MCP orchestrator: reads **Claude Desktop** `mcpServers`, lazy-spawns fleet `-mcp` repos over stdio when the LLM picks a tool. See [docs/MCP_REGISTRY.md](docs/MCP_REGISTRY.md). |
| **Product pivot (2026-07)** | **Family concierge** (Plex first; email + news/TTS later; no dev tools). See [docs/CONCIERGE_PLAN.md](docs/CONCIERGE_PLAN.md), `PRD.md`, `STATUS.md`, `TODO.md`. |

The UI **ready/total MCP** count is **registered Claude config entries**, not live fleet discovery.

## How it works (orchestrator mode)

```
You (web UI or API)
   → local LLM (LM Studio / Ollama) with tool manifest
   → pick server + tool from Claude Desktop registry
   → spawn MCP subprocess (uv … in D:\Dev\repos\*-mcp)
   → return summarized result
```

Optional family filter: `EDNA_MCP_ALLOWLIST=plex-mcp,tapo-camera-mcp` (see `.env.example`).

## Planned: family concierge (Track B / V1+)

Plex REST slice is in repo; Telegram routing and widened tools (email, news) are phased in [docs/CONCIERGE_PLAN.md](docs/CONCIERGE_PLAN.md). See `TODO.md` RECOMMENDED V1.

## Running (dev)

```powershell
Set-Location D:\Dev\repos\ednaficator
uv run python -m ednaficator      # API :10942
uv run python start_all.py        # API + UI :10943
uv run python tests/smoke_test.py
```

Copy `.env.example` → `.env` for `CLAUDE_DESKTOP_CONFIG`, LLM, and optional `EDNA_MCP_ALLOWLIST`.

LLM provider via env: `EDNA_LLM_PROVIDER=lmstudio` (default, :1234) or `ollama` (:11434).
Details in `REVIVE.md` and [docs/MCP_REGISTRY.md](docs/MCP_REGISTRY.md).

## Requirements (dev)

- Python 3.11+ / uv
- Claude Desktop config with `mcpServers` pointing at fleet repos (or set `CLAUDE_DESKTOP_CONFIG`)
- LM Studio or Ollama with a tool-capable model

Media concierge (Plex, Telegram, whisper) requirements are in `PRD.md` / `TODO.md` for Track B/V1.

## Non-goals (orchestrator mode)

Exposing winops/gitops/fileops to non-admin family users — use `EDNA_MCP_ALLOWLIST` until Track B per-tool whitelist lands.

## Non-goals (product)

General SaaS · commodity voice-assistant clone · full fleet exposure to relatives without curation.

## License / audience

Private family deployment. Not published to any registry.
