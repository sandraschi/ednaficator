param(
    [switch]$Headless,
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$NoBrowser
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$FleetStartPath = Join-Path $ProjectRoot "scripts\FleetStartMode.ps1"
if (-not (Test-Path -LiteralPath $FleetStartPath)) {
    Write-Host "ERROR: Missing vendored launcher helper: $FleetStartPath" -ForegroundColor Red
    exit 1
}
. $FleetStartPath
$FleetStart = Initialize-FleetStartMode @PSBoundParameters
Enter-FleetHeadlessConsole -Headless:$Headless -BackendOnly:$BackendOnly

$BackendPort = 10942
$FrontendPort = 10943
Stop-FleetPortSquatters -Ports @($BackendPort, $FrontendPort) -Label "ednaficator"

if (-not (Assert-FleetPortsAvailable -Ports @($BackendPort, $FrontendPort) -Label "ednaficator")) { exit 1 }

$env:FASTMCP_LOG_LEVEL = 'WARNING'

Set-Location $PSScriptRoot

if ($Headless) {
    Write-Host 'Starting ednaficator API (headless)...' -ForegroundColor Cyan
    uv run -m ednaficator
    exit
}

Write-Host 'Starting ednaficator (API + UI)...' -ForegroundColor Cyan
Write-Host '  Backend:  http://localhost:10942' -ForegroundColor DarkGray
Write-Host '  Frontend: http://localhost:10943' -ForegroundColor DarkGray
uv run python start_all.py


