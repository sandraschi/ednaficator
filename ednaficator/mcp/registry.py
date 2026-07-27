"""
MCPRegistryLoader — reads claude_desktop_config.json and builds a tool manifest.

Ednaficator does NOT scan the fleet repo tree. It mirrors whatever is listed under
mcpServers in Claude Desktop config (or CLAUDE_DESKTOP_CONFIG). Each entry becomes a
lazy stdio subprocess when a tool call targets that server name.

Optional EDNA_MCP_ALLOWLIST (comma-separated server names) restricts which entries load.
Does NOT spawn processes — that is MCPStdioClient's job.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from loguru import logger


def default_config_path() -> Path:
    return Path(
        os.environ.get(
            "CLAUDE_DESKTOP_CONFIG",
            r"C:\Users\sandr\AppData\Roaming\Claude\claude_desktop_config.json",
        )
    )


DEFAULT_CONFIG_PATH = default_config_path()


@dataclass
class ServerEntry:
    name: str
    command: str
    args: list[str]
    env: dict[str, str]
    enabled: bool = True


@dataclass
class MCPRegistry:
    servers: dict[str, ServerEntry] = field(default_factory=dict)
    config_path: Path = field(default_factory=default_config_path)
    allowlist: set[str] | None = None

    @property
    def enabled_servers(self) -> dict[str, ServerEntry]:
        return {k: v for k, v in self.servers.items() if v.enabled}

    def server_names(self) -> list[str]:
        return sorted(self.enabled_servers.keys())

    def get(self, name: str) -> ServerEntry | None:
        return self.enabled_servers.get(name)

    def info(self) -> dict[str, Any]:
        return {
            "source": "claude_desktop_config",
            "config_path": str(self.config_path),
            "allowlist_active": self.allowlist is not None,
            "allowlist": sorted(self.allowlist) if self.allowlist else [],
            "registered": len(self.servers),
            "enabled": len(self.enabled_servers),
        }


def parse_allowlist(raw: str | None = None) -> set[str] | None:
    """Parse EDNA_MCP_ALLOWLIST (comma-separated server names). None = no filter."""
    value = raw if raw is not None else os.environ.get("EDNA_MCP_ALLOWLIST", "")
    value = value.strip()
    if not value:
        return None
    names = {part.strip() for part in value.split(",") if part.strip()}
    return names or None


def load_registry(config_path: Path | None = None) -> MCPRegistry:
    """
    Parse claude_desktop_config.json and return an MCPRegistry.

    Servers whose key starts with '_' are treated as disabled (Claude Desktop convention).
    Missing config → logs a warning and returns empty registry (don't crash Edna on startup).
    """
    path = config_path or default_config_path()
    allowlist = parse_allowlist()
    registry = MCPRegistry(config_path=path, allowlist=allowlist)

    if not path.exists():
        logger.warning(f"Claude Desktop config not found at {path}")
        return registry

    try:
        raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.error(f"Failed to parse {path}: {exc}")
        return registry

    mcp_servers: dict[str, Any] = raw.get("mcpServers", {})

    for key, cfg in mcp_servers.items():
        enabled = not key.startswith("_")
        # Strip leading underscores for the canonical name
        name = key.lstrip("_")

        entry = ServerEntry(
            name=name,
            command=cfg.get("command", ""),
            args=cfg.get("args", []),
            env=cfg.get("env", {}),
            enabled=enabled,
        )
        if allowlist is not None and name not in allowlist:
            logger.debug(f"Registry: {name} skipped (not in EDNA_MCP_ALLOWLIST)")
            continue

        registry.servers[name] = entry
        status = "enabled" if enabled else "disabled"
        logger.debug(f"Registry: {name} ({status})")

    if allowlist is not None:
        logger.info(
            f"Allowlist active ({len(allowlist)} names) — "
            f"{len(registry.enabled_servers)} servers loaded from {path}"
        )
    else:
        logger.info(
            f"Loaded {len(registry.enabled_servers)} enabled / "
            f"{len(registry.servers) - len(registry.enabled_servers)} disabled servers "
            f"from {path}"
        )
    return registry
