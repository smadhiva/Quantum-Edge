"""
Risk Profiling Agent - Risk assessment and management
"""
from typing import Dict, Any, List
from datetime import datetime

from .base_agent import BaseAgent
from services.market_data import MarketDataService


class RiskProfilingAgent(BaseAgent):
    """
    Specialized agent for risk profiling and assessment
    
    Capabilities:
    - Portfolio risk assessment
    - User risk profiling
    - Risk metrics calculation
    - Diversification analysis
    """
    
    def __init__(self):
        super().__init__(
            name="Risk Profiling Agent",
            description="""Expert risk analyst specializing in:
            - Portfolio risk assessment (volatility, beta, VaR)
            - User risk tolerance profiling
            - Diversification analysis
            - Concentration risk identification
            - Stress testing and scenario analysis"""
        )
        self.market_service = MarketDataService()
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute risk assessment task"""
        task_type = task.get("type", "assess_portfolio")
        
        if task_type == "assess_portfolio":
            portfolio = task.get("portfolio", {})
            return await self.assess_portfolio_risk(portfolio)
        elif task_type == "profile_user":
            answers = task.get("answers", {})
            return await self.profile_user_risk(answers)
        else:
            return {"error": f"Unknown task type: {task_type}"}
    
    async def assess_portfolio_risk(self, portfolio: Dict) -> Dict[str, Any]:
        """
        Comprehensive portfolio risk assessment
        """
        holdings = portfolio.get("holdings", [])
        total_value = portfolio.get("total_value", 0)
        
        if not holdings or total_value == 0:
            return {
                "risk_score": 0,
                "assessment": "No holdings to assess",
                "recommendations": ["Add holdings to your portfolio"]
            }
        
        # Calculate risk metrics
        risk_metrics = await self._calculate_risk_metrics(holdings, total_value)
        
        # Check diversification
        diversification = self._assess_diversification(holdings, total_value)
        
        # Concentration risk
        concentration = self._assess_concentration(holdings, total_value)
        
        # Calculate overall risk score (1-10)
        risk_score = self._calculate_risk_score(risk_metrics, diversification, concentration)
        
        # Build context for LLM analysis
        context = f"""
Portfolio Value: ${total_value:,.2f}
Number of Holdings: {len(holdings)}

Risk Metrics:
{risk_metrics}

Diversification:
{diversification}

Concentration Risk:
{concentration}

Overall Risk Score: {risk_score}/10
"""
        
        prompt = """Based on this risk analysis, provide:
1. Risk level assessment (conservative/moderate/aggressive)
2. Key risk factors
3. Areas of concern
4. Risk reduction recommendations
5. Suggested rebalancing actions"""
        
        analysis = await self.think(prompt, context)
        
        return {
            "portfolio_id": portfolio.get("id"),
            "risk_score": risk_score,
            "risk_level": self._get_risk_level(risk_score),
            "metrics": risk_metrics,
            "diversification": diversification,
            "concentration": concentration,
            "analysis": analysis,
            "recommendations": self._generate_risk_recommendations(
                risk_metrics, diversification, concentration
            ),
            "assessed_at": datetime.now().isoformat()
        }
    
    async def profile_user_risk(self, answers: Dict) -> Dict[str, Any]:
        """
        Profile user risk tolerance based on questionnaire
        """
        # Risk profiling questions and scoring
        score = 0
        
        # Investment horizon
        horizon = answers.get("investment_horizon", "medium")
        if horizon == "long":
            score += 3
        elif horizon == "medium":
            score += 2
        else:
            score += 1
        
        # Risk tolerance
        tolerance = answers.get("risk_tolerance", "moderate")
        if tolerance == "aggressive":
            score += 3
        elif tolerance == "moderate":
            score += 2
        else:
            score += 1
        
        # Reaction to loss
        loss_reaction = answers.get("loss_reaction", "hold")
        if loss_reaction == "buy_more":
            score += 3
        elif loss_reaction == "hold":
            score += 2
        else:
            score += 1
        
        # Income stability
        income = answers.get("income_stability", "stable")
        if income == "very_stable":
            score += 2
        elif income == "stable":
            score += 1
        
        # Calculate risk profile
        max_score = 11
        risk_percentage = (score / max_score) * 100
        
        if risk_percentage >= 70:
            profile = "aggressive"
            description = "You have a high risk tolerance and can handle market volatility"
            allocation = {"stocks": 80, "bonds": 15, "cash": 5}
        elif risk_percentage >= 40:
            profile = "moderate"
            description = "You seek a balance between growth and stability"
            allocation = {"stocks": 60, "bonds": 30, "cash": 10}
        else:
            profile = "conservative"
            description = "You prefer capital preservation over high returns"
            allocation = {"stocks": 30, "bonds": 50, "cash": 20}
        
        return {
            "risk_profile": profile,
            "risk_score": round(risk_percentage, 1),
            "description": description,
            "recommended_allocation": allocation,
            "investment_horizon": horizon,
            "suggestions": self._get_profile_suggestions(profile)
        }
    
    async def _calculate_risk_metrics(self, holdings: List[Dict], total_value: float) -> Dict[str, Any]:
        """
        Calculate portfolio risk metrics
        """
        metrics = {
            "estimated_volatility": 0,
            "estimated_beta": 0,
            "var_95": 0,  # Value at Risk
            "max_drawdown": 0
        }
        
        # Fetch data for each holding
        weighted_beta = 0
        weighted_volatility = 0
        
        for holding in holdings:
            symbol = holding.get("symbol", "")
            weight = holding.get("current_value", 0) / total_value if total_value > 0 else 0
            
            # Get stock data
            try:
                historical = await self.market_service.get_historical_data(symbol, "3m")
                if historical:
                    prices = [h.get("close", 0) for h in historical]
                    if len(prices) > 1:
                        # Calculate returns
                        returns = [(prices[i] - prices[i-1]) / prices[i-1] 
                                   for i in range(1, len(prices)) if prices[i-1] > 0]
                        
                        # Volatility (standard deviation of returns)
                        if returns:
                            mean_return = sum(returns) / len(returns)
                            variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
                            volatility = variance ** 0.5 * (252 ** 0.5)  # Annualized
                            weighted_volatility += weight * volatility
            except:
                pass
        
        metrics["estimated_volatility"] = round(weighted_volatility * 100, 2)  # As percentage
        metrics["estimated_beta"] = round(weighted_volatility / 0.15, 2)  # Rough beta estimate
        metrics["var_95"] = round(total_value * weighted_volatility * 1.65, 2)  # 95% VaR
        
        return metrics
    
    def _assess_diversification(self, holdings: List[Dict], total_value: float) -> Dict[str, Any]:
        """
        Assess portfolio diversification
        """
        # Count unique holdings
        num_holdings = len(holdings)
        
        # Calculate Herfindahl-Hirschman Index (HHI)
        weights = []
        for h in holdings:
            weight = (h.get("current_value", 0) / total_value * 100) if total_value > 0 else 0
            weights.append(weight)
        
        hhi = sum(w ** 2 for w in weights)
        
        # Diversification score
        if hhi < 1000:
            diversification_level = "well_diversified"
            score = 9
        elif hhi < 2500:
            diversification_level = "moderately_diversified"
            score = 6
        else:
            diversification_level = "concentrated"
            score = 3
        
        return {
            "num_holdings": num_holdings,
            "hhi_index": round(hhi, 2),
            "diversification_level": diversification_level,
            "diversification_score": score,
            "recommendation": self._get_diversification_recommendation(num_holdings, hhi)
        }
    
    def _assess_concentration(self, holdings: List[Dict], total_value: float) -> Dict[str, Any]:
        """
        Assess concentration risk
        """
        if not holdings or total_value == 0:
            return {"top_holding_weight": 0, "top_3_weight": 0}
        
        # Sort by value
        sorted_holdings = sorted(
            holdings, 
            key=lambda x: x.get("current_value", 0), 
            reverse=True
        )
        
        # Top holding
        top_weight = (sorted_holdings[0].get("current_value", 0) / total_value * 100) if sorted_holdings else 0
        
        # Top 3 holdings
        top_3_value = sum(h.get("current_value", 0) for h in sorted_holdings[:3])
        top_3_weight = (top_3_value / total_value * 100) if total_value > 0 else 0
        
        # Risk level
        if top_weight > 30:
            concentration_risk = "high"
        elif top_weight > 20:
            concentration_risk = "moderate"
        else:
            concentration_risk = "low"
        
        return {
            "top_holding": sorted_holdings[0].get("symbol", "N/A") if sorted_holdings else "N/A",
            "top_holding_weight": round(top_weight, 2),
            "top_3_weight": round(top_3_weight, 2),
            "concentration_risk": concentration_risk
        }
    
    def _calculate_risk_score(
        self, 
        risk_metrics: Dict, 
        diversification: Dict, 
        concentration: Dict
    ) -> float:
        """
        Calculate overall risk score (1-10)
        """
        score = 5  # Base score
        
        # Adjust based on volatility
        vol = risk_metrics.get("estimated_volatility", 15)
        if vol > 30:
            score += 2
        elif vol > 20:
            score += 1
        elif vol < 10:
            score -= 1
        
        # Adjust based on diversification
        div_score = diversification.get("diversification_score", 5)
        score += (5 - div_score) / 2
        
        # Adjust based on concentration
        if concentration.get("concentration_risk") == "high":
            score += 2
        elif concentration.get("concentration_risk") == "moderate":
            score += 1
        
        return max(1, min(10, round(score, 1)))
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Get risk level from score"""
        if risk_score >= 7:
            return "high"
        elif risk_score >= 4:
            return "moderate"
        else:
            return "low"
    
    def _generate_risk_recommendations(
        self, 
        risk_metrics: Dict, 
        diversification: Dict, 
        concentration: Dict
    ) -> List[str]:
        """
        Generate risk reduction recommendations
        """
        recommendations = []
        
        # Diversification recommendations
        if diversification.get("diversification_level") == "concentrated":
            recommendations.append("Consider adding more holdings to improve diversification")
        
        # Concentration recommendations
        if concentration.get("concentration_risk") == "high":
            top_holding = concentration.get("top_holding", "")
            recommendations.append(f"Reduce position in {top_holding} to below 20% of portfolio")
        
        # Volatility recommendations
        vol = risk_metrics.get("estimated_volatility", 15)
        if vol > 25:
            recommendations.append("Consider adding defensive sectors (utilities, staples) to reduce volatility")
        
        # General recommendations
        recommendations.append("Regular rebalancing helps maintain target risk levels")
        
        return recommendations
    
    def _get_diversification_recommendation(self, num_holdings: int, hhi: float) -> str:
        """Get diversification recommendation"""
        if num_holdings < 5:
            return "Add more holdings (recommend 10-15) for better diversification"
        elif hhi > 2500:
            return "Rebalance to more equal weights across holdings"
        elif hhi > 1500:
            return "Consider reducing position sizes in top holdings"
        else:
            return "Diversification is adequate"
    
    def _get_profile_suggestions(self, profile: str) -> List[str]:
        """Get investment suggestions based on risk profile"""
        suggestions = {
            "conservative": [
                "Focus on dividend-paying stocks",
                "Consider bond ETFs for stability",
                "Maintain adequate cash reserves",
                "Look into Treasury bonds"
            ],
            "moderate": [
                "Mix of growth and value stocks",
                "Include some international exposure",
                "Consider balanced funds",
                "Rebalance quarterly"
            ],
            "aggressive": [
                "Growth stocks and emerging markets",
                "Consider sector-specific ETFs",
                "Small-cap exposure for higher returns",
                "Stay invested through volatility"
            ]
        }
        return suggestions.get(profile, [])
