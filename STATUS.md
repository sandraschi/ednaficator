# Ednaficator — STATUS

**Date:** 2026-07-20 · **Verdict: viable core, wrong wrapper — decision pending (see TODO.md)**

## What this project actually is (per PRD.md)

A **conversational MCP orchestrator**: family members talk in plain language, a local LLM
(LM Studio/Ollama on the 4090) picks a tool from the Claude Desktop MCP registry and calls
it over stdio. *Not* a standalone AI assistant. Target users: Sandra's non-technical
family/housemates. Canonical example: Marion asks "Is Benny's camera online?" →
tapo-camera-mcp answers, no Sandra required.

## What exists and runs (verified state as of REVIVE.md, 2026-05-21)

- Boots: `uv run python -m ednaficator` (API :10942), `start_all.py` adds React UI (:10943)
- LLM provider switch: LM Studio (default, :1234) / Ollama (:11434), qwen2.5:27b default
- MCP stdio spawning works (VIRTUAL_ENV stripped for child uv projects, memops lazy-start)
- Registry: Claude Desktop `mcpServers` via `CLAUDE_DESKTOP_CONFIG`; optional `EDNA_MCP_ALLOWLIST`
- Smoke test: `uv run python tests/smoke_test.py` (needs Claude config with >=1 server)
- Packaged: `dist/ednaficator-v2.0.0.mcpb` exists
- Git repo initialized (root ASSESSMENT.md claiming "no git" is **stale/wrong** — dated
  auto-scan from 2026-01-01, predates revival; treat as historical only)

## Known debris (honest list)

- `api_bridge.py` + `_backup` + `_fixed` — three variants, one truth unknown without diffing
- `ednaficator/nlp/processor.py` + `_enhanced` + `_fixed` — a hand-rolled NLP intent layer
  that native LLM tool-calling made obsolete; candidate for deletion, not repair
- `ednaficator/memory/engine.py` + `engine_enhanced.py` + `edna_memory/*.json` — custom
  memory as flat JSON; fragile, duplicates what advanced-memory MCP already does
- `pyproject.toml.20260717.bak`, `.snapshots/`, marketing-heavy README
- `native/` Tauri shell — untested against current backend; family users are on phones,
  a Windows installer serves nobody in the target audience
- `ednaficator/austrian/services.py` — never wired in (per REVIVE)

## Strategic status (the real blocker)

The code runs; the **product rationale** is what's under review. In 2026, generic
chat-with-a-nice-voice is a solved, free commodity (ChatGPT/Gemini voice modes with
memory). Ednaficator's only defensible value is the part no big-tech assistant can ever
ship: **the front door to THIS house** — Benny's camera, Plex on Goliath, Wienerlinien,
the fleet — with Sandra as visible, trusted admin.

Three tracks on the table (full argument in chat 2026-07-20 + `docs/` spec):

- **A. Sunset.** Set family up with commodity assistants; archive repo. Zero maintenance.
- **B. Narrow to fleet front-door** (= the original PRD concept, minus scope creep):
  curated tool whitelist, text-first, phone-reachable, Sandra-admin. Days of work.
- **C. Voice-first concierge per `ednaficator-spec.md` (2026-07-19):** full STT/TTS
  pipeline, PWA, server-side memory. Largest effort; competes head-on with commodity
  voice assistants on their strongest axis.

A "teach Edna AI literacy / vibecoding" angle was raised 2026-07-20 — assessment: real
value, but it's a *usage pattern and curriculum*, not a software feature. See TODO.md.

## Docs map

- `PRD.md` — original concept (authoritative for intent)
- `REVIVE.md` — 2026-05 revival, how to start it today
- `ednaficator-spec.md` / chat 2026-07-19 — voice-first re-architecture proposal (Track C)
- `ASSESSMENT.md`, `docs/ASSESSMENT-2025-08-10.md` — stale, historical
- `STATUS.md` (this file), `TODO.md` — current truth
- Central docs: `mcp-central-docs/projects/ednaficator.md`
