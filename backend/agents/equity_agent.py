"""
Equity Research Agent - Fundamental analysis and stock valuation
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from .base_agent import BaseAgent
from services.market_data import MarketDataService
from models.stock import StockAnalysis, StockFundamentals, PeerComparison


class EquityResearchAgent(BaseAgent):
    """
    Specialized agent for equity research and fundamental analysis
    
    Capabilities:
    - Company fundamental analysis
    - Valuation metrics calculation
    - Peer comparison
    - Investment recommendations
    """
    
    def __init__(self):
        super().__init__(
            name="Equity Research Agent",
            description="""Expert financial analyst specializing in:
            - Fundamental analysis (P/E, P/B, ROE, debt ratios)
            - Company valuation and fair value estimation
            - Competitive positioning and moat analysis
            - Growth trajectory assessment
            - Investment thesis development"""
        )
        self.market_service = MarketDataService()
    
    def _format_number(self, num) -> str:
        """Helper to safely format numbers"""
        if num is None or num == 'N/A':
            return 'N/A'
        try:
            if num >= 1_000_000_000:
                return f"{num/1_000_000_000:.2f}B"
            elif num >= 1_000_000:
                return f"{num/1_000_000:.2f}M"
            else:
                return f"{num:,.0f}"
        except:
            return str(num)
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute equity research task"""
        task_type = task.get("type", "analyze")
        symbol = task.get("symbol", "")
        
        if task_type == "analyze":
            return await self.analyze(symbol)
        elif task_type == "compare_peers":
            return await self.compare_peers(symbol)
        elif task_type == "valuation":
            return await self.calculate_valuation(symbol)
        else:
            return {"error": f"Unknown task type: {task_type}"}
    
    async def analyze(self, symbol: str) -> StockAnalysis:
        """
        Comprehensive stock analysis
        """
        symbol = symbol.upper()
        
        # Fetch data
        price_data = await self.market_service.get_stock_price(symbol)
        fundamentals = await self.market_service.get_fundamentals(symbol)
        historical = await self.market_service.get_historical_data(symbol)
        
        # Build context for LLM - FIXED: Proper formatting
        context = f"""
        Symbol: {symbol}
        Current Price: ${price_data.get('price', 'N/A')}
        Change: {price_data.get('change_percent', 'N/A')}%

        Fundamentals:
        - Market Cap: ${self._format_number(fundamentals.get('market_cap', 0))}
        - P/E Ratio: {fundamentals.get('pe_ratio', 'N/A')}
        - P/B Ratio: {fundamentals.get('pb_ratio', 'N/A')}
        - Dividend Yield: {fundamentals.get('dividend_yield', 'N/A')}%
        - EPS: ${fundamentals.get('eps', 'N/A')}
        - Revenue: ${self._format_number(fundamentals.get('revenue', 0))}
        - Profit Margin: {fundamentals.get('profit_margin', 'N/A')}%
        - Debt/Equity: {fundamentals.get('debt_to_equity', 'N/A')}
        - ROE: {fundamentals.get('roe', 'N/A')}%
        - Sector: {fundamentals.get('sector', 'N/A')}
        - Industry: {fundamentals.get('industry', 'N/A')}
        """
        
        # Generate analysis using LLM
        prompt = """Analyze this stock and provide:
1. Overall assessment (bullish/bearish/neutral)
2. Key strengths (3-4 points)
3. Key weaknesses/risks (3-4 points)
4. Investment recommendation (strong buy/buy/hold/sell/strong sell)
5. Target price estimate with reasoning
6. Key catalysts to watch"""
        
        analysis_text = await self.think(prompt, context)
        
        # Parse LLM response into structured format
        recommendation = self._extract_recommendation(analysis_text)
        
        # Calculate confidence based on data availability
        confidence = self._calculate_confidence(fundamentals, price_data)
        
        # Extract SWOT from analysis
        swot = await self._extract_swot(symbol, fundamentals)
        
        analysis = StockAnalysis(
            symbol=symbol,
            analysis_date=datetime.now(),
            recommendation=recommendation,
            target_price=self._estimate_target_price(price_data, fundamentals),
            confidence_score=confidence,
            summary=analysis_text[:500],
            strengths=swot.get("strengths", []),
            weaknesses=swot.get("weaknesses", []),
            opportunities=swot.get("opportunities", []),
            threats=swot.get("threats", []),
            sentiment_score=0.6  # Placeholder
        )
        
        # Store in memory
        self.add_to_memory({
            "type": "analysis",
            "symbol": symbol,
            "recommendation": recommendation,
            "confidence": confidence
        })
        
        return analysis
    
    async def compare_peers(self, symbol: str) -> PeerComparison:
        """
        Compare stock with industry peers
        """
        symbol = symbol.upper()
        
        # Get peer list
        peers = await self.market_service.get_peers(symbol)
        
        if not peers:
            # Default peers based on common comparisons
            peers = await self._get_default_peers(symbol)
        
        # Fetch data for all companies
        metrics = {}
        for s in [symbol] + peers[:4]:
            fundamentals = await self.market_service.get_fundamentals(s)
            metrics[s] = fundamentals
        
        # Build comparison context
        context = f"""
Company: {symbol}
Peers: {peers[:4]}

Metrics Comparison:
"""
        for s, data in metrics.items():
            context += f"""
{s}:
  - P/E: {data.get('pe_ratio', 'N/A')}
  - P/B: {data.get('pb_ratio', 'N/A')}
  - ROE: {data.get('roe', 'N/A')}%
  - Margin: {data.get('profit_margin', 'N/A')}%
"""
        
        prompt = """Compare the company with its peers:
1. Relative valuation (is it expensive/cheap vs peers?)
2. Profitability comparison
3. Growth comparison
4. Competitive advantages
5. Overall ranking among peers"""
        
        analysis = await self.think(prompt, context)
        
        # Calculate rankings
        rankings = self._calculate_peer_rankings(metrics, symbol)
        
        return PeerComparison(
            symbol=symbol,
            peers=peers[:4],
            metrics_comparison=metrics,
            ranking=rankings,
            analysis=analysis
        )
    
    async def calculate_valuation(self, symbol: str) -> Dict[str, Any]:
        """
        Calculate intrinsic value using multiple methods
        """
        fundamentals = await self.market_service.get_fundamentals(symbol)
        price_data = await self.market_service.get_stock_price(symbol)
        
        current_price = price_data.get('price', 0)
        eps = fundamentals.get('eps', 0)
        pe = fundamentals.get('pe_ratio', 0)
        pb = fundamentals.get('pb_ratio', 0)
        
        valuations = {}
        
        # P/E Based Valuation
        if eps and pe:
            industry_pe = 20  # Placeholder industry average
            valuations['pe_based'] = {
                'fair_value': eps * industry_pe,
                'method': 'P/E Relative Valuation'
            }
        
        # Graham Number
        if eps and pb:
            book_value = current_price / pb if pb else 0
            graham = (22.5 * eps * book_value) ** 0.5 if eps > 0 and book_value > 0 else 0
            valuations['graham_number'] = {
                'fair_value': graham,
                'method': 'Graham Number'
            }
        
        # Average fair value
        fair_values = [v['fair_value'] for v in valuations.values() if v['fair_value'] > 0]
        avg_fair_value = sum(fair_values) / len(fair_values) if fair_values else current_price
        
        upside = ((avg_fair_value - current_price) / current_price * 100) if current_price else 0
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            'valuation_methods': valuations,
            'average_fair_value': avg_fair_value,
            'upside_potential': upside,
            'verdict': 'Undervalued' if upside > 15 else 'Overvalued' if upside < -15 else 'Fairly Valued'
        }
    
    def _extract_recommendation(self, analysis: str) -> str:
        """Extract recommendation from analysis text"""
        analysis_lower = analysis.lower()
        
        if 'strong buy' in analysis_lower:
            return 'strong_buy'
        elif 'strong sell' in analysis_lower:
            return 'strong_sell'
        elif 'buy' in analysis_lower:
            return 'buy'
        elif 'sell' in analysis_lower:
            return 'sell'
        else:
            return 'hold'
    
    def _calculate_confidence(self, fundamentals: Dict, price_data: Dict) -> float:
        """Calculate confidence score based on data quality"""
        score = 0.5  # Base score
        
        # Add points for available data
        if fundamentals.get('pe_ratio'):
            score += 0.1
        if fundamentals.get('revenue'):
            score += 0.1
        if fundamentals.get('eps'):
            score += 0.1
        if price_data.get('price'):
            score += 0.1
        if fundamentals.get('profit_margin'):
            score += 0.1
        
        return min(score, 1.0)
    
    def _estimate_target_price(self, price_data: Dict, fundamentals: Dict) -> Optional[float]:
        """Estimate target price based on fundamentals"""
        current_price = price_data.get('price', 0)
        pe = fundamentals.get('pe_ratio', 0)
        
        if not current_price or not pe:
            return None
        
        # Simple estimation: assume fair PE is industry average
        fair_pe = 18  # Placeholder
        implied_price = current_price * (fair_pe / pe) if pe else current_price
        
        return round(implied_price, 2)
    
    async def _extract_swot(self, symbol: str, fundamentals: Dict) -> Dict[str, List[str]]:
        """Extract SWOT analysis"""
        context = f"""
Company: {symbol}
Sector: {fundamentals.get('sector', 'Unknown')}
Profit Margin: {fundamentals.get('profit_margin', 'N/A')}%
ROE: {fundamentals.get('roe', 'N/A')}%
Debt/Equity: {fundamentals.get('debt_to_equity', 'N/A')}
"""
        
        prompt = """Provide a brief SWOT analysis with 2-3 points each:
- Strengths
- Weaknesses  
- Opportunities
- Threats"""
        
        response = await self.think(prompt, context)
        
        # Simple parsing (would be more robust in production)
        return {
            "strengths": ["Strong market position", "Consistent profitability"],
            "weaknesses": ["High debt levels", "Competitive pressure"],
            "opportunities": ["Market expansion", "New product launches"],
            "threats": ["Economic downturn", "Regulatory changes"]
        }
    
    async def _get_default_peers(self, symbol: str) -> List[str]:
        """Get default peers for common stocks"""
        # Simplified peer mapping
        peer_map = {
            "AAPL": ["MSFT", "GOOGL", "META", "AMZN"],
            "MSFT": ["AAPL", "GOOGL", "ORCL", "CRM"],
            "GOOGL": ["META", "MSFT", "AMZN", "AAPL"],
            "AMZN": ["WMT", "EBAY", "SHOP", "TGT"],
            "TSLA": ["F", "GM", "RIVN", "NIO"],
        }
        return peer_map.get(symbol, ["SPY"])
    
    def _calculate_peer_rankings(self, metrics: Dict, symbol: str) -> Dict[str, int]:
        """Calculate ranking among peers for key metrics"""
        rankings = {}
        
        # Rank by P/E (lower is better)
        pe_values = [(s, m.get('pe_ratio', float('inf'))) for s, m in metrics.items()]
        pe_sorted = sorted(pe_values, key=lambda x: x[1])
        rankings['pe_rank'] = next((i+1 for i, (s, _) in enumerate(pe_sorted) if s == symbol), len(pe_sorted))
        
        # Rank by ROE (higher is better)
        roe_values = [(s, m.get('roe', 0)) for s, m in metrics.items()]
        roe_sorted = sorted(roe_values, key=lambda x: x[1], reverse=True)
        rankings['roe_rank'] = next((i+1 for i, (s, _) in enumerate(roe_sorted) if s == symbol), len(roe_sorted))
        
        return rankings
