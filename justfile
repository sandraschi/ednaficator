set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]

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
    pwsh.exe -NoProfile -ExecutionPolicy Bypass -File ./start.ps1

# API only (no Vite UI)
run-api:
    pwsh.exe -NoProfile -ExecutionPolicy Bypass -File ./start.ps1 -Headless

# --- 🧪 Quality Gates ---

# LINT: Check for code quality issues
lint:
    uv run ruff check .

# FIX: Auto-repair linting issues
fix:
    uv run ruff check --fix .
    uv run ruff format .

# TEST: Run the test suite
test:
    uv run pytest

# --- 🧹 Maintenance ---

# CLEAN: Purge artifacts and caches
clean:
    @Remove-Item -Recurse -Force .venv, .pytest_cache, .ruff_cache -ErrorAction SilentlyContinue
    @Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force

