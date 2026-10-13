set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]
import 'scripts/just/fleet.just'

# SOTA Fleet-Standard Justfile

set shell := ["powershell", "-c"]

# Open the interactive recipe dashboard in the browser
default:
    @just --list

# --- 🚀 Operations ---

# Start the API server (Canonical)
run:
    uv run python -m ednaficator

# Start API + React UI in separate consoles
dev:
    uv run python start_all.py

# START REPOSITORY: API + React UI (use -Headless in start.ps1 for API-only)
start:
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File ./start.ps1

# API only (no Vite UI)
run-api:
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File ./start.ps1 -Headless

# --- 🧪 Quality Gates ---

# LINT: Check for code quality issues
lint:
    uv run ruff check ednaficator tests api_bridge.py

# FIX: Auto-repair linting issues
fix:
    uv run ruff check --fix ednaficator tests api_bridge.py
    uv run ruff format ednaficator tests api_bridge.py

# TEST: Run the test suite
test:
    uv run pytest

# CI: Windows quality gate (ruff + pytest)
ci:
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File ./scripts/ci.ps1

# HOOKS: Install pre-commit git hooks
hooks-install:
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File ./scripts/install-pre-commit.ps1

# HOOKS: Run pre-commit on all files
hooks-run:
    uv run pre-commit run --all-files

# --- 🧹 Maintenance ---

# CLEAN: Purge artifacts and caches
clean:
    @Remove-Item -Recurse -Force .venv, .pytest_cache, .ruff_cache -ErrorAction SilentlyContinue
    @Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
