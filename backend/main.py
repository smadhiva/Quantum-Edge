"""
FastAPI Main Application - Finance Portfolio Copilot
FIXED VERSION - Corrected router prefixes
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from config import settings
from routes import portfolio, analysis, auth, rag
from pathway_engine.ingestion import start_pathway_pipeline
from services.market_data import MarketDataService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown"""
    print("🚀 Starting Finance Portfolio Copilot...")
    
    # Initialize data directories
    import os
    os.makedirs(settings.docs_path, exist_ok=True)
    os.makedirs(settings.prices_path, exist_ok=True)
    os.makedirs(settings.portfolios_path, exist_ok=True)
    
    # Start background tasks
    market_service = MarketDataService()
    
    # Start Pathway pipeline in background
    # asyncio.create_task(start_pathway_pipeline())
    
    print("✅ Finance Portfolio Copilot is ready!")
    print(f"📊 API Documentation: http://localhost:8000/docs")
    
    yield
    
    # Cleanup on shutdown
    print("👋 Shutting down Finance Portfolio Copilot...")


# Create FastAPI application
app = FastAPI(
    title="Finance Portfolio Copilot",
    description="""
    🦄 Live, Multi-Threaded, Agentic Investment Intelligence
    
    Powered by **Pathway + Gemini LLM**
    
    ## Features
    - 📈 Real-time market data streaming
    - 🤖 Multi-agent financial analysis
    - 📊 Portfolio management
    - 📰 Live news intelligence
    - 🔒 Document analysis with RAG
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers - FIXED: Correct prefixes to match your route definitions
# The routes in auth.py, portfolio.py, analysis.py don't have prefixes in their decorators
# So we need to add them here

# Include routers with correct prefixes
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio Management"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Financial Analysis"])
app.include_router(rag.router, prefix="/api", tags=["RAG Search"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "💰 Finance Portfolio Copilot API",
        "status": "running",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "pathway": "connected",
        "gemini": "ready"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )