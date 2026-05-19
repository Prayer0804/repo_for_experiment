$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

Write-Host "Starting Kafka, Flink, Realtime API and Dashboard..." -ForegroundColor Green
docker compose -f docker-compose.realtime.yml up -d --build kafka kafka-init jobmanager taskmanager flink-sql-client realtime-api dashboard

Write-Host ""
Write-Host "Service URLs:" -ForegroundColor Yellow
Write-Host "  Kafka external: localhost:19092"
Write-Host "  Flink Web UI: http://localhost:8081"
Write-Host "  Realtime API: http://localhost:8000/api/health"
Write-Host "  Realtime Dashboard: http://localhost:8080"
Write-Host ""
Write-Host "Open another terminal to produce events:" -ForegroundColor Cyan
Write-Host "  python scripts/produce_traffic_events.py --events-per-second 60"
