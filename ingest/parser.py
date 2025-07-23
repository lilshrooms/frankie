from typing import Dict, List, Optional
from datetime import datetime
import re


def normalize_zillow_rates(raw_data: List[Dict]) -> List[Dict]:
    """
    Normalize scraped Zillow rate data into standardized format.
    
    Args:
        raw_data (List[Dict]): Raw rate data from Zillow scraper
        
    Returns:
        List[Dict]: Standardized rate objects
    """
    normalized_rates = []
    
    for rate_data in raw_data:
        try:
            # Extract and validate required fields
            loan_type = _normalize_loan_type(rate_data.get('product', ''))
            rate = _validate_rate(rate_data.get('rate'))
            apr = _validate_rate(rate_data.get('apr'))
            
            if not all([loan_type, rate, apr]):
                continue
            
            # Determine lock period based on loan type
            lock_period = _determine_lock_period(loan_type)
            
            # Create standardized rate object
            normalized_rate = {
                "loan_type": loan_type,
                "rate": rate,
                "apr": apr,
                "lock_period": lock_period,
                "source": "zillow",
                "timestamp": rate_data.get('timestamp', datetime.now().isoformat()),
                "fees": rate_data.get('fees', 0)  # Optional field
            }
            
            normalized_rates.append(normalized_rate)
            
        except Exception as e:
            print(f"Error normalizing rate data: {e}")
            continue
    
    return normalized_rates


def _normalize_loan_type(product: str) -> Optional[str]:
    """
    Normalize loan product type to standard format.
    
    Args:
        product (str): Raw product type from scraper
        
    Returns:
        Optional[str]: Normalized loan type or None if invalid
    """
    if not product:
        return None
    
    product_lower = product.lower().strip()
    
    # Map various product names to standard types
    loan_type_mapping = {
        # 30-year fixed variations
        '30yr_fixed': '30yr_fixed',
        '30_year_fixed': '30yr_fixed',
        '30-year_fixed': '30yr_fixed',
        '30 year fixed': '30yr_fixed',
        '30yr': '30yr_fixed',
        '30_year': '30yr_fixed',
        
        # 15-year fixed variations
        '15yr_fixed': '15yr_fixed',
        '15_year_fixed': '15yr_fixed',
        '15-year-fixed': '15yr_fixed',
        '15 year fixed': '15yr_fixed',
        '15yr': '15yr_fixed',
        '15_year': '15yr_fixed',
        
        # FHA variations
        'fha_30yr': 'fha_30yr',
        'fha_30_year': 'fha_30yr',
        'fha_30-year': 'fha_30yr',
        'fha': 'fha_30yr',
        
        # VA variations
        'va_30yr': 'va_30yr',
        'va_30_year': 'va_30yr',
        'va_30-year': 'va_30yr',
        'va': 'va_30yr',
        
        # Jumbo variations
        'jumbo_30yr': 'jumbo_30yr',
        'jumbo_30_year': 'jumbo_30yr',
        'jumbo_30-year': 'jumbo_30yr',
        'jumbo': 'jumbo_30yr',
        
        # ARM variations
        '5_1_arm': '5_1_arm',
        '7_1_arm': '7_1_arm',
        '10_1_arm': '10_1_arm',
        '5/1_arm': '5_1_arm',
        '7/1_arm': '7_1_arm',
        '10/1_arm': '10_1_arm',
    }
    
    # Try exact match first
    if product_lower in loan_type_mapping:
        return loan_type_mapping[product_lower]
    
    # Try partial matching
    for key, value in loan_type_mapping.items():
        if key in product_lower or product_lower in key:
            return value
    
    # Try regex matching for common patterns
    if re.search(r'30.*year.*fixed', product_lower):
        return '30yr_fixed'
    elif re.search(r'15.*year.*fixed', product_lower):
        return '15yr_fixed'
    elif re.search(r'fha', product_lower):
        return 'fha_30yr'
    elif re.search(r'va', product_lower):
        return 'va_30yr'
    elif re.search(r'jumbo', product_lower):
        return 'jumbo_30yr'
    elif re.search(r'5.*1.*arm', product_lower):
        return '5_1_arm'
    elif re.search(r'7.*1.*arm', product_lower):
        return '7_1_arm'
    elif re.search(r'10.*1.*arm', product_lower):
        return '10_1_arm'
    
    return None


def _validate_rate(rate_value) -> Optional[float]:
    """
    Validate and convert rate value to float.
    
    Args:
        rate_value: Rate value from scraper
        
    Returns:
        Optional[float]: Validated rate or None if invalid
    """
    if rate_value is None:
        return None
    
    try:
        rate = float(rate_value)
        
        # Check if rate is in reasonable range (0.1% to 20%)
        if 0.1 <= rate <= 20.0:
            return round(rate, 3)  # Round to 3 decimal places
        else:
            return None
            
    except (ValueError, TypeError):
        return None


def _determine_lock_period(loan_type: str) -> int:
    """
    Determine lock period in days based on loan type.
    
    Args:
        loan_type (str): Normalized loan type
        
    Returns:
        int: Lock period in days
    """
    # Standard lock periods for different loan types
    lock_periods = {
        '30yr_fixed': 30,
        '15yr_fixed': 30,
        'fha_30yr': 30,
        'va_30yr': 30,
        'jumbo_30yr': 30,
        '5_1_arm': 30,
        '7_1_arm': 30,
        '10_1_arm': 30,
    }
    
    return lock_periods.get(loan_type, 30)  # Default to 30 days


def filter_rates_by_type(rates: List[Dict], loan_types: List[str] = None) -> List[Dict]:
    """
    Filter rates by loan type.
    
    Args:
        rates (List[Dict]): List of normalized rates
        loan_types (List[str]): List of loan types to include (None for all)
        
    Returns:
        List[Dict]: Filtered rates
    """
    if not loan_types:
        return rates
    
    return [rate for rate in rates if rate.get('loan_type') in loan_types]


def get_latest_rates(rates: List[Dict], limit: int = 5) -> List[Dict]:
    """
    Get the most recent rates, sorted by timestamp.
    
    Args:
        rates (List[Dict]): List of normalized rates
        limit (int): Maximum number of rates to return
        
    Returns:
        List[Dict]: Latest rates
    """
    # Sort by timestamp (newest first)
    sorted_rates = sorted(
        rates, 
        key=lambda x: x.get('timestamp', ''), 
        reverse=True
    )
    
    return sorted_rates[:limit]


def calculate_rate_stats(rates: List[Dict]) -> Dict:
    """
    Calculate statistics for a list of rates.
    
    Args:
        rates (List[Dict]): List of normalized rates
        
    Returns:
        Dict: Rate statistics
    """
    if not rates:
        return {}
    
    # Group by loan type
    rates_by_type = {}
    for rate in rates:
        loan_type = rate.get('loan_type')
        if loan_type not in rates_by_type:
            rates_by_type[loan_type] = []
        rates_by_type[loan_type].append(rate)
    
    stats = {}
    for loan_type, type_rates in rates_by_type.items():
        rates_list = [r.get('rate', 0) for r in type_rates]
        aprs_list = [r.get('apr', 0) for r in type_rates]
        
        if rates_list:
            stats[loan_type] = {
                'count': len(type_rates),
                'min_rate': min(rates_list),
                'max_rate': max(rates_list),
                'avg_rate': sum(rates_list) / len(rates_list),
                'min_apr': min(aprs_list),
                'max_apr': max(aprs_list),
                'avg_apr': sum(aprs_list) / len(aprs_list),
            }
    
    return stats


if __name__ == "__main__":
    # Test with sample data
    sample_raw_data = [
        {
            "product": "30yr_fixed",
            "rate": 6.75,
            "apr": 6.91,
            "fees": 1500,
            "source": "zillow",
            "timestamp": "2025-01-23T10:00:00Z"
        },
        {
            "product": "15yr_fixed",
            "rate": 6.25,
            "apr": 6.42,
            "fees": 1200,
            "source": "zillow",
            "timestamp": "2025-01-23T10:00:00Z"
        },
        {
            "product": "fha_30yr",
            "rate": 6.50,
            "apr": 6.67,
            "fees": 2000,
            "source": "zillow",
            "timestamp": "2025-01-23T10:00:00Z"
        }
    ]
    
    print("Testing rate normalization...")
    normalized = normalize_zillow_rates(sample_raw_data)
    
    print(f"Normalized {len(normalized)} rates:")
    for rate in normalized:
        print(f"  {rate['loan_type']}: {rate['rate']}% (APR: {rate['apr']}%, Lock: {rate['lock_period']} days)")
    
    # Test filtering
    print("\nFiltering for 30-year fixed rates:")
    filtered = filter_rates_by_type(normalized, ['30yr_fixed'])
    for rate in filtered:
        print(f"  {rate['loan_type']}: {rate['rate']}%")
    
    # Test stats
    print("\nRate statistics:")
    stats = calculate_rate_stats(normalized)
    for loan_type, stat in stats.items():
        print(f"  {loan_type}: Avg rate {stat['avg_rate']:.3f}%, Avg APR {stat['avg_apr']:.3f}%") 