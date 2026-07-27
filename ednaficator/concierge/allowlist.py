"""Parse EDNA_CONCIERGE_TOOLS allowlist."""

from __future__ import annotations

import os

DEFAULT_TOOLS = frozenset({"plex"})


def parse_concierge_tools(raw: str | None = None) -> set[str]:
    value = raw if raw is not None else os.environ.get("EDNA_CONCIERGE_TOOLS", "plex")
    value = value.strip()
    if not value:
        return set(DEFAULT_TOOLS)
    names = {part.strip().lower() for part in value.split(",") if part.strip()}
    return names or set(DEFAULT_TOOLS)
