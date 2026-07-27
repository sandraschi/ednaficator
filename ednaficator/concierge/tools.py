"""
The three PRD.md v1 concierge verbs, built on top of `plex_tools`.

`PlexConcierge` is the thing api_bridge.py (and later EdnaCore, when
EDNA_MODE=concierge) calls. It owns the lazy PlexServer connection and turns
plex_tools' MediaHit/PlayResult primitives into plain dicts suitable for a
Telegram bot (choices → inline buttons) or a JSON API response.

Auto-play threshold: a single hit scoring >= AUTO_PLAY_SCORE is played directly
(matches PRD "thirty seconds later the right episode is playing"); anything else
returns a `choices` list — never guesses among ambiguous matches.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from loguru import logger

from ednaficator.concierge.plex_tools import (
    ClientUnreachable,
    MediaHit,
    PlexUnavailable,
    get_server,
    list_clients,
    play,
    resolve_media,
    resolve_music,
)

AUTO_PLAY_SCORE = 90.0


@dataclass
class ConciergeResult:
    """Uniform response shape for all three concierge tools."""

    success: bool
    message: str
    played: dict[str, Any] | None = None
    choices: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _hit_to_choice(hit: MediaHit) -> dict[str, Any]:
    label = hit.title if not hit.year else f"{hit.title} ({hit.year})"
    return {
        "rating_key": hit.rating_key,
        "label": label,
        "media_type": hit.media_type,
        "score": round(hit.score, 1),
    }


class PlexConcierge:
    """Holds Plex connection config; one instance per api_bridge/EdnaCore process."""

    def __init__(self, url: str, token: str, default_client: str = ""):
        self.url = url
        self.token = token
        self.default_client = default_client
        self._server = None

    @property
    def configured(self) -> bool:
        return bool(self.url and self.token)

    def _get_server(self):
        if self._server is None:
            self._server = get_server(self.url, self.token)
        return self._server

    def clients(self) -> list[str]:
        return list_clients(self._get_server())

    # ------------------------------------------------------------------
    # The three PRD verbs
    # ------------------------------------------------------------------

    def resolve_and_play(self, query: str, client: str | None = None) -> ConciergeResult:
        """Fuzzy NL -> Plex item -> playback on the named client. The whole product."""
        target_client = client or self.default_client
        if not target_client:
            return ConciergeResult(success=False, message="Kein Plex-Client angegeben.")

        try:
            server = self._get_server()
        except PlexUnavailable as exc:
            logger.error(f"resolve_and_play: {exc}")
            return ConciergeResult(
                success=False, message="Schalt bitte den Fernseher ein und schick's nochmal."
            )

        hits = resolve_media(server, query)
        if not hits:
            return ConciergeResult(
                success=False, message="Das hab ich nicht gefunden. Meinst du vielleicht …?"
            )

        best = hits[0]
        if best.score >= AUTO_PLAY_SCORE and (len(hits) == 1 or best.score - hits[1].score >= 15):
            try:
                result = play(server, best.rating_key, target_client)
            except ClientUnreachable as exc:
                logger.warning(f"resolve_and_play playback failed: {exc}")
                return ConciergeResult(
                    success=False,
                    message="Schalt bitte den Fernseher ein und schick's nochmal.",
                )
            return ConciergeResult(success=True, message=result.message, played=asdict(result))

        return ConciergeResult(
            success=True,
            message="Meinst du vielleicht …?",
            choices=[_hit_to_choice(h) for h in hits],
        )

    def browse(self, query: str) -> ConciergeResult:
        """ "was hast du mit Poirot?" -> short list (<=5), as buttons."""
        try:
            server = self._get_server()
        except PlexUnavailable as exc:
            logger.error(f"browse: {exc}")
            return ConciergeResult(success=False, message="Plex ist gerade nicht erreichbar.")

        hits = resolve_media(server, query, min_score=45.0)
        if not hits:
            return ConciergeResult(success=False, message="Dazu hab ich nichts gefunden.")

        return ConciergeResult(
            success=True,
            message=f"{len(hits)} Treffer:",
            choices=[_hit_to_choice(h) for h in hits],
        )

    def play_music(self, query: str, client: str | None = None) -> ConciergeResult:
        """Artist / era / mood -> Plex music playback (Austropop first)."""
        target_client = client or self.default_client
        if not target_client:
            return ConciergeResult(success=False, message="Kein Plex-Client angegeben.")

        try:
            server = self._get_server()
        except PlexUnavailable as exc:
            logger.error(f"play_music: {exc}")
            return ConciergeResult(
                success=False, message="Schalt bitte den Fernseher ein und schick's nochmal."
            )

        hits = resolve_music(server, query)
        if not hits:
            return ConciergeResult(success=False, message="Diese Musik hab ich nicht gefunden.")

        best = hits[0]
        if best.score >= AUTO_PLAY_SCORE and (len(hits) == 1 or best.score - hits[1].score >= 15):
            try:
                result = play(server, best.rating_key, target_client)
            except ClientUnreachable as exc:
                logger.warning(f"play_music playback failed: {exc}")
                return ConciergeResult(
                    success=False,
                    message="Schalt bitte den Fernseher ein und schick's nochmal.",
                )
            return ConciergeResult(success=True, message=result.message, played=asdict(result))

        return ConciergeResult(
            success=True,
            message="Meinst du vielleicht …?",
            choices=[_hit_to_choice(h) for h in hits],
        )

    def play_rating_key(self, rating_key: int, client: str | None = None) -> ConciergeResult:
        """Play a Plex item chosen from inline buttons (Telegram callback)."""
        target_client = client or self.default_client
        if not target_client:
            return ConciergeResult(success=False, message="Kein Plex-Client angegeben.")
        try:
            server = self._get_server()
            result = play(server, rating_key, target_client)
        except PlexUnavailable as exc:
            logger.error(f"play_rating_key: {exc}")
            return ConciergeResult(success=False, message="Plex ist gerade nicht erreichbar.")
        except ClientUnreachable as exc:
            logger.warning(f"play_rating_key playback failed: {exc}")
            return ConciergeResult(
                success=False,
                message="Schalt bitte den Fernseher ein und schick's nochmal.",
            )
        return ConciergeResult(success=True, message=result.message, played=asdict(result))
