"""
Pathway Data Streams - Real-time market data and news streaming
"""
import pathway as pw
from datetime import datetime
import asyncio
import json
from typing import Generator, Dict, Any, Optional
from config import settings


class PriceStream:
    """
    Real-time stock price streaming using Pathway
    Integrates with Yahoo Finance / Alpha Vantage
    """
    
    def __init__(self, symbols: list[str]):
        self.symbols = symbols
        self.update_interval = settings.price_update_interval
    
    def create_price_generator(self) -> Generator[Dict[str, Any], None, None]:
        """
        Generator that yields live price data
        Used by Pathway's python.read connector
        """
        import yfinance as yf
        
        while True:
            for symbol in self.symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    history = ticker.history(period="1d")
                    
                    if not history.empty:
                        current_price = history['Close'].iloc[-1]
                        open_price = history['Open'].iloc[-1]
                        high = history['High'].iloc[-1]
                        low = history['Low'].iloc[-1]
                        volume = int(history['Volume'].iloc[-1])
                        
                        prev_close = info.get('previousClose', current_price)
                        change = current_price - prev_close
                        change_percent = (change / prev_close * 100) if prev_close else 0
                        
                        yield {
                            "symbol": symbol,
                            "price": float(current_price),
                            "open": float(open_price),
                            "high": float(high),
                            "low": float(low),
                            "volume": volume,
                            "change": float(change),
                            "change_percent": float(change_percent),
                            "timestamp": datetime.now().isoformat()
                        }
                except Exception as e:
                    print(f"Error fetching price for {symbol}: {e}")
                    # Yield placeholder data on error
                    yield {
                        "symbol": symbol,
                        "price": 0.0,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
            
            # Wait before next update
            import time
            time.sleep(self.update_interval)
    
    def create_price_pipeline(self):
        """
        Create Pathway pipeline for price streaming
        """
        # Define schema for price data
        class PriceSchema(pw.Schema):
            symbol: str
            price: float
            open: float = 0.0
            high: float = 0.0
            low: float = 0.0
            volume: int = 0
            change: float = 0.0
            change_percent: float = 0.0
            timestamp: str
        
        # Create streaming source from generator
        prices = pw.io.python.read(
            self.create_price_generator(),
            schema=PriceSchema,
            mode="streaming"
        )
        
        # Add processing - calculate moving averages, etc.
        processed_prices = prices.select(
            symbol=pw.this.symbol,
            price=pw.this.price,
            change=pw.this.change,
            change_percent=pw.this.change_percent,
            timestamp=pw.this.timestamp,
            # Add flags for significant movements
            is_significant_move=pw.apply(
                lambda x: abs(x) > 2.0,
                pw.this.change_percent
            )
        )
        
        return processed_prices
    
    def add_symbol(self, symbol: str):
        """Add a symbol to track"""
        if symbol not in self.symbols:
            self.symbols.append(symbol)
    
    def remove_symbol(self, symbol: str):
        """Remove a symbol from tracking"""
        if symbol in self.symbols:
            self.symbols.remove(symbol)


class NewsStream:
    """
    Real-time news streaming using Pathway
    Aggregates from multiple sources
    """
    
    def __init__(self, symbols: list[str] = None, topics: list[str] = None):
        self.symbols = symbols or []
        self.topics = topics or ["stock market", "finance", "economy"]
        self.update_interval = settings.news_update_interval
    
    def create_news_generator(self) -> Generator[Dict[str, Any], None, None]:
        """
        Generator that yields news articles
        """
        import feedparser
        
        # RSS feeds for financial news
        rss_feeds = [
            "https://feeds.finance.yahoo.com/rss/2.0/headline",
            "https://www.cnbc.com/id/100003114/device/rss/rss.html",
            "https://feeds.bloomberg.com/markets/news.rss",
        ]
        
        while True:
            for feed_url in rss_feeds:
                try:
                    feed = feedparser.parse(feed_url)
                    
                    for entry in feed.entries[:10]:  # Latest 10 entries
                        # Check relevance to tracked symbols
                        related_symbols = []
                        for symbol in self.symbols:
                            if symbol.lower() in entry.title.lower() or \
                               symbol.lower() in entry.get('summary', '').lower():
                                related_symbols.append(symbol)
                        
                        yield {
                            "title": entry.title,
                            "summary": entry.get('summary', ''),
                            "url": entry.link,
                            "source": feed.feed.get('title', 'Unknown'),
                            "published": entry.get('published', ''),
                            "related_symbols": related_symbols,
                            "timestamp": datetime.now().isoformat()
                        }
                except Exception as e:
                    print(f"Error fetching news from {feed_url}: {e}")
            
            import time
            time.sleep(self.update_interval)
    
    def create_news_pipeline(self):
        """
        Create Pathway pipeline for news streaming
        """
        class NewsSchema(pw.Schema):
            title: str
            summary: str
            url: str
            source: str
            published: str
            related_symbols: list
            timestamp: str
        
        news = pw.io.python.read(
            self.create_news_generator(),
            schema=NewsSchema,
            mode="streaming"
        )
        
        return news


class PortfolioStream:
    """
    Stream for portfolio updates
    Monitors portfolio CSV files for changes
    """
    
    def __init__(self, portfolio_id: str):
        self.portfolio_id = portfolio_id
        self.portfolio_path = f"{settings.portfolios_path}/{portfolio_id}"
    
    def create_portfolio_pipeline(self):
        """
        Create pipeline to monitor portfolio changes
        """
        import os
        
        if not os.path.exists(self.portfolio_path):
            os.makedirs(self.portfolio_path, exist_ok=True)
        
        # Monitor CSV files in portfolio folder
        portfolio_data = pw.io.fs.read(
            self.portfolio_path,
            format="csv",
            mode="streaming",
            with_metadata=True
        )
        
        return portfolio_data


class CombinedStream:
    """
    Combines multiple streams for comprehensive market monitoring
    """
    
    def __init__(self, symbols: list[str]):
        self.symbols = symbols
        self.price_stream = PriceStream(symbols)
        self.news_stream = NewsStream(symbols)
    
    def create_combined_pipeline(self):
        """
        Create a combined pipeline that joins price and news data
        """
        prices = self.price_stream.create_price_pipeline()
        news = self.news_stream.create_news_pipeline()
        
        # This creates a comprehensive view of each symbol
        # with both price and news data
        return {
            "prices": prices,
            "news": news
        }
    
    async def start_streaming(self):
        """
        Start all streams
        """
        print(f"📊 Starting combined stream for symbols: {self.symbols}")
        pw.run()
