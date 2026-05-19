# Activate virtual environment
# Usage: .\activate.ps1

Write-Host "Activating BigData project virtual environment..." -ForegroundColor Green
& "$PSScriptRoot\venv\Scripts\Activate.ps1"
Write-Host "Virtual environment activated!" -ForegroundColor Green
Write-Host ""
Write-Host "Common commands:" -ForegroundColor Yellow
Write-Host "  python -m pytest tests/ -v          # Run tests"
Write-Host "  python scripts/export_offline_dashboard.py  # Export offline data"
Write-Host "  python -m http.server 8088 --directory frontend/public  # Start static server"
Write-Host ""
