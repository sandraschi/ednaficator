"""
OllamaClient — async wrapper around Ollama's /api/chat endpoint.
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from loguru import logger

from ednaficator.llm.base import TOOL_CALL_SYSTEM, parse_tool_call_response

OLLAMA_BASE = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("EDNA_OLLAMA_MODEL", "qwen2.5:27b")


class OllamaClient:
    provider = "ollama"

    def __init__(
        self,
        base_url: str = OLLAMA_BASE,
        model: str = DEFAULT_MODEL,
        timeout: float = 120.0,
        quick_timeout: float = 5.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._client = httpx.AsyncClient(timeout=timeout)
        self._quick = httpx.AsyncClient(timeout=quick_timeout)

    async def close(self) -> None:
        await self._client.aclose()
        await self._quick.aclose()

    async def chat(
        self,
        messages: list[dict[str, str]],
        system: str | None = None,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        if system:
            payload["system"] = system

        try:
            resp = await self._client.post(f"{self.base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["message"]["content"]
        except httpx.HTTPError as exc:
            logger.error(f"Ollama HTTP error: {exc}")
            raise

    async def tool_call_or_chat(
        self,
        user_message: str,
        tool_manifest: str,
        history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        system = TOOL_CALL_SYSTEM.format(tool_manifest=tool_manifest)
        messages = list(history or [])
        messages.append({"role": "user", "content": user_message})
        raw = await self.chat(messages, system=system)
        return parse_tool_call_response(raw)

    async def is_available(self) -> bool:
        try:
            resp = await self._quick.get(f"{self.base_url}/api/tags")
            return resp.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        try:
            resp = await self._quick.get(f"{self.base_url}/api/tags")
            resp.raise_for_status()
            return [m["name"] for m in resp.json().get("models", [])]
        except Exception as exc:
            logger.warning(f"Could not list Ollama models: {exc}")
            return []
