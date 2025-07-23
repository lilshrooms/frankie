#!/usr/bin/env python3
"""
Gemini Rate Integration Module
Provides current mortgage rates to Gemini for analyzing prospective homeowners.
"""

import json
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta
from pathlib import Path

from rate_scheduler import RateScheduler
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'engine'))
from quote_engine import quote_rate, get_quote_comparison


class GeminiRateIntegration:
    """Integrates current rates with Gemini analysis for prospective homeowners."""
    
    def __init__(self, data_dir: str = "rate_data"):
        self.scheduler = RateScheduler(data_dir)
    
    def get_current_rates_context(self) -> str:
        """
        Get current rates formatted as context for Gemini analysis.
        
        Returns:
            str: Formatted rate context for Gemini prompts
        """
        
        rates_data = self.scheduler.get_rates_for_gemini()
        
        if not rates_data["current_rates"]:
            return "No current mortgage rates available."
        
        context = "CURRENT MORTGAGE RATES:\n\n"
        
        # Add rate summary
        summary = rates_data["rate_summary"]
        context += f"Rate Summary (as of {summary['last_updated']}):\n"
        context += f"- Total rates available: {summary['total_rates']}\n"
        context += f"- Loan types: {', '.join(summary['loan_types'])}\n"
        context += f"- Rate range: {summary['rate_range']['min']}% - {summary['rate_range']['max']}%\n\n"
        
        # Add detailed rates by loan type
        for loan_type, rates in rates_data["rate_breakdown"].items():
            context += f"{loan_type.upper()}:\n"
            for rate in rates:
                context += f"  - Rate: {rate['rate']}% | APR: {rate['apr']}% | Lock: {rate['lock_period']} days\n"
            context += "\n"
        
        return context
    
    def generate_rate_quote_for_borrower(self, borrower_info: Dict) -> Dict:
        """
        Generate a rate quote for a specific borrower based on their profile.
        
        Args:
            borrower_info: Dictionary containing borrower information
                - loan_amount: float
                - credit_score: int
                - ltv: float (loan-to-value ratio)
                - loan_type: str (optional, will compare all if not specified)
                - property_value: float (optional)
                - down_payment: float (optional)
        
        Returns:
            Dict: Rate quote and analysis for the borrower
        """
        
        current_rates = self.scheduler.get_current_rates()
        
        if not current_rates:
            return {
                "error": True,
                "message": "No current rates available"
            }
        
        # Extract borrower information
        loan_amount = borrower_info.get('loan_amount', 0)
        credit_score = borrower_info.get('credit_score', 0)
        ltv = borrower_info.get('ltv', 0)
        loan_type = borrower_info.get('loan_type')
        
        if not all([loan_amount, credit_score, ltv]):
            return {
                "error": True,
                "message": "Missing required borrower information"
            }
        
        # Generate quote(s)
        if loan_type:
            # Single loan type quote
            quote = quote_rate(loan_amount, credit_score, ltv, loan_type, current_rates)
            quotes = {loan_type: quote} if not quote.get('error') else {}
        else:
            # Compare all loan types
            comparison = get_quote_comparison(loan_amount, credit_score, ltv, current_rates)
            quotes = comparison.get('quotes', {})
        
        # Format response for Gemini
        response = {
            "borrower_info": borrower_info,
            "current_rates_summary": self.scheduler.get_rates_for_gemini()["rate_summary"],
            "quotes": quotes,
            "recommendations": self._generate_recommendations(quotes, borrower_info),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return response
    
    def _generate_recommendations(self, quotes: Dict, borrower_info: Dict) -> List[str]:
        """Generate recommendations based on quotes and borrower profile."""
        
        recommendations = []
        
        if not quotes:
            recommendations.append("Unable to generate quotes with current borrower profile.")
            return recommendations
        
        # Find best rate
        best_rate = min([q['final_rate'] for q in quotes.values() if not q.get('error')])
        best_loan_type = [k for k, v in quotes.items() if v.get('final_rate') == best_rate][0]
        
        recommendations.append(f"Best available rate: {best_rate}% ({best_loan_type})")
        
        # Credit score recommendations
        credit_score = borrower_info.get('credit_score', 0)
        if credit_score < 680:
            recommendations.append("Consider improving credit score to qualify for better rates")
        elif credit_score >= 760:
            recommendations.append("Excellent credit score - you qualify for the best rates")
        
        # LTV recommendations
        ltv = borrower_info.get('ltv', 0)
        if ltv > 80:
            recommendations.append("High LTV may result in higher rates - consider larger down payment")
        
        # Loan type recommendations
        if 'fha_30yr' in quotes and not quotes['fha_30yr'].get('error'):
            recommendations.append("FHA loan available for lower credit scores")
        
        if 'va_30yr' in quotes and not quotes['va_30yr'].get('error'):
            recommendations.append("VA loan available for veterans - typically lower rates")
        
        return recommendations
    
    def get_rate_trends(self, days: int = 7) -> Dict:
        """
        Get rate trends over the specified number of days.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict: Rate trends and analysis
        """
        
        data_dir = Path(self.scheduler.data_dir)
        historical_dir = data_dir / 'historical'
        
        trends = {
            "period_days": days,
            "rate_changes": {},
            "summary": {}
        }
        
        # Collect historical data
        historical_rates = []
        for i in range(days):
            date = datetime.now(timezone.utc) - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            historical_file = historical_dir / f'rates_{date_str}.json'
            
            if historical_file.exists():
                try:
                    with open(historical_file, 'r') as f:
                        data = json.load(f)
                        historical_rates.append(data)
                except Exception as e:
                    continue
        
        if not historical_rates:
            return {"error": "No historical data available"}
        
        # Analyze trends by loan type
        loan_types = set()
        for data in historical_rates:
            for rate in data.get('normalized_rates', []):
                loan_types.add(rate.get('loan_type'))
        
        for loan_type in loan_types:
            rates_over_time = []
            for data in historical_rates:
                for rate in data.get('normalized_rates', []):
                    if rate.get('loan_type') == loan_type:
                        rates_over_time.append({
                            'date': data.get('date'),
                            'rate': rate.get('rate')
                        })
                        break
            
            if len(rates_over_time) > 1:
                # Calculate trend
                first_rate = rates_over_time[0]['rate']
                last_rate = rates_over_time[-1]['rate']
                change = last_rate - first_rate
                
                trends["rate_changes"][loan_type] = {
                    "start_rate": first_rate,
                    "end_rate": last_rate,
                    "change": round(change, 3),
                    "change_percent": round((change / first_rate) * 100, 2),
                    "trend": "up" if change > 0 else "down" if change < 0 else "stable"
                }
        
        return trends
    
    def format_for_gemini_analysis(self, borrower_email_body: str, borrower_info: Dict = None) -> str:
        """
        Format current rates and borrower information for Gemini analysis.
        
        Args:
            borrower_email_body: Email body from prospective borrower
            borrower_info: Optional borrower information dictionary
            
        Returns:
            str: Formatted context for Gemini analysis
        """
        
        context = "MORTGAGE RATE ANALYSIS CONTEXT:\n\n"
        
        # Add current rates
        context += self.get_current_rates_context()
        context += "\n"
        
        # Add borrower information if available
        if borrower_info:
            context += "BORROWER PROFILE:\n"
            for key, value in borrower_info.items():
                context += f"- {key.replace('_', ' ').title()}: {value}\n"
            context += "\n"
        
        # Add email content
        context += "BORROWER EMAIL:\n"
        context += borrower_email_body
        context += "\n\n"
        
        # Add analysis instructions
        context += "ANALYSIS INSTRUCTIONS:\n"
        context += "1. Analyze the borrower's loan request\n"
        context += "2. Compare with current market rates\n"
        context += "3. Provide rate recommendations\n"
        context += "4. Suggest appropriate loan types\n"
        context += "5. Include rate quotes if borrower information is sufficient\n"
        
        return context


if __name__ == "__main__":
    # Test the integration
    integration = GeminiRateIntegration()
    
    print("=== Testing Gemini Rate Integration ===\n")
    
    # Test current rates context
    print("1. Current Rates Context:")
    context = integration.get_current_rates_context()
    print(context[:500] + "..." if len(context) > 500 else context)
    
    # Test borrower quote
    print("\n2. Sample Borrower Quote:")
    borrower_info = {
        "loan_amount": 500000,
        "credit_score": 720,
        "ltv": 85,
        "property_value": 588235,
        "down_payment": 88235
    }
    
    quote_result = integration.generate_rate_quote_for_borrower(borrower_info)
    print(f"Quote Result: {quote_result.get('quotes', {})}")
    
    # Test Gemini analysis format
    print("\n3. Gemini Analysis Format:")
    email_body = "Hi, I'm looking to refinance my home. Current loan is $400k at 7.5%. Credit score 750, home value $500k."
    formatted = integration.format_for_gemini_analysis(email_body, borrower_info)
    print(formatted[:300] + "..." if len(formatted) > 300 else formatted) 