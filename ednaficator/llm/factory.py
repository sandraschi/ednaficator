"""Build the active LLM client from Edna config."""

from __future__ import annotations

from typing import Any

from ednaficator.llm.base import LLMClient, LLMProvider
from ednaficator.llm.lmstudio_client import LMStudioClient
from ednaficator.llm.ollama_client import OllamaClient


def create_llm_client(config: dict[str, Any]) -> LLMClient:
    provider: LLMProvider = config.get("llm_provider", "ollama")  # type: ignore[assignment]

    if provider == "lmstudio":
        return LMStudioClient(
            base_url=config.get("lmstudio_base_url", "http://127.0.0.1:1234/v1"),
            model=config.get("lmstudio_model", ""),
        )

    return OllamaClient(
        base_url=config.get("ollama_base_url", "http://localhost:11434"),
        model=config.get("ollama_model", "qwen2.5:27b"),
    )


def active_model_name(config: dict[str, Any]) -> str:
    if config.get("llm_provider") == "lmstudio":
        return config.get("lmstudio_model") or "(auto)"
    return config.get("ollama_model", "qwen2.5:27b")
