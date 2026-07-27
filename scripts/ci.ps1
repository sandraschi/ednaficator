# Windows-only local CI (same gates as .github/workflows/ci.yml)
# Usage: powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/ci.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

Write-Host "== ednaficator CI (Windows) ==" -ForegroundColor Cyan

Write-Host "`n[1/4] uv sync --group dev" -ForegroundColor Yellow
uv sync --group dev
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n[2/4] ruff check" -ForegroundColor Yellow
uv run ruff check ednaficator tests api_bridge.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n[3/4] ruff format --check" -ForegroundColor Yellow
uv run ruff format --check ednaficator tests api_bridge.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n[4/4] pytest" -ForegroundColor Yellow
uv run pytest -q --tb=short
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`nCI passed." -ForegroundColor Green
