"""
Analysis routes - AI-powered financial analysis
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse,Response, HTMLResponse, PlainTextResponse
import io
from pydantic import BaseModel
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


class ChatRequest(BaseModel):
    message: str
    portfolio_id: Optional[str] = None

@router.post("/chat")
async def chat_with_copilot(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """Chat with the AI copilot"""
    try:
        response = await orchestrator.chat(
            message=request.message,
            user_id=current_user.id,
            portfolio_id=request.portfolio_id
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
    """Generate downloadable portfolio report - FIXED"""
    
    # Import here to avoid issues if portfolio module not available
    from routes.portfolio import portfolios_db
    
    try:
        # Get portfolio
        portfolio = portfolios_db.get(portfolio_id)
        
        if not portfolio or portfolio["user_id"] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
        
        if format == "html":
            # Generate HTML report
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Portfolio Report - {portfolio['name']}</title>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 40px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .metric {{
            background: #ecf0f1;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }}
        .metric-label {{
            color: #7f8c8d;
            margin-top: 5px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin-top: 30px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
            font-weight: 600;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        tr:hover {{
            background-color: #f0f0f0;
        }}
        .positive {{ color: #27ae60; }}
        .negative {{ color: #e74c3c; }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #7f8c8d;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Portfolio Report: {portfolio['name']}</h1>
        <p><strong>Description:</strong> {portfolio.get('description', 'N/A')}</p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        
        <div class="summary">
            <div class="metric">
                <div class="metric-value">${portfolio.get('total_value', 0):,.2f}</div>
                <div class="metric-label">Total Value</div>
            </div>
            <div class="metric">
                <div class="metric-value">${portfolio.get('total_invested', 0):,.2f}</div>
                <div class="metric-label">Total Invested</div>
            </div>
            <div class="metric">
                <div class="metric-value {'positive' if portfolio.get('total_gain_loss', 0) >= 0 else 'negative'}">
                    ${portfolio.get('total_gain_loss', 0):,.2f}
                </div>
                <div class="metric-label">Gain/Loss</div>
            </div>
            <div class="metric">
                <div class="metric-value">{len(portfolio.get('holdings', []))}</div>
                <div class="metric-label">Holdings</div>
            </div>
        </div>
        
        <h2>Holdings Details</h2>
        <table>
            <thead>
                <tr>
                    <th>Symbol</th>
                    <th>Name</th>
                    <th>Quantity</th>
                    <th>Avg Cost</th>
                    <th>Current Price</th>
                    <th>Value</th>
                    <th>Gain/Loss</th>
                    <th>Return %</th>
                </tr>
            </thead>
            <tbody>
"""
            
            for holding in portfolio.get('holdings', []):
                gain_loss = holding.get('gain_loss', 0)
                gain_loss_class = 'positive' if gain_loss >= 0 else 'negative'
                
                html_content += f"""
                <tr>
                    <td><strong>{holding['symbol']}</strong></td>
                    <td>{holding.get('name', holding['symbol'])}</td>
                    <td>{holding['quantity']:.2f}</td>
                    <td>${holding['average_cost']:.2f}</td>
                    <td>${holding.get('current_price', 0):.2f}</td>
                    <td>${holding.get('current_value', 0):,.2f}</td>
                    <td class="{gain_loss_class}">${gain_loss:,.2f}</td>
                    <td class="{gain_loss_class}">{holding.get('gain_loss_percent', 0):.2f}%</td>
                </tr>
"""
            
            html_content += """
            </tbody>
        </table>
        
        <div class="footer">
            <p>Generated by Finance Portfolio Copilot</p>
            <p>This report is for informational purposes only and does not constitute investment advice.</p>
        </div>
    </div>
</body>
</html>
"""
            
            return HTMLResponse(content=html_content)
        
        elif format == "pdf":
            # Simple PDF generation
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import inch
            
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            
            # Title
            p.setFont("Helvetica-Bold", 20)
            p.drawString(1*inch, height - 1*inch, f"Portfolio Report: {portfolio['name']}")
            
            # Summary
            p.setFont("Helvetica-Bold", 12)
            y = height - 1.5*inch
            p.drawString(1*inch, y, "Summary:")
            
            p.setFont("Helvetica", 10)
            y -= 0.3*inch
            p.drawString(1*inch, y, f"Total Value: ${portfolio.get('total_value', 0):,.2f}")
            y -= 0.2*inch
            p.drawString(1*inch, y, f"Total Invested: ${portfolio.get('total_invested', 0):,.2f}")
            y -= 0.2*inch
            p.drawString(1*inch, y, f"Gain/Loss: ${portfolio.get('total_gain_loss', 0):,.2f}")
            
            # Holdings
            y -= 0.5*inch
            p.setFont("Helvetica-Bold", 12)
            p.drawString(1*inch, y, "Holdings:")
            
            p.setFont("Helvetica", 9)
            y -= 0.3*inch
            for holding in portfolio.get('holdings', [])[:15]:  # Limit to first 15
                if y < 1*inch:
                    p.showPage()
                    y = height - 1*inch
                p.drawString(1*inch, y, 
                    f"{holding['symbol']}: {holding['quantity']:.2f} @ ${holding['average_cost']:.2f} = ${holding.get('current_value', 0):,.2f}")
                y -= 0.2*inch
            
            # Footer
            p.setFont("Helvetica", 8)
            p.drawString(1*inch, 0.5*inch, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            p.showPage()
            p.save()
            
            buffer.seek(0)
            return Response(
                content=buffer.getvalue(),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=portfolio_{portfolio_id}.pdf"
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error generating report: {str(e)}"
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
