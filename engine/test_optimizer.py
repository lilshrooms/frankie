#!/usr/bin/env python3
"""
Comprehensive test script for the Rate Optimizer
Shows detailed optimization results and analysis.
"""

from optimizer import optimize_scenario
import json


def test_optimizer_comprehensive():
    """Test the optimizer with comprehensive output."""
    
    print("=== Comprehensive Rate Optimizer Test ===\n")
    
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
        
        result = optimize_scenario(
            scenario['loan_amount'],
            scenario['credit_score'],
            scenario['ltv'],
            scenario['loan_type']
        )
        
        if result.get('error'):
            print(f"Error: {result['message']}")
            continue
        
        # Current scenario
        current = result['current_scenario']
        print(f"Current Scenario:")
        print(f"  Rate: {current['final_rate']}%")
        print(f"  Monthly Payment: ${current['monthly_payment']:,.2f}")
        print(f"  Total Interest: ${current['total_interest']:,.2f}")
        print()
        
        # Summary
        summary = result['summary']
        print(f"Total Potential Savings: ${summary['total_potential_savings']:,.2f}")
        print()
        
        # Credit score optimizations
        credit_opts = result.get('credit_score_optimizations', [])
        if credit_opts:
            print("Credit Score Optimizations:")
            for opt in credit_opts:
                print(f"  Improve to {opt['target_value']} ({opt['description']}):")
                print(f"    Rate savings: {opt['rate_savings']}%")
                print(f"    Monthly savings: ${opt['monthly_savings']:,.2f}")
                print(f"    Total savings: ${opt['total_savings']:,.2f}")
                print(f"    Feasibility: {opt['feasibility']}")
                print(f"    Timeframe: {opt['timeframe']}")
                print()
        
        # LTV optimizations
        ltv_opts = result.get('ltv_optimizations', [])
        if ltv_opts:
            print("LTV Optimizations:")
            for opt in ltv_opts:
                print(f"  Reduce LTV to {opt['target_value']}% ({opt['description']}):")
                print(f"    Rate savings: {opt['rate_savings']}%")
                print(f"    Monthly savings: ${opt['monthly_savings']:,.2f}")
                print(f"    Total savings: ${opt['total_savings']:,.2f}")
                print(f"    Additional down payment: ${opt['additional_down_payment']:,.2f}")
                print(f"    ROI: {opt['roi_analysis']['roi_percentage']}%")
                print(f"    Payback period: {opt['roi_analysis']['payback_period']} years")
                print(f"    Feasibility: {opt['feasibility']}")
                print()
        
        # Loan amount optimizations
        amount_opts = result.get('loan_amount_optimizations', [])
        if amount_opts:
            print("Loan Amount Optimizations:")
            for opt in amount_opts:
                print(f"  {opt['description']}:")
                print(f"    Reduce by: ${opt['reduction_amount']:,.2f} ({opt['reduction_percentage']}%)")
                print(f"    Monthly savings: ${opt['monthly_savings']:,.2f}")
                print(f"    Total savings: ${opt['total_savings']:,.2f}")
                print(f"    New monthly payment: ${opt['new_monthly_payment']:,.2f}")
                print(f"    Feasibility: {opt['feasibility']}")
                print(f"    Impact: {opt['impact']}")
                print()
        
        # Loan type optimizations
        loan_type_opts = result.get('loan_type_optimizations', [])
        if loan_type_opts:
            print("Loan Type Optimizations:")
            for opt in loan_type_opts:
                print(f"  Switch to {opt['alternative_loan_type']}:")
                print(f"    {opt['description']}")
                print(f"    Rate savings: {opt['rate_savings']}%")
                print(f"    Monthly savings: ${opt['monthly_savings']:,.2f}")
                print(f"    Total savings: ${opt['total_savings']:,.2f}")
                print(f"    New rate: {opt['new_rate']}%")
                print(f"    Feasibility: {opt['feasibility']}")
                print(f"    Considerations: {', '.join(opt['considerations'])}")
                print()
        
        # Top recommendations
        print("Top Recommendations:")
        for i, rec in enumerate(summary['recommendations'][:3], 1):
            print(f"{i}. {rec}")
        print()
        
        # Quick wins vs long-term improvements
        quick_wins = summary.get('quick_wins', [])
        long_term = summary.get('long_term_improvements', [])
        
        if quick_wins:
            print("Quick Wins (Immediate Impact):")
            for win in quick_wins:
                print(f"  {win['description']}: ${win['savings']:,.0f} savings")
            print()
        
        if long_term:
            print("Long-term Improvements:")
            for improvement in long_term:
                print(f"  {improvement['description']}: ${improvement['savings']:,.0f} savings")
            print()
        
        print("=" * 60)
        print()


def test_specific_optimization():
    """Test a specific optimization scenario."""
    
    print("=== Specific Optimization Test ===\n")
    
    # Test a specific scenario
    loan_amount = 500000
    credit_score = 680
    ltv = 85
    
    print(f"Testing LTV optimization:")
    print(f"  Current LTV: {ltv}%")
    print(f"  Target LTV: 80%")
    print()
    
    result = optimize_scenario(loan_amount, credit_score, ltv)
    
    if not result.get('error'):
        ltv_opts = result.get('ltv_optimizations', [])
        for opt in ltv_opts:
            if opt['target_value'] == 80:
                print(f"LTV Optimization to 80%:")
                print(f"  Current rate: {result['current_scenario']['final_rate']}%")
                print(f"  New rate: {opt['new_rate']}%")
                print(f"  Rate reduction: {opt['rate_savings']}%")
                print(f"  Monthly savings: ${opt['monthly_savings']:,.2f}")
                print(f"  Total savings: ${opt['total_savings']:,.2f}")
                print(f"  Additional down payment needed: ${opt['additional_down_payment']:,.2f}")
                print(f"  ROI: {opt['roi_analysis']['roi_percentage']}%")
                print(f"  Payback period: {opt['roi_analysis']['payback_period']} years")
                print()
                
                # Calculate property value
                property_value = loan_amount / (ltv / 100)
                print(f"Property Value: ${property_value:,.2f}")
                print(f"Current Down Payment: ${property_value - loan_amount:,.2f}")
                print(f"New Down Payment: ${opt['additional_down_payment'] + (property_value - loan_amount):,.2f}")


if __name__ == "__main__":
    # Run comprehensive test
    test_optimizer_comprehensive()
    
    # Run specific test
    test_specific_optimization() 