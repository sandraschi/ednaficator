"""
Telegram bot front-end for Edna family concierge (RECIPE-EDNA-V1 Step 4).

Run: uv run python -m ednaficator.bot
Requires: uv sync --extra telegram
"""

from __future__ import annotations

import asyncio
import io
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from loguru import logger

from ednaficator.concierge.allowlist import parse_concierge_tools
from ednaficator.concierge.email_concierge import EmailConcierge
from ednaficator.concierge.news_concierge import NewsConcierge
from ednaficator.concierge.router import ConciergeRouter
from ednaficator.concierge.tools import PlexConcierge
from ednaficator.core.edna import EdnaResponse
from ednaficator.llm.factory import create_llm_client


def _parse_allowed_ids(raw: str) -> set[int]:
    ids: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            ids.add(int(part))
    return ids


def _load_users(path: Path) -> dict[str, dict[str, Any]]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError as exc:
        logger.warning(f"Could not parse {path}: {exc}")
        return {}


def _plex_client_for_user(user_id: int, users: dict[str, dict[str, Any]], default: str) -> str:
    entry = users.get(str(user_id), {})
    return str(entry.get("plex_client") or default)


def _choices_keyboard(choices: list[dict[str, Any]]):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    rows = []
    for choice in choices[:5]:
        label = str(choice.get("label") or "Auswahl")[:40]
        rating_key = choice.get("rating_key")
        if rating_key is None:
            continue
        rows.append([InlineKeyboardButton(label, callback_data=f"plex:{rating_key}")])
    if not rows:
        return None
    return InlineKeyboardMarkup(rows)


async def _run_turn(
    router: ConciergeRouter,
    llm,
    text: str,
    *,
    plex_client: str,
) -> EdnaResponse:
    return await router.process(text, llm=llm, plex_client=plex_client)


async def _reply_concierge(
    message,
    router: ConciergeRouter,
    llm,
    text: str,
    *,
    plex_client: str,
) -> None:
    response = await _run_turn(router, llm, text, plex_client=plex_client)
    markup = _choices_keyboard(response.choices)
    await message.reply_text(response.message, reply_markup=markup)

    if response.tool_result and response.tool_result.get("has_audio"):
        news = NewsConcierge()
        audio_result = news.read_digest_aloud()
        if audio_result.audio_bytes:
            await message.reply_audio(
                audio=io.BytesIO(audio_result.audio_bytes),
                filename="nachrichten.wav",
            )


async def run_bot() -> None:
    try:
        from telegram import Update
        from telegram.ext import (
            Application,
            CallbackQueryHandler,
            CommandHandler,
            ContextTypes,
            MessageHandler,
            filters,
        )
    except ImportError as exc:
        raise SystemExit(
            "python-telegram-bot not installed. Run: uv sync --extra telegram"
        ) from exc

    token = os.environ.get("EDNA_TELEGRAM_TOKEN", "").strip()
    if not token:
        raise SystemExit("Set EDNA_TELEGRAM_TOKEN")

    allowed = _parse_allowed_ids(os.environ.get("EDNA_ALLOWED_IDS", ""))
    if not allowed:
        logger.warning("EDNA_ALLOWED_IDS empty — bot will ignore all users")

    users_path = Path(os.environ.get("EDNA_USERS_FILE", "users.json"))
    users = _load_users(users_path)
    default_client = os.environ.get("EDNA_PLEX_DEFAULT_CLIENT", "Wohnzimmer TV")

    llm = create_llm_client(
        {
            "llm_provider": os.environ.get("EDNA_LLM_PROVIDER", "lmstudio"),
            "ollama_base_url": os.environ.get("EDNA_OLLAMA_BASE_URL", "http://localhost:11434"),
            "ollama_model": os.environ.get("EDNA_OLLAMA_MODEL", "qwen2.5:27b"),
            "lmstudio_base_url": os.environ.get(
                "EDNA_LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1"
            ),
            "lmstudio_model": os.environ.get("EDNA_LMSTUDIO_MODEL", ""),
        }
    )
    if hasattr(llm, "resolve_default_model"):
        await llm.resolve_default_model()  # type: ignore[attr-defined]

    plex = PlexConcierge(
        url=os.environ.get("EDNA_PLEX_URL", "http://localhost:32400"),
        token=os.environ.get("EDNA_PLEX_TOKEN", ""),
        default_client=default_client,
    )
    router = ConciergeRouter(
        plex=plex,
        email=EmailConcierge(),
        news=NewsConcierge(),
        enabled=parse_concierge_tools(),
        default_plex_client=default_client,
    )

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_user or update.effective_user.id not in allowed:
            return
        await update.message.reply_text("Servus! Sag mir was du schauen oder hören willst.")

    async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_user or not update.message:
            return
        user_id = update.effective_user.id
        if user_id not in allowed:
            return
        text = (update.message.text or "").strip()
        if not text:
            return
        client = _plex_client_for_user(user_id, users, default_client)
        await _reply_concierge(update.message, router, llm, text, plex_client=client)

    async def on_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_user or not update.message or not update.message.voice:
            return
        user_id = update.effective_user.id
        if user_id not in allowed:
            return

        voice = update.message.voice
        tmp_path = Path(tempfile.gettempdir()) / f"edna-voice-{voice.file_unique_id}.ogg"
        try:
            tg_file = await context.bot.get_file(voice.file_id)
            await tg_file.download_to_drive(custom_path=str(tmp_path))
            from ednaficator.concierge.voice_tools import VoiceUnavailable, transcribe_audio

            text = transcribe_audio(tmp_path)
        except VoiceUnavailable as exc:
            await update.message.reply_text(str(exc))
            return
        except Exception as exc:
            logger.error(f"Voice note failed: {exc}")
            await update.message.reply_text("Die Sprachnachricht konnte ich nicht verarbeiten.")
            return
        finally:
            tmp_path.unlink(missing_ok=True)

        await update.message.reply_text(f"Verstanden: {text}")
        client = _plex_client_for_user(user_id, users, default_client)
        await _reply_concierge(update.message, router, llm, text, plex_client=client)

    async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        if not query or not query.data or not update.effective_user:
            return
        if update.effective_user.id not in allowed:
            await query.answer()
            return
        await query.answer()
        if not query.data.startswith("plex:"):
            return
        rating_key = int(query.data.split(":", 1)[1])
        client = _plex_client_for_user(update.effective_user.id, users, default_client)
        result = router.execute_tool(
            "play_rating_key",
            {"rating_key": rating_key},
            plex_client=client,
        )
        await query.edit_message_text(result.message)

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_handler(MessageHandler(filters.VOICE, on_voice))
    app.add_handler(CallbackQueryHandler(on_callback))

    logger.info("Edna Telegram bot starting (long polling)")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        await llm.close()


def main() -> None:
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
