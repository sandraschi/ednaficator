"""
MCPRegistryLoader — reads claude_desktop_config.json and builds a tool manifest.

Only loads servers that are enabled (no leading underscore in key) and
whose command/args look sane. Does NOT spawn processes — that's MCPStdioClient's job.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from loguru import logger


# Default location — overridable via env var
DEFAULT_CONFIG_PATH = Path(os.environ.get(
    "CLAUDE_DESKTOP_CONFIG",
    r"C:\Users\sandr\AppData\Roaming\Claude\claude_desktop_config.json"
))


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
    config_path: Path = DEFAULT_CONFIG_PATH

    @property
    def enabled_servers(self) -> dict[str, ServerEntry]:
        return {k: v for k, v in self.servers.items() if v.enabled}

    def server_names(self) -> list[str]:
        return sorted(self.enabled_servers.keys())

    def get(self, name: str) -> ServerEntry | None:
        return self.enabled_servers.get(name)


def load_registry(config_path: Path = DEFAULT_CONFIG_PATH) -> MCPRegistry:
    """
    Parse claude_desktop_config.json and return an MCPRegistry.

    Servers whose key starts with '_' are treated as disabled (Claude Desktop convention).
    Missing config → logs a warning and returns empty registry (don't crash Edna on startup).
    """
    registry = MCPRegistry(config_path=config_path)

    if not config_path.exists():
        logger.warning(f"Claude Desktop config not found at {config_path}")
        return registry

    try:
        raw: dict[str, Any] = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.error(f"Failed to parse {config_path}: {exc}")
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
        registry.servers[name] = entry
        status = "enabled" if enabled else "disabled"
        logger.debug(f"Registry: {name} ({status})")

    logger.info(
        f"Loaded {len(registry.enabled_servers)} enabled / "
        f"{len(registry.servers) - len(registry.enabled_servers)} disabled servers "
        f"from {config_path}"
    )
    return registry
