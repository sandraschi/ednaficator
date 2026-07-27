"""
Deterministic Plex tool layer for the Edna Media Concierge (PRD.md, RECIPE-EDNA-V1.md Step 2).

Intentionally has NO LLM in it — fuzzy matching (rapidfuzz) + plexapi calls only, so
it is independently testable against a live Plex server. `concierge/tools.py` maps the
PRD's three verbs (resolve_and_play, browse, play_music) onto these primitives.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from loguru import logger

try:
    from plexapi.exceptions import NotFound
    from plexapi.server import PlexServer
except ImportError:  # pragma: no cover - plexapi is a hard dep now, but stay defensive
    PlexServer = None  # type: ignore[assignment,misc]
    NotFound = Exception  # type: ignore[assignment,misc]

try:
    from rapidfuzz import fuzz
except ImportError:  # pragma: no cover
    fuzz = None  # type: ignore[assignment]


MediaType = Literal["movie", "show", "episode"]


class PlexUnavailable(RuntimeError):
    """Plex server unreachable, misconfigured, or plexapi missing."""


class ClientUnreachable(RuntimeError):
    """Named Plex client not found, or playback command failed."""


@dataclass
class MediaHit:
    rating_key: int
    title: str
    year: int | None
    media_type: str  # movie | show | episode | artist | album | track | playlist
    library: str
    score: float = 100.0


@dataclass
class PlayResult:
    success: bool
    client: str
    title: str
    message: str


_UMLAUT_MAP = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})


def _normalize(text: str) -> str:
    return text.lower().translate(_UMLAUT_MAP).strip()


def _score(query: str, *candidates: str) -> float:
    q = _normalize(query)
    names = [_normalize(c) for c in candidates if c]
    if not names:
        return 0.0
    if fuzz is None:  # pragma: no cover - only hit if rapidfuzz missing
        return 100.0 if any(q in n for n in names) else 0.0
    return max(fuzz.WRatio(q, n) for n in names)


def get_server(url: str, token: str) -> PlexServer:
    """Connect to Plex. Raises PlexUnavailable on any failure (unreachable, bad token)."""
    if PlexServer is None:
        raise PlexUnavailable("plexapi is not installed")
    if not url or not token:
        raise PlexUnavailable("PLEX_URL / PLEX_TOKEN not configured")
    try:
        return PlexServer(url, token)
    except Exception as exc:  # plexapi raises several exception types on connect failure
        raise PlexUnavailable(f"Cannot reach Plex at {url}: {exc}") from exc


def list_clients(server: PlexServer) -> list[str]:
    """Names of currently-registered/reachable Plex clients (TVs, apps)."""
    try:
        return [c.title for c in server.clients()]
    except Exception as exc:
        logger.warning(f"list_clients failed: {exc}")
        return []


def resolve_media(
    server: PlexServer,
    query: str,
    media_type: MediaType | None = None,
    limit: int = 5,
    min_score: float = 60.0,
) -> list[MediaHit]:
    """Fuzzy search movie/show libraries for `query`. Matches title + original title."""
    hits: list[MediaHit] = []

    for section in server.library.sections():
        if section.type not in ("movie", "show"):
            continue
        if media_type and section.type != media_type:
            continue
        try:
            items = section.all()
        except Exception as exc:
            logger.warning(f"resolve_media: section '{section.title}' scan failed: {exc}")
            continue

        for item in items:
            titles = [item.title, getattr(item, "originalTitle", "") or ""]
            score = _score(query, *titles)
            if score >= min_score:
                hits.append(
                    MediaHit(
                        rating_key=item.ratingKey,
                        title=item.title,
                        year=getattr(item, "year", None),
                        media_type=section.type,
                        library=section.title,
                        score=score,
                    )
                )

    hits.sort(key=lambda h: h.score, reverse=True)
    return hits[:limit]


def resolve_music(
    server: PlexServer,
    query: str,
    limit: int = 5,
    min_score: float = 55.0,
) -> list[MediaHit]:
    """Fuzzy search artist/album/playlist names for `query`."""
    hits: list[MediaHit] = []

    for section in server.library.sections():
        if section.type != "artist":
            continue
        try:
            artists = (
                section.searchArtists() if hasattr(section, "searchArtists") else section.all()
            )
        except Exception as exc:
            logger.warning(f"resolve_music: section '{section.title}' scan failed: {exc}")
            continue

        for artist in artists:
            score = _score(query, artist.title)
            if score >= min_score:
                hits.append(
                    MediaHit(
                        rating_key=artist.ratingKey,
                        title=artist.title,
                        year=None,
                        media_type="artist",
                        library=section.title,
                        score=score,
                    )
                )

    try:
        for playlist in server.playlists(playlistType="audio"):
            score = _score(query, playlist.title)
            if score >= min_score:
                hits.append(
                    MediaHit(
                        rating_key=playlist.ratingKey,
                        title=playlist.title,
                        year=None,
                        media_type="playlist",
                        library="Playlists",
                        score=score,
                    )
                )
    except Exception as exc:
        logger.debug(f"resolve_music: playlist scan skipped: {exc}")

    hits.sort(key=lambda h: h.score, reverse=True)
    return hits[:limit]


def play(server: PlexServer, rating_key: int, client_name: str) -> PlayResult:
    """Play the item identified by `rating_key` on the named Plex client."""
    try:
        item = server.fetchItem(rating_key)
    except NotFound as exc:
        raise ClientUnreachable(f"Media item {rating_key} not found: {exc}") from exc

    try:
        client = server.client(client_name)
    except NotFound as exc:
        raise ClientUnreachable(f"Plex client '{client_name}' not found or offline: {exc}") from exc

    try:
        client.proxyThroughServer()
        client.playMedia(item)
    except Exception as exc:
        raise ClientUnreachable(f"Playback on '{client_name}' failed: {exc}") from exc

    return PlayResult(
        success=True,
        client=client_name,
        title=item.title,
        message=f"'{item.title}' spielt jetzt auf {client_name}.",
    )
