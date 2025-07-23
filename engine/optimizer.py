#!/usr/bin/env python3
"""
Rate Optimization Engine
Suggests ways for borrowers to reduce rates or fees by adjusting loan parameters.
"""

from typing import Dict, List, Optional, Tuple
from quote_engine import quote_rate, get_quote_comparison
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ingest'))
from gemini_rate_integration import GeminiRateIntegration


class RateOptimizer:
    """Optimizes loan scenarios to find better rates and fees."""
    
    def __init__(self):
        self.integration = GeminiRateIntegration()
        self.current_rates = self.integration.scheduler.get_current_rates()
    
    def optimize_scenario(self, loan_amount: float, credit_score: int, ltv: float, 
                         loan_type: str = "30yr_fixed") -> Dict:
        """
        Analyze current scenario and suggest optimizations to reduce rates or fees.
        
        Args:
            loan_amount: Current loan amount
            credit_score: Current credit score
            ltv: Current loan-to-value ratio
            loan_type: Loan type to analyze
            
        Returns:
            Dict: Optimization suggestions and potential savings
        """
        
        if not self.current_rates:
            return {
                "error": True,
                "message": "No current rates available for optimization"
            }
        
        # Get current quote
        current_quote = quote_rate(loan_amount, credit_score, ltv, loan_type, self.current_rates)
        
        if current_quote.get('error'):
            return {
                "error": True,
                "message": f"Unable to generate current quote: {current_quote.get('error_message', 'Unknown error')}"
            }
        
        # Generate optimization scenarios
        optimizations = {
            "current_scenario": current_quote,
            "credit_score_optimizations": self._optimize_credit_score(loan_amount, credit_score, ltv, loan_type),
            "ltv_optimizations": self._optimize_ltv(loan_amount, credit_score, ltv, loan_type),
            "loan_amount_optimizations": self._optimize_loan_amount(loan_amount, credit_score, ltv, loan_type),
            "loan_type_optimizations": self._optimize_loan_type(loan_amount, credit_score, ltv),
            "summary": {}
        }
        
        # Generate summary and recommendations
        optimizations["summary"] = self._generate_summary(optimizations)
        
        return optimizations
    
    def _optimize_credit_score(self, loan_amount: float, current_credit: int, ltv: float, 
                              loan_type: str) -> List[Dict]:
        """Suggest credit score improvements."""
        
        optimizations = []
        
        # Define credit score improvement targets
        credit_targets = [
            (680, "Good credit threshold"),
            (720, "Excellent credit threshold"),
            (760, "Premium credit tier")
        ]
        
        current_quote = quote_rate(loan_amount, current_credit, ltv, loan_type, self.current_rates)
        
        for target_credit, description in credit_targets:
            if target_credit > current_credit:
                improved_quote = quote_rate(loan_amount, target_credit, ltv, loan_type, self.current_rates)
                
                if not improved_quote.get('error'):
                    rate_savings = current_quote['final_rate'] - improved_quote['final_rate']
                    monthly_savings = current_quote['monthly_payment'] - improved_quote['monthly_payment']
                    total_savings = current_quote['total_interest'] - improved_quote['total_interest']
                    
                    if rate_savings > 0:
                        optimizations.append({
                            "type": "credit_score",
                            "current_value": current_credit,
                            "target_value": target_credit,
                            "improvement_needed": target_credit - current_credit,
                            "description": description,
                            "rate_savings": round(rate_savings, 3),
                            "monthly_savings": round(monthly_savings, 2),
                            "total_savings": round(total_savings, 2),
                            "new_rate": improved_quote['final_rate'],
                            "new_monthly_payment": improved_quote['monthly_payment'],
                            "feasibility": self._assess_credit_improvement_feasibility(current_credit, target_credit),
                            "timeframe": self._estimate_credit_improvement_timeframe(current_credit, target_credit)
                        })
        
        return optimizations
    
    def _optimize_ltv(self, loan_amount: float, credit_score: int, current_ltv: float, 
                     loan_type: str) -> List[Dict]:
        """Suggest LTV improvements."""
        
        optimizations = []
        
        # Define LTV improvement targets
        ltv_targets = [
            (80, "Conventional loan threshold"),
            (70, "Better rate tier"),
            (60, "Premium rate tier")
        ]
        
        current_quote = quote_rate(loan_amount, credit_score, current_ltv, loan_type, self.current_rates)
        
        for target_ltv, description in ltv_targets:
            if target_ltv < current_ltv:
                improved_quote = quote_rate(loan_amount, credit_score, target_ltv, loan_type, self.current_rates)
                
                if not improved_quote.get('error'):
                    rate_savings = current_quote['final_rate'] - improved_quote['final_rate']
                    monthly_savings = current_quote['monthly_payment'] - improved_quote['monthly_payment']
                    total_savings = current_quote['total_interest'] - improved_quote['total_interest']
                    
                    # Calculate additional down payment needed
                    # LTV = Loan Amount / Property Value, so Property Value = Loan Amount / LTV
                    property_value = loan_amount / (current_ltv / 100)
                    current_down_payment = property_value - loan_amount
                    target_loan_amount = property_value * (target_ltv / 100)
                    target_down_payment = property_value - target_loan_amount
                    additional_down_payment = target_down_payment - current_down_payment
                    
                    if rate_savings > 0:
                        optimizations.append({
                            "type": "ltv",
                            "current_value": current_ltv,
                            "target_value": target_ltv,
                            "improvement_needed": current_ltv - target_ltv,
                            "description": description,
                            "rate_savings": round(rate_savings, 3),
                            "monthly_savings": round(monthly_savings, 2),
                            "total_savings": round(total_savings, 2),
                            "additional_down_payment": round(additional_down_payment, 2),
                            "new_rate": improved_quote['final_rate'],
                            "new_monthly_payment": improved_quote['monthly_payment'],
                            "feasibility": self._assess_ltv_improvement_feasibility(current_ltv, target_ltv),
                            "roi_analysis": self._calculate_ltv_roi(additional_down_payment, total_savings)
                        })
        
        return optimizations
    
    def _optimize_loan_amount(self, current_amount: float, credit_score: int, ltv: float, 
                            loan_type: str) -> List[Dict]:
        """Suggest loan amount optimizations."""
        
        optimizations = []
        
        # Define loan amount reduction scenarios
        reduction_scenarios = [
            (0.05, "5% reduction"),
            (0.10, "10% reduction"),
            (0.15, "15% reduction")
        ]
        
        current_quote = quote_rate(current_amount, credit_score, ltv, loan_type, self.current_rates)
        
        for reduction_pct, description in reduction_scenarios:
            new_amount = current_amount * (1 - reduction_pct)
            reduced_quote = quote_rate(new_amount, credit_score, ltv, loan_type, self.current_rates)
            
            if not reduced_quote.get('error'):
                monthly_savings = current_quote['monthly_payment'] - reduced_quote['monthly_payment']
                total_savings = current_quote['total_interest'] - reduced_quote['total_interest']
                amount_reduction = current_amount - new_amount
                
                optimizations.append({
                    "type": "loan_amount",
                    "current_value": current_amount,
                    "target_value": new_amount,
                    "reduction_amount": round(amount_reduction, 2),
                    "reduction_percentage": round(reduction_pct * 100, 1),
                    "description": description,
                    "monthly_savings": round(monthly_savings, 2),
                    "total_savings": round(total_savings, 2),
                    "new_monthly_payment": reduced_quote['monthly_payment'],
                    "feasibility": "high" if reduction_pct <= 0.10 else "medium",
                    "impact": "significant" if reduction_pct >= 0.10 else "moderate"
                })
        
        return optimizations
    
    def _optimize_loan_type(self, loan_amount: float, credit_score: int, ltv: float) -> List[Dict]:
        """Suggest alternative loan types."""
        
        optimizations = []
        
        # Get comparison of all loan types
        comparison = get_quote_comparison(loan_amount, credit_score, ltv, self.current_rates)
        quotes = comparison.get('quotes', {})
        
        if not quotes:
            return optimizations
        
        # Find the best rate
        best_rate = min([q['final_rate'] for q in quotes.values() if not q.get('error')])
        best_loan_type = [k for k, v in quotes.items() if v.get('final_rate') == best_rate][0]
        
        # Compare current loan type (assume 30yr_fixed) with alternatives
        current_quote = quotes.get('30yr_fixed')
        if not current_quote or current_quote.get('error'):
            return optimizations
        
        for loan_type, quote in quotes.items():
            if loan_type != '30yr_fixed' and not quote.get('error'):
                rate_savings = current_quote['final_rate'] - quote['final_rate']
                monthly_savings = current_quote['monthly_payment'] - quote['monthly_payment']
                total_savings = current_quote['total_interest'] - quote['total_interest']
                
                if rate_savings > 0:
                    optimizations.append({
                        "type": "loan_type",
                        "current_loan_type": "30yr_fixed",
                        "alternative_loan_type": loan_type,
                        "rate_savings": round(rate_savings, 3),
                        "monthly_savings": round(monthly_savings, 2),
                        "total_savings": round(total_savings, 2),
                        "new_rate": quote['final_rate'],
                        "new_monthly_payment": quote['monthly_payment'],
                        "description": self._get_loan_type_description(loan_type),
                        "considerations": self._get_loan_type_considerations(loan_type),
                        "feasibility": self._assess_loan_type_feasibility(loan_type, credit_score, ltv)
                    })
        
        return optimizations
    
    def _generate_summary(self, optimizations: Dict) -> Dict:
        """Generate summary of all optimizations."""
        
        summary = {
            "total_potential_savings": 0,
            "best_optimizations": [],
            "quick_wins": [],
            "long_term_improvements": [],
            "recommendations": []
        }
        
        # Calculate total potential savings
        all_savings = []
        
        # Credit score optimizations
        for opt in optimizations.get("credit_score_optimizations", []):
            all_savings.append({
                "type": "credit_score",
                "savings": opt.get("total_savings", 0),
                "description": f"Improve credit to {opt['target_value']}",
                "timeframe": opt.get("timeframe", "unknown")
            })
        
        # LTV optimizations
        for opt in optimizations.get("ltv_optimizations", []):
            all_savings.append({
                "type": "ltv",
                "savings": opt.get("total_savings", 0),
                "description": f"Reduce LTV to {opt['target_value']}%",
                "cost": opt.get("additional_down_payment", 0)
            })
        
        # Loan type optimizations
        for opt in optimizations.get("loan_type_optimizations", []):
            all_savings.append({
                "type": "loan_type",
                "savings": opt.get("total_savings", 0),
                "description": f"Switch to {opt['alternative_loan_type']}"
            })
        
        # Sort by savings
        all_savings.sort(key=lambda x: x["savings"], reverse=True)
        
        summary["total_potential_savings"] = sum(opt["savings"] for opt in all_savings)
        summary["best_optimizations"] = all_savings[:3]  # Top 3
        
        # Categorize optimizations
        for opt in all_savings:
            if opt["type"] in ["ltv", "loan_type"]:
                summary["quick_wins"].append(opt)
            else:
                summary["long_term_improvements"].append(opt)
        
        # Generate recommendations
        summary["recommendations"] = self._generate_recommendations(optimizations)
        
        return summary
    
    def _generate_recommendations(self, optimizations: Dict) -> List[str]:
        """Generate actionable recommendations."""
        
        recommendations = []
        
        # Credit score recommendations
        credit_opts = optimizations.get("credit_score_optimizations", [])
        if credit_opts:
            best_credit_opt = max(credit_opts, key=lambda x: x.get("total_savings", 0))
            recommendations.append(
                f"Improve your credit score to {best_credit_opt['target_value']} to save "
                f"${best_credit_opt['total_savings']:,.0f} over the life of the loan."
            )
        
        # LTV recommendations
        ltv_opts = optimizations.get("ltv_optimizations", [])
        if ltv_opts:
            best_ltv_opt = max(ltv_opts, key=lambda x: x.get("total_savings", 0))
            recommendations.append(
                f"Increase your down payment by ${best_ltv_opt['additional_down_payment']:,.0f} "
                f"to reduce LTV to {best_ltv_opt['target_value']}% and save "
                f"${best_ltv_opt['total_savings']:,.0f} in interest."
            )
        
        # Loan type recommendations
        loan_type_opts = optimizations.get("loan_type_optimizations", [])
        if loan_type_opts:
            best_loan_opt = max(loan_type_opts, key=lambda x: x.get("total_savings", 0))
            recommendations.append(
                f"Consider a {best_loan_opt['alternative_loan_type']} loan to save "
                f"${best_loan_opt['total_savings']:,.0f} in interest."
            )
        
        return recommendations
    
    def _assess_credit_improvement_feasibility(self, current_credit: int, target_credit: int) -> str:
        """Assess feasibility of credit score improvement."""
        improvement_needed = target_credit - current_credit
        
        if improvement_needed <= 20:
            return "high"
        elif improvement_needed <= 50:
            return "medium"
        else:
            return "low"
    
    def _estimate_credit_improvement_timeframe(self, current_credit: int, target_credit: int) -> str:
        """Estimate timeframe for credit score improvement."""
        improvement_needed = target_credit - current_credit
        
        if improvement_needed <= 20:
            return "3-6 months"
        elif improvement_needed <= 50:
            return "6-12 months"
        else:
            return "12+ months"
    
    def _assess_ltv_improvement_feasibility(self, current_ltv: float, target_ltv: float) -> str:
        """Assess feasibility of LTV improvement."""
        improvement_needed = current_ltv - target_ltv
        
        if improvement_needed <= 5:
            return "high"
        elif improvement_needed <= 15:
            return "medium"
        else:
            return "low"
    
    def _calculate_ltv_roi(self, additional_down_payment: float, total_savings: float) -> Dict:
        """Calculate ROI of additional down payment."""
        if additional_down_payment <= 0:
            return {"roi_percentage": 0, "payback_period": 0}
        
        roi_percentage = (total_savings / additional_down_payment) * 100
        payback_period = additional_down_payment / (total_savings / 30)  # Years to payback
        
        return {
            "roi_percentage": round(roi_percentage, 2),
            "payback_period": round(payback_period, 1)
        }
    
    def _assess_loan_type_feasibility(self, loan_type: str, credit_score: int, ltv: float) -> str:
        """Assess feasibility of loan type change."""
        if loan_type == "fha_30yr" and credit_score >= 680:
            return "low"  # Better rates available with conventional
        elif loan_type == "va_30yr":
            return "conditional"  # Requires VA eligibility
        elif loan_type == "jumbo_30yr" and ltv > 80:
            return "low"  # Jumbo loans typically require lower LTV
        else:
            return "high"
    
    def _get_loan_type_description(self, loan_type: str) -> str:
        """Get description of loan type."""
        descriptions = {
            "15yr_fixed": "15-year fixed rate mortgage - lower rate, higher payment",
            "fha_30yr": "FHA loan - lower credit requirements, higher fees",
            "va_30yr": "VA loan - for veterans, typically lower rates",
            "jumbo_30yr": "Jumbo loan - for larger loan amounts",
            "5_1_arm": "5/1 ARM - lower initial rate, adjusts after 5 years",
            "7_1_arm": "7/1 ARM - lower initial rate, adjusts after 7 years",
            "10_1_arm": "10/1 ARM - lower initial rate, adjusts after 10 years"
        }
        return descriptions.get(loan_type, "Alternative loan type")
    
    def _get_loan_type_considerations(self, loan_type: str) -> List[str]:
        """Get considerations for loan type."""
        considerations = {
            "15yr_fixed": [
                "Higher monthly payment",
                "Lower total interest paid",
                "Faster equity building"
            ],
            "fha_30yr": [
                "Mortgage insurance required",
                "Lower credit score requirements",
                "Higher overall costs"
            ],
            "va_30yr": [
                "VA funding fee required",
                "Veteran eligibility required",
                "Typically lower rates"
            ],
            "jumbo_30yr": [
                "Higher credit requirements",
                "Lower LTV limits",
                "May require larger reserves"
            ],
            "5_1_arm": [
                "Rate adjusts after 5 years",
                "Lower initial payment",
                "Rate cap protection"
            ]
        }
        return considerations.get(loan_type, ["Review terms carefully"])


def optimize_scenario(loan_amount: float, credit_score: int, ltv: float, 
                     loan_type: str = "30yr_fixed") -> Dict:
    """
    Main function to optimize a loan scenario.
    
    Args:
        loan_amount: Current loan amount
        credit_score: Current credit score
        ltv: Current loan-to-value ratio
        loan_type: Loan type to analyze
        
    Returns:
        Dict: Optimization suggestions and potential savings
    """
    
    optimizer = RateOptimizer()
    return optimizer.optimize_scenario(loan_amount, credit_score, ltv, loan_type)


if __name__ == "__main__":
    # Test the optimizer
    print("=== Testing Rate Optimizer ===\n")
    
    # Test scenario
    loan_amount = 500000
    credit_score = 680
    ltv = 85
    
    print(f"Optimizing scenario:")
    print(f"  Loan Amount: ${loan_amount:,}")
    print(f"  Credit Score: {credit_score}")
    print(f"  LTV: {ltv}%")
    print()
    
    result = optimize_scenario(loan_amount, credit_score, ltv)
    
    if result.get('error'):
        print(f"Error: {result['message']}")
    else:
        current = result['current_scenario']
        print(f"Current Rate: {current['final_rate']}%")
        print(f"Current Monthly Payment: ${current['monthly_payment']:,.2f}")
        print(f"Current Total Interest: ${current['total_interest']:,.2f}")
        print()
        
        # Show optimizations
        summary = result['summary']
        print(f"Total Potential Savings: ${summary['total_potential_savings']:,.2f}")
        print()
        
        print("Top Recommendations:")
        for i, rec in enumerate(summary['recommendations'][:3], 1):
            print(f"{i}. {rec}")
        print()
        
        print("Best Optimizations:")
        for opt in summary['best_optimizations']:
            print(f"  {opt['description']}: ${opt['savings']:,.0f} savings") 