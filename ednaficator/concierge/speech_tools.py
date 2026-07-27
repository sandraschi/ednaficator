"""
Thin HTTP adapter to speech-mcp TTS for Edna family concierge (Phase 3).
"""

from __future__ import annotations

import os

import httpx
from loguru import logger


class SpeechUnavailable(Exception):
    """speech-mcp unreachable or TTS failed."""


def _base_url() -> str:
    return os.environ.get("EDNA_SPEECH_MCP_URL", "http://127.0.0.1:10909").rstrip("/")


def configured() -> bool:
    return bool(_base_url())


def synthesize_wav(text: str, *, provider: str = "windows", max_chars: int = 8000) -> bytes:
    """Return WAV bytes from speech-mcp GET /api/v1/tts/wav."""
    snippet = text.strip()[:max_chars]
    if not snippet:
        raise SpeechUnavailable("Kein Text zum Vorlesen.")

    try:
        with httpx.Client(base_url=_base_url(), timeout=60.0) as client:
            response = client.get(
                "/api/v1/tts/wav",
                params={"text": snippet, "provider": provider},
            )
    except httpx.HTTPError as exc:
        logger.error(f"synthesize_wav: {exc}")
        raise SpeechUnavailable("Sprachausgabe ist gerade nicht erreichbar.") from exc

    if response.status_code >= 400:
        raise SpeechUnavailable(f"TTS fehlgeschlagen (HTTP {response.status_code}).")
    return response.content
