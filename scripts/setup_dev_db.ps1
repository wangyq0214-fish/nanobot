# Setup development database for nanobot
# Usage: .\scripts\setup_dev_db.ps1

Write-Host "Setting up development database..." -ForegroundColor Cyan

# Check if Docker is running
try {
    docker info 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker not running"
    }
} catch {
    Write-Host "Error: Docker is not running" -ForegroundColor Red
    exit 1
}

# Start PostgreSQL
Write-Host "Starting PostgreSQL..." -ForegroundColor Yellow
docker-compose -f docker-compose.dev.yml up -d postgres

# Wait for PostgreSQL to be ready
Write-Host "Waiting for PostgreSQL to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check if PostgreSQL is ready
$maxRetries = 30
$retryCount = 0
while ($retryCount -lt $maxRetries) {
    $result = docker exec nanobot-postgres pg_isready -U nanobot -d nanobot 2>&1
    if ($LASTEXITCODE -eq 0) {
        break
    }
    Write-Host "Waiting for PostgreSQL..." -ForegroundColor Yellow
    Start-Sleep -Seconds 2
    $retryCount++
}

if ($retryCount -eq $maxRetries) {
    Write-Host "Error: PostgreSQL failed to start" -ForegroundColor Red
    exit 1
}

Write-Host "✓ PostgreSQL is ready" -ForegroundColor Green

# Run database migration
Write-Host "Running database migration..." -ForegroundColor Yellow
Set-Location (Split-Path -Parent $PSScriptRoot)
python -m nanobot.cli.commands migrate-db run

Write-Host ""
Write-Host "✓ Development database setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Connection details:" -ForegroundColor Cyan
Write-Host "  Host: localhost"
Write-Host "  Port: 5432"
Write-Host "  Database: nanobot"
Write-Host "  User: nanobot"
Write-Host "  Password: nanobot"
Write-Host ""
Write-Host "Connection URL: postgresql+asyncpg://nanobot:nanobot@localhost:5432/nanobot" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start pgAdmin (optional):" -ForegroundColor Yellow
Write-Host "  docker-compose -f docker-compose.dev.yml --profile admin up -d"
Write-Host "  Open http://localhost:5050"
Write-Host "  Email: admin@nanobot.local"
Write-Host "  Password: admin"
