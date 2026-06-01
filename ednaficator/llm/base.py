"""Shared LLM client types and tool-call parsing."""

from __future__ import annotations

import json
from typing import Any, Literal, Protocol, runtime_checkable

LLMProvider = Literal["ollama", "lmstudio"]

TOOL_CALL_SYSTEM = """\
You are Ednaficator, a home automation and personal assistant AI running on a private \
local server in Vienna. You orchestrate a fleet of MCP (Model Context Protocol) tools.

When the user's request maps to one of the available tools, respond with ONLY a JSON \
object on a single line in this exact format (no markdown, no explanation):
{"tool_call": {"server": "<server_name>", "tool": "<tool_name>", "arguments": {<args>}}}

If no tool fits, or the user is just chatting, respond normally in plain text.
Be concise. Austrian-friendly tone. Default language: English unless user writes German.

Available tools:
{tool_manifest}
"""


def parse_tool_call_response(raw: str) -> dict[str, Any]:
    """Parse LLM output into tool_call or plain text."""
    stripped = raw.strip()

    if stripped.startswith("```"):
        lines = stripped.split("\n")
        lines = lines[1:] if lines[0].startswith("```") else lines
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()

    if '"tool_call"' in stripped:
        start = stripped.find("{")
        end = stripped.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                obj = json.loads(stripped[start:end])
                tc = obj.get("tool_call", {})
                if tc.get("server") and tc.get("tool"):
                    return {
                        "type": "tool_call",
                        "server": tc["server"],
                        "tool": tc["tool"],
                        "arguments": tc.get("arguments", {}),
                    }
            except json.JSONDecodeError:
                pass

    return {"type": "text", "content": stripped}


@runtime_checkable
class LLMClient(Protocol):
    provider: LLMProvider
    base_url: str
    model: str

    async def close(self) -> None: ...

    async def chat(
        self,
        messages: list[dict[str, str]],
        system: str | None = None,
    ) -> str: ...

    async def tool_call_or_chat(
        self,
        user_message: str,
        tool_manifest: str,
        history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]: ...

    async def is_available(self) -> bool: ...

    async def list_models(self) -> list[str]: ...
