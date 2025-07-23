#!/usr/bin/env python3
"""
Test the quote engine with real rates from Zillow scraper.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'rate_ingest'))

from zillow_scraper import scrape_zillow_rates
from parser import normalize_zillow_rates
from quote_engine import quote_rate, get_quote_comparison


def main():
    print("=== Testing Quote Engine with Real Zillow Rates ===\n")
    
    # Step 1: Scrape real rates from Zillow
    print("1. Scraping rates from Zillow...")
    raw_rates = scrape_zillow_rates()
    print(f"   Found {len(raw_rates)} raw rate entries")
    
    # Step 2: Normalize the rates
    print("\n2. Normalizing rates...")
    normalized_rates = normalize_zillow_rates(raw_rates)
    print(f"   Normalized {len(normalized_rates)} rates")
    
    # Display available rates
    print("\n3. Available Rates:")
    for rate in normalized_rates:
        print(f"   {rate['loan_type']}: {rate['rate']}% (APR: {rate['apr']}%)")
    
    # Step 3: Test different scenarios
    test_scenarios = [
        {
            "name": "High Credit, Low LTV",
            "loan_amount": 500000,
            "credit_score": 780,
            "ltv": 70,
            "loan_type": "30yr_fixed"
        },
        {
            "name": "Low Credit, High LTV",
            "loan_amount": 400000,
            "credit_score": 650,
            "ltv": 90,
            "loan_type": "30yr_fixed"
        },
        {
            "name": "FHA Loan",
            "loan_amount": 350000,
            "credit_score": 620,
            "ltv": 95,
            "loan_type": "fha_30yr"
        },
        {
            "name": "Jumbo Loan",
            "loan_amount": 800000,
            "credit_score": 750,
            "ltv": 75,
            "loan_type": "jumbo_30yr"
        }
    ]
    
    print("\n4. Testing Different Scenarios:")
    for scenario in test_scenarios:
        print(f"\n--- {scenario['name']} ---")
        print(f"Loan: ${scenario['loan_amount']:,}, Credit: {scenario['credit_score']}, LTV: {scenario['ltv']}%")
        
        quote = quote_rate(
            scenario['loan_amount'],
            scenario['credit_score'],
            scenario['ltv'],
            scenario['loan_type'],
            normalized_rates
        )
        
        if quote.get('error'):
            print(f"  Error: {quote['error_message']}")
        else:
            print(f"  Base Rate: {quote['base_rate']}%")
            print(f"  Final Rate: {quote['final_rate']}%")
            print(f"  Final APR: {quote['final_apr']}%")
            print(f"  Monthly Payment: ${quote['monthly_payment']:,.2f}")
            print(f"  Total Interest: ${quote['total_interest']:,.2f}")
            print(f"  LLPAs: {quote['llpa_adjustments']}")
            print(f"  Eligible: {quote['is_eligible']}")
    
    # Step 4: Test quote comparison
    print(f"\n5. Quote Comparison (${500000:,}, 720 credit, 85% LTV):")
    comparison = get_quote_comparison(500000, 720, 85, normalized_rates)
    
    if comparison['quotes']:
        for loan_type, quote in comparison['quotes'].items():
            print(f"  {loan_type}: {quote['final_rate']}% (${quote['monthly_payment']:,.2f}/month)")
        
        print(f"\nBest Rate: {comparison['best_rate']}% ({comparison['best_loan_type']})")
    else:
        print("  No quotes available for comparison")
    
    # Step 5: Test edge cases
    print(f"\n6. Testing Edge Cases:")
    
    # Invalid credit score
    quote = quote_rate(500000, 200, 80, "30yr_fixed", normalized_rates)
    print(f"  Low credit (200): {'Error' if quote.get('error') else 'Unexpected success'}")
    
    # Invalid LTV
    quote = quote_rate(500000, 720, 110, "30yr_fixed", normalized_rates)
    print(f"  High LTV (110%): {'Error' if quote.get('error') else 'Unexpected success'}")
    
    # Invalid loan type
    quote = quote_rate(500000, 720, 80, "invalid_type", normalized_rates)
    print(f"  Invalid loan type: {'Error' if quote.get('error') else 'Unexpected success'}")
    
    print("\n=== Test Complete ===")


if __name__ == "__main__":
    main() 