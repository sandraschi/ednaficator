"""
MCPOrchestrator 2.0 — manages a pool of real MCPStdioClient instances.

Replaces the old mock-based orchestrator entirely.

Responsibilities:
  - Lazy-start server processes on first use (avoid spawning 18 processes at boot)
  - Maintain a tool manifest (server → tool list) for the LLM prompt
  - Route tool calls to the correct client
  - Graceful shutdown of all subprocesses
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from loguru import logger

from ednaficator.mcp.registry import MCPRegistry, ServerEntry, load_registry
from ednaficator.mcp.stdio_client import MCPStdioClient, ToolDef


# Servers to eagerly start on initialize() (always-useful ones).
# Everything else is lazy-started on first call.
# memops is slow to boot; lazy-start on first memory write instead
EAGER_SERVERS: set[str] = {"fileops"}


@dataclass
class ServerState:
    entry: ServerEntry
    client: MCPStdioClient | None = None
    start_attempted: bool = False
    start_error: str | None = None

    @property
    def ready(self) -> bool:
        return self.client is not None and self.client.running


class MCPOrchestrator:
    def __init__(self, registry: MCPRegistry | None = None):
        self.registry: MCPRegistry = registry or load_registry()
        self._states: dict[str, ServerState] = {
            name: ServerState(entry=entry)
            for name, entry in self.registry.enabled_servers.items()
        }
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Startup / shutdown
    # ------------------------------------------------------------------

    async def initialize(self) -> None:
        """Eagerly start the priority servers; others start on demand."""
        tasks = [
            self._ensure_started(name)
            for name in EAGER_SERVERS
            if name in self._states
        ]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        logger.info(
            f"Orchestrator ready — {len(self._states)} servers in registry, "
            f"{self.ready_count} started"
        )

    async def shutdown(self) -> None:
        tasks = [
            state.client.stop()
            for state in self._states.values()
            if state.client is not None
        ]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("Orchestrator shutdown complete")

    # ------------------------------------------------------------------
    # Tool discovery (for LLM prompt)
    # ------------------------------------------------------------------

    async def get_tool_manifest(self, server_names: list[str] | None = None) -> str:
        """
        Return a compact text tool manifest for inclusion in the Ollama system prompt.
        If server_names is None, uses all ready (already-started) servers to avoid
        cold-starting everything just to build a prompt.
        """
        lines: list[str] = []
        for name, state in self._states.items():
            if server_names is not None and name not in server_names:
                continue
            if not state.ready:
                continue
            for tool in state.client.tools:  # type: ignore[union-attr]
                desc = tool.description[:120].replace("\n", " ")
                lines.append(f"  [{name}] {tool.name} — {desc}")
        return "\n".join(lines) if lines else "(no tools currently loaded)"

    async def all_tools(self) -> list[ToolDef]:
        """Flat list of all tools across ready servers."""
        tools: list[ToolDef] = []
        for state in self._states.values():
            if state.ready and state.client:
                tools.extend(state.client.tools)
        return tools

    # ------------------------------------------------------------------
    # Tool execution
    # ------------------------------------------------------------------

    async def call_tool(
        self, server_name: str, tool_name: str, arguments: dict[str, Any]
    ) -> Any:
        """
        Call a tool on the named server. Lazy-starts the server if not running.
        Raises MCPStdioError on protocol errors, ValueError if server unknown.
        """
        if server_name not in self._states:
            raise ValueError(f"Unknown server: {server_name}")

        await self._ensure_started(server_name)
        state = self._states[server_name]

        if not state.ready:
            raise RuntimeError(
                f"Server {server_name} failed to start: {state.start_error}"
            )

        logger.debug(f"[{server_name}] calling {tool_name}({arguments})")
        result = await state.client.call_tool(tool_name, arguments)  # type: ignore[union-attr]
        return result

    async def call_tool_by_def(self, tool_def: ToolDef, arguments: dict[str, Any]) -> Any:
        return await self.call_tool(tool_def.server, tool_def.name, arguments)

    # ------------------------------------------------------------------
    # Server management
    # ------------------------------------------------------------------

    async def _ensure_started(self, name: str) -> None:
        state = self._states.get(name)
        if state is None or state.ready or state.start_attempted:
            return

        async with self._lock:
            # Re-check under lock
            if state.ready or state.start_attempted:
                return

            state.start_attempted = True
            client = MCPStdioClient(state.entry)
            try:
                await client.start()
                state.client = client
                logger.info(f"[{name}] started ({len(client.tools)} tools)")
            except Exception as exc:
                err_msg = str(exc) if str(exc) else type(exc).__name__
                state.start_error = err_msg
                logger.warning(f"[{name}] failed to start: {err_msg}")

    async def start_server(self, name: str) -> bool:
        """Explicitly start a server. Returns True if successful."""
        state = self._states.get(name)
        if not state:
            return False
        # Reset so _ensure_started will retry
        state.start_attempted = False
        state.start_error = None
        await self._ensure_started(name)
        return self._states[name].ready

    # ------------------------------------------------------------------
    # Status helpers
    # ------------------------------------------------------------------

    @property
    def ready_count(self) -> int:
        return sum(1 for s in self._states.values() if s.ready)

    def get_status(self) -> dict[str, dict]:
        return {
            name: {
                "ready": state.ready,
                "tool_count": len(state.client.tools) if state.client else 0,
                "error": state.start_error,
            }
            for name, state in self._states.items()
        }

    # ------------------------------------------------------------------
    # Legacy compat shim (old EdnaCore called this)
    # ------------------------------------------------------------------

    async def discover_servers(self) -> None:
        """Alias for initialize() — keeps old call sites working."""
        await self.initialize()

    @property
    def servers(self) -> dict[str, ServerState]:
        """Legacy attribute access."""
        return self._states
