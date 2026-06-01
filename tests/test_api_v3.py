import pytest
from fastapi.testclient import TestClient
from api_bridge import app, settings, SettingsUpdate
import json

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Ednaficator API"
    assert "model" in data

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_get_settings():
    response = client.get("/api/settings")
    assert response.status_code == 200
    data = response.json()
    assert data["ollama_model"] == settings.ollama_model
    assert data["llm_provider"] in ("ollama", "lmstudio")

def test_update_settings():
    old_model = settings.ollama_model
    new_model = "qwen2.5:7b"
    
    response = client.post("/api/settings", json={"ollama_model": new_model})
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert settings.ollama_model == new_model
    
    # Reset
    settings.ollama_model = old_model

def test_api_servers_uninitialized():
    # If edna is not initialized (it only initializes in lifespan)
    # the /api/servers endpoint should return 503
    response = client.get("/api/servers")
    assert response.status_code == 503
    assert response.json()["detail"] == "Edna not initialized"

def test_providers_endpoint():
    response = client.get("/api/providers")
    assert response.status_code == 200
    data = response.json()
    assert "ollama" in data
    assert "lmstudio" in data


def test_chat_invalid_body():
    response = client.post("/api/chat", json={})
    assert response.status_code == 422 # FastAPI validation error for missing required field
