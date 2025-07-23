#!/usr/bin/env python3
"""
Test script to demonstrate the complete Zillow rate scraping and parsing workflow.
"""

from zillow_scraper import scrape_zillow_rates, save_rates_to_file
from parser import normalize_zillow_rates, filter_rates_by_type, calculate_rate_stats
import json


def main():
    print("=== Zillow Rate Scraping & Parsing Workflow ===\n")
    
    # Step 1: Scrape rates from Zillow
    print("1. Scraping rates from Zillow...")
    raw_rates = scrape_zillow_rates()
    print(f"   Found {len(raw_rates)} raw rate entries")
    
    # Step 2: Save raw data
    print("\n2. Saving raw data...")
    save_rates_to_file(raw_rates, "raw_zillow_rates.json")
    
    # Step 3: Normalize the rates
    print("\n3. Normalizing rates...")
    normalized_rates = normalize_zillow_rates(raw_rates)
    print(f"   Normalized {len(normalized_rates)} rates")
    
    # Step 4: Display normalized rates
    print("\n4. Normalized Rate Data:")
    for rate in normalized_rates:
        print(f"   {rate['loan_type']}: {rate['rate']}% (APR: {rate['apr']}%, Lock: {rate['lock_period']} days)")
    
    # Step 5: Filter by loan type
    print("\n5. Filtering for 30-year fixed rates:")
    fixed_30yr = filter_rates_by_type(normalized_rates, ['30yr_fixed'])
    for rate in fixed_30yr:
        print(f"   {rate['loan_type']}: {rate['rate']}%")
    
    # Step 6: Calculate statistics
    print("\n6. Rate Statistics:")
    stats = calculate_rate_stats(normalized_rates)
    for loan_type, stat in stats.items():
        print(f"   {loan_type}:")
        print(f"     Count: {stat['count']}")
        print(f"     Rate Range: {stat['min_rate']:.3f}% - {stat['max_rate']:.3f}%")
        print(f"     Average Rate: {stat['avg_rate']:.3f}%")
        print(f"     Average APR: {stat['avg_apr']:.3f}%")
    
    # Step 7: Save normalized data
    print("\n7. Saving normalized data...")
    with open("normalized_rates.json", 'w') as f:
        json.dump(normalized_rates, f, indent=2)
    print("   Saved to normalized_rates.json")
    
    print("\n=== Workflow Complete ===")
    print(f"Raw data: raw_zillow_rates.json")
    print(f"Normalized data: normalized_rates.json")


if __name__ == "__main__":
    main() 