#!/usr/bin/env python3
"""
Gemini Rate Optimizer Integration
Combines rate optimization with Gemini AI for enhanced analysis and recommendations.
"""

import google.generativeai as genai
from typing import Dict, List, Optional
from optimizer import optimize_scenario
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ingest'))
from gemini_rate_integration import GeminiRateIntegration
import json


class GeminiOptimizerIntegration:
    """Integrates rate optimization with Gemini AI for enhanced analysis."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the integration."""
        self.rate_integration = GeminiRateIntegration(api_key)
        self.gemini_model = self.rate_integration.model
        
    def analyze_optimization_with_ai(self, loan_amount: float, credit_score: int, 
                                   ltv: float, loan_type: str = "30yr_fixed") -> Dict:
        """
        Analyze optimization results with Gemini AI for enhanced insights.
        
        Args:
            loan_amount: Loan amount
            credit_score: Credit score
            ltv: Loan-to-value ratio
            loan_type: Loan type
            
        Returns:
            Dict: Enhanced optimization analysis with AI insights
        """
        
        # Get optimization results
        optimization_result = optimize_scenario(loan_amount, credit_score, ltv, loan_type)
        
        if optimization_result.get('error'):
            return optimization_result
        
        # Get current rates context
        rates_context = self.rate_integration.get_rates_context()
        
        # Prepare data for Gemini analysis
        analysis_data = {
            "borrower_profile": {
                "loan_amount": loan_amount,
                "credit_score": credit_score,
                "ltv": ltv,
                "loan_type": loan_type
            },
            "current_scenario": optimization_result['current_scenario'],
            "optimizations": optimization_result,
            "rates_context": rates_context
        }
        
        # Generate AI analysis
        ai_analysis = self._generate_ai_analysis(analysis_data)
        
        # Combine results
        enhanced_result = {
            **optimization_result,
            "ai_analysis": ai_analysis
        }
        
        return enhanced_result
    
    def _generate_ai_analysis(self, analysis_data: Dict) -> Dict:
        """Generate AI analysis of optimization results."""
        
        # Prepare prompt
        prompt = self._create_analysis_prompt(analysis_data)
        
        try:
            # Generate response
            response = self.gemini_model.generate_content(prompt)
            
            # Parse response
            ai_insights = self._parse_ai_response(response.text)
            
            return {
                "insights": ai_insights,
                "raw_response": response.text,
                "success": True
            }
            
        except Exception as e:
            return {
                "insights": {},
                "error": str(e),
                "success": False
            }
    
    def _create_analysis_prompt(self, data: Dict) -> str:
        """Create prompt for AI analysis."""
        
        borrower = data['borrower_profile']
        current = data['current_scenario']
        optimizations = data['optimizations']
        rates_context = data['rates_context']
        
        prompt = f"""
You are a mortgage optimization expert. Analyze the following loan scenario and provide actionable insights.

BORROWER PROFILE:
- Loan Amount: ${borrower['loan_amount']:,}
- Credit Score: {borrower['credit_score']}
- LTV: {borrower['ltv']}%
- Loan Type: {borrower['loan_type']}

CURRENT SCENARIO:
- Rate: {current['final_rate']}%
- Monthly Payment: ${current['monthly_payment']:,.2f}
- Total Interest: ${current['total_interest']:,.2f}

OPTIMIZATION RESULTS:
{json.dumps(optimizations['summary'], indent=2)}

CURRENT MARKET CONTEXT:
{rates_context}

Please provide:

1. PRIORITY RECOMMENDATIONS (3-5 items):
   - Rank the most impactful optimizations
   - Consider feasibility and timeframe
   - Focus on actionable steps

2. MARKET INSIGHTS:
   - How do current rates compare to historical trends?
   - Is this a good time for this borrower to optimize?
   - Any market-specific considerations?

3. BORROWER-SPECIFIC ADVICE:
   - Tailored recommendations based on their profile
   - Risk considerations
   - Timeline suggestions

4. FINANCIAL IMPACT ANALYSIS:
   - ROI analysis for each major optimization
   - Break-even analysis
   - Opportunity cost considerations

5. NEXT STEPS:
   - Specific actions the borrower should take
   - Timeline for implementation
   - Resources or tools they might need

Format your response as structured insights that can be easily parsed and displayed to the borrower.
"""
        
        return prompt
    
    def _parse_ai_response(self, response_text: str) -> Dict:
        """Parse AI response into structured format."""
        
        # Simple parsing - in production, you might want more sophisticated parsing
        insights = {
            "priority_recommendations": [],
            "market_insights": "",
            "borrower_advice": "",
            "financial_impact": "",
            "next_steps": []
        }
        
        # Extract sections (basic parsing)
        lines = response_text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Detect sections
            if 'PRIORITY RECOMMENDATIONS' in line.upper():
                current_section = 'priority_recommendations'
            elif 'MARKET INSIGHTS' in line.upper():
                current_section = 'market_insights'
            elif 'BORROWER-SPECIFIC ADVICE' in line.upper():
                current_section = 'borrower_advice'
            elif 'FINANCIAL IMPACT' in line.upper():
                current_section = 'financial_impact'
            elif 'NEXT STEPS' in line.upper():
                current_section = 'next_steps'
            elif line.startswith('-') or line.startswith('•') or line.startswith('*'):
                # Bullet points
                if current_section == 'priority_recommendations':
                    insights['priority_recommendations'].append(line[1:].strip())
                elif current_section == 'next_steps':
                    insights['next_steps'].append(line[1:].strip())
            elif current_section and line and not line.isupper():
                # Regular content
                if current_section == 'market_insights':
                    insights['market_insights'] += line + ' '
                elif current_section == 'borrower_advice':
                    insights['borrower_advice'] += line + ' '
                elif current_section == 'financial_impact':
                    insights['financial_impact'] += line + ' '
        
        # Clean up
        for key in ['market_insights', 'borrower_advice', 'financial_impact']:
            insights[key] = insights[key].strip()
        
        return insights
    
    def generate_optimization_report(self, loan_amount: float, credit_score: int, 
                                   ltv: float, loan_type: str = "30yr_fixed") -> str:
        """
        Generate a comprehensive optimization report.
        
        Args:
            loan_amount: Loan amount
            credit_score: Credit score
            ltv: Loan-to-value ratio
            loan_type: Loan type
            
        Returns:
            str: Formatted optimization report
        """
        
        result = self.analyze_optimization_with_ai(loan_amount, credit_score, ltv, loan_type)
        
        if result.get('error'):
            return f"Error generating report: {result['message']}"
        
        # Format report
        report = []
        report.append("=" * 60)
        report.append("MORTGAGE OPTIMIZATION REPORT")
        report.append("=" * 60)
        report.append("")
        
        # Borrower profile
        report.append("BORROWER PROFILE:")
        report.append(f"  Loan Amount: ${loan_amount:,}")
        report.append(f"  Credit Score: {credit_score}")
        report.append(f"  LTV: {ltv}%")
        report.append(f"  Loan Type: {loan_type}")
        report.append("")
        
        # Current scenario
        current = result['current_scenario']
        report.append("CURRENT SCENARIO:")
        report.append(f"  Rate: {current['final_rate']}%")
        report.append(f"  Monthly Payment: ${current['monthly_payment']:,.2f}")
        report.append(f"  Total Interest: ${current['total_interest']:,.2f}")
        report.append("")
        
        # Summary
        summary = result['summary']
        report.append("OPTIMIZATION SUMMARY:")
        report.append(f"  Total Potential Savings: ${summary['total_potential_savings']:,.2f}")
        report.append(f"  Quick Wins Available: {len(summary.get('quick_wins', []))}")
        report.append(f"  Long-term Improvements: {len(summary.get('long_term_improvements', []))}")
        report.append("")
        
        # AI insights
        if result.get('ai_analysis', {}).get('success'):
            ai_insights = result['ai_analysis']['insights']
            
            if ai_insights.get('priority_recommendations'):
                report.append("AI PRIORITY RECOMMENDATIONS:")
                for i, rec in enumerate(ai_insights['priority_recommendations'], 1):
                    report.append(f"  {i}. {rec}")
                report.append("")
            
            if ai_insights.get('market_insights'):
                report.append("MARKET INSIGHTS:")
                report.append(f"  {ai_insights['market_insights']}")
                report.append("")
            
            if ai_insights.get('borrower_advice'):
                report.append("BORROWER-SPECIFIC ADVICE:")
                report.append(f"  {ai_insights['borrower_advice']}")
                report.append("")
            
            if ai_insights.get('next_steps'):
                report.append("NEXT STEPS:")
                for i, step in enumerate(ai_insights['next_steps'], 1):
                    report.append(f"  {i}. {step}")
                report.append("")
        
        # Top recommendations
        report.append("TOP RECOMMENDATIONS:")
        for i, rec in enumerate(summary['recommendations'][:3], 1):
            report.append(f"  {i}. {rec}")
        report.append("")
        
        report.append("=" * 60)
        
        return '\n'.join(report)


def analyze_optimization_with_ai(loan_amount: float, credit_score: int, 
                               ltv: float, loan_type: str = "30yr_fixed") -> Dict:
    """
    Main function to analyze optimization with AI.
    
    Args:
        loan_amount: Loan amount
        credit_score: Credit score
        ltv: Loan-to-value ratio
        loan_type: Loan type
        
    Returns:
        Dict: Enhanced optimization analysis
    """
    
    integration = GeminiOptimizerIntegration()
    return integration.analyze_optimization_with_ai(loan_amount, credit_score, ltv, loan_type)


def generate_optimization_report(loan_amount: float, credit_score: int, 
                               ltv: float, loan_type: str = "30yr_fixed") -> str:
    """
    Generate optimization report.
    
    Args:
        loan_amount: Loan amount
        credit_score: Credit score
        ltv: Loan-to-value ratio
        loan_type: Loan type
        
    Returns:
        str: Formatted report
    """
    
    integration = GeminiOptimizerIntegration()
    return integration.generate_optimization_report(loan_amount, credit_score, ltv, loan_type)


if __name__ == "__main__":
    # Test the integration
    print("=== Testing Gemini Optimizer Integration ===\n")
    
    # Test scenario
    loan_amount = 500000
    credit_score = 680
    ltv = 85
    
    print(f"Analyzing scenario:")
    print(f"  Loan Amount: ${loan_amount:,}")
    print(f"  Credit Score: {credit_score}")
    print(f"  LTV: {ltv}%")
    print()
    
    # Generate report
    report = generate_optimization_report(loan_amount, credit_score, ltv)
    print(report) 