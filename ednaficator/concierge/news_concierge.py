"""Family news digest concierge (German copy) over news_tools + speech_tools."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from ednaficator.concierge import news_tools, speech_tools


@dataclass
class ConciergeResult:
    success: bool
    message: str
    digest: dict[str, Any] | None = None
    spoken_text: str | None = None
    audio_bytes: bytes | None = field(default=None, repr=False)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("audio_bytes", None)
        data["has_audio"] = self.audio_bytes is not None
        return data


class NewsConcierge:
    @property
    def configured(self) -> bool:
        return news_tools.configured()

    def status(self) -> dict[str, Any]:
        return {
            "configured": self.configured,
            "aiwatcher_url": news_tools._base_url(),
            "speech_configured": speech_tools.configured(),
        }

    def latest_digest(self, *, hours: int = 24) -> ConciergeResult:
        try:
            digest = news_tools.fetch_digest(hours=hours)
        except news_tools.NewsUnavailable as exc:
            return ConciergeResult(success=False, message=str(exc))

        if not digest.text_body:
            return ConciergeResult(
                success=True,
                message="Heute gibt es keine Nachrichten.",
                digest=digest.to_dict(),
            )

        return ConciergeResult(
            success=True,
            message=f"{digest.item_count or 'Einige'} Meldungen: {digest.subject}",
            digest=digest.to_dict(),
        )

    def read_digest_aloud(self, *, hours: int = 24) -> ConciergeResult:
        try:
            digest = news_tools.fetch_digest(hours=hours)
        except news_tools.NewsUnavailable as exc:
            return ConciergeResult(success=False, message=str(exc))

        spoken = news_tools.family_spoken_intro(digest)
        if not digest.text_body:
            return ConciergeResult(
                success=True,
                message=spoken,
                digest=digest.to_dict(),
                spoken_text=spoken,
            )

        try:
            audio = speech_tools.synthesize_wav(spoken)
        except speech_tools.SpeechUnavailable as exc:
            return ConciergeResult(
                success=False,
                message=str(exc),
                digest=digest.to_dict(),
                spoken_text=spoken,
            )

        return ConciergeResult(
            success=True,
            message="Nachrichten werden vorgelesen.",
            digest=digest.to_dict(),
            spoken_text=spoken,
            audio_bytes=audio,
        )
