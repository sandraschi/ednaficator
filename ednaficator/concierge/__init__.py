"""
Edna Media Concierge (Track B, PRD.md) — narrow Plex-only concierge module.

Scope per PRD.md v1: three tools (resolve_and_play, browse, play_music) against
Sandra's Plex library, for Edna via Telegram (later). This package is additive —
it does not touch the existing MCP orchestrator / EdnaCore chat path. It is wired
in at the API layer (see api_bridge.py `/api/concierge/*` routes) and, once
EDNA_MODE=concierge lands, at the chat layer.
"""
