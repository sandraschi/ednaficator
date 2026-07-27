"""Family email concierge verbs (German copy) over email_tools."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from ednaficator.concierge import email_tools


@dataclass
class ConciergeResult:
    success: bool
    message: str
    items: list[dict[str, Any]] = field(default_factory=list)
    sent: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EmailConcierge:
    @property
    def configured(self) -> bool:
        return email_tools.configured()

    def status(self) -> dict[str, Any]:
        return {"configured": self.configured, "base_url": email_tools._base_url()}

    def unread_summaries(self, *, limit: int = 5) -> ConciergeResult:
        try:
            rows = email_tools.list_unread_summaries(limit=limit)
        except email_tools.EmailUnavailable as exc:
            return ConciergeResult(success=False, message=str(exc))

        if not rows:
            return ConciergeResult(success=True, message="Keine ungelesenen E-Mails.")

        items = [row.to_dict() for row in rows]
        return ConciergeResult(
            success=True,
            message=f"{len(items)} ungelesene E-Mail(s).",
            items=items,
        )

    def send(self, *, to: str, subject: str, body: str) -> ConciergeResult:
        result = email_tools.send_short_message(to=to, subject=subject, body=body)
        if not result.get("success"):
            return ConciergeResult(
                success=False,
                message=str(result.get("error") or "Senden fehlgeschlagen."),
            )
        return ConciergeResult(
            success=True,
            message=str(result.get("message") or "Gesendet."),
            sent=result.get("detail"),
        )
