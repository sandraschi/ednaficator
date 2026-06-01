from __future__ import annotations

import sys
import json
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, List, Dict, Optional, Literal

from loguru import logger
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings

from ednaficator.core.edna import EdnaCore

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
_ws_connections: List[WebSocket] = []

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

# ---------------------------------------------------------------------------
# Lifespan (Startup / Shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    global edna
    logger.info(
        f"Ednaficator API starting — provider={settings.llm_provider} "
        f"model={settings.active_model}"
    )

    config = {
        "llm_provider": settings.llm_provider,
        "ollama_base_url": settings.ollama_base_url,
        "ollama_model": settings.ollama_model,
        "lmstudio_base_url": settings.lmstudio_base_url,
        "lmstudio_model": settings.lmstudio_model,
    }
    
    edna = EdnaCore(config)
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
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://localhost:{settings.ui_port}",
        "http://localhost:5173",
        "http://localhost:3000",
        "*" # Allow all for local fleet access
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
    llm_provider: Optional[Literal["ollama", "lmstudio"]] = None
    ollama_base_url: Optional[str] = None
    ollama_model: Optional[str] = None
    lmstudio_base_url: Optional[str] = None
    lmstudio_model: Optional[str] = None
    debug: Optional[bool] = None

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
        "timestamp": _now()
    }

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "edna_ready": edna is not None and edna.running,
        "ws_connections": len(_ws_connections),
        "timestamp": _now()
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
        "success": response.success,
        "timestamp": _now(),
    }

@app.get("/api/servers")
async def list_servers():
    if not edna:
        raise HTTPException(status_code=503, detail="Edna not initialized")
    
    status = edna.mcp_orchestrator.get_status()
    return [
        {
            "name": name,
            "ready": info["ready"],
            "tool_count": info["tool_count"],
            "error": info["error"],
        }
        for name, info in status.items()
    ]

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
    from ednaficator.llm.ollama_client import OllamaClient
    from ednaficator.llm.lmstudio_client import LMStudioClient

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
    return settings.model_dump()

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
        logger.info(
            f"LLM provider swap: {settings.llm_provider} model={edna.llm.model}"
        )

    return {"success": True, "settings": settings.model_dump(), "modified": modified}

# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    _ws_connections.append(websocket)
    logger.info(f"WS connected: {websocket.client} (Total: {len(_ws_connections)})")
    
    try:
        await websocket.send_json({
            "type": "system",
            "message": "Servus! Ednaficator connected.",
            "timestamp": _now(),
        })
        
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
                await websocket.send_json({
                    "type": "response",
                    "message": response.message,
                    "actions_taken": response.actions_taken,
                    "suggestions": response.suggestions,
                    "success": response.success,
                    "tool_call": response.tool_call,
                    "timestamp": _now(),
                })
                
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
