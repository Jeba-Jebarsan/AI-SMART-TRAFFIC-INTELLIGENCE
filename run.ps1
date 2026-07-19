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

# The dashboard shows ONLY real, live AI results — there is no mock/demo data.
# Each Go Live / Play Live session starts clean and streams real detections.

# Launch the server + open the browser
Write-Host "`nStarting dashboard at http://localhost:8000 ..." -ForegroundColor Yellow
Start-Process "http://localhost:8000"
& $py -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000
