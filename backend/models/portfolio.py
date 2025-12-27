"""
Portfolio models for managing investment portfolios
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class AssetType(str, Enum):
    """Types of assets"""
    STOCK = "stock"
    MUTUAL_FUND = "mutual_fund"
    ETF = "etf"
    BOND = "bond"
    CRYPTO = "crypto"
    CASH = "cash"


class TransactionType(str, Enum):
    """Types of transactions"""
    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"


class PortfolioHolding(BaseModel):
    """Individual holding in a portfolio"""
    symbol: str
    name: str
    asset_type: AssetType
    quantity: float
    average_cost: float
    current_price: Optional[float] = None
    current_value: Optional[float] = None
    gain_loss: Optional[float] = None
    gain_loss_percent: Optional[float] = None
    weight: Optional[float] = None  # percentage of portfolio


class Transaction(BaseModel):
    """Portfolio transaction"""
    id: str
    portfolio_id: str
    symbol: str
    transaction_type: TransactionType
    quantity: float
    price: float
    total_amount: float
    timestamp: datetime
    notes: Optional[str] = None


class PortfolioBase(BaseModel):
    """Base portfolio model"""
    name: str
    description: Optional[str] = None


class PortfolioCreate(PortfolioBase):
    """Portfolio creation model"""
    initial_holdings: Optional[List[dict]] = []


class Portfolio(PortfolioBase):
    """Full portfolio model"""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    holdings: List[PortfolioHolding] = []
    total_value: float = 0.0
    total_invested: float = 0.0
    total_gain_loss: float = 0.0
    total_gain_loss_percent: float = 0.0
    
    class Config:
        from_attributes = True


class PortfolioResponse(BaseModel):
    """Portfolio response with analysis"""
    id: str
    name: str
    description: Optional[str]
    holdings: List[PortfolioHolding]
    total_value: float
    total_invested: float
    total_gain_loss: float
    total_gain_loss_percent: float
    allocation: dict  # asset type -> percentage
    risk_score: Optional[float] = None
    recommendations: Optional[List[str]] = None


class PortfolioSummary(BaseModel):
    """Portfolio summary for listing"""
    id: str
    name: str
    total_value: float
    daily_change: float
    daily_change_percent: float
    holdings_count: int


class PortfolioAnalysis(BaseModel):
    """Detailed portfolio analysis"""
    portfolio_id: str
    analysis_date: datetime
    risk_metrics: dict
    performance_metrics: dict
    sector_allocation: dict
    geographic_allocation: dict
    recommendations: List[str]
    insights: List[str]
