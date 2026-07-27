# Ednaficator — revival notes (2026-05-21)

## What it is

Conversational front-end for MCP tools listed in **Claude Desktop config** (not fleet auto-scan). Family asks in plain language; Edna picks a tool via local LLM and calls the right MCP over stdio.

Full detail: [docs/MCP_REGISTRY.md](docs/MCP_REGISTRY.md)

## MCP registry

| Env | Purpose |
|-----|---------|
| `CLAUDE_DESKTOP_CONFIG` | Path to JSON with `mcpServers` |
| `EDNA_MCP_ALLOWLIST` | Optional comma-separated names (family safety) |

Only `fileops` starts at boot; other servers lazy-start on first tool call.

## Start

```powershell
Set-Location D:\Dev\repos\ednaficator

# API only (port 10942)
uv run python -m ednaficator

# API + UI (ports 10942 + 10943)
uv run python start_all.py
```

**LLM provider** (Settings UI or env):

| Provider | Default | Env |
|----------|---------|-----|
| **LM Studio** (default) | `http://127.0.0.1:1234/v1` | `EDNA_LLM_PROVIDER=lmstudio` |
| Ollama | `http://localhost:11434` | `EDNA_LLM_PROVIDER=ollama` |

LM Studio: load a model, turn on **Local Server** in the app. Ollama health checks use a 5s timeout so a hung Ollama no longer blocks startup when using LM Studio.

## Quality gates (Windows)

```powershell
just ci                  # ruff + pytest (same as scripts/ci.ps1)
just hooks-install       # pre-commit git hooks
just lint
just test
```

Fleet CI file: `.github/workflows/ci.yml` (Windows-only). Private repo: keep GitHub Actions disabled at account level; run `just ci` locally.

## Smoke test

```powershell
uv run python tests/smoke_test.py
```

## Fixes applied

- `ConfigDict` import in `api_bridge.py`
- `ednaficator/__main__.py` — real server entry
- MCP spawn strips `VIRTUAL_ENV` so child `uv` projects start cleanly
- `start_all.py` backend port 10942
- Default Ollama model aligned to `qwen2.5:27b`
- `memops` lazy-start only (slow boot); `INIT_TIMEOUT` 45s
- Removed 37 `.bak` files; `git init` + `.gitignore`

## Still optional

- `git init` + push to GitHub
- Delete remaining `.bak` files
- Wire Austrian services / trim marketing README
- CI, MCPB packaging per old ASSESSMENT.md
