"""
Stock models for market data and analysis
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class StockPrice(BaseModel):
    """Real-time stock price"""
    symbol: str
    price: float
    change: float
    change_percent: float
    volume: int
    timestamp: datetime
    high: Optional[float] = None
    low: Optional[float] = None
    open: Optional[float] = None
    previous_close: Optional[float] = None


class StockFundamentals(BaseModel):
    """Company fundamental data"""
    symbol: str
    name: str
    sector: str
    industry: str
    market_cap: float
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    eps: Optional[float] = None
    revenue: Optional[float] = None
    profit_margin: Optional[float] = None
    debt_to_equity: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None


class Stock(BaseModel):
    """Complete stock information"""
    symbol: str
    name: str
    exchange: str
    currency: str
    price: StockPrice
    fundamentals: Optional[StockFundamentals] = None


class StockAnalysis(BaseModel):
    """AI-generated stock analysis"""
    symbol: str
    analysis_date: datetime
    recommendation: str  # strong_buy, buy, hold, sell, strong_sell
    target_price: Optional[float] = None
    confidence_score: float
    summary: str
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    threats: List[str]
    peer_comparison: Optional[dict] = None
    technical_indicators: Optional[dict] = None
    sentiment_score: Optional[float] = None


class PeerComparison(BaseModel):
    """Peer company comparison"""
    symbol: str
    peers: List[str]
    metrics_comparison: dict  # metric -> {symbol: value}
    ranking: dict  # metric -> rank
    analysis: str


class NewsItem(BaseModel):
    """News article related to stock"""
    title: str
    source: str
    url: str
    published_at: datetime
    summary: Optional[str] = None
    sentiment: Optional[str] = None  # positive, negative, neutral
    relevance_score: Optional[float] = None
    related_symbols: List[str] = []


class MarketTrend(BaseModel):
    """Market trend analysis"""
    symbol: str
    timeframe: str  # 1d, 1w, 1m, 3m, 1y
    trend: str  # bullish, bearish, sideways
    support_levels: List[float]
    resistance_levels: List[float]
    moving_averages: dict
    rsi: Optional[float] = None
    macd: Optional[dict] = None
    volume_trend: str
    analysis: str
