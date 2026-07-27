# Install pre-commit git hooks for ednaficator
# Usage: powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/install-pre-commit.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

Write-Host "Syncing dev dependencies..." -ForegroundColor Cyan
uv sync --group dev
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Installing pre-commit hooks..." -ForegroundColor Cyan
uv run pre-commit install
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Running hooks once on all files (may auto-fix)..." -ForegroundColor Cyan
uv run pre-commit run --all-files
exit $LASTEXITCODE
