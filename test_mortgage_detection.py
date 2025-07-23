#!/usr/bin/env python3
"""
Quick test for mortgage detection
"""

from email_ingest.gmail_fetcher import is_mortgage_email

def test_mortgage_detection():
    test_cases = [
        {
            "subject": "process this mortgage inbound via our website",
            "body": "",
            "expected": True,
            "description": "Mortgage inbound email"
        },
        {
            "subject": "homeowner with 740 credit score looking to buy a $500K home",
            "body": "",
            "expected": True,
            "description": "Credit score email"
        },
        {
            "subject": "Top co-founder profile picks for the week",
            "body": "Some startup content",
            "expected": False,
            "description": "YC startup email"
        }
    ]
    
    print("Testing mortgage email detection:")
    print("=" * 50)
    
    for i, test in enumerate(test_cases, 1):
        result = is_mortgage_email(test["subject"], test["body"])
        status = "✓" if result == test["expected"] else "✗"
        print(f"{status} Test {i}: {test['description']}")
        print(f"   Subject: {test['subject']}")
        print(f"   Expected: {test['expected']}, Got: {result}")
        print()

if __name__ == "__main__":
    test_mortgage_detection() 