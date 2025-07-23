#!/usr/bin/env python3
import os
import sys
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from email_ingest.gmail_fetcher import extract_fields_with_gemini, is_mortgage_email
from email_ingest.gemini_analyzer import analyze_with_gemini

def test_full_pipeline():
    # Test with the sample email content
    test_email_body = """
    Hi there,
    
    I have a borrower who is single, buying SFH in SF CA for 400k, needs a 300k loan. Credit score is high 700s.
    
    Including paystub and 1 bank statements.
    
    Thanks!
    """
    
    test_subject = "inbound mortgage request"
    
    print("Testing full email processing pipeline...")
    print(f"Subject: {test_subject}")
    print(f"Email body: {test_email_body}")
    print("\n" + "="*50 + "\n")
    
    # Step 1: Check if it's mortgage-related
    is_mortgage = is_mortgage_email(test_subject, test_email_body)
    print(f"Step 1 - Mortgage detection: {is_mortgage}")
    
    if not is_mortgage:
        print("Email not detected as mortgage-related. Stopping.")
        return
    
    # Step 2: Extract fields from email body
    print("\nStep 2 - Extracting fields from email body...")
    gemini_fields = extract_fields_with_gemini(test_email_body)
    print(f"Extracted fields: {gemini_fields}")
    
    # Step 3: Format extracted fields for analysis
    if gemini_fields and isinstance(gemini_fields, dict):
        formatted_fields = []
        for k, v in gemini_fields.items():
            if v and v != "null" and v != "None":
                formatted_fields.append(f"{k.replace('_', ' ').title()}: {v}")
        pre_extracted_str = '\n'.join(formatted_fields) if formatted_fields else 'None found.'
    else:
        pre_extracted_str = 'None found.'
    
    print(f"\nFormatted extracted fields: {pre_extracted_str}")
    
    # Step 4: Load criteria and run analysis
    print("\nStep 3 - Running full analysis...")
    try:
        with open('../criteria/conventional.yaml', 'r') as f:
            criteria = yaml.safe_load(f)
        
        # Mock attachments (empty for this test)
        parsed_attachments = []
        
        # Run the full analysis
        analysis = analyze_with_gemini(test_email_body, parsed_attachments, criteria, pre_extracted_str)
        
        print("\n" + "="*50)
        print("FINAL ANALYSIS RESULT:")
        print("="*50)
        print(analysis)
        
    except Exception as e:
        print(f"Error in analysis: {e}")

if __name__ == "__main__":
    test_full_pipeline() 