#!/bin/bash
# Finance Portfolio Copilot - Startup Script
# Run this script to start all services

echo "🚀 Starting Finance Portfolio Copilot..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📋 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your GEMINI_API_KEY before continuing."
    echo "   Get your API key from: https://makersuite.google.com/app/apikey"
    exit 1
fi

# Check if GEMINI_API_KEY is set
if ! grep -q "GEMINI_API_KEY=." .env; then
    echo "⚠️  GEMINI_API_KEY is not set in .env file."
    echo "   Please add your API key before continuing."
    exit 1
fi

echo ""
echo "📦 Building and starting containers..."
docker-compose up --build -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
BACKEND_RUNNING=$(docker ps --filter "name=finance-copilot-backend" --format "{{.Names}}")
FRONTEND_RUNNING=$(docker ps --filter "name=finance-copilot-frontend" --format "{{.Names}}")

if [ -n "$BACKEND_RUNNING" ] && [ -n "$FRONTEND_RUNNING" ]; then
    echo ""
    echo "✅ Finance Portfolio Copilot is running!"
    echo ""
    echo "📊 Access the application:"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend API: http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
    echo ""
    echo "📝 Useful commands:"
    echo "   Stop:    docker-compose down"
    echo "   Logs:    docker-compose logs -f"
    echo "   Rebuild: docker-compose up --build -d"
else
    echo ""
    echo "❌ Some services failed to start. Check logs with:"
    echo "   docker-compose logs"
fi
