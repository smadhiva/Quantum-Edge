"""
News Intelligence Agent - Live news monitoring and sentiment analysis
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
import asyncio

from .base_agent import BaseAgent
from models.stock import NewsItem
from services.news_service import NewsService


class NewsIntelligenceAgent(BaseAgent):
    """
    Specialized agent for news intelligence and sentiment analysis
    
    Capabilities:
    - Real-time news aggregation
    - Sentiment analysis
    - Impact assessment
    - News summarization
    """
    
    def __init__(self):
        super().__init__(
            name="News Intelligence Agent",
            description="""Expert news analyst specializing in:
            - Financial news monitoring and aggregation
            - Sentiment analysis (bullish/bearish/neutral)
            - Impact assessment on stock prices
            - News summarization and key takeaways
            - Identifying market-moving events"""
        )
        self.news_service = NewsService()
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute news intelligence task"""
        task_type = task.get("type", "get_news")
        symbols = task.get("symbols", [])
        
        if task_type == "get_news":
            symbol = task.get("symbol", symbols[0] if symbols else "")
            return await self.get_news(symbol)
        elif task_type == "analyze_sentiment":
            return await self.analyze_sentiment(task.get("text", ""))
        elif task_type == "portfolio_news":
            return await self.get_portfolio_news(symbols)
        else:
            return {"error": f"Unknown task type: {task_type}"}
    
    async def get_news(self, symbol: str, limit: int = 10) -> List[NewsItem]:
        """
        Get latest news for a stock with sentiment analysis
        """
        symbol = symbol.upper()
        
        # Fetch news
        raw_news = await self.news_service.fetch_news(symbol, limit)
        
        # Analyze each article
        news_items = []
        for article in raw_news[:limit]:
            # Analyze sentiment
            sentiment = await self._analyze_article_sentiment(article)
            
            news_item = NewsItem(
                title=article.get('title', ''),
                source=article.get('source', 'Unknown'),
                url=article.get('url', ''),
                published_at=article.get('published_at', datetime.now()),
                summary=article.get('summary', ''),
                sentiment=sentiment.get('sentiment', 'neutral'),
                relevance_score=sentiment.get('relevance', 0.5),
                related_symbols=[symbol]
            )
            news_items.append(news_item)
        
        # Store in memory
        self.add_to_memory({
            "type": "news_fetch",
            "symbol": symbol,
            "count": len(news_items),
            "sentiments": [n.sentiment for n in news_items]
        })
        
        return news_items
    
    async def get_portfolio_news(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Get aggregated news for portfolio holdings
        """
        all_news = []
        symbol_news = {}
        
        # Fetch news for each symbol
        for symbol in symbols[:10]:  # Limit to top 10
            news = await self.get_news(symbol, limit=3)
            symbol_news[symbol] = news
            all_news.extend(news)
        
        # Sort by recency
        all_news.sort(key=lambda x: x.published_at, reverse=True)
        
        # Generate portfolio news summary
        summary = await self._generate_news_summary(all_news, symbols)
        
        # Calculate overall sentiment
        sentiments = [n.sentiment for n in all_news]
        overall_sentiment = self._calculate_overall_sentiment(sentiments)
        
        return {
            "symbols": symbols,
            "news_by_symbol": {s: [n.model_dump() for n in news] for s, news in symbol_news.items()},
            "recent_news": [n.model_dump() for n in all_news[:10]],
            "summary": summary,
            "overall_sentiment": overall_sentiment,
            "generated_at": datetime.now().isoformat()
        }
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of given text
        """
        prompt = """Analyze the sentiment of this financial text:

Text: {text}

Provide:
1. Sentiment: bullish, bearish, or neutral
2. Confidence: 0.0 to 1.0
3. Key phrases driving the sentiment
4. Potential market impact"""
        
        response = await self.think(prompt.format(text=text))
        
        # Parse response
        sentiment = "neutral"
        if "bullish" in response.lower():
            sentiment = "positive"
        elif "bearish" in response.lower():
            sentiment = "negative"
        
        return {
            "text": text[:200],
            "sentiment": sentiment,
            "analysis": response,
            "confidence": 0.7  # Placeholder
        }
    
    async def summarize_news(self, news_items: List[Dict]) -> str:
        """
        Summarize multiple news articles
        """
        if not news_items:
            return "No recent news available."
        
        context = "Recent news articles:\n\n"
        for i, item in enumerate(news_items[:5], 1):
            context += f"{i}. {item.get('title', 'No title')}\n"
            context += f"   Source: {item.get('source', 'Unknown')}\n"
            context += f"   Summary: {item.get('summary', 'No summary')[:200]}\n\n"
        
        prompt = """Provide a concise summary of these news articles:
1. Key themes and trends
2. Most impactful news
3. Overall market sentiment
4. What investors should watch"""
        
        summary = await self.think(prompt, context)
        return summary
    
    async def _analyze_article_sentiment(self, article: Dict) -> Dict[str, Any]:
        """
        Analyze sentiment of a single article
        """
        title = article.get('title', '')
        summary = article.get('summary', '')
        
        # Quick keyword-based sentiment (for speed)
        text = f"{title} {summary}".lower()
        
        positive_words = ['surge', 'gain', 'rise', 'up', 'growth', 'profit', 'beat', 'strong', 'bullish']
        negative_words = ['fall', 'drop', 'decline', 'down', 'loss', 'miss', 'weak', 'bearish', 'crash']
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count + 1:
            sentiment = "positive"
        elif negative_count > positive_count + 1:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        # Calculate relevance (simplified)
        relevance = min(1.0, (positive_count + negative_count) / 5)
        
        return {
            "sentiment": sentiment,
            "relevance": max(0.3, relevance)
        }
    
    async def _generate_news_summary(self, news_items: List[NewsItem], symbols: List[str]) -> str:
        """
        Generate summary for portfolio news
        """
        if not news_items:
            return "No recent news for your portfolio holdings."
        
        context = f"""
Portfolio symbols: {symbols}

Recent headlines:
"""
        for item in news_items[:10]:
            context += f"- [{item.sentiment.upper()}] {item.title} ({item.source})\n"
        
        prompt = """Based on these news items, provide a brief portfolio news summary:
1. Key developments affecting the portfolio
2. Stocks with notable news
3. Overall sentiment assessment
4. Recommended actions based on news"""
        
        return await self.think(prompt, context)
    
    def _calculate_overall_sentiment(self, sentiments: List[str]) -> str:
        """
        Calculate overall sentiment from list of sentiments
        """
        if not sentiments:
            return "neutral"
        
        positive = sentiments.count("positive")
        negative = sentiments.count("negative")
        total = len(sentiments)
        
        if positive > total * 0.6:
            return "bullish"
        elif negative > total * 0.6:
            return "bearish"
        elif positive > negative:
            return "slightly_bullish"
        elif negative > positive:
            return "slightly_bearish"
        else:
            return "neutral"
