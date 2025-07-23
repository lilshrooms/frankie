from typing import Dict, List, Optional, Tuple
import math


def quote_rate(loan_amount: float, credit_score: int, ltv: float, 
               loan_type: str, rates_data: List[Dict]) -> Dict:
    """
    Calculate the best matching rate quote based on loan parameters and rates data.
    
    Args:
        loan_amount (float): Loan amount in dollars
        credit_score (int): Borrower's credit score (300-850)
        ltv (float): Loan-to-value ratio as percentage (0-100)
        loan_type (str): Type of loan (e.g., '30yr_fixed', '15yr_fixed', 'fha_30yr')
        rates_data (List[Dict]): List of rate data from rate sources
        
    Returns:
        Dict: Quote information including rate, APR, adjustments, and details
    """
    
    # Validate inputs
    if not _validate_inputs(loan_amount, credit_score, ltv, loan_type):
        return _create_error_quote("Invalid input parameters")
    
    # Filter rates by loan type
    matching_rates = _filter_rates_by_type(rates_data, loan_type)
    if not matching_rates:
        return _create_error_quote(f"No rates found for loan type: {loan_type}")
    
    # Get base rate (lowest available rate for the loan type)
    base_rate = _get_base_rate(matching_rates)
    if not base_rate:
        return _create_error_quote("No valid base rate found")
    
    # Calculate LLPAs (Loan Level Price Adjustments)
    llpa_adjustments = _calculate_llpas(credit_score, ltv, loan_type)
    
    # Calculate final rate
    final_rate = base_rate + llpa_adjustments['total_adjustment']
    final_apr = _calculate_apr(final_rate, loan_amount, base_rate, matching_rates)
    
    # Determine if loan is eligible
    is_eligible = _check_eligibility(credit_score, ltv, loan_type)
    
    # Create quote response
    quote = {
        "loan_amount": loan_amount,
        "credit_score": credit_score,
        "ltv": ltv,
        "loan_type": loan_type,
        "base_rate": base_rate,
        "final_rate": round(final_rate, 3),
        "final_apr": round(final_apr, 3),
        "is_eligible": is_eligible,
        "llpa_adjustments": llpa_adjustments,
        "monthly_payment": _calculate_monthly_payment(loan_amount, final_rate, loan_type),
        "total_interest": _calculate_total_interest(loan_amount, final_rate, loan_type),
        "rate_source": matching_rates[0].get('source', 'unknown'),
        "lock_period": matching_rates[0].get('lock_period', 30),
        "timestamp": matching_rates[0].get('timestamp', ''),
        "quote_id": _generate_quote_id()
    }
    
    return quote


def _validate_inputs(loan_amount: float, credit_score: int, ltv: float, loan_type: str) -> bool:
    """Validate input parameters."""
    
    if loan_amount <= 0 or loan_amount > 10000000:  # Max $10M
        return False
    
    if credit_score < 300 or credit_score > 850:
        return False
    
    if ltv <= 0 or ltv > 100:
        return False
    
    valid_loan_types = [
        '30yr_fixed', '15yr_fixed', 'fha_30yr', 'va_30yr', 
        'jumbo_30yr', '5_1_arm', '7_1_arm', '10_1_arm'
    ]
    
    if loan_type not in valid_loan_types:
        return False
    
    return True


def _filter_rates_by_type(rates_data: List[Dict], loan_type: str) -> List[Dict]:
    """Filter rates data by loan type."""
    return [rate for rate in rates_data if rate.get('loan_type') == loan_type]


def _get_base_rate(rates: List[Dict]) -> Optional[float]:
    """Get the lowest (best) rate from the available rates."""
    if not rates:
        return None
    
    valid_rates = [rate.get('rate') for rate in rates if rate.get('rate') is not None]
    if not valid_rates:
        return None
    
    return min(valid_rates)


def _calculate_llpas(credit_score: int, ltv: float, loan_type: str) -> Dict:
    """
    Calculate Loan Level Price Adjustments (LLPAs).
    
    Mock LLPAs:
    - Credit score < 680: +0.125%
    - LTV > 80%: +0.25%
    - Additional adjustments for specific loan types
    """
    
    adjustments = {
        "credit_adjustment": 0.0,
        "ltv_adjustment": 0.0,
        "loan_type_adjustment": 0.0,
        "total_adjustment": 0.0
    }
    
    # Credit score adjustment
    if credit_score < 680:
        adjustments["credit_adjustment"] = 0.125
    elif credit_score < 720:
        adjustments["credit_adjustment"] = 0.0625
    elif credit_score < 760:
        adjustments["credit_adjustment"] = 0.0
    else:
        adjustments["credit_adjustment"] = -0.0625  # Premium for excellent credit
    
    # LTV adjustment
    if ltv > 80:
        adjustments["ltv_adjustment"] = 0.25
    elif ltv > 70:
        adjustments["ltv_adjustment"] = 0.125
    elif ltv > 60:
        adjustments["ltv_adjustment"] = 0.0625
    
    # Loan type specific adjustments
    if loan_type == 'fha_30yr':
        adjustments["loan_type_adjustment"] = 0.375  # FHA typically higher rates
    elif loan_type == 'va_30yr':
        adjustments["loan_type_adjustment"] = 0.125  # VA typically lower rates
    elif loan_type == 'jumbo_30yr':
        adjustments["loan_type_adjustment"] = 0.25   # Jumbo typically higher rates
    elif 'arm' in loan_type:
        adjustments["loan_type_adjustment"] = -0.125  # ARMs typically lower rates
    
    # Calculate total adjustment
    adjustments["total_adjustment"] = (
        adjustments["credit_adjustment"] + 
        adjustments["ltv_adjustment"] + 
        adjustments["loan_type_adjustment"]
    )
    
    return adjustments


def _calculate_apr(base_rate: float, loan_amount: float, final_rate: float, 
                  rates_data: List[Dict]) -> float:
    """
    Calculate APR based on final rate and estimated fees.
    This is a simplified calculation - real APR would include all closing costs.
    """
    
    # Get average fees from rates data
    fees = [rate.get('fees', 2000) for rate in rates_data if rate.get('fees')]
    avg_fees = sum(fees) / len(fees) if fees else 2000
    
    # Simplified APR calculation
    # In reality, APR includes all costs over the life of the loan
    apr = final_rate + (avg_fees / loan_amount) * 100 * 0.1  # Rough approximation
    
    return apr


def _check_eligibility(credit_score: int, ltv: float, loan_type: str) -> bool:
    """Check if the loan meets basic eligibility criteria."""
    
    # Credit score minimums
    min_credit_scores = {
        '30yr_fixed': 620,
        '15yr_fixed': 620,
        'fha_30yr': 580,
        'va_30yr': 620,
        'jumbo_30yr': 700,
        '5_1_arm': 620,
        '7_1_arm': 620,
        '10_1_arm': 620
    }
    
    min_credit = min_credit_scores.get(loan_type, 620)
    if credit_score < min_credit:
        return False
    
    # LTV maximums
    max_ltv = {
        '30yr_fixed': 95,
        '15yr_fixed': 90,
        'fha_30yr': 96.5,
        'va_30yr': 100,
        'jumbo_30yr': 80,
        '5_1_arm': 95,
        '7_1_arm': 95,
        '10_1_arm': 95
    }
    
    max_ltv_allowed = max_ltv.get(loan_type, 95)
    if ltv > max_ltv_allowed:
        return False
    
    return True


def _calculate_monthly_payment(loan_amount: float, rate: float, loan_type: str) -> float:
    """Calculate monthly payment using standard mortgage formula."""
    
    # Determine loan term in years
    term_years = {
        '30yr_fixed': 30,
        '15yr_fixed': 15,
        'fha_30yr': 30,
        'va_30yr': 30,
        'jumbo_30yr': 30,
        '5_1_arm': 30,
        '7_1_arm': 30,
        '10_1_arm': 30
    }
    
    years = term_years.get(loan_type, 30)
    monthly_rate = rate / 100 / 12
    num_payments = years * 12
    
    if monthly_rate == 0:
        return loan_amount / num_payments
    
    # Standard mortgage payment formula
    monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
    
    return round(monthly_payment, 2)


def _calculate_total_interest(loan_amount: float, rate: float, loan_type: str) -> float:
    """Calculate total interest paid over the life of the loan."""
    
    monthly_payment = _calculate_monthly_payment(loan_amount, rate, loan_type)
    
    # Determine loan term in years
    term_years = {
        '30yr_fixed': 30,
        '15yr_fixed': 15,
        'fha_30yr': 30,
        'va_30yr': 30,
        'jumbo_30yr': 30,
        '5_1_arm': 30,
        '7_1_arm': 30,
        '10_1_arm': 30
    }
    
    years = term_years.get(loan_type, 30)
    total_payments = monthly_payment * years * 12
    total_interest = total_payments - loan_amount
    
    return round(total_interest, 2)


def _generate_quote_id() -> str:
    """Generate a unique quote ID."""
    import uuid
    return f"quote_{uuid.uuid4().hex[:8]}"


def _create_error_quote(error_message: str) -> Dict:
    """Create an error quote response."""
    return {
        "error": True,
        "error_message": error_message,
        "loan_amount": 0,
        "credit_score": 0,
        "ltv": 0,
        "loan_type": "",
        "base_rate": 0,
        "final_rate": 0,
        "final_apr": 0,
        "is_eligible": False,
        "llpa_adjustments": {},
        "monthly_payment": 0,
        "total_interest": 0,
        "rate_source": "",
        "lock_period": 0,
        "timestamp": "",
        "quote_id": ""
    }


def get_quote_comparison(loan_amount: float, credit_score: int, ltv: float, 
                        rates_data: List[Dict]) -> Dict:
    """
    Get quotes for all available loan types for comparison.
    
    Args:
        loan_amount (float): Loan amount in dollars
        credit_score (int): Borrower's credit score
        ltv (float): Loan-to-value ratio
        rates_data (List[Dict]): Available rates data
        
    Returns:
        Dict: Comparison of quotes across all loan types
    """
    
    loan_types = ['30yr_fixed', '15yr_fixed', 'fha_30yr', 'va_30yr', 'jumbo_30yr']
    quotes = {}
    
    for loan_type in loan_types:
        quote = quote_rate(loan_amount, credit_score, ltv, loan_type, rates_data)
        if not quote.get('error'):
            quotes[loan_type] = quote
    
    # Sort by final rate
    sorted_quotes = dict(sorted(quotes.items(), key=lambda x: x[1]['final_rate']))
    
    return {
        "loan_amount": loan_amount,
        "credit_score": credit_score,
        "ltv": ltv,
        "quotes": sorted_quotes,
        "best_rate": min([q['final_rate'] for q in quotes.values()]) if quotes else None,
        "best_loan_type": list(sorted_quotes.keys())[0] if sorted_quotes else None
    }


if __name__ == "__main__":
    # Test the quote engine
    sample_rates = [
        {
            "loan_type": "30yr_fixed",
            "rate": 6.75,
            "apr": 6.91,
            "lock_period": 30,
            "source": "zillow",
            "timestamp": "2025-01-23T10:00:00Z",
            "fees": 1500
        },
        {
            "loan_type": "15yr_fixed",
            "rate": 6.25,
            "apr": 6.42,
            "lock_period": 30,
            "source": "zillow",
            "timestamp": "2025-01-23T10:00:00Z",
            "fees": 1200
        },
        {
            "loan_type": "fha_30yr",
            "rate": 6.50,
            "apr": 6.67,
            "lock_period": 30,
            "source": "zillow",
            "timestamp": "2025-01-23T10:00:00Z",
            "fees": 2000
        }
    ]
    
    print("Testing Quote Engine...")
    
    # Test single quote
    quote = quote_rate(500000, 720, 85, "30yr_fixed", sample_rates)
    print(f"\nSingle Quote (30yr fixed, $500k, 720 credit, 85% LTV):")
    print(f"  Base Rate: {quote['base_rate']}%")
    print(f"  Final Rate: {quote['final_rate']}%")
    print(f"  Final APR: {quote['final_apr']}%")
    print(f"  Monthly Payment: ${quote['monthly_payment']:,.2f}")
    print(f"  Total Interest: ${quote['total_interest']:,.2f}")
    print(f"  LLPAs: {quote['llpa_adjustments']}")
    print(f"  Eligible: {quote['is_eligible']}")
    
    # Test quote comparison
    comparison = get_quote_comparison(500000, 720, 85, sample_rates)
    print(f"\nQuote Comparison:")
    for loan_type, quote in comparison['quotes'].items():
        print(f"  {loan_type}: {quote['final_rate']}% (${quote['monthly_payment']:,.2f}/month)")
    
    print(f"\nBest Rate: {comparison['best_rate']}% ({comparison['best_loan_type']})") 