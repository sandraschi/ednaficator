"""Tests for Edna news + speech concierge adapters."""

from __future__ import annotations

from ednaficator.concierge import news_tools, speech_tools
from ednaficator.concierge.news_concierge import NewsConcierge
from ednaficator.concierge.news_tools import DigestSnapshot


def test_fetch_digest_parses_preview(monkeypatch):
    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "subject": "AI News",
                "text_body": "OpenAI released a model.",
                "html_body": "<p>html</p>",
                "item_ids": [1, 2],
            }

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, path, params=None):
            assert path == "/api/digest/preview"
            return FakeResponse()

    monkeypatch.setattr(news_tools.httpx, "Client", FakeClient)
    digest = news_tools.fetch_digest(hours=24)
    assert digest.subject == "AI News"
    assert digest.item_count == 2


def test_family_spoken_intro():
    digest = DigestSnapshot(
        subject="Fleet",
        text_body="Item one.",
        html_body="",
        item_count=1,
    )
    spoken = news_tools.family_spoken_intro(digest)
    assert "Nachrichten-Zusammenfassung" in spoken
    assert "Item one." in spoken


def test_read_digest_aloud_success(monkeypatch):
    digest = DigestSnapshot(
        subject="News",
        text_body="Hello fleet.",
        html_body="",
        item_count=1,
    )
    monkeypatch.setattr(news_tools, "fetch_digest", lambda **kw: digest)
    monkeypatch.setattr(speech_tools, "synthesize_wav", lambda text: b"RIFF")
    concierge = NewsConcierge()
    result = concierge.read_digest_aloud()
    assert result.success is True
    assert result.audio_bytes == b"RIFF"


def test_synthesize_wav_http_error(monkeypatch):
    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, path, params=None):
            class R:
                status_code = 503
                content = b""

            return R()

    monkeypatch.setattr(speech_tools.httpx, "Client", FakeClient)
    try:
        speech_tools.synthesize_wav("test")
        raise AssertionError("expected SpeechUnavailable")
    except speech_tools.SpeechUnavailable:
        pass
