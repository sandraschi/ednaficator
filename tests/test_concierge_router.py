"""Tests for concierge chat router (Phase 4)."""

from __future__ import annotations

import pytest
from ednaficator.concierge.email_concierge import EmailConcierge
from ednaficator.concierge.news_concierge import NewsConcierge
from ednaficator.concierge.router import ConciergeRouter
from ednaficator.concierge.tools import PlexConcierge


class FakeLLM:
    provider = "lmstudio"
    base_url = "http://test"
    model = "test"

    def __init__(self, raw: str):
        self._raw = raw
        self._available = True

    async def is_available(self) -> bool:
        return self._available

    async def chat(self, messages, system=None) -> str:
        return self._raw

    async def close(self) -> None:
        pass


@pytest.fixture
def router() -> ConciergeRouter:
    return ConciergeRouter(
        plex=PlexConcierge(url="http://localhost:32400", token="x", default_client="TV"),
        email=EmailConcierge(),
        news=NewsConcierge(),
        enabled={"plex", "email", "news"},
        default_plex_client="TV",
    )


@pytest.mark.asyncio
async def test_concierge_plain_text_reply(router):
    llm = FakeLLM("Servus! Was möchtest du schauen?")
    response = await router.process("hallo", llm=llm)
    assert response.success is True
    assert "Servus" in response.message


@pytest.mark.asyncio
async def test_concierge_executes_plex_tool(monkeypatch, router):
    llm = FakeLLM(
        '{"tool_call": {"server": "concierge", "tool": "browse", "arguments": {"query": "poirot"}}}'
    )

    def fake_browse(query: str):
        from ednaficator.concierge.tools import ConciergeResult

        return ConciergeResult(
            success=True,
            message="2 Treffer:",
            choices=[{"rating_key": 1, "label": "Poirot A", "media_type": "episode", "score": 80}],
        )

    monkeypatch.setattr(router.plex, "browse", fake_browse)
    response = await router.process("was hast du mit poirot", llm=llm)
    assert response.success is True
    assert len(response.choices) == 1
    assert response.choices[0]["label"] == "Poirot A"


def test_execute_play_rating_key(monkeypatch, router):
    from ednaficator.concierge.tools import ConciergeResult

    monkeypatch.setattr(
        router.plex,
        "play_rating_key",
        lambda rating_key, client=None: ConciergeResult(
            success=True,
            message="Läuft.",
            played={"title": "Rex"},
        ),
    )
    response = router.execute_tool("play_rating_key", {"rating_key": 42}, plex_client="TV")
    assert response.success is True
    assert "Läuft" in response.message


def test_tool_manifest_respects_allowlist():
    router = ConciergeRouter(
        plex=PlexConcierge(url="", token="", default_client="TV"),
        email=EmailConcierge(),
        news=NewsConcierge(),
        enabled={"plex"},
        default_plex_client="TV",
    )
    manifest = router.tool_manifest()
    assert "resolve_and_play" in manifest
    assert "email_unread" not in manifest
