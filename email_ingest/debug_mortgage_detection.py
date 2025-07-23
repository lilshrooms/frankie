#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from email_ingest.gmail_fetcher import is_mortgage_email

def debug_mortgage_detection():
    test_email_body = """
    Hi there,
    
    I have a borrower who is single, buying SFH in SF CA for 400k, needs a 300k loan. Credit score is high 700s.
    
    Including paystub and 1 bank statements.
    
    Thanks!
    """
    
    test_subject = "inbound mortgage request"
    
    print("Debugging mortgage detection...")
    print(f"Subject: '{test_subject}'")
    print(f"Body: '{test_email_body}'")
    
    subject_lower = test_subject.lower()
    body_lower = test_email_body.lower()
    text = subject_lower + " " + body_lower
    
    print(f"\nCombined text: '{text}'")
    
    # Check for "mortgage" in subject
    print(f"\n'mortgage' in subject_lower: {'mortgage' in subject_lower}")
    
    # Check strong mortgage indicators
    strong_mortgage_indicators = [
        'credit score', 'buy a home', 'purchase home', 'mortgage loan', 'loan request',
        'home loan', 'mortgage application', 'loan application', 'pre-approval',
        'prequalification', 'underwriting', 'borrower', 'property address',
        'closing disclosure', 'settlement statement', 'good faith estimate', 'loan estimate',
        'down payment', 'earnest money', 'appraisal', 'credit report',
        'income verification', 'bank statement', 'w-2', 'pay stub', 'asset statement',
        'purchase contract', 'sales contract', 'real estate agent', 'mls',
        'fha', 'va', 'usda', 'conventional', 'jumbo', 'non-qm', 'conforming',
        'commitment letter', 'clear to close', 'heloc', 'home equity',
        'mortgage inbound', 'process mortgage', 'mortgage inquiry', 'mortgage request',
        'mortgage lead', 'mortgage application', 'mortgage pre-approval', 'mortgage prequal',
        'mortgage pre-qual', 'mortgage prequalification', 'mortgage pre-qualification', 'refi', 'refinance', 
        'refinancing', 'refinance loan', 'refinance mortgage', 'refinance mortgage loan', 'refinance mortgage application', 'refinance loan application', 'refinance pre-approval', 
        'refinance prequalification', 'refinance underwriting', 'refinance borrower', 'refinance property address', 'refinancing closing disclosure', 'refinancing settlement statement', 'refinancing good faith estimate', 'refinancing loan estimate', 'refinancing down payment', 'refinancing earnest money', 'refinancing appraisal', 'refinancing credit report', 'refinancing income verification', 'refinancing bank statement', 'refinancing w-2', 'refinancing pay stub', 'refinancing asset statement', 'refinancing purchase contract', 'refinancing sales contract', 'refinancing real estate agent', 'refinancing mls', 'refinancing fha', 'refinancing va', 'refinancing usda', 'refinancing conventional', 'refinancing jumbo', 'refinancing non-qm', 'refinancing conforming', 'refinancing commitment letter', 'refinancing clear to close', 'refinancing heloc', 'refinancing home equity'
    ]
    
    # Check subject indicators
    subject_mortgage_count = sum(1 for keyword in strong_mortgage_indicators if keyword in subject_lower)
    print(f"\nSubject mortgage indicators found: {subject_mortgage_count}")
    
    # Check body indicators
    body_mortgage_count = sum(1 for keyword in strong_mortgage_indicators if keyword in body_lower)
    print(f"Body mortgage indicators found: {body_mortgage_count}")
    
    # Show which indicators were found
    found_in_subject = [keyword for keyword in strong_mortgage_indicators if keyword in subject_lower]
    found_in_body = [keyword for keyword in strong_mortgage_indicators if keyword in body_lower]
    
    print(f"\nFound in subject: {found_in_subject}")
    print(f"Found in body: {found_in_body}")
    
    # Test the actual function
    result = is_mortgage_email(test_subject, test_email_body)
    print(f"\nFinal result: {result}")

if __name__ == "__main__":
    debug_mortgage_detection() 