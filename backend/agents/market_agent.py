"""
Market Trend Agent - Technical analysis and market trends
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from .base_agent import BaseAgent
from models.stock import MarketTrend
from services.market_data import MarketDataService


class MarketTrendAgent(BaseAgent):
    """
    Specialized agent for technical analysis and market trends
    
    Capabilities:
    - Technical indicator analysis
    - Trend identification
    - Support/resistance levels
    - Market overview
    """
    
    def __init__(self):
        super().__init__(
            name="Market Trend Agent",
            description="""Expert technical analyst specializing in:
            - Price trend analysis and pattern recognition
            - Technical indicators (RSI, MACD, Moving Averages)
            - Support and resistance level identification
            - Volume analysis and market breadth
            - Market sentiment indicators"""
        )
        self.market_service = MarketDataService()
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute market trend task"""
        task_type = task.get("type", "analyze_trend")
        symbol = task.get("symbol", "")
        
        if task_type == "analyze_trend":
            timeframe = task.get("timeframe", "1m")
            return await self.analyze_trend(symbol, timeframe)
        elif task_type == "market_overview":
            return await self.get_market_overview()
        elif task_type == "sector_performance":
            return await self.get_sector_performance()
        else:
            return {"error": f"Unknown task type: {task_type}"}
    
    async def analyze_trend(self, symbol: str, timeframe: str = "1m") -> MarketTrend:
        """
        Analyze market trend for a symbol
        """
        symbol = symbol.upper()
        
        # Fetch historical data
        historical = await self.market_service.get_historical_data(symbol, timeframe)
        price_data = await self.market_service.get_stock_price(symbol)
        
        # Calculate technical indicators
        indicators = self._calculate_indicators(historical)
        
        # Identify support/resistance
        support_resistance = self._find_support_resistance(historical)
        
        # Determine trend
        trend = self._determine_trend(historical, indicators)
        
        # Build context for LLM analysis
        context = f"""
Symbol: {symbol}
Timeframe: {timeframe}
Current Price: ${price_data.get('price', 'N/A')}

Technical Indicators:
- RSI (14): {indicators.get('rsi', 'N/A')}
- MACD: {indicators.get('macd', {})}
- SMA 20: ${indicators.get('sma_20', 'N/A')}
- SMA 50: ${indicators.get('sma_50', 'N/A')}
- SMA 200: ${indicators.get('sma_200', 'N/A')}

Support Levels: {support_resistance.get('support', [])}
Resistance Levels: {support_resistance.get('resistance', [])}

Volume: {indicators.get('volume_trend', 'N/A')}
"""
        
        prompt = """Provide technical analysis:
1. Current trend direction (bullish/bearish/sideways)
2. Key technical levels to watch
3. Momentum assessment
4. Volume analysis
5. Short-term outlook"""
        
        analysis = await self.think(prompt, context)
        
        return MarketTrend(
            symbol=symbol,
            timeframe=timeframe,
            trend=trend,
            support_levels=support_resistance.get('support', []),
            resistance_levels=support_resistance.get('resistance', []),
            moving_averages={
                'sma_20': indicators.get('sma_20'),
                'sma_50': indicators.get('sma_50'),
                'sma_200': indicators.get('sma_200')
            },
            rsi=indicators.get('rsi'),
            macd=indicators.get('macd'),
            volume_trend=indicators.get('volume_trend', 'normal'),
            analysis=analysis
        )
    
    async def get_market_overview(self) -> Dict[str, Any]:
        """
        Get overall market overview
        """
        # Fetch major indices
        indices = {
            'SPY': 'S&P 500',
            'QQQ': 'NASDAQ 100',
            'DIA': 'Dow Jones',
            'IWM': 'Russell 2000',
            'VIX': 'Volatility Index'
        }
        
        market_data = {}
        for symbol, name in indices.items():
            try:
                price = await self.market_service.get_stock_price(symbol)
                market_data[name] = {
                    'symbol': symbol,
                    'price': price.get('price', 0),
                    'change': price.get('change', 0),
                    'change_percent': price.get('change_percent', 0)
                }
            except Exception as e:
                market_data[name] = {'error': str(e)}
        
        # Generate market commentary
        context = f"Market Data:\n{market_data}"
        prompt = """Based on the market data, provide:
1. Overall market sentiment (risk-on/risk-off)
2. Key observations
3. Sector rotation signals
4. What to watch today"""
        
        commentary = await self.think(prompt, context)
        
        return {
            'indices': market_data,
            'commentary': commentary,
            'timestamp': datetime.now().isoformat()
        }
    
    async def get_sector_performance(self) -> Dict[str, Any]:
        """
        Get sector performance analysis
        """
        # Sector ETFs
        sectors = {
            'XLK': 'Technology',
            'XLF': 'Financials',
            'XLV': 'Healthcare',
            'XLE': 'Energy',
            'XLY': 'Consumer Discretionary',
            'XLP': 'Consumer Staples',
            'XLI': 'Industrials',
            'XLB': 'Materials',
            'XLRE': 'Real Estate',
            'XLU': 'Utilities',
            'XLC': 'Communication Services'
        }
        
        sector_data = {}
        for symbol, name in sectors.items():
            try:
                price = await self.market_service.get_stock_price(symbol)
                sector_data[name] = {
                    'symbol': symbol,
                    'change_percent': price.get('change_percent', 0)
                }
            except Exception as e:
                sector_data[name] = {'error': str(e)}
        
        # Sort by performance
        sorted_sectors = sorted(
            sector_data.items(), 
            key=lambda x: x[1].get('change_percent', 0) if isinstance(x[1], dict) else 0,
            reverse=True
        )
        
        # Generate analysis
        context = f"Sector Performance:\n{dict(sorted_sectors)}"
        prompt = """Analyze sector performance:
1. Leading sectors and why
2. Lagging sectors and concerns
3. Rotation patterns
4. Sector recommendations"""
        
        analysis = await self.think(prompt, context)
        
        return {
            'sectors': dict(sorted_sectors),
            'leaders': [s[0] for s in sorted_sectors[:3]],
            'laggards': [s[0] for s in sorted_sectors[-3:]],
            'analysis': analysis,
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_indicators(self, historical: List[Dict]) -> Dict[str, Any]:
        """
        Calculate technical indicators from historical data
        """
        if not historical:
            return {}
        
        prices = [h.get('close', 0) for h in historical]
        volumes = [h.get('volume', 0) for h in historical]
        
        indicators = {}
        
        # Simple Moving Averages
        if len(prices) >= 20:
            indicators['sma_20'] = round(sum(prices[-20:]) / 20, 2)
        if len(prices) >= 50:
            indicators['sma_50'] = round(sum(prices[-50:]) / 50, 2)
        if len(prices) >= 200:
            indicators['sma_200'] = round(sum(prices[-200:]) / 200, 2)
        
        # RSI (simplified)
        if len(prices) >= 15:
            changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
            gains = [c for c in changes[-14:] if c > 0]
            losses = [-c for c in changes[-14:] if c < 0]
            
            avg_gain = sum(gains) / 14 if gains else 0
            avg_loss = sum(losses) / 14 if losses else 0.0001
            
            rs = avg_gain / avg_loss
            indicators['rsi'] = round(100 - (100 / (1 + rs)), 2)
        
        # Volume trend
        if len(volumes) >= 20:
            recent_vol = sum(volumes[-5:]) / 5
            avg_vol = sum(volumes[-20:]) / 20
            
            if recent_vol > avg_vol * 1.5:
                indicators['volume_trend'] = 'high'
            elif recent_vol < avg_vol * 0.5:
                indicators['volume_trend'] = 'low'
            else:
                indicators['volume_trend'] = 'normal'
        
        # MACD (simplified)
        if len(prices) >= 26:
            ema_12 = sum(prices[-12:]) / 12  # Simplified as SMA
            ema_26 = sum(prices[-26:]) / 26
            macd_line = ema_12 - ema_26
            indicators['macd'] = {
                'macd_line': round(macd_line, 4),
                'signal': 'bullish' if macd_line > 0 else 'bearish'
            }
        
        return indicators
    
    def _find_support_resistance(self, historical: List[Dict]) -> Dict[str, List[float]]:
        """
        Find support and resistance levels
        """
        if not historical or len(historical) < 10:
            return {'support': [], 'resistance': []}
        
        prices = [h.get('close', 0) for h in historical]
        highs = [h.get('high', 0) for h in historical]
        lows = [h.get('low', 0) for h in historical]
        
        current_price = prices[-1]
        
        # Find local maxima and minima
        resistance_levels = []
        support_levels = []
        
        for i in range(2, len(prices) - 2):
            # Local maximum
            if highs[i] > highs[i-1] and highs[i] > highs[i+1] and highs[i] > current_price:
                resistance_levels.append(round(highs[i], 2))
            
            # Local minimum
            if lows[i] < lows[i-1] and lows[i] < lows[i+1] and lows[i] < current_price:
                support_levels.append(round(lows[i], 2))
        
        # Get unique levels, sorted
        resistance_levels = sorted(list(set(resistance_levels)))[:3]
        support_levels = sorted(list(set(support_levels)), reverse=True)[:3]
        
        return {
            'support': support_levels,
            'resistance': resistance_levels
        }
    
    def _determine_trend(self, historical: List[Dict], indicators: Dict) -> str:
        """
        Determine overall trend direction
        """
        if not historical or len(historical) < 20:
            return 'sideways'
        
        prices = [h.get('close', 0) for h in historical]
        current = prices[-1]
        
        sma_20 = indicators.get('sma_20', current)
        sma_50 = indicators.get('sma_50', current)
        rsi = indicators.get('rsi', 50)
        
        bullish_signals = 0
        bearish_signals = 0
        
        # Price vs MAs
        if current > sma_20:
            bullish_signals += 1
        else:
            bearish_signals += 1
        
        if current > sma_50:
            bullish_signals += 1
        else:
            bearish_signals += 1
        
        # RSI
        if rsi > 50:
            bullish_signals += 1
        elif rsi < 50:
            bearish_signals += 1
        
        # Recent price action
        recent_change = (current - prices[-20]) / prices[-20] * 100 if prices[-20] else 0
        if recent_change > 5:
            bullish_signals += 1
        elif recent_change < -5:
            bearish_signals += 1
        
        if bullish_signals >= 3:
            return 'bullish'
        elif bearish_signals >= 3:
            return 'bearish'
        else:
            return 'sideways'
