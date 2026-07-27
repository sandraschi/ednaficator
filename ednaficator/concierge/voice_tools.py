"""
Voice note transcription for Edna Telegram bot (RECIPE Step 5).

Optional extra: uv sync --extra voice
"""

from __future__ import annotations

import os
from pathlib import Path

from loguru import logger


class VoiceUnavailable(Exception):
    """faster-whisper not installed or transcription failed."""


def transcribe_audio(path: Path, *, language: str | None = None) -> str:
    """Transcribe an audio file to text (default language: de)."""
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise VoiceUnavailable(
            "faster-whisper nicht installiert. Run: uv sync --extra voice"
        ) from exc

    if not path.is_file():
        raise VoiceUnavailable(f"Audiodatei fehlt: {path}")

    model_name = os.environ.get("EDNA_WHISPER_MODEL", "large-v3-turbo")
    device = os.environ.get("EDNA_WHISPER_DEVICE", "cuda")
    compute_type = os.environ.get("EDNA_WHISPER_COMPUTE_TYPE", "int8")
    lang = language or os.environ.get("EDNA_WHISPER_LANGUAGE", "de")

    logger.info(f"Whisper transcribe: model={model_name} device={device} lang={lang}")
    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    segments, _info = model.transcribe(str(path), language=lang, beam_size=1)
    text = " ".join(segment.text.strip() for segment in segments if segment.text.strip())
    if not text:
        raise VoiceUnavailable("Konnte die Sprachnachricht nicht verstehen.")
    return text
