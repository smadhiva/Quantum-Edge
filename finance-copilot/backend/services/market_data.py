"""
Market Data Service - Real-time and historical market data
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import aiohttp
from config import settings


class MarketDataService:
    """
    Service for fetching market data from various sources
    
    Supports:
    - Yahoo Finance (primary)
    - Alpha Vantage (backup)
    """
    
    def __init__(self):
        self.cache: Dict[str, Dict] = {}
        self.cache_ttl = 60  # seconds
    
    async def get_stock_price(self, symbol: str) -> Dict[str, Any]:
        """
        Get current stock price
        """
        symbol = symbol.upper()
        
        # Check cache
        cache_key = f"price_{symbol}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]["data"]
        
        try:
            # Use yfinance
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            info = ticker.info
            history = ticker.history(period="1d")
            
            if history.empty:
                return self._get_fallback_price(symbol)
            
            current_price = float(history['Close'].iloc[-1])
            prev_close = info.get('previousClose', current_price)
            change = current_price - prev_close
            change_percent = (change / prev_close * 100) if prev_close else 0
            
            data = {
                "symbol": symbol,
                "price": round(current_price, 2),
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "volume": int(history['Volume'].iloc[-1]),
                "high": round(float(history['High'].iloc[-1]), 2),
                "low": round(float(history['Low'].iloc[-1]), 2),
                "open": round(float(history['Open'].iloc[-1]), 2),
                "previous_close": round(prev_close, 2),
                "timestamp": datetime.now().isoformat()
            }
            
            # Update cache
            self._update_cache(cache_key, data)
            
            return data
            
        except Exception as e:
            print(f"Error fetching price for {symbol}: {e}")
            return self._get_fallback_price(symbol)
    
    async def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """
        Get company fundamentals
        """
        symbol = symbol.upper()
        
        cache_key = f"fundamentals_{symbol}"
        if self._is_cache_valid(cache_key, ttl=300):  # 5 min cache
            return self.cache[cache_key]["data"]
        
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            data = {
                "symbol": symbol,
                "name": info.get("longName", symbol),
                "sector": info.get("sector", "Unknown"),
                "industry": info.get("industry", "Unknown"),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "pb_ratio": info.get("priceToBook"),
                "dividend_yield": info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0,
                "eps": info.get("trailingEps"),
                "revenue": info.get("totalRevenue", 0),
                "profit_margin": info.get("profitMargins", 0) * 100 if info.get("profitMargins") else 0,
                "operating_margin": info.get("operatingMargins", 0) * 100 if info.get("operatingMargins") else 0,
                "debt_to_equity": info.get("debtToEquity"),
                "roe": info.get("returnOnEquity", 0) * 100 if info.get("returnOnEquity") else 0,
                "roa": info.get("returnOnAssets", 0) * 100 if info.get("returnOnAssets") else 0,
                "beta": info.get("beta"),
                "52_week_high": info.get("fiftyTwoWeekHigh"),
                "52_week_low": info.get("fiftyTwoWeekLow"),
                "avg_volume": info.get("averageVolume"),
                "description": info.get("longBusinessSummary", "")[:500]
            }
            
            self._update_cache(cache_key, data)
            return data
            
        except Exception as e:
            print(f"Error fetching fundamentals for {symbol}: {e}")
            return {"symbol": symbol, "error": str(e)}
    
    async def get_historical_data(
        self, 
        symbol: str, 
        period: str = "1m"
    ) -> List[Dict[str, Any]]:
        """
        Get historical price data
        
        period: 1d, 5d, 1m, 3m, 6m, 1y, 2y, 5y, max
        """
        symbol = symbol.upper()
        
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            history = ticker.history(period=period)
            
            if history.empty:
                return []
            
            data = []
            for date, row in history.iterrows():
                data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "open": round(float(row['Open']), 2),
                    "high": round(float(row['High']), 2),
                    "low": round(float(row['Low']), 2),
                    "close": round(float(row['Close']), 2),
                    "volume": int(row['Volume'])
                })
            
            return data
            
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {e}")
            return []
    
    async def get_peers(self, symbol: str) -> List[str]:
        """
        Get peer companies
        """
        symbol = symbol.upper()
        
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # yfinance doesn't have direct peer info
            # We'll use sector-based peers
            sector = info.get("sector", "")
            
            # Predefined sector ETFs as peer proxies
            sector_etfs = {
                "Technology": ["MSFT", "AAPL", "GOOGL", "META", "NVDA"],
                "Financial Services": ["JPM", "BAC", "WFC", "GS", "MS"],
                "Healthcare": ["JNJ", "UNH", "PFE", "ABBV", "MRK"],
                "Consumer Cyclical": ["AMZN", "TSLA", "HD", "NKE", "MCD"],
                "Communication Services": ["GOOGL", "META", "DIS", "NFLX", "CMCSA"],
                "Industrials": ["HON", "UPS", "CAT", "BA", "GE"],
                "Energy": ["XOM", "CVX", "COP", "SLB", "EOG"],
            }
            
            peers = sector_etfs.get(sector, [])
            # Remove the symbol itself from peers
            peers = [p for p in peers if p != symbol][:4]
            
            return peers
            
        except Exception as e:
            print(f"Error fetching peers for {symbol}: {e}")
            return []
    
    async def get_batch_prices(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Get prices for multiple symbols
        """
        tasks = [self.get_stock_price(s) for s in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            symbols[i]: results[i] if not isinstance(results[i], Exception) else {"error": str(results[i])}
            for i in range(len(symbols))
        }
    
    def _is_cache_valid(self, key: str, ttl: int = None) -> bool:
        """Check if cache entry is valid"""
        if key not in self.cache:
            return False
        
        cache_ttl = ttl or self.cache_ttl
        cached_at = self.cache[key].get("timestamp", 0)
        return (datetime.now().timestamp() - cached_at) < cache_ttl
    
    def _update_cache(self, key: str, data: Dict):
        """Update cache entry"""
        self.cache[key] = {
            "data": data,
            "timestamp": datetime.now().timestamp()
        }
    
    def _get_fallback_price(self, symbol: str) -> Dict[str, Any]:
        """Return fallback price data"""
        return {
            "symbol": symbol,
            "price": 0,
            "change": 0,
            "change_percent": 0,
            "error": "Unable to fetch price",
            "timestamp": datetime.now().isoformat()
        }


class AlphaVantageService:
    """
    Alternative market data source using Alpha Vantage API
    """
    
    def __init__(self):
        self.api_key = settings.alpha_vantage_api_key
        self.base_url = "https://www.alphavantage.co/query"
    
    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get stock quote from Alpha Vantage"""
        if not self.api_key:
            return {"error": "Alpha Vantage API key not configured"}
        
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    data = await response.json()
                    
                    if "Global Quote" not in data:
                        return {"error": "No data returned"}
                    
                    quote = data["Global Quote"]
                    return {
                        "symbol": symbol,
                        "price": float(quote.get("05. price", 0)),
                        "change": float(quote.get("09. change", 0)),
                        "change_percent": float(quote.get("10. change percent", "0%").replace("%", "")),
                        "volume": int(quote.get("06. volume", 0))
                    }
        except Exception as e:
            return {"error": str(e)}
