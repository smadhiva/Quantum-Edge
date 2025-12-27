"""
News Service - News aggregation and processing
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
import aiohttp
import feedparser
from config import settings


class NewsService:
    """
    Service for fetching and processing financial news
    
    Sources:
    - RSS feeds (Yahoo Finance, CNBC, Bloomberg)
    - Google News (via RSS)
    """
    
    def __init__(self):
        self.rss_feeds = [
            {
                "name": "Yahoo Finance",
                "url": "https://finance.yahoo.com/news/rssindex"
            },
            {
                "name": "CNBC",
                "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html"
            },
            {
                "name": "MarketWatch",
                "url": "http://feeds.marketwatch.com/marketwatch/topstories"
            },
            {
                "name": "Reuters Business",
                "url": "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best"
            }
        ]
        self.cache: Dict[str, Dict] = {}
        self.cache_ttl = 300  # 5 minutes
    
    async def fetch_news(self, symbol: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch news, optionally filtered by symbol
        """
        cache_key = f"news_{symbol or 'general'}"
        
        if self._is_cache_valid(cache_key):
            cached = self.cache[cache_key]["data"]
            return cached[:limit]
        
        all_news = []
        
        # Fetch from RSS feeds
        for feed in self.rss_feeds:
            try:
                news = await self._fetch_rss(feed["url"], feed["name"])
                all_news.extend(news)
            except Exception as e:
                print(f"Error fetching from {feed['name']}: {e}")
        
        # Fetch symbol-specific news if symbol provided
        if symbol:
            try:
                symbol_news = await self._fetch_yahoo_symbol_news(symbol)
                all_news.extend(symbol_news)
            except Exception as e:
                print(f"Error fetching Yahoo news for {symbol}: {e}")
        
        # Remove duplicates and sort by date
        seen_titles = set()
        unique_news = []
        for item in all_news:
            title = item.get("title", "")
            if title not in seen_titles:
                seen_titles.add(title)
                unique_news.append(item)
        
        # Sort by date (newest first)
        unique_news.sort(
            key=lambda x: x.get("published_at", datetime.min),
            reverse=True
        )
        
        # Filter by symbol if provided
        if symbol:
            symbol_upper = symbol.upper()
            filtered_news = [
                n for n in unique_news
                if symbol_upper in n.get("title", "").upper() or
                   symbol_upper in n.get("summary", "").upper()
            ]
            # If not enough symbol-specific news, include general news
            if len(filtered_news) < limit:
                filtered_news.extend(unique_news[:limit - len(filtered_news)])
            unique_news = filtered_news
        
        # Update cache
        self._update_cache(cache_key, unique_news)
        
        return unique_news[:limit]
    
    async def _fetch_rss(self, url: str, source: str) -> List[Dict[str, Any]]:
        """
        Fetch news from RSS feed
        """
        try:
            # feedparser is synchronous, run in executor
            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, url)
            
            news = []
            for entry in feed.entries[:20]:
                # Parse published date
                published_at = datetime.now()
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        published_at = datetime(*entry.published_parsed[:6])
                    except:
                        pass
                
                news.append({
                    "title": entry.get("title", "No title"),
                    "summary": entry.get("summary", entry.get("description", ""))[:500],
                    "url": entry.get("link", ""),
                    "source": source,
                    "published_at": published_at
                })
            
            return news
            
        except Exception as e:
            print(f"RSS fetch error for {url}: {e}")
            return []
    
    async def _fetch_yahoo_symbol_news(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Fetch symbol-specific news from Yahoo Finance
        """
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            if not news:
                return []
            
            formatted_news = []
            for item in news[:10]:
                published_at = datetime.fromtimestamp(item.get("providerPublishTime", 0))
                
                formatted_news.append({
                    "title": item.get("title", ""),
                    "summary": item.get("title", ""),  # Yahoo doesn't always have summaries
                    "url": item.get("link", ""),
                    "source": item.get("publisher", "Yahoo Finance"),
                    "published_at": published_at,
                    "related_symbols": [symbol]
                })
            
            return formatted_news
            
        except Exception as e:
            print(f"Yahoo news fetch error for {symbol}: {e}")
            return []
    
    async def fetch_google_news(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch news from Google News RSS
        """
        url = f"https://news.google.com/rss/search?q={query}+stock+market&hl=en-US&gl=US&ceid=US:en"
        
        try:
            news = await self._fetch_rss(url, "Google News")
            return news[:limit]
        except Exception as e:
            print(f"Google News fetch error: {e}")
            return []
    
    async def get_market_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get general market news
        """
        return await self.fetch_news(limit=limit)
    
    async def get_trending_topics(self) -> List[str]:
        """
        Get trending financial topics
        """
        news = await self.fetch_news(limit=50)
        
        # Extract common keywords (simplified)
        word_count: Dict[str, int] = {}
        stop_words = {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'or', 'is', 'are'}
        
        for item in news:
            words = item.get("title", "").lower().split()
            for word in words:
                word = word.strip('.,!?()[]{}":;')
                if word and len(word) > 3 and word not in stop_words:
                    word_count[word] = word_count.get(word, 0) + 1
        
        # Sort by frequency
        sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        
        return [word for word, count in sorted_words[:10]]
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache is valid"""
        if key not in self.cache:
            return False
        
        cached_at = self.cache[key].get("timestamp", 0)
        return (datetime.now().timestamp() - cached_at) < self.cache_ttl
    
    def _update_cache(self, key: str, data: List):
        """Update cache"""
        self.cache[key] = {
            "data": data,
            "timestamp": datetime.now().timestamp()
        }
