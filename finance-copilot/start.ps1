# Finance Portfolio Copilot - Startup Script
# Run this script to start all services

Write-Host "🚀 Starting Finance Portfolio Copilot..." -ForegroundColor Cyan

# Check if Docker is installed
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker is not installed. Please install Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if .env file exists
if (!(Test-Path ".env")) {
    Write-Host "📋 Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "⚠️  Please edit .env and add your GEMINI_API_KEY before continuing." -ForegroundColor Yellow
    Write-Host "   Get your API key from: https://makersuite.google.com/app/apikey" -ForegroundColor Gray
    exit 1
}

# Check if GEMINI_API_KEY is set
$envContent = Get-Content ".env" -Raw
if ($envContent -notmatch "GEMINI_API_KEY=.+") {
    Write-Host "⚠️  GEMINI_API_KEY is not set in .env file." -ForegroundColor Yellow
    Write-Host "   Please add your API key before continuing." -ForegroundColor Gray
    exit 1
}

Write-Host ""
Write-Host "📦 Building and starting containers..." -ForegroundColor Green
docker-compose up --build -d

Write-Host ""
Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check if services are running
$backendRunning = docker ps --filter "name=finance-copilot-backend" --format "{{.Names}}"
$frontendRunning = docker ps --filter "name=finance-copilot-frontend" --format "{{.Names}}"

if ($backendRunning -and $frontendRunning) {
    Write-Host ""
    Write-Host "✅ Finance Portfolio Copilot is running!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Access the application:" -ForegroundColor Cyan
    Write-Host "   Frontend: http://localhost:3000" -ForegroundColor White
    Write-Host "   Backend API: http://localhost:8000" -ForegroundColor White
    Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor White
    Write-Host ""
    Write-Host "📝 Useful commands:" -ForegroundColor Cyan
    Write-Host "   Stop:   docker-compose down" -ForegroundColor Gray
    Write-Host "   Logs:   docker-compose logs -f" -ForegroundColor Gray
    Write-Host "   Rebuild: docker-compose up --build -d" -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "❌ Some services failed to start. Check logs with:" -ForegroundColor Red
    Write-Host "   docker-compose logs" -ForegroundColor Gray
}
