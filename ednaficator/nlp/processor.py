"""
NLPProcessor — lightweight intent parsing layer.

In Ednaficator 2.0 most heavy lifting moved to OllamaClient.tool_call_or_chat().
This module is now a thin pre-processor:
  - quick keyword triage (returns early for obvious cases)
  - falls back to Ollama for anything ambiguous
  - retains Austrian German normalization

Kept structurally close to the original so tests can still import it.
"""

from __future__ import annotations

import re
import asyncio
from dataclasses import dataclass, field
from typing import Any

from loguru import logger


@dataclass
class Intent:
    """Parsed user intent — used internally and in legacy code paths."""
    category: str        # home, media, austrian_services, shopping, general, workflow
    action: str
    target: str
    params: dict[str, Any] = field(default_factory=dict)
    workflow: str | None = None
    confidence: float = 0.0


# Keyword → category quick-match table
_QUICK_PATTERNS: list[tuple[str, str, str, str]] = [
    # (pattern, category, action, target)
    (r"(vacation|urlaub|verreise)", "workflow", "execute_workflow", "vacation_mode"),
    (r"(guten morgen|morning routine)", "workflow", "execute_workflow", "morning_routine"),
    (r"(sicher|secure|alarm|lock).*(haus|home|wohn)", "home", "secure_home", "security_system"),
    (r"(kamera|camera|cam).*(status|online|check)", "home", "camera_status", "camera"),
    (r"(musik|music|spiel|play).*(plex|media)", "media", "play", "music"),
    (r"(buch|book|calibre)", "media", "search", "book"),
    (r"(film|movie|serie)", "media", "search", "movie"),
    (r"(öbb|bahn|zug|train|wiener.linien|u-bahn)", "austrian_services", "check", "transport"),
    (r"(parkschein|parking.permit|kurzparkzone)", "austrian_services", "help", "parking"),
    (r"(preis|price|günstig|geizhals)", "shopping", "price_check", "product"),
    (r"(wetter|weather|regen|temperatur)", "general", "weather", "vienna"),
]

_AUSTRIAN_MAP = {
    "grüß gott": "hello",
    "servus": "hello",
    "baba": "goodbye",
    "pfiat di": "goodbye",
    "passt scho": "okay",
    "eh klar": "of course",
    "ur leiwand": "very cool",
    "ur ": "very ",
    "leiwand": "cool",
}


class NLPProcessor:
    """
    Lightweight pre-processor. Does quick keyword triage; delegates to
    OllamaClient for anything that doesn't match.

    Note: _llm_parse_intent requires an OllamaClient injected at construction
    or set later via .llm_client. If None, low-confidence intents return
    a generic 'general' intent.
    """

    def __init__(self, local_llm_endpoint: str | None = None, llm_client=None):
        # local_llm_endpoint kept for API compat; actual inference via llm_client
        self.local_llm_endpoint = local_llm_endpoint
        self.llm_client = llm_client  # OllamaClient | None

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    async def parse_intent(self, user_input: str) -> Intent:
        normalized = self._normalize(user_input)
        intent = self._quick_match(normalized)
        if intent.confidence < 0.7 and self.llm_client is not None:
            intent = await self._llm_parse_intent(normalized)
        return intent

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _normalize(self, text: str) -> str:
        t = text.lower().strip()
        for austrian, std in _AUSTRIAN_MAP.items():
            t = t.replace(austrian, std)
        return t

    def _quick_match(self, text: str) -> Intent:
        for pattern, category, action, target in _QUICK_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return Intent(
                    category=category,
                    action=action,
                    target=target,
                    params={"raw": text},
                    workflow=target if category == "workflow" else None,
                    confidence=0.85,
                )
        return Intent(
            category="general",
            action="respond",
            target="conversation",
            params={"raw": text},
            confidence=0.3,
        )

    async def _llm_parse_intent(self, text: str) -> Intent:
        """
        Use OllamaClient for intent extraction when keyword matching fails.
        Returns a structured Intent from a JSON reply.
        """
        if self.llm_client is None:
            return Intent(
                category="general",
                action="respond",
                target="conversation",
                params={"raw": text},
                confidence=0.3,
            )

        prompt = (
            "Classify this user request into a JSON intent object. "
            "Reply with ONLY valid JSON, no markdown.\n"
            'Schema: {"category": str, "action": str, "target": str, '
            '"params": {}, "workflow": str|null, "confidence": float}\n'
            f"Categories: home, media, austrian_services, shopping, workflow, general\n"
            f"Request: {text}"
        )
        try:
            raw = await self.llm_client.chat([{"role": "user", "content": prompt}])
            # Strip possible markdown fences
            raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            import json
            data = json.loads(raw)
            return Intent(
                category=data.get("category", "general"),
                action=data.get("action", "respond"),
                target=data.get("target", "conversation"),
                params=data.get("params", {}),
                workflow=data.get("workflow"),
                confidence=float(data.get("confidence", 0.6)),
            )
        except Exception as exc:
            logger.debug(f"LLM intent parse failed ({exc}), using fallback")
            return Intent(
                category="general",
                action="respond",
                target="conversation",
                params={"raw": text},
                confidence=0.3,
            )

    def extract_entities(self, text: str) -> dict[str, Any]:
        """Extract times and Vienna districts from raw text."""
        entities: dict[str, Any] = {}
        time_matches = re.findall(r"(\d{1,2}):(\d{2})|(\d{1,2})\s*(uhr|h)", text, re.I)
        if time_matches:
            entities["time"] = time_matches
        districts = [
            "innere stadt", "leopoldstadt", "landstraße", "wieden", "margareten",
            "mariahilf", "neubau", "josefstadt", "alsergrund", "favoriten",
        ]
        for d in districts:
            if d in text.lower():
                entities["vienna_district"] = d
                break
        return entities
