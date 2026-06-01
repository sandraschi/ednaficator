"""
MCPStdioClient — spawns an MCP server process and speaks JSON-RPC 2.0 over stdio.

Protocol: MCP spec (https://spec.modelcontextprotocol.io)
  - initialize handshake on first call
  - tools/list to discover tools
  - tools/call to invoke a tool
  - process is kept alive for the session lifetime

One client instance per server. EdnaCore manages the pool.
"""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass, field
from typing import Any

from loguru import logger

from ednaficator.mcp.registry import ServerEntry


# How long to wait for a response from an MCP server (seconds)
CALL_TIMEOUT = 30.0
INIT_TIMEOUT = 45.0


@dataclass
class ToolDef:
    name: str
    description: str
    input_schema: dict[str, Any]
    server: str  # which server owns this tool


class MCPStdioError(Exception):
    pass


class MCPStdioClient:
    """
    Manages a single MCP server subprocess.
    Thread-safe: uses asyncio.Lock around writes so multiple coroutines
    can queue requests without interleaving JSON on the pipe.
    """

    def __init__(self, entry: ServerEntry):
        self.entry = entry
        self.name = entry.name
        self._proc: asyncio.subprocess.Process | None = None
        self._lock = asyncio.Lock()
        self._req_id = 0
        self._initialized = False
        self.tools: list[ToolDef] = []

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Spawn the server process and run initialize + tools/list."""
        if self._proc is not None:
            return

        env = {**os.environ, **self.entry.env}
        # Child MCP servers use their own uv project; inherited venv vars confuse uv.
        for key in ("VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT"):
            env.pop(key, None)

        logger.debug(f"[{self.name}] spawning: {self.entry.command} {' '.join(self.entry.args)}")
        self._proc = await asyncio.create_subprocess_exec(
            self.entry.command,
            *self.entry.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        # Give the process a moment — if it exits immediately, capture why
        await asyncio.sleep(0.3)
        if self._proc.returncode is not None:
            stderr_raw = b""
            try:
                _, stderr_raw = await asyncio.wait_for(self._proc.communicate(), timeout=2.0)
            except Exception:
                pass
            stderr_text = stderr_raw.decode(errors="replace").strip()[:300]
            raise MCPStdioError(
                f"Process exited immediately (rc={self._proc.returncode}): {stderr_text or '(no stderr)'}"
            )

        try:
            await asyncio.wait_for(self._initialize(), timeout=INIT_TIMEOUT)
            await asyncio.wait_for(self._discover_tools(), timeout=INIT_TIMEOUT)
            logger.info(f"[{self.name}] ready — {len(self.tools)} tools")
        except Exception as exc:
            # Grab any stderr for diagnostics
            stderr_text = ""
            try:
                if self._proc and self._proc.stderr:
                    raw = await asyncio.wait_for(self._proc.stderr.read(2048), timeout=1.0)
                    stderr_text = raw.decode(errors="replace").strip()
            except Exception:
                pass
            err_msg = str(exc) or type(exc).__name__
            if stderr_text:
                err_msg = f"{err_msg} | stderr: {stderr_text[:200]}"
            logger.error(f"[{self.name}] startup failed: {err_msg}")
            await self.stop()
            raise MCPStdioError(err_msg) from exc

    async def stop(self) -> None:
        if self._proc is None:
            return
        try:
            self._proc.terminate()
            await asyncio.wait_for(self._proc.wait(), timeout=5.0)
        except Exception:
            self._proc.kill()
        self._proc = None
        self._initialized = False
        logger.debug(f"[{self.name}] stopped")

    @property
    def running(self) -> bool:
        return self._proc is not None and self._proc.returncode is None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool on the server. Returns the tool result content."""
        if not self.running:
            raise MCPStdioError(f"[{self.name}] not running")

        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
        }

        response = await asyncio.wait_for(self._send(payload), timeout=CALL_TIMEOUT)
        self._raise_if_error(response)

        result = response.get("result", {})
        # MCP spec: result.content is a list of content blocks
        content = result.get("content", [])
        if not content:
            return result

        # Flatten text blocks for easy consumption
        texts = [c.get("text", "") for c in content if c.get("type") == "text"]
        if texts:
            combined = "\n".join(texts)
            # Try to parse as JSON if it looks like it
            try:
                return json.loads(combined)
            except (json.JSONDecodeError, ValueError):
                return combined

        return content

    # ------------------------------------------------------------------
    # Internal protocol
    # ------------------------------------------------------------------

    async def _initialize(self) -> None:
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "ednaficator", "version": "2.0.0"},
            },
        }
        response = await self._send(payload)
        self._raise_if_error(response)

        # Send initialized notification (no response expected)
        notif = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        await self._write_line(json.dumps(notif))

        self._initialized = True
        server_info = response.get("result", {}).get("serverInfo", {})
        logger.debug(f"[{self.name}] initialized — server: {server_info}")

    async def _discover_tools(self) -> None:
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/list",
            "params": {},
        }
        response = await self._send(payload)
        self._raise_if_error(response)

        raw_tools = response.get("result", {}).get("tools", [])
        self.tools = [
            ToolDef(
                name=t["name"],
                description=t.get("description", ""),
                input_schema=t.get("inputSchema", {}),
                server=self.name,
            )
            for t in raw_tools
        ]

    async def _send(self, payload: dict) -> dict:
        line = json.dumps(payload)
        await self._write_line(line)
        return await self._read_response(payload["id"])

    async def _write_line(self, line: str) -> None:
        async with self._lock:
            if self._proc is None or self._proc.stdin is None:
                raise MCPStdioError(f"[{self.name}] stdin not available")
            self._proc.stdin.write((line + "\n").encode())
            await self._proc.stdin.drain()

    async def _read_response(self, req_id: int) -> dict:
        """Read lines from stdout until we get the response matching req_id."""
        assert self._proc and self._proc.stdout
        while True:
            raw = await self._proc.stdout.readline()
            if not raw:
                raise MCPStdioError(f"[{self.name}] stdout closed unexpectedly")
            line = raw.decode().strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                logger.debug(f"[{self.name}] non-JSON stdout: {line[:120]}")
                continue
            # Skip notifications (no "id")
            if msg.get("id") == req_id:
                return msg

    @staticmethod
    def _raise_if_error(response: dict) -> None:
        if "error" in response:
            err = response["error"]
            raise MCPStdioError(f"MCP error {err.get('code')}: {err.get('message')}")

    def _next_id(self) -> int:
        self._req_id += 1
        return self._req_id
