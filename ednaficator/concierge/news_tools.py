"""
Thin HTTP adapter to aiwatcher-mcp digest API for Edna family concierge (Phase 3).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx
from loguru import logger


class NewsUnavailable(Exception):
    """aiwatcher-mcp unreachable."""


@dataclass
class DigestSnapshot:
    subject: str
    text_body: str
    html_body: str
    item_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "text_body": self.text_body,
            "html_body": self.html_body,
            "item_count": self.item_count,
        }


def _base_url() -> str:
    return os.environ.get("EDNA_AIWATCHER_MCP_URL", "http://127.0.0.1:10946").rstrip("/")


def configured() -> bool:
    return bool(_base_url())


def fetch_digest(*, hours: int = 24) -> DigestSnapshot:
    """Fetch latest digest preview from aiwatcher-mcp."""
    hours = max(1, min(hours, 72))
    try:
        with httpx.Client(base_url=_base_url(), timeout=120.0) as client:
            response = client.get("/api/digest/preview", params={"hours": hours})
    except httpx.HTTPError as exc:
        logger.error(f"fetch_digest: {exc}")
        raise NewsUnavailable("Nachrichten sind gerade nicht erreichbar.") from exc

    if response.status_code >= 400:
        raise NewsUnavailable(f"Digest fehlgeschlagen (HTTP {response.status_code}).")

    data = response.json()
    text_body = str(data.get("text_body") or "").strip()
    subject = str(data.get("subject") or "Nachrichten")
    html_body = str(data.get("html_body") or "")
    item_ids = data.get("item_ids") or []
    return DigestSnapshot(
        subject=subject,
        text_body=text_body,
        html_body=html_body,
        item_count=len(item_ids) if isinstance(item_ids, list) else 0,
    )


def family_spoken_intro(digest: DigestSnapshot) -> str:
    """German intro + digest text for TTS (Edna-facing)."""
    if not digest.text_body:
        return "Heute gibt es keine Nachrichten zum Vorlesen."
    intro = f"Hier ist die Nachrichten-Zusammenfassung: {digest.subject}."
    return f"{intro}\n\n{digest.text_body}"
