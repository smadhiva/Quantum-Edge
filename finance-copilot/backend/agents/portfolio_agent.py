"""
Portfolio Monitor Agent - Portfolio health and monitoring
"""
from typing import Dict, Any, List
from datetime import datetime

from .base_agent import BaseAgent
from services.market_data import MarketDataService


class PortfolioMonitorAgent(BaseAgent):
    """
    Specialized agent for portfolio monitoring and health assessment
    
    Capabilities:
    - Portfolio health monitoring
    - Performance tracking
    - Rebalancing recommendations
    - Alert generation
    """
    
    def __init__(self):
        super().__init__(
            name="Portfolio Monitor Agent",
            description="""Expert portfolio manager specializing in:
            - Portfolio health monitoring
            - Performance attribution analysis
            - Rebalancing recommendations
            - Drift monitoring
            - Cost and tax efficiency"""
        )
        self.market_service = MarketDataService()
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute portfolio monitoring task"""
        task_type = task.get("type", "analyze_health")
        portfolio = task.get("portfolio", {})
        
        if task_type == "analyze_health":
            return await self.analyze_health(portfolio)
        elif task_type == "check_drift":
            target_allocation = task.get("target_allocation", {})
            return await self.check_drift(portfolio, target_allocation)
        elif task_type == "rebalance":
            return await self.suggest_rebalancing(portfolio)
        else:
            return {"error": f"Unknown task type: {task_type}"}
    
    async def analyze_health(self, portfolio: Dict) -> Dict[str, Any]:
        """
        Analyze overall portfolio health
        """
        holdings = portfolio.get("holdings", [])
        total_value = portfolio.get("total_value", 0)
        total_invested = portfolio.get("total_invested", 0)
        
        if not holdings:
            return {
                "health_score": 0,
                "status": "empty",
                "message": "Portfolio has no holdings"
            }
        
        # Calculate metrics
        metrics = {
            "total_return": self._calculate_return(total_value, total_invested),
            "winning_positions": 0,
            "losing_positions": 0,
            "best_performer": None,
            "worst_performer": None
        }
        
        # Analyze each holding
        for holding in holdings:
            gain_loss = holding.get("gain_loss", 0)
            if gain_loss >= 0:
                metrics["winning_positions"] += 1
            else:
                metrics["losing_positions"] += 1
            
            # Track best/worst
            if metrics["best_performer"] is None or \
               holding.get("gain_loss_percent", 0) > metrics["best_performer"].get("gain_loss_percent", 0):
                metrics["best_performer"] = holding
            
            if metrics["worst_performer"] is None or \
               holding.get("gain_loss_percent", 0) < metrics["worst_performer"].get("gain_loss_percent", 0):
                metrics["worst_performer"] = holding
        
        # Calculate health score
        health_score = await self._calculate_health_score(portfolio, metrics)
        
        # Generate analysis
        context = f"""
Portfolio Value: ${total_value:,.2f}
Total Return: {metrics['total_return']:.2f}%
Winning Positions: {metrics['winning_positions']}
Losing Positions: {metrics['losing_positions']}
Best Performer: {metrics['best_performer'].get('symbol') if metrics['best_performer'] else 'N/A'}
Worst Performer: {metrics['worst_performer'].get('symbol') if metrics['worst_performer'] else 'N/A'}
"""
        
        prompt = """Based on this portfolio data, provide:
1. Overall health assessment
2. Key strengths
3. Areas for improvement
4. Immediate action items"""
        
        analysis = await self.think(prompt, context)
        
        return {
            "portfolio_id": portfolio.get("id"),
            "health_score": health_score,
            "status": self._get_health_status(health_score),
            "metrics": metrics,
            "analysis": analysis,
            "alerts": self._generate_alerts(holdings, metrics),
            "analyzed_at": datetime.now().isoformat()
        }
    
    async def check_drift(
        self, 
        portfolio: Dict, 
        target_allocation: Dict
    ) -> Dict[str, Any]:
        """
        Check portfolio drift from target allocation
        """
        holdings = portfolio.get("holdings", [])
        total_value = portfolio.get("total_value", 0)
        
        if not holdings or total_value == 0:
            return {"drift": 0, "needs_rebalancing": False}
        
        # Calculate current allocation by asset type
        current_allocation = {}
        for holding in holdings:
            asset_type = holding.get("asset_type", "stock")
            weight = (holding.get("current_value", 0) / total_value * 100)
            current_allocation[asset_type] = current_allocation.get(asset_type, 0) + weight
        
        # Calculate drift
        drift_by_type = {}
        total_drift = 0
        
        for asset_type, target_weight in target_allocation.items():
            current_weight = current_allocation.get(asset_type, 0)
            drift = current_weight - target_weight
            drift_by_type[asset_type] = round(drift, 2)
            total_drift += abs(drift)
        
        # Determine if rebalancing needed (>5% total drift)
        needs_rebalancing = total_drift > 5
        
        return {
            "target_allocation": target_allocation,
            "current_allocation": current_allocation,
            "drift_by_type": drift_by_type,
            "total_drift": round(total_drift, 2),
            "needs_rebalancing": needs_rebalancing,
            "recommendation": self._get_drift_recommendation(drift_by_type)
        }
    
    async def suggest_rebalancing(self, portfolio: Dict) -> Dict[str, Any]:
        """
        Suggest rebalancing trades
        """
        holdings = portfolio.get("holdings", [])
        total_value = portfolio.get("total_value", 0)
        
        if not holdings:
            return {"trades": [], "message": "No holdings to rebalance"}
        
        # Default target: equal weight
        num_holdings = len(holdings)
        target_weight = 100 / num_holdings
        
        trades = []
        for holding in holdings:
            current_weight = (holding.get("current_value", 0) / total_value * 100) if total_value else 0
            drift = current_weight - target_weight
            
            if abs(drift) > 2:  # Only rebalance if drift > 2%
                action = "SELL" if drift > 0 else "BUY"
                amount = abs(drift) * total_value / 100
                
                trades.append({
                    "symbol": holding.get("symbol"),
                    "action": action,
                    "current_weight": round(current_weight, 2),
                    "target_weight": round(target_weight, 2),
                    "drift": round(drift, 2),
                    "estimated_amount": round(amount, 2)
                })
        
        # Sort by absolute drift
        trades.sort(key=lambda x: abs(x["drift"]), reverse=True)
        
        return {
            "strategy": "equal_weight",
            "trades": trades,
            "total_trades": len(trades),
            "estimated_turnover": sum(t["estimated_amount"] for t in trades),
            "note": "Review trades before executing. Consider tax implications."
        }
    
    async def _calculate_health_score(self, portfolio: Dict, metrics: Dict) -> float:
        """
        Calculate portfolio health score (0-100)
        """
        score = 50  # Base score
        
        # Return contribution
        total_return = metrics.get("total_return", 0)
        if total_return > 20:
            score += 20
        elif total_return > 10:
            score += 15
        elif total_return > 0:
            score += 10
        elif total_return > -10:
            score += 0
        else:
            score -= 10
        
        # Win/loss ratio
        winners = metrics.get("winning_positions", 0)
        losers = metrics.get("losing_positions", 0)
        total = winners + losers
        
        if total > 0:
            win_rate = winners / total
            if win_rate > 0.7:
                score += 15
            elif win_rate > 0.5:
                score += 10
            elif win_rate > 0.3:
                score += 5
            else:
                score -= 5
        
        # Diversification bonus
        holdings = portfolio.get("holdings", [])
        if len(holdings) >= 10:
            score += 10
        elif len(holdings) >= 5:
            score += 5
        
        return max(0, min(100, score))
    
    def _get_health_status(self, score: float) -> str:
        """Get health status from score"""
        if score >= 80:
            return "excellent"
        elif score >= 60:
            return "good"
        elif score >= 40:
            return "fair"
        elif score >= 20:
            return "poor"
        else:
            return "critical"
    
    def _generate_alerts(self, holdings: List[Dict], metrics: Dict) -> List[Dict]:
        """
        Generate portfolio alerts
        """
        alerts = []
        
        # Large loss alert
        for holding in holdings:
            loss_percent = holding.get("gain_loss_percent", 0)
            if loss_percent < -20:
                alerts.append({
                    "type": "loss_alert",
                    "severity": "high",
                    "symbol": holding.get("symbol"),
                    "message": f"{holding.get('symbol')} is down {abs(loss_percent):.1f}%. Consider reviewing position."
                })
            elif loss_percent < -10:
                alerts.append({
                    "type": "loss_alert",
                    "severity": "medium",
                    "symbol": holding.get("symbol"),
                    "message": f"{holding.get('symbol')} is down {abs(loss_percent):.1f}%."
                })
        
        # Concentration alert
        for holding in holdings:
            weight = holding.get("weight", 0)
            if weight > 25:
                alerts.append({
                    "type": "concentration_alert",
                    "severity": "medium",
                    "symbol": holding.get("symbol"),
                    "message": f"{holding.get('symbol')} represents {weight:.1f}% of portfolio. Consider reducing."
                })
        
        # Overall performance
        total_return = metrics.get("total_return", 0)
        if total_return < -15:
            alerts.append({
                "type": "performance_alert",
                "severity": "high",
                "message": f"Portfolio is down {abs(total_return):.1f}%. Review overall strategy."
            })
        
        return alerts
    
    def _calculate_return(self, current_value: float, invested: float) -> float:
        """Calculate percentage return"""
        if invested == 0:
            return 0
        return ((current_value - invested) / invested) * 100
    
    def _get_drift_recommendation(self, drift_by_type: Dict) -> str:
        """Get recommendation based on drift"""
        max_drift_type = max(drift_by_type.items(), key=lambda x: abs(x[1]), default=(None, 0))
        
        if max_drift_type[0] is None:
            return "Portfolio is well balanced"
        
        if max_drift_type[1] > 0:
            return f"Consider reducing {max_drift_type[0]} allocation by {abs(max_drift_type[1]):.1f}%"
        else:
            return f"Consider increasing {max_drift_type[0]} allocation by {abs(max_drift_type[1]):.1f}%"
