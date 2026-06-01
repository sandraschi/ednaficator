"""
LMStudioClient — OpenAI-compatible local API (LM Studio default port 1234).

Docs: https://lmstudio.ai/docs/developer/openai-compat
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from loguru import logger

from ednaficator.llm.base import TOOL_CALL_SYSTEM, parse_tool_call_response

LMSTUDIO_BASE = os.environ.get("EDNA_LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
DEFAULT_MODEL = os.environ.get("EDNA_LMSTUDIO_MODEL", "")


class LMStudioClient:
    provider = "lmstudio"

    def __init__(
        self,
        base_url: str = LMSTUDIO_BASE,
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
        payload_messages: list[dict[str, str]] = []
        if system:
            payload_messages.append({"role": "system", "content": system})
        payload_messages.extend(messages)

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": payload_messages,
            "stream": False,
        }

        try:
            resp = await self._client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPError as exc:
            logger.error(f"LM Studio HTTP error: {exc}")
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
            resp = await self._quick.get(f"{self.base_url}/models")
            return resp.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        try:
            resp = await self._quick.get(f"{self.base_url}/models")
            resp.raise_for_status()
            data = resp.json().get("data", [])
            ids = [m.get("id", "") for m in data if m.get("id")]
            return ids
        except Exception as exc:
            logger.warning(f"Could not list LM Studio models: {exc}")
            return []

    async def resolve_default_model(self) -> None:
        """Pick first loaded model if none configured."""
        if self.model:
            return
        models = await self.list_models()
        if models:
            self.model = models[0]
            logger.info(f"LM Studio auto-selected model: {self.model}")
