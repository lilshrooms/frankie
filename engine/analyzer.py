#!/usr/bin/env python3
"""
Gemini-Powered Rate Analyzer
Provides human-readable explanations of rate quotes and improvement suggestions.
"""

import google.generativeai as genai
from typing import Dict, List, Optional, Any
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'rate_ingest'))
from gemini_rate_integration import GeminiRateIntegration
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiRateAnalyzer:
    """Analyzes rate quotes using Gemini AI to provide human-readable explanations."""
    
    def __init__(self, api_key: Optional[str] = None, data_dir: str = "rate_data"):
        """Initialize the analyzer with Gemini integration."""
        self.rate_integration = GeminiRateIntegration(data_dir)
        
        # Initialize Gemini model
        if api_key:
            genai.configure(api_key=api_key)
        else:
            # Try to get from environment variable
            import os
            api_key = os.getenv('GOOGLE_API_KEY')
            if api_key:
                genai.configure(api_key=api_key)
            else:
                # For testing without API key, create a mock model
                self.gemini_model = None
                return
        
        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        
    def analyze_quote(self, quote_result: Dict, borrower_profile: Dict) -> Dict:
        """
        Analyze a rate quote and provide human-readable explanation.
        
        Args:
            quote_result: Result from quote_engine.quote_rate()
            borrower_profile: Dictionary with borrower information
            
        Returns:
            Dict: Analysis with explanation and improvement suggestions
        """
        
        if quote_result.get('error'):
            return {
                "success": False,
                "error": quote_result.get('error_message', 'Unknown error'),
                "explanation": "Unable to analyze quote due to error in quote generation."
            }
        
        # Get current market context
        rates_context = self.rate_integration.get_current_rates_context()
        
        # Prepare analysis data
        analysis_data = {
            "quote_result": quote_result,
            "borrower_profile": borrower_profile,
            "rates_context": rates_context
        }
        
        # Generate analysis
        analysis = self._generate_quote_analysis(analysis_data)
        
        return {
            "success": True,
            "explanation": analysis.get("explanation", ""),
            "improvement_suggestions": analysis.get("improvements", []),
            "rate_breakdown": analysis.get("rate_breakdown", {}),
            "market_context": analysis.get("market_context", ""),
            "raw_analysis": analysis.get("raw_response", "")
        }
    
    def _generate_quote_analysis(self, data: Dict) -> Dict:
        """Generate AI analysis of the quote."""
        
        # Prepare prompt
        prompt = self._create_analysis_prompt(data)
        
        try:
            # Check if model is available
            if not self.gemini_model:
                return {
                    "explanation": "AI analysis not available (no API key configured).",
                    "improvements": [
                        {
                            "suggestion": "Improve your credit score to 720 or higher",
                            "impact": "Could reduce your rate by 0.125% or more",
                            "action": "Pay bills on time and reduce credit utilization"
                        },
                        {
                            "suggestion": "Increase your down payment to reduce LTV below 80%",
                            "impact": "Could reduce your rate by 0.25% or more",
                            "action": "Save additional funds for down payment"
                        }
                    ],
                    "rate_breakdown": {
                        "description": "Your rate includes the base market rate plus adjustments for credit score and LTV."
                    },
                    "market_context": "Current market rates are available for comparison.",
                    "raw_response": "Mock response for testing",
                    "success": True
                }
            
            # Generate response
            response = self.gemini_model.generate_content(prompt)
            
            # Parse response
            analysis = self._parse_analysis_response(response.text)
            
            return {
                "explanation": analysis.get("explanation", ""),
                "improvements": analysis.get("improvements", []),
                "rate_breakdown": analysis.get("rate_breakdown", {}),
                "market_context": analysis.get("market_context", ""),
                "raw_response": response.text,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error generating quote analysis: {str(e)}")
            return {
                "explanation": "Unable to generate AI analysis at this time.",
                "improvements": [],
                "rate_breakdown": {},
                "market_context": "",
                "error": str(e),
                "success": False
            }
    
    def _create_analysis_prompt(self, data: Dict) -> str:
        """Create prompt for quote analysis."""
        
        quote = data['quote_result']
        borrower = data['borrower_profile']
        rates_context = data['rates_context']
        
        prompt = f"""
You are a mortgage expert explaining rate quotes to borrowers in clear, friendly language.

BORROWER PROFILE:
- Loan Amount: ${borrower.get('loan_amount', 0):,}
- Credit Score: {borrower.get('credit_score', 'N/A')}
- LTV: {borrower.get('ltv', 'N/A')}%
- Loan Type: {borrower.get('loan_type', 'N/A')}
- Property Type: {borrower.get('property_type', 'Primary Residence')}
- Occupancy: {borrower.get('occupancy', 'Owner Occupied')}

QUOTE RESULT:
- Final Rate: {quote.get('final_rate', 'N/A')}%
- Base Rate: {quote.get('base_rate', 'N/A')}%
- LLPAs Applied: {quote.get('llpas_applied', [])}
- Monthly Payment: ${quote.get('monthly_payment', 0):,.2f}
- Total Interest: ${quote.get('total_interest', 0):,.2f}
- Loan Amount: ${quote.get('loan_amount', 0):,}

RATE BREAKDOWN:
{json.dumps(quote.get('rate_breakdown', {}), indent=2)}

CURRENT MARKET CONTEXT:
{rates_context}

Please provide a clear, conversational explanation in this format:

EXPLANATION:
[Explain in 2-3 sentences why they got this specific rate. Include:
- How their credit score affects the rate
- How their down payment (LTV) impacts pricing
- Any other relevant factors
- Compare to current market rates
- Use friendly, non-technical language]

RATE BREAKDOWN:
[Explain each component that makes up their rate:
- Base rate from market
- Credit score adjustments
- LTV adjustments
- Any other fees or adjustments
- Keep it simple and clear]

IMPROVEMENT SUGGESTIONS:
[Provide 1-2 specific, actionable ways they could improve their rate:
- Be specific about what they need to change
- Include the potential rate improvement
- Explain the impact on monthly payment
- Make it realistic and achievable
- Focus on the most impactful changes first]

MARKET CONTEXT:
[Brief note about current market conditions and timing]

Use a warm, helpful tone. Avoid jargon. Make the borrower feel confident about understanding their rate and options.
"""
        
        return prompt
    
    def _parse_analysis_response(self, response_text: str) -> Dict:
        """Parse AI response into structured format."""
        
        analysis = {
            "explanation": "",
            "improvements": [],
            "rate_breakdown": {},
            "market_context": ""
        }
        
        lines = response_text.split('\n')
        current_section = None
        section_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect sections
            if 'EXPLANATION:' in line.upper():
                if current_section and section_content:
                    analysis = self._process_section(current_section, section_content, analysis)
                current_section = 'explanation'
                section_content = []
            elif 'RATE BREAKDOWN:' in line.upper():
                if current_section and section_content:
                    analysis = self._process_section(current_section, section_content, analysis)
                current_section = 'rate_breakdown'
                section_content = []
            elif 'IMPROVEMENT SUGGESTIONS:' in line.upper():
                if current_section and section_content:
                    analysis = self._process_section(current_section, section_content, analysis)
                current_section = 'improvements'
                section_content = []
            elif 'MARKET CONTEXT:' in line.upper():
                if current_section and section_content:
                    analysis = self._process_section(current_section, section_content, analysis)
                current_section = 'market_context'
                section_content = []
            elif current_section:
                section_content.append(line)
        
        # Process final section
        if current_section and section_content:
            analysis = self._process_section(current_section, section_content, analysis)
        
        return analysis
    
    def _process_section(self, section: str, content: List[str], analysis: Dict) -> Dict:
        """Process content for a specific section."""
        
        if section == 'explanation':
            analysis['explanation'] = ' '.join(content)
        elif section == 'rate_breakdown':
            analysis['rate_breakdown'] = {
                'description': ' '.join(content),
                'components': self._extract_rate_components(content)
            }
        elif section == 'improvements':
            analysis['improvements'] = self._extract_improvements(content)
        elif section == 'market_context':
            analysis['market_context'] = ' '.join(content)
        
        return analysis
    
    def _extract_rate_components(self, content: List[str]) -> Dict:
        """Extract rate components from content."""
        components = {}
        
        for line in content:
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip().lower()
                    value = parts[1].strip()
                    components[key] = value
        
        return components
    
    def _extract_improvements(self, content: List[str]) -> List[Dict]:
        """Extract improvement suggestions from content."""
        improvements = []
        current_improvement = {}
        
        for line in content:
            line = line.strip()
            if not line:
                continue
            
            # Look for numbered or bulleted improvements
            if (line.startswith('-') or line.startswith('•') or 
                line.startswith('*') or line[0].isdigit()):
                
                if current_improvement:
                    improvements.append(current_improvement)
                
                current_improvement = {
                    'suggestion': line.lstrip('-•*0123456789. '),
                    'impact': '',
                    'action': ''
                }
            elif current_improvement and line:
                # Additional details for current improvement
                if 'rate' in line.lower() or '%' in line:
                    current_improvement['impact'] = line
                elif 'improve' in line.lower() or 'increase' in line.lower():
                    current_improvement['action'] = line
        
        # Add final improvement
        if current_improvement:
            improvements.append(current_improvement)
        
        return improvements
    
    def generate_quote_summary(self, quote_result: Dict, borrower_profile: Dict) -> str:
        """
        Generate a formatted summary of the quote analysis.
        
        Args:
            quote_result: Result from quote_engine.quote_rate()
            borrower_profile: Dictionary with borrower information
            
        Returns:
            str: Formatted summary
        """
        
        analysis = self.analyze_quote(quote_result, borrower_profile)
        
        if not analysis.get('success'):
            return f"Unable to analyze quote: {analysis.get('error', 'Unknown error')}"
        
        # Format summary
        summary = []
        summary.append("=" * 60)
        summary.append("RATE QUOTE ANALYSIS")
        summary.append("=" * 60)
        summary.append("")
        
        # Borrower info
        summary.append("BORROWER PROFILE:")
        summary.append(f"  Loan Amount: ${borrower_profile.get('loan_amount', 0):,}")
        summary.append(f"  Credit Score: {borrower_profile.get('credit_score', 'N/A')}")
        summary.append(f"  LTV: {borrower_profile.get('ltv', 'N/A')}%")
        summary.append(f"  Loan Type: {borrower_profile.get('loan_type', 'N/A')}")
        summary.append("")
        
        # Quote details
        summary.append("YOUR RATE QUOTE:")
        summary.append(f"  Final Rate: {quote_result.get('final_rate', 'N/A')}%")
        summary.append(f"  Monthly Payment: ${quote_result.get('monthly_payment', 0):,.2f}")
        summary.append(f"  Total Interest: ${quote_result.get('total_interest', 0):,.2f}")
        summary.append("")
        
        # Explanation
        if analysis.get('explanation'):
            summary.append("WHY YOU GOT THIS RATE:")
            summary.append(f"  {analysis['explanation']}")
            summary.append("")
        
        # Rate breakdown
        if analysis.get('rate_breakdown', {}).get('description'):
            summary.append("RATE BREAKDOWN:")
            summary.append(f"  {analysis['rate_breakdown']['description']}")
            summary.append("")
        
        # Improvement suggestions
        if analysis.get('improvement_suggestions'):
            summary.append("WAYS TO IMPROVE YOUR RATE:")
            for i, improvement in enumerate(analysis['improvement_suggestions'], 1):
                summary.append(f"  {i}. {improvement.get('suggestion', '')}")
                if improvement.get('impact'):
                    summary.append(f"     Impact: {improvement['impact']}")
                if improvement.get('action'):
                    summary.append(f"     Action: {improvement['action']}")
                summary.append("")
        
        # Market context
        if analysis.get('market_context'):
            summary.append("MARKET CONTEXT:")
            summary.append(f"  {analysis['market_context']}")
            summary.append("")
        
        summary.append("=" * 60)
        
        return '\n'.join(summary)


def analyze_quote(quote_result: Dict, borrower_profile: Dict) -> Dict:
    """
    Main function to analyze a rate quote.
    
    Args:
        quote_result: Result from quote_engine.quote_rate()
        borrower_profile: Dictionary with borrower information
        
    Returns:
        Dict: Analysis results
    """
    
    analyzer = GeminiRateAnalyzer()
    return analyzer.analyze_quote(quote_result, borrower_profile)


def generate_quote_summary(quote_result: Dict, borrower_profile: Dict) -> str:
    """
    Generate a formatted quote summary.
    
    Args:
        quote_result: Result from quote_engine.quote_rate()
        borrower_profile: Dictionary with borrower information
        
    Returns:
        str: Formatted summary
    """
    
    analyzer = GeminiRateAnalyzer()
    return analyzer.generate_quote_summary(quote_result, borrower_profile)


if __name__ == "__main__":
    # Test the analyzer
    print("=== Testing Gemini Rate Analyzer ===\n")
    
    # Import quote engine for testing
    from quote_engine import quote_rate
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'rate_ingest'))
    from gemini_rate_integration import GeminiRateIntegration
    
    # Get current rates
    rate_integration = GeminiRateIntegration()
    current_rates = rate_integration.scheduler.get_current_rates()
    
    if not current_rates:
        print("No current rates available. Please run the rate scheduler first.")
        exit(1)
    
    # Test scenario
    loan_amount = 500000
    credit_score = 680
    ltv = 85
    loan_type = "30yr_fixed"
    
    print(f"Analyzing quote for:")
    print(f"  Loan Amount: ${loan_amount:,}")
    print(f"  Credit Score: {credit_score}")
    print(f"  LTV: {ltv}%")
    print(f"  Loan Type: {loan_type}")
    print()
    
    # Get quote
    quote_result = quote_rate(loan_amount, credit_score, ltv, loan_type, current_rates)
    
    if quote_result.get('error'):
        print(f"Error getting quote: {quote_result['error_message']}")
        exit(1)
    
    # Borrower profile
    borrower_profile = {
        "loan_amount": loan_amount,
        "credit_score": credit_score,
        "ltv": ltv,
        "loan_type": loan_type,
        "property_type": "Primary Residence",
        "occupancy": "Owner Occupied"
    }
    
    # Analyze quote
    analysis = analyze_quote(quote_result, borrower_profile)
    
    if analysis.get('success'):
        print("ANALYSIS RESULTS:")
        print(f"Explanation: {analysis['explanation']}")
        print()
        
        if analysis.get('improvement_suggestions'):
            print("IMPROVEMENT SUGGESTIONS:")
            for i, improvement in enumerate(analysis['improvement_suggestions'], 1):
                print(f"{i}. {improvement.get('suggestion', '')}")
                if improvement.get('impact'):
                    print(f"   Impact: {improvement['impact']}")
        print()
        
        # Generate full summary
        print("FULL SUMMARY:")
        summary = generate_quote_summary(quote_result, borrower_profile)
        print(summary)
    else:
        print(f"Analysis failed: {analysis.get('error', 'Unknown error')}") 