"""
Portfolio Service - Portfolio management and calculations
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
import os
import json
import pandas as pd
from config import settings


class PortfolioService:
    """
    Service for portfolio management and calculations
    """
    
    def __init__(self):
        self.portfolios_path = settings.portfolios_path
        os.makedirs(self.portfolios_path, exist_ok=True)
    
    async def save_portfolio(self, portfolio_id: str, data: Dict) -> bool:
        """
        Save portfolio to file system
        """
        try:
            portfolio_dir = os.path.join(self.portfolios_path, portfolio_id)
            os.makedirs(portfolio_dir, exist_ok=True)
            
            # Save portfolio data
            data_file = os.path.join(portfolio_dir, "portfolio.json")
            with open(data_file, 'w') as f:
                json.dump(data, f, default=str, indent=2)
            
            # Save holdings as CSV
            holdings = data.get("holdings", [])
            if holdings:
                df = pd.DataFrame(holdings)
                csv_file = os.path.join(portfolio_dir, "holdings.csv")
                df.to_csv(csv_file, index=False)
            
            return True
        except Exception as e:
            print(f"Error saving portfolio {portfolio_id}: {e}")
            return False
    
    async def load_portfolio(self, portfolio_id: str) -> Optional[Dict]:
        """
        Load portfolio from file system
        """
        try:
            data_file = os.path.join(self.portfolios_path, portfolio_id, "portfolio.json")
            
            if not os.path.exists(data_file):
                return None
            
            with open(data_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading portfolio {portfolio_id}: {e}")
            return None
    
    async def calculate_performance(
        self, 
        holdings: List[Dict],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Calculate portfolio performance metrics
        """
        if not holdings:
            return {}
        
        total_invested = sum(
            h.get("quantity", 0) * h.get("average_cost", 0) 
            for h in holdings
        )
        
        total_value = sum(
            h.get("current_value", 0) 
            for h in holdings
        )
        
        total_gain_loss = total_value - total_invested
        total_return_pct = (total_gain_loss / total_invested * 100) if total_invested > 0 else 0
        
        # Calculate by holding
        performance_by_holding = []
        for h in holdings:
            invested = h.get("quantity", 0) * h.get("average_cost", 0)
            current = h.get("current_value", 0)
            gain_loss = current - invested
            return_pct = (gain_loss / invested * 100) if invested > 0 else 0
            
            performance_by_holding.append({
                "symbol": h.get("symbol"),
                "invested": invested,
                "current_value": current,
                "gain_loss": gain_loss,
                "return_percent": return_pct,
                "weight": (current / total_value * 100) if total_value > 0 else 0
            })
        
        # Sort by performance
        performance_by_holding.sort(key=lambda x: x["return_percent"], reverse=True)
        
        return {
            "total_invested": total_invested,
            "total_value": total_value,
            "total_gain_loss": total_gain_loss,
            "total_return_percent": total_return_pct,
            "best_performers": performance_by_holding[:3],
            "worst_performers": performance_by_holding[-3:],
            "all_holdings": performance_by_holding
        }
    
    async def calculate_allocation(self, holdings: List[Dict]) -> Dict[str, float]:
        """
        Calculate portfolio allocation by asset type
        """
        total_value = sum(h.get("current_value", 0) for h in holdings)
        
        if total_value == 0:
            return {}
        
        allocation = {}
        for h in holdings:
            asset_type = h.get("asset_type", "stock")
            value = h.get("current_value", 0)
            weight = value / total_value * 100
            
            allocation[asset_type] = allocation.get(asset_type, 0) + weight
        
        return {k: round(v, 2) for k, v in allocation.items()}
    
    async def calculate_sector_allocation(
        self, 
        holdings: List[Dict],
        sector_map: Dict[str, str]
    ) -> Dict[str, float]:
        """
        Calculate portfolio allocation by sector
        """
        total_value = sum(h.get("current_value", 0) for h in holdings)
        
        if total_value == 0:
            return {}
        
        allocation = {}
        for h in holdings:
            symbol = h.get("symbol", "")
            sector = sector_map.get(symbol, "Unknown")
            value = h.get("current_value", 0)
            weight = value / total_value * 100
            
            allocation[sector] = allocation.get(sector, 0) + weight
        
        return {k: round(v, 2) for k, v in allocation.items()}
    
    async def suggest_rebalancing(
        self,
        holdings: List[Dict],
        target_allocation: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Suggest trades to achieve target allocation
        """
        current_allocation = await self.calculate_allocation(holdings)
        total_value = sum(h.get("current_value", 0) for h in holdings)
        
        trades = []
        
        for asset_type, target_weight in target_allocation.items():
            current_weight = current_allocation.get(asset_type, 0)
            diff = target_weight - current_weight
            
            if abs(diff) > 2:  # Only if drift > 2%
                action = "BUY" if diff > 0 else "SELL"
                amount = abs(diff) * total_value / 100
                
                trades.append({
                    "asset_type": asset_type,
                    "action": action,
                    "current_weight": current_weight,
                    "target_weight": target_weight,
                    "diff": diff,
                    "estimated_amount": round(amount, 2)
                })
        
        return trades
    
    async def import_from_csv(self, file_path: str) -> List[Dict]:
        """
        Import holdings from CSV file
        """
        try:
            df = pd.read_csv(file_path)
            
            required_cols = ["symbol", "quantity", "average_cost"]
            if not all(col in df.columns for col in required_cols):
                raise ValueError(f"CSV must contain columns: {required_cols}")
            
            holdings = df.to_dict('records')
            return holdings
        except Exception as e:
            print(f"Error importing CSV: {e}")
            raise
    
    async def export_to_csv(
        self, 
        holdings: List[Dict], 
        file_path: str
    ) -> bool:
        """
        Export holdings to CSV file
        """
        try:
            df = pd.DataFrame(holdings)
            df.to_csv(file_path, index=False)
            return True
        except Exception as e:
            print(f"Error exporting CSV: {e}")
            return False
    
    async def calculate_risk_metrics(self, holdings: List[Dict]) -> Dict[str, Any]:
        """
        Calculate basic risk metrics
        """
        total_value = sum(h.get("current_value", 0) for h in holdings)
        
        if not holdings or total_value == 0:
            return {}
        
        # Concentration (Herfindahl-Hirschman Index)
        weights = [(h.get("current_value", 0) / total_value) for h in holdings]
        hhi = sum(w ** 2 for w in weights) * 10000
        
        # Top holding weight
        max_weight = max(weights) * 100 if weights else 0
        
        return {
            "hhi_index": round(hhi, 2),
            "num_holdings": len(holdings),
            "max_holding_weight": round(max_weight, 2),
            "is_diversified": hhi < 2500,
            "concentration_risk": "high" if max_weight > 25 else "moderate" if max_weight > 15 else "low"
        }
