"""
Thin HTTP adapter to email-mcp for Edna family concierge (Phase 2).

Uses email-mcp REST (port 10813) with HTTP Basic auth, not MCP stdio.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx
from loguru import logger


class EmailUnavailable(Exception):
    """email-mcp unreachable or misconfigured."""


@dataclass
class EmailSummary:
    message_id: str
    subject: str
    sender: str
    date: str
    preview: str
    unread: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "subject": self.subject,
            "from": self.sender,
            "date": self.date,
            "preview": self.preview,
            "unread": self.unread,
        }


def _base_url() -> str:
    return os.environ.get("EDNA_EMAIL_MCP_URL", "http://127.0.0.1:10813").rstrip("/")


def _auth() -> tuple[str, str]:
    user = os.environ.get("EDNA_EMAIL_MCP_USER", os.environ.get("MCP_WEB_USER", "sandra"))
    password = os.environ.get(
        "EDNA_EMAIL_MCP_PASSWORD",
        os.environ.get("MCP_WEB_PASSWORD", "vienna2026"),
    )
    return user, password


def configured() -> bool:
    return bool(_base_url())


def _client() -> httpx.Client:
    return httpx.Client(base_url=_base_url(), auth=_auth(), timeout=30.0)


def _raise_for_status(response: httpx.Response) -> None:
    if response.status_code == 401:
        raise EmailUnavailable("email-mcp auth failed (check EDNA_EMAIL_MCP_USER/PASSWORD)")
    if response.status_code >= 400:
        raise EmailUnavailable(f"email-mcp HTTP {response.status_code}: {response.text[:200]}")


def _preview(body: str, limit: int = 120) -> str:
    text = " ".join(body.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def list_unread_summaries(*, limit: int = 5, service: str = "default") -> list[EmailSummary]:
    """Fetch unread inbox rows as short German-friendly summaries."""
    try:
        with _client() as client:
            response = client.get(
                "/api/inbox",
                params={
                    "service": service,
                    "limit": limit,
                    "unread_only": True,
                },
            )
            _raise_for_status(response)
            payload = response.json()
    except httpx.HTTPError as exc:
        logger.error(f"list_unread_summaries: {exc}")
        raise EmailUnavailable("Postfach ist gerade nicht erreichbar.") from exc

    emails = payload.get("emails") or payload.get("messages") or []
    summaries: list[EmailSummary] = []
    for row in emails[:limit]:
        if not isinstance(row, dict):
            continue
        body = str(row.get("text_body") or row.get("body") or row.get("snippet") or "")
        summaries.append(
            EmailSummary(
                message_id=str(row.get("id") or row.get("message_id") or ""),
                subject=str(row.get("subject") or "(ohne Betreff)"),
                sender=str(row.get("from") or row.get("sender") or "Unbekannt"),
                date=str(row.get("date") or ""),
                preview=_preview(body),
                unread=bool(row.get("unread", True)),
            )
        )
    return summaries


def send_short_message(
    *,
    to: str,
    subject: str,
    body: str,
    service: str = "default",
) -> dict[str, Any]:
    """Send a plain-text family email via email-mcp."""
    if not to.strip():
        return {"success": False, "error": "Empfänger fehlt."}
    if not subject.strip() or not body.strip():
        return {"success": False, "error": "Betreff und Text sind nötig."}

    try:
        with _client() as client:
            response = client.post(
                "/api/send",
                json={
                    "to": to.strip(),
                    "subject": subject.strip(),
                    "body": body.strip(),
                    "service": service,
                },
            )
            _raise_for_status(response)
            result = response.json()
    except httpx.HTTPError as exc:
        logger.error(f"send_short_message: {exc}")
        return {"success": False, "error": "E-Mail konnte nicht gesendet werden."}

    if not result.get("success", True):
        return {
            "success": False,
            "error": result.get("error") or result.get("message") or "Senden fehlgeschlagen.",
        }
    return {
        "success": True,
        "message": f"E-Mail an {to.strip()} gesendet.",
        "detail": result,
    }
