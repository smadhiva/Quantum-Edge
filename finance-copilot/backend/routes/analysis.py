"""
Analysis routes - AI-powered financial analysis
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
import io

from models.user import User
from models.stock import StockAnalysis, PeerComparison, NewsItem, MarketTrend
from routes.auth import get_current_user
from agents.orchestrator import AgentOrchestrator
from agents.equity_agent import EquityResearchAgent
from agents.news_agent import NewsIntelligenceAgent
from agents.market_agent import MarketTrendAgent

router = APIRouter()

# Initialize agents
orchestrator = AgentOrchestrator()
equity_agent = EquityResearchAgent()
news_agent = NewsIntelligenceAgent()
market_agent = MarketTrendAgent()


@router.get("/stock/{symbol}", response_model=StockAnalysis)
async def analyze_stock(
    symbol: str,
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive AI analysis for a stock"""
    symbol = symbol.upper()
    
    try:
        analysis = await equity_agent.analyze(symbol)
        return analysis
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze stock: {str(e)}"
        )


@router.get("/stock/{symbol}/peers", response_model=PeerComparison)
async def get_peer_comparison(
    symbol: str,
    current_user: User = Depends(get_current_user)
):
    """Get peer comparison analysis"""
    symbol = symbol.upper()
    
    try:
        comparison = await equity_agent.compare_peers(symbol)
        return comparison
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get peer comparison: {str(e)}"
        )


@router.get("/stock/{symbol}/news", response_model=List[NewsItem])
async def get_stock_news(
    symbol: str,
    limit: int = Query(default=10, le=50),
    current_user: User = Depends(get_current_user)
):
    """Get latest news for a stock with sentiment analysis"""
    symbol = symbol.upper()
    
    try:
        news = await news_agent.get_news(symbol, limit)
        return news
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get news: {str(e)}"
        )


@router.get("/stock/{symbol}/trend", response_model=MarketTrend)
async def get_market_trend(
    symbol: str,
    timeframe: str = Query(default="1m", regex="^(1d|1w|1m|3m|1y)$"),
    current_user: User = Depends(get_current_user)
):
    """Get technical analysis and market trend"""
    symbol = symbol.upper()
    
    try:
        trend = await market_agent.analyze_trend(symbol, timeframe)
        return trend
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze trend: {str(e)}"
        )


@router.get("/portfolio/{portfolio_id}/analysis")
async def analyze_portfolio(
    portfolio_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive portfolio analysis from all agents"""
    try:
        analysis = await orchestrator.analyze_portfolio(portfolio_id, current_user.id)
        return analysis
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze portfolio: {str(e)}"
        )


@router.get("/portfolio/{portfolio_id}/recommendations")
async def get_recommendations(
    portfolio_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get AI-powered investment recommendations"""
    try:
        recommendations = await orchestrator.get_recommendations(portfolio_id, current_user.id)
        return recommendations
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recommendations: {str(e)}"
        )


@router.post("/chat")
async def chat_with_copilot(
    message: str,
    portfolio_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Chat with the Finance Copilot"""
    try:
        response = await orchestrator.chat(
            message=message,
            user_id=current_user.id,
            portfolio_id=portfolio_id
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(e)}"
        )


@router.get("/portfolio/{portfolio_id}/report")
async def generate_report(
    portfolio_id: str,
    format: str = Query(default="pdf", regex="^(pdf|html)$"),
    current_user: User = Depends(get_current_user)
):
    """Generate downloadable portfolio report"""
    try:
        report = await orchestrator.generate_report(portfolio_id, current_user.id, format)
        
        if format == "pdf":
            return StreamingResponse(
                io.BytesIO(report),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=portfolio_report_{portfolio_id}.pdf"
                }
            )
        else:
            return StreamingResponse(
                io.BytesIO(report.encode()),
                media_type="text/html",
                headers={
                    "Content-Disposition": f"attachment; filename=portfolio_report_{portfolio_id}.html"
                }
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate report: {str(e)}"
        )


@router.get("/market/overview")
async def market_overview(current_user: User = Depends(get_current_user)):
    """Get overall market overview"""
    try:
        overview = await market_agent.get_market_overview()
        return overview
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get market overview: {str(e)}"
        )


@router.get("/market/sectors")
async def sector_performance(current_user: User = Depends(get_current_user)):
    """Get sector performance analysis"""
    try:
        sectors = await market_agent.get_sector_performance()
        return sectors
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get sector performance: {str(e)}"
        )
