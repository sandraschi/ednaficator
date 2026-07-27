"""
Tests for ednaficator/concierge/tools.py — the PRD.md v1 verbs, with plex_tools
mocked out so these run without a live Plex server.
"""

from __future__ import annotations

import pytest
from ednaficator.concierge import tools as concierge_tools
from ednaficator.concierge.plex_tools import (
    ClientUnreachable,
    MediaHit,
    PlayResult,
    PlexUnavailable,
)
from ednaficator.concierge.tools import PlexConcierge


@pytest.fixture
def concierge() -> PlexConcierge:
    c = PlexConcierge(
        url="http://localhost:32400", token="fake-token", default_client="Wohnzimmer TV"
    )
    c._server = object()  # bypass get_server(); resolve_media/play are mocked anyway
    return c


def test_not_configured_without_url_or_token():
    c = PlexConcierge(url="", token="")
    assert c.configured is False


def test_configured_with_url_and_token():
    c = PlexConcierge(url="http://localhost:32400", token="x")
    assert c.configured is True


def test_resolve_and_play_requires_client():
    c = PlexConcierge(url="http://localhost:32400", token="x", default_client="")
    result = c.resolve_and_play("kommissar rex", client=None)
    assert result.success is False
    assert "Client" in result.message


def test_resolve_and_play_auto_plays_confident_single_match(monkeypatch, concierge):
    hit = MediaHit(
        rating_key=101,
        title="Kommissar Rex",
        year=1994,
        media_type="show",
        library="TV",
        score=98.0,
    )
    monkeypatch.setattr(concierge_tools, "resolve_media", lambda server, query, **kw: [hit])
    monkeypatch.setattr(
        concierge_tools,
        "play",
        lambda server, rating_key, client_name: PlayResult(
            success=True,
            client=client_name,
            title="Kommissar Rex",
            message="'Kommissar Rex' spielt jetzt auf Wohnzimmer TV.",
        ),
    )

    result = concierge.resolve_and_play("i wüll den Rex schauen")

    assert result.success is True
    assert result.played is not None
    assert result.played["client"] == "Wohnzimmer TV"
    assert not result.choices


def test_resolve_and_play_returns_choices_when_ambiguous(monkeypatch, concierge):
    hits = [
        MediaHit(
            rating_key=1,
            title="Miss Marple (Hickson)",
            year=1984,
            media_type="show",
            library="TV",
            score=70.0,
        ),
        MediaHit(
            rating_key=2,
            title="Miss Marple (McEwan)",
            year=2004,
            media_type="show",
            library="TV",
            score=68.0,
        ),
    ]
    monkeypatch.setattr(concierge_tools, "resolve_media", lambda server, query, **kw: hits)
    played_called = False

    def _play(*args, **kwargs):
        nonlocal played_called
        played_called = True
        raise AssertionError("play() should not be called for ambiguous matches")

    monkeypatch.setattr(concierge_tools, "play", _play)

    result = concierge.resolve_and_play("die alte Dame, die strickt")

    assert result.success is True
    assert result.played is None
    assert len(result.choices) == 2
    assert played_called is False


def test_resolve_and_play_no_match(monkeypatch, concierge):
    monkeypatch.setattr(concierge_tools, "resolve_media", lambda server, query, **kw: [])
    result = concierge.resolve_and_play("etwas ganz unbekanntes")
    assert result.success is False
    assert not result.choices


def test_resolve_and_play_client_unreachable_gives_german_failure_copy(monkeypatch, concierge):
    hit = MediaHit(
        rating_key=1, title="Kommissar Rex", year=1994, media_type="show", library="TV", score=99.0
    )
    monkeypatch.setattr(concierge_tools, "resolve_media", lambda server, query, **kw: [hit])

    def _play(*args, **kwargs):
        raise ClientUnreachable("client offline")

    monkeypatch.setattr(concierge_tools, "play", _play)

    result = concierge.resolve_and_play("kommissar rex")

    assert result.success is False
    assert "Fernseher" in result.message


def test_browse_returns_up_to_five_choices(monkeypatch, concierge):
    hits = [
        MediaHit(
            rating_key=i,
            title=f"Poirot Folge {i}",
            year=1990 + i,
            media_type="episode",
            library="TV",
            score=80.0,
        )
        for i in range(5)
    ]
    monkeypatch.setattr(concierge_tools, "resolve_media", lambda server, query, **kw: hits)

    result = concierge.browse("poirot")

    assert result.success is True
    assert len(result.choices) == 5


def test_play_music_auto_plays_confident_match(monkeypatch, concierge):
    hit = MediaHit(
        rating_key=55,
        title="Wolfgang Ambros",
        year=None,
        media_type="artist",
        library="Music",
        score=95.0,
    )
    monkeypatch.setattr(concierge_tools, "resolve_music", lambda server, query, **kw: [hit])
    monkeypatch.setattr(
        concierge_tools,
        "play",
        lambda server, rating_key, client_name: PlayResult(
            success=True, client=client_name, title="Wolfgang Ambros", message="ok"
        ),
    )

    result = concierge.play_music("spü mir an Ambros")

    assert result.success is True
    assert result.played["title"] == "Wolfgang Ambros"


def test_play_music_plex_unavailable(monkeypatch):
    c = PlexConcierge(url="http://localhost:32400", token="fake", default_client="Wohnzimmer TV")

    def _get_server(url, token):
        raise PlexUnavailable("down")

    monkeypatch.setattr(concierge_tools, "get_server", _get_server)

    result = c.play_music("ambros")

    assert result.success is False
    assert "Fernseher" in result.message
