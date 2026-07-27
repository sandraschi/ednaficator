"""Tests for voice_tools (mocked faster-whisper)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from ednaficator.concierge import voice_tools


def test_transcribe_missing_file():
    with pytest.raises(voice_tools.VoiceUnavailable):
        voice_tools.transcribe_audio(Path("/nonexistent/file.ogg"))


def test_transcribe_success(monkeypatch, tmp_path: Path):
    audio = tmp_path / "note.ogg"
    audio.write_bytes(b"fake")

    class FakeSegment:
        def __init__(self, text: str):
            self.text = text

    class FakeModel:
        def __init__(self, *args, **kwargs):
            pass

        def transcribe(self, path, **kwargs):
            assert Path(path) == audio
            return ([FakeSegment("spü mir an Ambros")], None)

    fake_mod = type(sys)("faster_whisper")
    fake_mod.WhisperModel = FakeModel
    monkeypatch.setitem(sys.modules, "faster_whisper", fake_mod)

    text = voice_tools.transcribe_audio(audio)
    assert "Ambros" in text
