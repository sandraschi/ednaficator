from __future__ import annotations

import asyncio
import sys
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Literal

from ednaficator.concierge.allowlist import parse_concierge_tools
from ednaficator.concierge.email_concierge import EmailConcierge
from ednaficator.concierge.news_concierge import NewsConcierge
from ednaficator.concierge.router import ConciergeRouter
from ednaficator.concierge.tools import PlexConcierge
from ednaficator.core.edna import EdnaCore
from ednaficator.mcp.orchestrator import EAGER_SERVERS
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings
from starlette.responses import Response

# Windows: uvicorn defaults to SelectorEventLoop which doesn't support
# create_subprocess_exec. Must set ProactorEventLoop before uvicorn starts.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


class Settings(BaseSettings):
    llm_provider: Literal["ollama", "lmstudio"] = "lmstudio"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:27b"
    lmstudio_base_url: str = "http://127.0.0.1:1234/v1"
    lmstudio_model: str = ""
    ui_port: int = 10943
    api_port: int = 10942
    debug: bool = False

    # Track B — Edna Media Concierge (PRD.md). "orchestrator" keeps today's
    # full MCP-fleet chat; "concierge" narrows chat to the Plex tools below.
    mode: Literal["orchestrator", "concierge"] = "orchestrator"
    plex_url: str = "http://localhost:32400"
    plex_token: str = ""
    plex_default_client: str = ""

    model_config = ConfigDict(env_prefix="EDNA_", case_sensitive=False)

    @property
    def active_model(self) -> str:
        if self.llm_provider == "lmstudio":
            return self.lmstudio_model or "(auto)"
        return self.ollama_model


settings = Settings()

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------

edna: EdnaCore | None = None
_ws_connections: list[WebSocket] = []
concierge = PlexConcierge(
    url=settings.plex_url,
    token=settings.plex_token,
    default_client=settings.plex_default_client,
)
email_concierge = EmailConcierge()
news_concierge = NewsConcierge()
concierge_router = ConciergeRouter(
    plex=concierge,
    email=email_concierge,
    news=news_concierge,
    enabled=parse_concierge_tools(),
    default_plex_client=settings.plex_default_client,
)


def _now() -> str:
    return datetime.now(UTC).isoformat()


# ---------------------------------------------------------------------------
# Lifespan (Startup / Shutdown)
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    global edna
    logger.info(
        f"Ednaficator API starting — provider={settings.llm_provider} model={settings.active_model}"
    )

    config = {
        "llm_provider": settings.llm_provider,
        "ollama_base_url": settings.ollama_base_url,
        "ollama_model": settings.ollama_model,
        "lmstudio_base_url": settings.lmstudio_base_url,
        "lmstudio_model": settings.lmstudio_model,
        "mode": settings.mode,
        "plex_default_client": settings.plex_default_client,
    }

    edna = EdnaCore(config, concierge_router=concierge_router)
    try:
        await edna.initialize()
        logger.info("Edna core initialized and ready.")
    except Exception as exc:
        logger.error(f"Edna initialization error: {exc}")

    yield

    # Shutdown
    if edna:
        await edna.shutdown()
    logger.info("Ednaficator API shut down gracefully.")


# ---------------------------------------------------------------------------
# App Assembly
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Ednaficator API",
    version="3.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://localhost:{settings.ui_port}",
        "http://localhost:5173",
        "http://localhost:3000",
        "*",  # Allow all for local fleet access
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    message: str


class SettingsUpdate(BaseModel):
    llm_provider: Literal["ollama", "lmstudio"] | None = None
    ollama_base_url: str | None = None
    ollama_model: str | None = None
    lmstudio_base_url: str | None = None
    lmstudio_model: str | None = None
    debug: bool | None = None


class ConciergePlayRequest(BaseModel):
    query: str
    client: str | None = None


class ConciergeBrowseRequest(BaseModel):
    query: str


class ConciergeEmailSendRequest(BaseModel):
    to: str
    subject: str
    body: str


class ConciergeEmailUnreadRequest(BaseModel):
    limit: int = 5


class ConciergeNewsDigestRequest(BaseModel):
    hours: int = 24


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/")
async def root():
    return {
        "name": "Ednaficator API",
        "version": "3.0.0",
        "status": "running",
        "llm_provider": settings.llm_provider,
        "model": settings.active_model,
        "timestamp": _now(),
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "edna_ready": edna is not None and edna.running,
        "ws_connections": len(_ws_connections),
        "timestamp": _now(),
    }


@app.get("/api/status")
async def get_status():
    if not edna:
        raise HTTPException(status_code=503, detail="Edna not initialized")
    return {"timestamp": _now(), **edna.get_status()}


@app.post("/api/chat")
async def chat(request: ChatRequest):
    if not edna:
        raise HTTPException(status_code=503, detail="Edna not initialized")

    msg = request.message.strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Empty message")

    response = await edna.process_request(msg)
    return {
        "message": response.message,
        "actions_taken": response.actions_taken,
        "suggestions": response.suggestions,
        "choices": response.choices,
        "success": response.success,
        "mode": settings.mode,
        "timestamp": _now(),
    }


@app.get("/api/servers")
async def list_servers():
    if not edna:
        raise HTTPException(status_code=503, detail="Edna not initialized")

    status = edna.mcp_orchestrator.get_status()
    registry = edna.mcp_orchestrator.registry
    return {
        **registry.info(),
        "eager_servers": sorted(EAGER_SERVERS),
        "servers": [
            {
                "name": name,
                "ready": info["ready"],
                "tool_count": info["tool_count"],
                "error": info["error"],
            }
            for name, info in status.items()
        ],
    }


@app.get("/api/models")
async def list_models():
    """List models from the active LLM provider."""
    if not edna:
        raise HTTPException(status_code=503, detail="Edna not initialized")

    models = await edna.llm.list_models()
    return {
        "models": models,
        "current": edna.llm.model,
        "provider": edna.llm.provider,
    }


@app.get("/api/providers")
async def list_providers():
    """Health check for both local LLM backends."""
    from ednaficator.llm.lmstudio_client import LMStudioClient
    from ednaficator.llm.ollama_client import OllamaClient

    ollama = OllamaClient(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
    )
    lmstudio = LMStudioClient(
        base_url=settings.lmstudio_base_url,
        model=settings.lmstudio_model,
    )
    try:
        ollama_ok = await ollama.is_available()
        lmstudio_ok = await lmstudio.is_available()
        ollama_models = await ollama.list_models() if ollama_ok else []
        lmstudio_models = await lmstudio.list_models() if lmstudio_ok else []
    finally:
        await ollama.close()
        await lmstudio.close()

    return {
        "active": settings.llm_provider,
        "ollama": {
            "available": ollama_ok,
            "base_url": settings.ollama_base_url,
            "models": ollama_models,
        },
        "lmstudio": {
            "available": lmstudio_ok,
            "base_url": settings.lmstudio_base_url,
            "models": lmstudio_models,
        },
    }


@app.get("/api/settings")
async def get_settings():
    data = settings.model_dump()
    if data.get("plex_token"):
        data["plex_token"] = "***set***"
    return data


@app.post("/api/settings")
async def update_settings(update: SettingsUpdate):
    global edna
    modified = False
    llm_swap = False

    if update.llm_provider is not None and update.llm_provider != settings.llm_provider:
        settings.llm_provider = update.llm_provider
        llm_swap = True
        modified = True

    if update.ollama_base_url is not None:
        settings.ollama_base_url = update.ollama_base_url.rstrip("/")
        if settings.llm_provider == "ollama":
            llm_swap = True
        modified = True

    if update.ollama_model is not None and update.ollama_model != settings.ollama_model:
        settings.ollama_model = update.ollama_model
        if settings.llm_provider == "ollama" and edna and not llm_swap:
            edna.llm.model = update.ollama_model
            logger.info(f"Ollama model hotswapped to: {update.ollama_model}")
        elif settings.llm_provider == "ollama":
            llm_swap = True
        modified = True

    if update.lmstudio_base_url is not None:
        settings.lmstudio_base_url = update.lmstudio_base_url.rstrip("/")
        if settings.llm_provider == "lmstudio":
            llm_swap = True
        modified = True

    if update.lmstudio_model is not None and update.lmstudio_model != settings.lmstudio_model:
        settings.lmstudio_model = update.lmstudio_model
        if settings.llm_provider == "lmstudio" and edna and not llm_swap:
            edna.llm.model = update.lmstudio_model
            logger.info(f"LM Studio model hotswapped to: {update.lmstudio_model}")
        elif settings.llm_provider == "lmstudio":
            llm_swap = True
        modified = True

    if update.debug is not None:
        settings.debug = update.debug
        modified = True

    if llm_swap and edna:
        await edna.replace_llm(settings.model_dump())
        logger.info(f"LLM provider swap: {settings.llm_provider} model={edna.llm.model}")

    dump = settings.model_dump()
    if dump.get("plex_token"):
        dump["plex_token"] = "***set***"
    return {"success": True, "settings": dump, "modified": modified}


# ---------------------------------------------------------------------------
# Concierge (Track B — Edna Media Concierge, PRD.md)
#
# Narrow Plex-only endpoints, additive to the existing orchestrator chat path.
# Not gated behind settings.mode: these are opt-in by URL, always available so
# the Telegram bot (later) and manual testing can hit them regardless of
# whether chat is running in "orchestrator" or "concierge" mode.
# ---------------------------------------------------------------------------


def _require_plex_configured() -> None:
    if not concierge.configured:
        raise HTTPException(
            status_code=503,
            detail="Plex not configured — set EDNA_PLEX_URL and EDNA_PLEX_TOKEN",
        )


@app.get("/api/concierge/status")
async def concierge_status():
    return {
        "configured": concierge.configured,
        "mode": settings.mode,
        "plex_url": settings.plex_url,
        "default_client": settings.plex_default_client,
        "email_configured": email_concierge.configured,
        "news_configured": news_concierge.configured,
    }


@app.get("/api/concierge/clients")
async def concierge_clients():
    _require_plex_configured()
    return {"clients": concierge.clients()}


@app.post("/api/concierge/resolve_and_play")
async def concierge_resolve_and_play(request: ConciergePlayRequest):
    """Tool 1 — fuzzy NL -> Plex item -> playback. The whole product (PRD.md)."""
    _require_plex_configured()
    result = concierge.resolve_and_play(request.query, request.client)
    return {**result.to_dict(), "timestamp": _now()}


@app.post("/api/concierge/browse")
async def concierge_browse(request: ConciergeBrowseRequest):
    """Tool 2 — "was hast du mit Poirot?" -> short list, as buttons."""
    _require_plex_configured()
    result = concierge.browse(request.query)
    return {**result.to_dict(), "timestamp": _now()}


@app.post("/api/concierge/play_music")
async def concierge_play_music(request: ConciergePlayRequest):
    """Tool 3 — artist / era / mood -> Plex music playback."""
    _require_plex_configured()
    result = concierge.play_music(request.query, request.client)
    return {**result.to_dict(), "timestamp": _now()}


def _require_email_configured() -> None:
    if not email_concierge.configured:
        raise HTTPException(status_code=503, detail="email-mcp URL not configured")


@app.get("/api/concierge/email/status")
async def concierge_email_status():
    return {**email_concierge.status(), "timestamp": _now()}


@app.post("/api/concierge/email/unread")
async def concierge_email_unread(request: ConciergeEmailUnreadRequest):
    """Unread inbox summaries for family concierge (German copy)."""
    _require_email_configured()
    limit = max(1, min(request.limit, 20))
    result = email_concierge.unread_summaries(limit=limit)
    return {**result.to_dict(), "timestamp": _now()}


@app.post("/api/concierge/email/send")
async def concierge_email_send(request: ConciergeEmailSendRequest):
    """Send a short plain-text email via email-mcp."""
    _require_email_configured()
    result = email_concierge.send(
        to=request.to,
        subject=request.subject,
        body=request.body,
    )
    return {**result.to_dict(), "timestamp": _now()}


def _require_news_configured() -> None:
    if not news_concierge.configured:
        raise HTTPException(status_code=503, detail="aiwatcher-mcp URL not configured")


@app.get("/api/concierge/news/status")
async def concierge_news_status():
    return {**news_concierge.status(), "timestamp": _now()}


@app.post("/api/concierge/news/digest")
async def concierge_news_digest(request: ConciergeNewsDigestRequest):
    """Latest aiwatcher digest summary for family concierge."""
    _require_news_configured()
    hours = max(1, min(request.hours, 72))
    result = news_concierge.latest_digest(hours=hours)
    return {**result.to_dict(), "timestamp": _now()}


@app.post("/api/concierge/news/read-aloud")
async def concierge_news_read_aloud(request: ConciergeNewsDigestRequest):
    """Fetch digest and return WAV audio via speech-mcp."""
    _require_news_configured()
    hours = max(1, min(request.hours, 72))
    result = news_concierge.read_digest_aloud(hours=hours)
    if not result.success:
        return JSONResponse(
            {**result.to_dict(), "timestamp": _now()},
            status_code=503,
        )
    if result.audio_bytes:
        return Response(content=result.audio_bytes, media_type="audio/wav")
    return {**result.to_dict(), "timestamp": _now()}


@app.post("/api/concierge/chat")
async def concierge_chat(request: ChatRequest):
    """Family concierge chat (always uses ConciergeRouter, ignores EDNA_MODE)."""
    if not edna:
        raise HTTPException(status_code=503, detail="Edna not initialized")
    msg = request.message.strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Empty message")
    response = await concierge_router.process(
        msg,
        llm=edna.llm,
        plex_client=settings.plex_default_client,
    )
    return {
        "message": response.message,
        "actions_taken": response.actions_taken,
        "choices": response.choices,
        "success": response.success,
        "timestamp": _now(),
    }


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    _ws_connections.append(websocket)
    logger.info(f"WS connected: {websocket.client} (Total: {len(_ws_connections)})")

    try:
        await websocket.send_json(
            {
                "type": "system",
                "message": "Servus! Ednaficator connected.",
                "timestamp": _now(),
            }
        )

        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "chat")

            if msg_type == "chat":
                user_msg = data.get("message", "").strip()
                if not user_msg:
                    continue

                if not edna:
                    await websocket.send_json({"type": "error", "message": "Edna not initialized"})
                    continue

                # Thinking indicator
                await websocket.send_json({"type": "thinking", "timestamp": _now()})

                response = await edna.process_request(user_msg)
                await websocket.send_json(
                    {
                        "type": "response",
                        "message": response.message,
                        "actions_taken": response.actions_taken,
                        "suggestions": response.suggestions,
                        "choices": response.choices,
                        "success": response.success,
                        "tool_call": response.tool_call,
                        "mode": settings.mode,
                        "timestamp": _now(),
                    }
                )

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong", "timestamp": _now()})

    except WebSocketDisconnect:
        logger.info(f"WS disconnected: {websocket.client}")
    except Exception as exc:
        logger.error(f"WS generic error: {exc}")
    finally:
        if websocket in _ws_connections:
            _ws_connections.remove(websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api_bridge:app", host="0.0.0.0", port=settings.api_port, reload=True)
