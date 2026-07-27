"""
Concierge chat router — EDNA_MODE=concierge and Telegram bot entry point.

Uses direct Python adapters (plex/email/news), not MCP stdio.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from ednaficator.concierge.allowlist import parse_concierge_tools
from ednaficator.concierge.email_concierge import EmailConcierge
from ednaficator.concierge.news_concierge import NewsConcierge
from ednaficator.concierge.prompts import CONCIERGE_TOOL_CALL_SYSTEM
from ednaficator.concierge.tools import PlexConcierge
from ednaficator.core.edna import EdnaResponse
from ednaficator.llm.base import LLMClient, parse_tool_call_response


class ConciergeRouter:
    def __init__(
        self,
        *,
        plex: PlexConcierge,
        email: EmailConcierge,
        news: NewsConcierge,
        enabled: set[str] | None = None,
        default_plex_client: str = "",
    ):
        self.plex = plex
        self.email = email
        self.news = news
        self.enabled = enabled if enabled is not None else parse_concierge_tools()
        self.default_plex_client = default_plex_client

    def tool_manifest(self) -> str:
        lines: list[str] = []
        if "plex" in self.enabled:
            lines.extend(
                [
                    "- resolve_and_play(query: str) — Film/Serie auf dem Fernseher abspielen",
                    "- browse(query: str) — Auswahl zeigen (≤5 Treffer)",
                    "- play_music(query: str) — Musik abspielen (Austropop, Künstler, Stimmung)",
                    "- play_rating_key(rating_key: int) — gewählten Plex-Titel abspielen (Buttons)",
                ]
            )
        if "email" in self.enabled:
            lines.append("- email_unread(limit: int=5) — ungelesene E-Mails kurz zusammenfassen")
        if "news" in self.enabled:
            lines.extend(
                [
                    "- news_digest(hours: int=24) — Nachrichten-Zusammenfassung",
                    "- news_read_aloud(hours: int=24) — Nachrichten vorlesen",
                ]
            )
        return "\n".join(lines) if lines else "(keine Tools aktiv — EDNA_CONCIERGE_TOOLS setzen)"

    async def process(
        self,
        user_input: str,
        *,
        llm: LLMClient,
        history: list[dict[str, str]] | None = None,
        plex_client: str | None = None,
    ) -> EdnaResponse:
        if not await llm.is_available():
            return EdnaResponse(
                message=(f"Kein LLM erreichbar ({llm.provider}). Starte LM Studio oder Ollama."),
                success=False,
            )

        manifest = self.tool_manifest()
        system = CONCIERGE_TOOL_CALL_SYSTEM.format(tool_manifest=manifest)
        messages = list(history or [])
        messages.append({"role": "user", "content": user_input})
        raw = await llm.chat(messages, system=system)
        parsed = parse_tool_call_response(raw)

        if parsed["type"] != "tool_call" or parsed.get("server") not in (None, "concierge"):
            return EdnaResponse(message=parsed.get("content", raw))

        tool = parsed.get("tool", "")
        args = parsed.get("arguments") or {}
        return self.execute_tool(tool, args, plex_client=plex_client or self.default_plex_client)

    def execute_tool(
        self,
        tool: str,
        args: dict[str, Any],
        *,
        plex_client: str | None = None,
    ) -> EdnaResponse:
        client = plex_client or self.default_plex_client
        logger.info(f"Concierge tool: {tool}({args}) client={client!r}")

        if tool in {"resolve_and_play", "browse", "play_music", "play_rating_key"}:
            if "plex" not in self.enabled:
                return EdnaResponse(
                    message="Fernsehen ist gerade nicht freigeschaltet.", success=False
                )
            return self._plex_tool(tool, args, client)

        if tool == "email_unread":
            if "email" not in self.enabled:
                return EdnaResponse(
                    message="E-Mail ist gerade nicht freigeschaltet.", success=False
                )
            limit = int(args.get("limit") or 5)
            result = self.email.unread_summaries(limit=limit)
            suggestions = [f"{i['subject']} — {i['from']}" for i in result.items[:5]]
            return EdnaResponse(
                message=result.message,
                success=result.success,
                actions_taken=["email_unread"] if result.success else [],
                suggestions=suggestions,
            )

        if tool in {"news_digest", "news_read_aloud"}:
            if "news" not in self.enabled:
                return EdnaResponse(
                    message="Nachrichten sind gerade nicht freigeschaltet.", success=False
                )
            hours = int(args.get("hours") or 24)
            if tool == "news_digest":
                result = self.news.latest_digest(hours=hours)
                text = (result.digest or {}).get("text_body", "") if result.digest else ""
                msg = result.message
                if text and len(text) < 500:
                    msg = f"{msg}\n\n{text[:500]}"
                return EdnaResponse(
                    message=msg,
                    success=result.success,
                    actions_taken=["news_digest"] if result.success else [],
                )
            result = self.news.read_digest_aloud(hours=hours)
            return EdnaResponse(
                message=result.message,
                success=result.success,
                actions_taken=["news_read_aloud"] if result.success else [],
                tool_result={
                    "spoken_text": result.spoken_text,
                    "has_audio": result.audio_bytes is not None,
                },
            )

        return EdnaResponse(
            message=f"Das Tool '{tool}' kenne ich nicht.",
            success=False,
        )

    def _plex_tool(self, tool: str, args: dict[str, Any], client: str | None) -> EdnaResponse:
        if tool == "play_rating_key":
            rating_key = args.get("rating_key")
            if rating_key is None:
                return EdnaResponse(message="Kein Titel gewählt.", success=False)
            result = self.plex.play_rating_key(int(rating_key), client)
        elif tool == "browse":
            result = self.plex.browse(str(args.get("query") or ""))
        elif tool == "play_music":
            result = self.plex.play_music(str(args.get("query") or ""), client)
        else:
            result = self.plex.resolve_and_play(str(args.get("query") or ""), client)

        choices = [
            {
                "rating_key": c["rating_key"],
                "label": c["label"],
                "media_type": c.get("media_type"),
            }
            for c in result.choices
        ]
        return EdnaResponse(
            message=result.message,
            success=result.success,
            actions_taken=[tool] if result.success else [],
            choices=choices,
            tool_call={"tool": tool, "arguments": args} if result.played else None,
        )
