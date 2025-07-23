#!/usr/bin/env python3
"""
Test script for Gemini Rate Analyzer with real API key.
This script shows how to use the analyzer with a Google Gemini API key.
"""

import os
from analyzer import analyze_quote, generate_quote_summary
from quote_engine import quote_rate
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'rate_ingest'))
from gemini_rate_integration import GeminiRateIntegration


def test_analyzer_with_api():
    """Test the analyzer with a real API key."""
    
    print("=== Testing Gemini Rate Analyzer with API ===\n")
    
    # Check for API key
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("❌ No Google API key found!")
        print("To test with real AI analysis:")
        print("1. Get a Google Gemini API key from: https://makersuite.google.com/app/apikey")
        print("2. Set the environment variable:")
        print("   export GOOGLE_API_KEY='your-api-key-here'")
        print("3. Run this script again")
        print()
        print("Running with mock analysis instead...")
        return test_analyzer_mock()
    
    print("✅ Google API key found!")
    print()
    
    # Get current rates
    rate_integration = GeminiRateIntegration()
    current_rates = rate_integration.scheduler.get_current_rates()
    
    if not current_rates:
        print("❌ No current rates available. Please run the rate scheduler first.")
        return
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Average Borrower",
            "loan_amount": 400000,
            "credit_score": 680,
            "ltv": 85,
            "loan_type": "30yr_fixed"
        },
        {
            "name": "High Credit Borrower",
            "loan_amount": 600000,
            "credit_score": 750,
            "ltv": 75,
            "loan_type": "30yr_fixed"
        },
        {
            "name": "First Time Buyer",
            "loan_amount": 300000,
            "credit_score": 650,
            "ltv": 90,
            "loan_type": "30yr_fixed"
        }
    ]
    
    for scenario in test_scenarios:
        print(f"--- {scenario['name']} ---")
        print(f"Loan Amount: ${scenario['loan_amount']:,}")
        print(f"Credit Score: {scenario['credit_score']}")
        print(f"LTV: {scenario['ltv']}%")
        print()
        
        # Get quote
        quote_result = quote_rate(
            scenario['loan_amount'],
            scenario['credit_score'],
            scenario['ltv'],
            scenario['loan_type'],
            current_rates
        )
        
        if quote_result.get('error'):
            print(f"❌ Error getting quote: {quote_result['error_message']}")
            continue
        
        # Create borrower profile
        borrower_profile = {
            "loan_amount": scenario['loan_amount'],
            "credit_score": scenario['credit_score'],
            "ltv": scenario['ltv'],
            "loan_type": scenario['loan_type'],
            "property_type": "Primary Residence",
            "occupancy": "Owner Occupied"
        }
        
        # Analyze quote
        print("🤖 Analyzing with Gemini AI...")
        analysis = analyze_quote(quote_result, borrower_profile)
        
        if analysis.get('success'):
            print("✅ Analysis completed!")
            print()
            
            # Show results
            print(f"Current Rate: {quote_result['final_rate']}%")
            print(f"Monthly Payment: ${quote_result['monthly_payment']:,.2f}")
            print()
            
            if analysis.get('explanation'):
                print("📝 EXPLANATION:")
                print(f"  {analysis['explanation']}")
                print()
            
            if analysis.get('improvement_suggestions'):
                print("💡 IMPROVEMENT SUGGESTIONS:")
                for i, improvement in enumerate(analysis['improvement_suggestions'], 1):
                    print(f"  {i}. {improvement.get('suggestion', '')}")
                    if improvement.get('impact'):
                        print(f"     Impact: {improvement['impact']}")
                    if improvement.get('action'):
                        print(f"     Action: {improvement['action']}")
                    print()
            
            if analysis.get('market_context'):
                print("📊 MARKET CONTEXT:")
                print(f"  {analysis['market_context']}")
                print()
        else:
            print(f"❌ Analysis failed: {analysis.get('error', 'Unknown error')}")
        
        print("=" * 60)
        print()


def test_analyzer_mock():
    """Test the analyzer with mock data (no API key)."""
    
    print("=== Testing with Mock Analysis ===\n")
    
    # Get current rates
    rate_integration = GeminiRateIntegration()
    current_rates = rate_integration.scheduler.get_current_rates()
    
    if not current_rates:
        print("❌ No current rates available. Please run the rate scheduler first.")
        return
    
    # Test single scenario
    loan_amount = 500000
    credit_score = 680
    ltv = 85
    loan_type = "30yr_fixed"
    
    print(f"Testing scenario:")
    print(f"  Loan Amount: ${loan_amount:,}")
    print(f"  Credit Score: {credit_score}")
    print(f"  LTV: {ltv}%")
    print()
    
    # Get quote
    quote_result = quote_rate(loan_amount, credit_score, ltv, loan_type, current_rates)
    
    if quote_result.get('error'):
        print(f"❌ Error getting quote: {quote_result['error_message']}")
        return
    
    # Create borrower profile
    borrower_profile = {
        "loan_amount": loan_amount,
        "credit_score": credit_score,
        "ltv": ltv,
        "loan_type": loan_type,
        "property_type": "Primary Residence",
        "occupancy": "Owner Occupied"
    }
    
    # Analyze quote
    print("🤖 Analyzing (mock mode)...")
    analysis = analyze_quote(quote_result, borrower_profile)
    
    if analysis.get('success'):
        print("✅ Analysis completed!")
        print()
        
        # Show results
        print(f"Current Rate: {quote_result['final_rate']}%")
        print(f"Monthly Payment: ${quote_result['monthly_payment']:,.2f}")
        print()
        
        if analysis.get('explanation'):
            print("📝 EXPLANATION:")
            print(f"  {analysis['explanation']}")
            print()
        
        if analysis.get('improvement_suggestions'):
            print("💡 IMPROVEMENT SUGGESTIONS:")
            for i, improvement in enumerate(analysis['improvement_suggestions'], 1):
                print(f"  {i}. {improvement.get('suggestion', '')}")
                if improvement.get('impact'):
                    print(f"     Impact: {improvement['impact']}")
                if improvement.get('action'):
                    print(f"     Action: {improvement['action']}")
                print()
        
        # Generate full summary
        print("📋 FULL SUMMARY:")
        summary = generate_quote_summary(quote_result, borrower_profile)
        print(summary)
    else:
        print(f"❌ Analysis failed: {analysis.get('error', 'Unknown error')}")


def test_api_integration():
    """Test the API integration."""
    
    print("=== Testing API Integration ===\n")
    
    # This would test the FastAPI endpoints
    print("To test the API:")
    print("1. Start the API server:")
    print("   python analyzer_api.py")
    print()
    print("2. Test the endpoints:")
    print("   curl -X POST 'http://localhost:8002/analyze/quick' \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"loan_amount\": 500000, \"credit_score\": 680, \"ltv\": 85}'")
    print()
    print("3. Visit http://localhost:8002/docs for interactive API documentation")


if __name__ == "__main__":
    # Test with API if available, otherwise use mock
    test_analyzer_with_api()
    
    print("\n" + "=" * 60)
    print()
    
    # Show API integration info
    test_api_integration() 