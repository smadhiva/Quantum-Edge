"""
Agent Orchestrator - Coordinates all agents for comprehensive analysis
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from .base_agent import BaseAgent, AgentState
from .equity_agent import EquityResearchAgent
from .news_agent import NewsIntelligenceAgent
from .market_agent import MarketTrendAgent
from .risk_agent import RiskProfilingAgent
from .portfolio_agent import PortfolioMonitorAgent
from services.market_data import MarketDataService
from pathway_engine.vector_store import PathwayVectorStore, RAGQueryEngine
from config import settings


class AgentOrchestrator:
    """
    Orchestrates multiple agents to provide comprehensive financial analysis
    Implements multi-threaded portfolio management
    """
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.portfolio_threads: Dict[str, AgentState] = {}
        self.market_service = MarketDataService()
        self.vector_store = None
        self.rag_engine = None
        self._initialize_agents()
        self._initialize_rag()
    
    def _initialize_agents(self):
        """Initialize all specialized agents"""
        self.agents = {
            "equity": EquityResearchAgent(),
            "news": NewsIntelligenceAgent(),
            "market": MarketTrendAgent(),
            "risk": RiskProfilingAgent(),
            "portfolio": PortfolioMonitorAgent()
        }
    
    def _initialize_rag(self):
        """Initialize RAG components"""
        try:
            self.vector_store = PathwayVectorStore()
            self.vector_store.from_folder(settings.docs_path)
            self.rag_engine = RAGQueryEngine(self.vector_store)
        except Exception as e:
            print(f"Failed to initialize RAG: {e}")
    
    def create_portfolio_thread(self, portfolio_id: str, user_id: str) -> AgentState:
        """
        Create a new portfolio thread with its own agent state
        Each portfolio runs independently
        """
        state = AgentState()
        state.update_context("portfolio_id", portfolio_id)
        state.update_context("user_id", user_id)
        state.update_context("created_at", datetime.now().isoformat())
        
        self.portfolio_threads[portfolio_id] = state
        return state
    
    def get_portfolio_thread(self, portfolio_id: str) -> Optional[AgentState]:
        """Get existing portfolio thread"""
        return self.portfolio_threads.get(portfolio_id)
    
    async def analyze_portfolio(self, portfolio_id: str, user_id: str) -> Dict[str, Any]:
        """
        Comprehensive portfolio analysis using all agents
        """
        # Get or create portfolio thread
        state = self.get_portfolio_thread(portfolio_id)
        if not state:
            state = self.create_portfolio_thread(portfolio_id, user_id)
        
        # Get portfolio data
        from routes.portfolio import portfolios_db
        portfolio = portfolios_db.get(portfolio_id)
        
        if not portfolio:
            return {"error": "Portfolio not found"}
        
        # Run all agents in parallel
        tasks = []
        symbols = [h["symbol"] for h in portfolio.get("holdings", [])]
        
        # 1. Equity Analysis for each holding
        equity_tasks = [
            self.agents["equity"].analyze(symbol) 
            for symbol in symbols[:5]  # Limit to top 5
        ]
        
        # 2. News Analysis
        news_task = self.agents["news"].get_portfolio_news(symbols)
        
        # 3. Market Overview
        market_task = self.agents["market"].get_market_overview()
        
        # 4. Risk Assessment
        risk_task = self.agents["risk"].assess_portfolio_risk(portfolio)
        
        # 5. Portfolio Health
        portfolio_task = self.agents["portfolio"].analyze_health(portfolio)
        
        # Execute all tasks
        try:
            equity_results = await asyncio.gather(*equity_tasks, return_exceptions=True)
            news_result = await news_task
            market_result = await market_task
            risk_result = await risk_task
            portfolio_result = await portfolio_task
        except Exception as e:
            print(f"Error in analysis: {e}")
            equity_results = []
            news_result = {}
            market_result = {}
            risk_result = {}
            portfolio_result = {}
        
        # Compile results
        analysis = {
            "portfolio_id": portfolio_id,
            "analysis_date": datetime.now().isoformat(),
            "holdings_analysis": [
                r for r in equity_results if not isinstance(r, Exception)
            ],
            "news_summary": news_result,
            "market_overview": market_result,
            "risk_assessment": risk_result,
            "portfolio_health": portfolio_result,
            "recommendations": await self._generate_recommendations(
                portfolio, equity_results, risk_result
            )
        }
        
        # Update state
        state.set_result("latest_analysis", analysis)
        state.complete_step("full_analysis")
        
        return analysis
    
    async def get_recommendations(self, portfolio_id: str, user_id: str) -> Dict[str, Any]:
        """
        Get AI-powered investment recommendations
        """
        from routes.portfolio import portfolios_db
        portfolio = portfolios_db.get(portfolio_id)
        
        if not portfolio:
            return {"error": "Portfolio not found"}
        
        # Get latest analysis or run new one
        state = self.get_portfolio_thread(portfolio_id)
        if state and "latest_analysis" in state.results:
            analysis = state.results["latest_analysis"]
        else:
            analysis = await self.analyze_portfolio(portfolio_id, user_id)
        
        return {
            "portfolio_id": portfolio_id,
            "recommendations": analysis.get("recommendations", []),
            "generated_at": datetime.now().isoformat()
        }
    
    async def _generate_recommendations(
        self, 
        portfolio: Dict, 
        equity_analyses: List,
        risk_assessment: Dict
    ) -> List[str]:
        """
        Generate actionable recommendations based on analyses
        """
        # Use the equity agent's LLM for recommendation generation
        equity_agent = self.agents["equity"]
        
        context = f"""
Portfolio Value: ${portfolio.get('total_value', 0):,.2f}
Holdings: {len(portfolio.get('holdings', []))}
Current P&L: {portfolio.get('total_gain_loss_percent', 0):.2f}%

Equity Analyses Summary:
{equity_analyses[:3] if equity_analyses else 'No analysis available'}

Risk Assessment:
{risk_assessment}
"""
        
        prompt = """Based on the portfolio analysis, provide 5 specific, actionable recommendations.
Consider:
1. Asset allocation optimization
2. Risk management
3. Underperforming holdings
4. Market opportunities
5. Diversification needs

Format each recommendation as a clear action item."""
        
        try:
            response = await equity_agent.think(prompt, context)
            # Parse recommendations from response
            recommendations = [
                line.strip() for line in response.split('\n')
                if line.strip() and (
                    line.strip()[0].isdigit() or 
                    line.strip().startswith('-') or
                    line.strip().startswith('•')
                )
            ]
            return recommendations[:5]
        except Exception as e:
            return [f"Analysis pending - {str(e)}"]
    
    async def chat(
        self, 
        message: str, 
        user_id: str, 
        portfolio_id: Optional[str] = None
    ) -> str:
        """
        Chat interface with the finance copilot
        Uses RAG for context-aware responses
        """
        # Build context from portfolio if available
        context = ""
        if portfolio_id:
            from routes.portfolio import portfolios_db
            portfolio = portfolios_db.get(portfolio_id)
            if portfolio:
                context = f"""
Current Portfolio: {portfolio.get('name')}
Total Value: ${portfolio.get('total_value', 0):,.2f}
Holdings: {[h['symbol'] for h in portfolio.get('holdings', [])]}
"""
        
        # Use RAG for additional context
        if self.rag_engine:
            try:
                rag_response = await self.rag_engine.query_with_sources(message)
                context += f"\nRelevant Documents:\n{rag_response.get('answer', '')}"
            except:
                pass
        
        # Determine which agent should respond
        agent = self._route_query(message)
        
        # Generate response
        response = await agent.think(
            prompt=message,
            context=context
        )
        
        return response
    
    def _route_query(self, message: str) -> BaseAgent:
        """
        Route query to appropriate agent based on content
        """
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['news', 'headline', 'article']):
            return self.agents["news"]
        elif any(word in message_lower for word in ['risk', 'volatility', 'drawdown']):
            return self.agents["risk"]
        elif any(word in message_lower for word in ['trend', 'technical', 'chart', 'price']):
            return self.agents["market"]
        elif any(word in message_lower for word in ['portfolio', 'allocation', 'rebalance']):
            return self.agents["portfolio"]
        else:
            return self.agents["equity"]  # Default to equity research
    
    async def generate_report(
        self, 
        portfolio_id: str, 
        user_id: str, 
        format: str = "pdf"
    ) -> bytes:
        """
        Generate downloadable portfolio report
        """
        # Get analysis
        analysis = await self.analyze_portfolio(portfolio_id, user_id)
        
        # Generate HTML report
        html_content = self._generate_html_report(analysis)
        
        if format == "html":
            return html_content.encode()
        
        # Convert to PDF (simplified - would use weasyprint or similar)
        return html_content.encode()
    
    def _generate_html_report(self, analysis: Dict) -> str:
        """Generate HTML report from analysis"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Portfolio Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #2c3e50; }}
        .section {{ margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 15px; background: white; border-radius: 4px; }}
    </style>
</head>
<body>
    <h1>📊 Portfolio Analysis Report</h1>
    <p>Generated: {analysis.get('analysis_date', 'N/A')}</p>
    
    <div class="section">
        <h2>Portfolio Health</h2>
        <pre>{analysis.get('portfolio_health', {})}</pre>
    </div>
    
    <div class="section">
        <h2>Risk Assessment</h2>
        <pre>{analysis.get('risk_assessment', {})}</pre>
    </div>
    
    <div class="section">
        <h2>Market Overview</h2>
        <pre>{analysis.get('market_overview', {})}</pre>
    </div>
    
    <div class="section">
        <h2>Recommendations</h2>
        <ul>
            {''.join(f'<li>{r}</li>' for r in analysis.get('recommendations', []))}
        </ul>
    </div>
</body>
</html>
"""
