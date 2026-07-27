"""Tests for MCP registry loading and allowlist."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from ednaficator.mcp.registry import load_registry, parse_allowlist


@pytest.fixture
def sample_config(tmp_path: Path) -> Path:
    cfg = {
        "mcpServers": {
            "plex-mcp": {"command": "uv", "args": ["run", "plex-mcp"], "env": {}},
            "_disabled": {"command": "uv", "args": ["run", "noop"], "env": {}},
            "fileops": {"command": "uv", "args": ["run", "fileops-mcp"], "env": {}},
            "winops": {"command": "uv", "args": ["run", "winops-mcp"], "env": {}},
        }
    }
    path = tmp_path / "claude_desktop_config.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def test_parse_allowlist_empty():
    assert parse_allowlist("") is None
    assert parse_allowlist("  ") is None


def test_parse_allowlist_names():
    assert parse_allowlist("a, b,c") == {"a", "b", "c"}


def test_load_registry_all_enabled(sample_config: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("EDNA_MCP_ALLOWLIST", raising=False)
    reg = load_registry(sample_config)
    assert reg.server_names() == ["fileops", "plex-mcp", "winops"]
    info = reg.info()
    assert info["source"] == "claude_desktop_config"
    assert info["enabled"] == 3


def test_load_registry_allowlist(sample_config: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("EDNA_MCP_ALLOWLIST", "plex-mcp,fileops")
    reg = load_registry(sample_config)
    assert reg.server_names() == ["fileops", "plex-mcp"]
    assert reg.info()["allowlist_active"] is True


def test_load_registry_missing_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("EDNA_MCP_ALLOWLIST", raising=False)
    reg = load_registry(tmp_path / "missing.json")
    assert reg.server_names() == []
