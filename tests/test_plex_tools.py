"""
Tests for ednaficator/concierge/plex_tools.py (RECIPE-EDNA-V1.md Step 2).

Pure-logic tests (normalize/score) run always. The `plex_live` tests hit a real
local Plex server (localhost:32400 by default) and are skipped automatically if
it isn't reachable — no mocks stand in for the live server per RECIPE-EDNA-V1.md.
"""

from __future__ import annotations

import os

import pytest
from ednaficator.concierge.plex_tools import (
    MediaHit,
    PlexUnavailable,
    _normalize,
    _score,
    get_server,
    list_clients,
    resolve_media,
)


def test_normalize_umlauts_and_case():
    assert _normalize("Kommissar Rex") == "kommissar rex"
    assert _normalize("Müller") == "mueller"
    assert _normalize("STRASSE") == "strasse"


def test_score_exact_match_is_high():
    assert _score("kommissar rex", "Kommissar Rex") >= 95.0


def test_score_dialect_query_still_matches():
    # PRD.md example: "den mit dem Hund" doesn't literally match "Kommissar Rex",
    # but a title-only fuzzy match on "rex" fragments should score reasonably.
    assert _score("rex", "Kommissar Rex") >= 50.0


def test_score_no_match_is_low():
    assert _score("xyzzy plugh quux", "Kommissar Rex") < 50.0


def test_score_empty_candidates_is_zero():
    assert _score("anything", "", "") == 0.0


def test_get_server_requires_url_and_token():
    with pytest.raises(PlexUnavailable):
        get_server("", "")
    with pytest.raises(PlexUnavailable):
        get_server("http://localhost:32400", "")


# ---------------------------------------------------------------------------
# Live Plex tests — RECIPE-EDNA-V1.md Step 2 verification gate.
# Skipped unless EDNA_PLEX_TOKEN is set and the server actually responds.
# ---------------------------------------------------------------------------


def _live_server():
    url = os.environ.get("EDNA_PLEX_URL", "http://localhost:32400")
    token = os.environ.get("EDNA_PLEX_TOKEN", "")
    if not token:
        pytest.skip("EDNA_PLEX_TOKEN not set — skipping live Plex test")
    try:
        return get_server(url, token)
    except PlexUnavailable as exc:
        pytest.skip(f"Plex not reachable: {exc}")


@pytest.mark.plex_live
def test_resolve_media_kommissar_rex_live():
    server = _live_server()
    hits = resolve_media(server, "kommissar rex")
    assert hits, "expected at least one hit for 'kommissar rex' against a live library"
    assert isinstance(hits[0], MediaHit)


@pytest.mark.plex_live
def test_list_clients_live():
    server = _live_server()
    clients = list_clients(server)
    assert isinstance(clients, list)
