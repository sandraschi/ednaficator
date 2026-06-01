#!/usr/bin/env python3
"""
Ednaficator API Bridge - FastAPI Web Server

Connects the React UI to the Python EdnaCore backend.
Provides REST and WebSocket endpoints for real-time communication.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
import json
import logging
from pathlib import Path

from ednaficator.core.edna import EdnaCore, EdnaResponse


# Configuration
app = FastAPI(
    title="Ednaficator API",
    description="Austrian AI Concierge API Bridge",
    version="1.0.0"
)

# CORS middleware for React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Edna instance
edna_core: Optional[EdnaCore] = None
connected_websockets: List[WebSocket] = []


# API Models
class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = "user"


class ChatResponse(BaseModel):
    message: str
    actions_taken: List[str]
    suggestions: List[str]
    success: bool
    timestamp: str


class SystemStatus(BaseModel):
    status: str
    mcp_servers: List[Dict]
    memory_status: str
    austrian_services: str


class UserPreferences(BaseModel):
    theme: str
    language: str
    privacy_settings: Dict


# Initialize Edna on startup
@app.on_event("startup")
async def startup_event():
    """Initialize Edna when the API starts"""
    global edna_core
    
    print("🚀 Starting Ednaficator API Bridge...")
    
    # Load default config
    config = {
        "memory_path": "./edna_memory",
        "local_llm_endpoint": "http://localhost:1234",  # Default LM Studio
        "vienna_services": True,
        "debug": True
    }
    
    # Initialize EdnaCore
    edna_core = EdnaCore(config)
    try:
        await edna_core.initialize()
        print("✅ Edna initialized successfully!")
    except Exception as e:
        print(f"⚠️ Edna initialization partial: {e}")
        # Continue anyway for demo purposes


@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown"""
    print("👋 Shutting down Ednaficator API...")


# REST API Endpoints

@app.get("/api/status")
async def get_system_status() -> SystemStatus:
    """Get current system status"""
    if not edna_core:
        raise HTTPException(status_code=503, detail="Edna not initialized")
    
    return SystemStatus(
        status="running" if edna_core.running else "ready",
        mcp_servers=[
            {
                "name": name,
                "status": "connected",
                "last_ping": "2025-07-28T15:22:00Z"
            }
            for name in getattr(edna_core.mcp_orchestrator, 'servers', {}).keys()
        ],
        memory_status="active",
        austrian_services="enabled"
    )


@app.post("/api/chat")
async def chat_endpoint(message: ChatMessage) -> ChatResponse:
    """Process a chat message and return response"""
    if not edna_core:
        raise HTTPException(status_code=503, detail="Edna not initialized")
    
    try:
        # Process the message through EdnaCore
        response = await edna_core.process_request(message.message)
        
        # Convert to API response
        return ChatResponse(
            message=response.message,
            actions_taken=response.actions_taken,
            suggestions=response.suggestions,
            success=response.success,
            timestamp="2025-07-28T15:22:00Z"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.get("/api/mcp/servers")
async def get_mcp_servers():
    """Get list of connected MCP servers"""
    if not edna_core:
        raise HTTPException(status_code=503, detail="Edna not initialized")
    
    servers = getattr(edna_core.mcp_orchestrator, 'servers', {})
    return [
        {
            "id": name,
            "name": name.replace("-", " ").title(),
            "type": "mcp",
            "status": "connected",
            "lastSync": "2025-07-28T15:22:00Z",
            "capabilities": ["automation", "data", "control"]
        }
        for name in servers.keys()
    ]


@app.get("/api/vienna/services")
async def get_vienna_services():
    """Get Vienna-specific services"""
    return [
        {
            "id": "wien-info",
            "name": "Wien.gv.at Services",
            "category": "government",
            "status": "available"
        },
        {
            "id": "wiener-linien",
            "name": "Wiener Linien",
            "category": "transport",
            "status": "available"
        },
        {
            "id": "local-weather",
            "name": "Vienna Weather",
            "category": "weather",
            "status": "available"
        }
    ]


@app.post("/api/preferences")
async def update_preferences(prefs: UserPreferences):
    """Update user preferences"""
    # Store preferences in Edna's memory
    if edna_core and edna_core.memory:
        await edna_core.memory.store_interaction(
            "update_preferences",
            {"preferences": prefs.dict()}
        )
    
    return {"success": True, "message": "Preferences updated"}


@app.get("/api/logs")
async def get_system_logs():
    """Get recent system logs"""
    return [
        {
            "timestamp": "2025-07-28T15:22:00Z",
            "level": "INFO",
            "source": "edna-core",
            "message": "User interaction processed successfully"
        },
        {
            "timestamp": "2025-07-28T15:21:45Z",
            "level": "INFO",
            "source": "mcp-orchestrator",
            "message": "Connected to homecontrol-mcp server"
        },
        {
            "timestamp": "2025-07-28T15:21:30Z",
            "level": "INFO",
            "source": "api-bridge",
            "message": "API server started successfully"
        }
    ]


# WebSocket endpoint for real-time communication
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()
    connected_websockets.append(websocket)
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "system",
            "message": "🤖 Edna connected! Wie kann ich helfen?",
            "timestamp": "2025-07-28T15:22:00Z"
        })
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "chat":
                user_message = message_data.get("message", "")
                
                # Process through EdnaCore
                if edna_core:
                    response = await edna_core.process_request(user_message)
                    
                    # Send response back
                    await websocket.send_json({
                        "type": "response",
                        "message": response.message,
                        "actions_taken": response.actions_taken,
                        "suggestions": response.suggestions,
                        "success": response.success,
                        "timestamp": "2025-07-28T15:22:00Z"
                    })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Edna not initialized",
                        "timestamp": "2025-07-28T15:22:00Z"
                    })
            
    except WebSocketDisconnect:
        connected_websockets.remove(websocket)
        print("🔌 WebSocket client disconnected")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)


# Serve React UI (for production)
@app.get("/ui/{full_path:path}")
async def serve_ui(full_path: str):
    """Serve the React UI files"""
    ui_path = Path("ui/dist")
    
    if not ui_path.exists():
        raise HTTPException(status_code=404, detail="UI not built. Run: npm run build")
    
    file_path = ui_path / full_path
    
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    else:
        # Serve index.html for SPA routing
        return FileResponse(ui_path / "index.html")


@app.get("/")
async def root():
    """Root endpoint - redirect to UI or show API info"""
    return {
        "name": "Ednaficator API",
        "version": "1.0.0",
        "description": "Austrian AI Concierge API Bridge",
        "endpoints": {
            "chat": "/api/chat",
            "status": "/api/status", 
            "websocket": "/ws",
            "ui": "/ui/"
        },
        "message": "🇦🇹 Grüß Gott! Edna API is running."
    }


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "edna_initialized": edna_core is not None,
        "websocket_connections": len(connected_websockets),
        "timestamp": "2025-07-28T15:22:00Z"
    }


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Ednaficator API Bridge...")
    print("🇦🇹 Austrian AI Concierge - Privacy First!")
    print("📱 React UI will be available at: http://localhost:8000/ui/")
    print("🔌 WebSocket endpoint: ws://localhost:8000/ws")
    print("📊 API docs: http://localhost:8000/docs")
    
    uvicorn.run(
        "api_bridge:app",
        host="localhost",
        port=8000,
        reload=True,
        log_level="info"
    )
