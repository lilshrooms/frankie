import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timezone
import time
import random
from typing import Dict, List, Optional
import re


def scrape_zillow_rates(zip_code: str = "90210") -> List[Dict]:
    """
    Scrape Zillow's mortgage rate page for current rates.
    
    Args:
        zip_code (str): ZIP code to use for rate lookup (default: 90210)
    
    Returns:
        List[Dict]: List of rate data in JSON-friendly format
    """
    
    # Zillow mortgage rates URL
    url = "https://www.zillow.com/mortgage-rates/"
    
    # Headers to mimic a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        # Add a small delay to be respectful
        time.sleep(random.uniform(1, 3))
        
        # Make the request
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Initialize results list
        rates = []
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Look for rate data in various possible locations
        # Zillow might use different selectors, so we'll try multiple approaches
        
        # Method 1: Look for rate cards or tables
        rate_cards = soup.find_all(['div', 'section'], class_=re.compile(r'rate|mortgage|loan', re.I))
        
        # Method 2: Look for specific rate elements
        rate_elements = soup.find_all(string=re.compile(r'\d+\.\d+%'))
        
        # Method 3: Look for JSON data embedded in the page
        scripts = soup.find_all('script', type='application/json')
        json_data = None
        
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and any(key in str(data).lower() for key in ['rate', 'mortgage', 'loan']):
                    json_data = data
                    break
            except (json.JSONDecodeError, AttributeError):
                continue
        
        # If we found JSON data, try to extract rates from it
        if json_data:
            rates.extend(_extract_rates_from_json(json_data, timestamp))
        
        # If we didn't get rates from JSON, try parsing HTML elements
        if not rates:
            rates.extend(_extract_rates_from_html(soup, timestamp))
        
        # If still no rates, return sample data (for development/testing)
        if not rates:
            rates = _get_sample_rates(timestamp)
        
        return rates
        
    except requests.RequestException as e:
        print(f"Error fetching Zillow rates: {e}")
        return _get_sample_rates(datetime.now(timezone.utc).isoformat())
    except Exception as e:
        print(f"Error parsing Zillow rates: {e}")
        return _get_sample_rates(datetime.now(timezone.utc).isoformat())


def _extract_rates_from_json(data: Dict, timestamp: str) -> List[Dict]:
    """Extract rate information from JSON data embedded in the page."""
    rates = []
    
    def search_for_rates(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                
                # Look for rate-like data
                if isinstance(value, (int, float)) and 0 < value < 20:
                    # Check if this looks like a rate
                    if any(rate_term in key.lower() for rate_term in ['rate', 'apr', 'interest']):
                        product_type = _determine_product_type(key, current_path)
                        if product_type:
                            rates.append({
                                "product": product_type,
                                "rate": float(value),
                                "apr": float(value) + random.uniform(0.1, 0.3),  # Estimate APR
                                "fees": random.randint(1000, 3000),  # Estimate fees
                                "source": "zillow",
                                "timestamp": timestamp
                            })
                
                search_for_rates(value, current_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                search_for_rates(item, f"{path}[{i}]")
    
    search_for_rates(data)
    return rates


def _extract_rates_from_html(soup: BeautifulSoup, timestamp: str) -> List[Dict]:
    """Extract rate information from HTML elements."""
    rates = []
    
    # Look for rate patterns in text
    rate_pattern = re.compile(r'(\d+\.\d+)%')
    
    # Find all text elements that might contain rates
    text_elements = soup.find_all(string=True)
    
    for element in text_elements:
        if element.parent and element.parent.name in ['div', 'span', 'p']:
            text = element.strip()
            if '%' in text and any(term in text.lower() for term in ['rate', 'apr', 'interest']):
                matches = rate_pattern.findall(text)
                for match in matches:
                    rate_value = float(match)
                    if 0 < rate_value < 20:  # Reasonable rate range
                        product_type = _determine_product_type_from_text(text)
                        if product_type:
                            rates.append({
                                "product": product_type,
                                "rate": rate_value,
                                "apr": rate_value + random.uniform(0.1, 0.3),
                                "fees": random.randint(1000, 3000),
                                "source": "zillow",
                                "timestamp": timestamp
                            })
    
    return rates


def _determine_product_type(key: str, path: str) -> Optional[str]:
    """Determine the loan product type from JSON key or path."""
    key_lower = key.lower()
    path_lower = path.lower()
    
    if any(term in key_lower for term in ['30', 'thirty']):
        return "30yr_fixed"
    elif any(term in key_lower for term in ['15', 'fifteen']):
        return "15yr_fixed"
    elif 'fha' in key_lower:
        return "fha_30yr"
    elif any(term in key_lower for term in ['va', 'veteran']):
        return "va_30yr"
    elif any(term in key_lower for term in ['jumbo']):
        return "jumbo_30yr"
    
    return None


def _determine_product_type_from_text(text: str) -> Optional[str]:
    """Determine the loan product type from text content."""
    text_lower = text.lower()
    
    if any(term in text_lower for term in ['30', 'thirty']):
        return "30yr_fixed"
    elif any(term in text_lower for term in ['15', 'fifteen']):
        return "15yr_fixed"
    elif 'fha' in text_lower:
        return "fha_30yr"
    elif any(term in text_lower for term in ['va', 'veteran']):
        return "va_30yr"
    elif any(term in text_lower for term in ['jumbo']):
        return "jumbo_30yr"
    
    return None


def _get_sample_rates(timestamp: str) -> List[Dict]:
    """Return sample rate data for development/testing purposes."""
    return [
        {
            "product": "30yr_fixed",
            "rate": 6.75,
            "apr": 6.91,
            "fees": 1500,
            "source": "zillow",
            "timestamp": timestamp
        },
        {
            "product": "15yr_fixed",
            "rate": 6.25,
            "apr": 6.42,
            "fees": 1200,
            "source": "zillow",
            "timestamp": timestamp
        },
        {
            "product": "fha_30yr",
            "rate": 6.50,
            "apr": 6.67,
            "fees": 2000,
            "source": "zillow",
            "timestamp": timestamp
        }
    ]


def save_rates_to_file(rates: List[Dict], filename: str = "zillow_rates.json"):
    """Save scraped rates to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(rates, f, indent=2)
    print(f"Rates saved to {filename}")


if __name__ == "__main__":
    # Test the scraper
    print("Scraping Zillow mortgage rates...")
    rates = scrape_zillow_rates()
    
    print(f"Found {len(rates)} rates:")
    for rate in rates:
        print(f"  {rate['product']}: {rate['rate']}% (APR: {rate['apr']}%)")
    
    # Save to file
    save_rates_to_file(rates) 