"""
Portfolio management routes
"""
from datetime import datetime
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
import pandas as pd
import io

from models.user import User
from models.portfolio import (
    Portfolio, PortfolioCreate, PortfolioResponse, 
    PortfolioSummary, PortfolioHolding, Transaction, TransactionType, AssetType
)
from routes.auth import get_current_user
from services.market_data import MarketDataService
from agents.orchestrator import AgentOrchestrator

router = APIRouter()

# In-memory portfolio storage (replace with database in production)
portfolios_db: dict[str, dict] = {}
market_service = MarketDataService()


@router.post("/create", response_model=PortfolioResponse)
async def create_portfolio(
    portfolio: PortfolioCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new portfolio thread"""
    portfolio_id = str(uuid.uuid4())
    
    # Process initial holdings
    holdings = []
    total_invested = 0.0
    
    for holding_data in portfolio.initial_holdings or []:
        symbol = holding_data.get("symbol", "").upper()
        quantity = holding_data.get("quantity", 0)
        avg_cost = holding_data.get("average_cost", 0)
        
        # Get current price
        price_data = await market_service.get_stock_price(symbol)
        current_price = price_data.get("price", avg_cost) if price_data else avg_cost
        current_value = quantity * current_price
        invested = quantity * avg_cost
        gain_loss = current_value - invested
        gain_loss_percent = (gain_loss / invested * 100) if invested > 0 else 0
        
        holding = PortfolioHolding(
            symbol=symbol,
            name=holding_data.get("name", symbol),
            asset_type=AssetType(holding_data.get("asset_type", "stock")),
            quantity=quantity,
            average_cost=avg_cost,
            current_price=current_price,
            current_value=current_value,
            gain_loss=gain_loss,
            gain_loss_percent=gain_loss_percent
        )
        holdings.append(holding)
        total_invested += invested
    
    # Calculate portfolio totals
    total_value = sum(h.current_value or 0 for h in holdings)
    total_gain_loss = total_value - total_invested
    total_gain_loss_percent = (total_gain_loss / total_invested * 100) if total_invested > 0 else 0
    
    # Calculate allocation
    allocation = {}
    for holding in holdings:
        asset_type = holding.asset_type.value
        weight = (holding.current_value / total_value * 100) if total_value > 0 else 0
        holding.weight = weight
        allocation[asset_type] = allocation.get(asset_type, 0) + weight
    
    portfolio_data = {
        "id": portfolio_id,
        "user_id": current_user.id,
        "name": portfolio.name,
        "description": portfolio.description,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "holdings": [h.model_dump() for h in holdings],
        "total_value": total_value,
        "total_invested": total_invested,
        "total_gain_loss": total_gain_loss,
        "total_gain_loss_percent": total_gain_loss_percent,
        "allocation": allocation
    }
    
    portfolios_db[portfolio_id] = portfolio_data
    
    return PortfolioResponse(
        id=portfolio_id,
        name=portfolio.name,
        description=portfolio.description,
        holdings=holdings,
        total_value=total_value,
        total_invested=total_invested,
        total_gain_loss=total_gain_loss,
        total_gain_loss_percent=total_gain_loss_percent,
        allocation=allocation
    )


@router.get("/list", response_model=List[PortfolioSummary])
async def list_portfolios(current_user: User = Depends(get_current_user)):
    """List all portfolios for current user"""
    user_portfolios = []
    
    for portfolio in portfolios_db.values():
        if portfolio["user_id"] == current_user.id:
            # Calculate daily change (simplified)
            total_value = portfolio["total_value"]
            daily_change = total_value * 0.01  # Placeholder
            
            summary = PortfolioSummary(
                id=portfolio["id"],
                name=portfolio["name"],
                total_value=total_value,
                daily_change=daily_change,
                daily_change_percent=1.0,  # Placeholder
                holdings_count=len(portfolio["holdings"])
            )
            user_portfolios.append(summary)
    
    return user_portfolios


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get portfolio details with live prices"""
    portfolio = portfolios_db.get(portfolio_id)
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    if portfolio["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this portfolio"
        )
    
    # Update with live prices
    holdings = []
    total_value = 0.0
    
    for h in portfolio["holdings"]:
        # Get live price
        price_data = await market_service.get_stock_price(h["symbol"])
        current_price = price_data.get("price", h["current_price"]) if price_data else h["current_price"]
        current_value = h["quantity"] * current_price
        invested = h["quantity"] * h["average_cost"]
        gain_loss = current_value - invested
        gain_loss_percent = (gain_loss / invested * 100) if invested > 0 else 0
        
        holding = PortfolioHolding(
            symbol=h["symbol"],
            name=h["name"],
            asset_type=AssetType(h["asset_type"]),
            quantity=h["quantity"],
            average_cost=h["average_cost"],
            current_price=current_price,
            current_value=current_value,
            gain_loss=gain_loss,
            gain_loss_percent=gain_loss_percent
        )
        holdings.append(holding)
        total_value += current_value
    
    # Recalculate weights
    for holding in holdings:
        holding.weight = (holding.current_value / total_value * 100) if total_value > 0 else 0
    
    total_invested = portfolio["total_invested"]
    total_gain_loss = total_value - total_invested
    total_gain_loss_percent = (total_gain_loss / total_invested * 100) if total_invested > 0 else 0
    
    return PortfolioResponse(
        id=portfolio["id"],
        name=portfolio["name"],
        description=portfolio["description"],
        holdings=holdings,
        total_value=total_value,
        total_invested=total_invested,
        total_gain_loss=total_gain_loss,
        total_gain_loss_percent=total_gain_loss_percent,
        allocation=portfolio["allocation"]
    )


@router.post("/{portfolio_id}/transaction")
async def add_transaction(
    portfolio_id: str,
    symbol: str,
    transaction_type: TransactionType,
    quantity: float,
    price: float,
    current_user: User = Depends(get_current_user)
):
    """Add a buy/sell transaction to portfolio"""
    portfolio = portfolios_db.get(portfolio_id)
    
    if not portfolio or portfolio["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    symbol = symbol.upper()
    total_amount = quantity * price
    
    # Find existing holding
    holding_idx = None
    for idx, h in enumerate(portfolio["holdings"]):
        if h["symbol"] == symbol:
            holding_idx = idx
            break
    
    if transaction_type == TransactionType.BUY:
        if holding_idx is not None:
            # Update existing holding
            old_qty = portfolio["holdings"][holding_idx]["quantity"]
            old_avg = portfolio["holdings"][holding_idx]["average_cost"]
            new_qty = old_qty + quantity
            new_avg = ((old_qty * old_avg) + (quantity * price)) / new_qty
            
            portfolio["holdings"][holding_idx]["quantity"] = new_qty
            portfolio["holdings"][holding_idx]["average_cost"] = new_avg
        else:
            # Add new holding
            new_holding = {
                "symbol": symbol,
                "name": symbol,
                "asset_type": "stock",
                "quantity": quantity,
                "average_cost": price,
                "current_price": price,
                "current_value": total_amount,
                "gain_loss": 0,
                "gain_loss_percent": 0
            }
            portfolio["holdings"].append(new_holding)
        
        portfolio["total_invested"] += total_amount
    
    elif transaction_type == TransactionType.SELL:
        if holding_idx is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No holding found for {symbol}"
            )
        
        if portfolio["holdings"][holding_idx]["quantity"] < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient quantity to sell"
            )
        
        portfolio["holdings"][holding_idx]["quantity"] -= quantity
        
        # Remove holding if quantity is 0
        if portfolio["holdings"][holding_idx]["quantity"] == 0:
            portfolio["holdings"].pop(holding_idx)
    
    portfolio["updated_at"] = datetime.utcnow()
    
    return {
        "message": f"Transaction completed: {transaction_type.value} {quantity} {symbol} @ ${price}",
        "portfolio_id": portfolio_id
    }


@router.post("/{portfolio_id}/upload-csv")
async def upload_portfolio_csv(
    portfolio_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload portfolio holdings from CSV"""
    portfolio = portfolios_db.get(portfolio_id)
    
    if not portfolio or portfolio["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    # Read CSV
    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents))
    
    # Expected columns: symbol, quantity, average_cost, name (optional), asset_type (optional)
    required_cols = ["symbol", "quantity", "average_cost"]
    if not all(col in df.columns for col in required_cols):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV must contain columns: {required_cols}"
        )
    
    # Process holdings
    new_holdings = []
    total_invested = 0.0
    
    for _, row in df.iterrows():
        symbol = str(row["symbol"]).upper()
        quantity = float(row["quantity"])
        avg_cost = float(row["average_cost"])
        name = row.get("name", symbol)
        asset_type = row.get("asset_type", "stock")
        
        # Get current price
        price_data = await market_service.get_stock_price(symbol)
        current_price = price_data.get("price", avg_cost) if price_data else avg_cost
        current_value = quantity * current_price
        invested = quantity * avg_cost
        gain_loss = current_value - invested
        gain_loss_percent = (gain_loss / invested * 100) if invested > 0 else 0
        
        holding = {
            "symbol": symbol,
            "name": name,
            "asset_type": asset_type,
            "quantity": quantity,
            "average_cost": avg_cost,
            "current_price": current_price,
            "current_value": current_value,
            "gain_loss": gain_loss,
            "gain_loss_percent": gain_loss_percent
        }
        new_holdings.append(holding)
        total_invested += invested
    
    # Update portfolio
    portfolio["holdings"] = new_holdings
    portfolio["total_invested"] = total_invested
    portfolio["total_value"] = sum(h["current_value"] for h in new_holdings)
    portfolio["updated_at"] = datetime.utcnow()
    
    return {
        "message": f"Portfolio updated with {len(new_holdings)} holdings",
        "total_invested": total_invested,
        "total_value": portfolio["total_value"]
    }


@router.get("/{portfolio_id}/export-csv")
async def export_portfolio_csv(
    portfolio_id: str,
    current_user: User = Depends(get_current_user)
):
    """Export portfolio holdings to CSV"""
    portfolio = portfolios_db.get(portfolio_id)
    
    if not portfolio or portfolio["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    # Create DataFrame
    df = pd.DataFrame(portfolio["holdings"])
    
    # Convert to CSV
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    
    return StreamingResponse(
        io.BytesIO(csv_buffer.getvalue().encode()),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={portfolio['name']}_holdings.csv"
        }
    )


@router.delete("/{portfolio_id}")
async def delete_portfolio(
    portfolio_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a portfolio"""
    portfolio = portfolios_db.get(portfolio_id)
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    if portfolio["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this portfolio"
        )
    
    del portfolios_db[portfolio_id]
    
    return {"message": "Portfolio deleted successfully"}
