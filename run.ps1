# =============================================================================
#  Smart Traffic Violation System - one-command launcher (Windows / PowerShell)
#  Usage:  ./run.ps1
# =============================================================================
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $root

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host " Smart Traffic Violation System" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan

# Pick python
$py = "python"
try { & $py --version | Out-Null } catch { $py = "py" }

# NOTE: no auto-seed — the dashboard shows ONLY real AI results by default.
# For a simulated safety-net dataset use the "Demo Data" button in the UI
# (clearly badged as SIMULATED) or run:  python backend\seed_demo.py

# Launch the server + open the browser
Write-Host "`nStarting dashboard at http://localhost:8000 ..." -ForegroundColor Yellow
Start-Process "http://localhost:8000"
& $py -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000
