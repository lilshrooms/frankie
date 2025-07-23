#!/usr/bin/env python3
import os
import sys
import requests
import json

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1/models/gemini-2.5-pro:generateContent?key=' + GEMINI_API_KEY

def extract_fields_with_gemini(email_body):
    # Use Gemini to extract key fields from the email body only
    prompt = f'''
You are a mortgage loan processor extracting key information from an email. Extract the following fields from the email body below:

**CRITICAL FIELDS TO EXTRACT:**
- Credit Score (look for numbers like "700s", "750", "high 700s", "low 600s", etc.)
- Loan Amount (look for amounts like "300k", "$300,000", "300k loan", etc.)
- Purchase Price (look for amounts like "400k", "$400,000", "buying for 400k", etc.)
- Property Type (SFH, condo, townhouse, etc.)
- Occupancy Type (primary, investment, second home)
- Borrower Name(s)
- Property Location (city, state)

**ADDITIONAL FIELDS:**
- Monthly Income
- Monthly Debts
- Down Payment Amount
- Loan Type (Conventional, FHA, VA, etc.)

**EMAIL BODY:**
{email_body}

**INSTRUCTIONS:**
1. Look carefully for any numbers that could be credit scores, loan amounts, or purchase prices
2. Pay attention to phrases like "needs a 300k loan", "buying for 400k", "credit score is high 700s"
3. Return ONLY a valid JSON object with the extracted fields
4. Use null for missing fields
5. For credit scores, extract the actual number or range (e.g., "750" or "700s")

**EXAMPLE OUTPUT:**
{{
  "credit_score": "750",
  "loan_amount": "300000",
  "purchase_price": "400000",
  "property_type": "SFH",
  "occupancy": "primary",
  "borrower_name": "John Doe",
  "property_location": "SF CA",
  "monthly_income": null,
  "monthly_debts": null,
  "down_payment": "100000",
  "loan_type": null
}}

Return ONLY the JSON object, no other text.
'''
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(GEMINI_API_URL, json=data)
    if response.status_code == 200:
        result = response.json()
        text = result['candidates'][0]['content']['parts'][0]['text']
        # Try to parse JSON from Gemini's response
        try:
            # Clean up the response to extract just the JSON
            text = text.strip()
            if text.startswith('```json'):
                text = text[7:]
            if text.endswith('```'):
                text = text[:-3]
            text = text.strip()
            return json.loads(text)
        except Exception as e:
            print(f"JSON parsing error: {e}")
            print(f"Raw response: {text}")
            return {"raw": text}
    else:
        return {"error": f"Error: {response.status_code} {response.text}"}

def test_email_extraction():
    # Test with the sample email content
    test_email_body = """
    Hi there,
    
    I have a borrower who is single, buying SFH in SF CA for 400k, needs a 300k loan. Credit score is high 700s.
    
    Including paystub and 1 bank statements.
    
    Thanks!
    """
    
    print("Testing email body extraction...")
    print(f"Email body: {test_email_body}")
    print("\n" + "="*50 + "\n")
    
    # Test the extraction
    extracted_fields = extract_fields_with_gemini(test_email_body)
    
    print("Extracted fields:")
    print(extracted_fields)
    
    if isinstance(extracted_fields, dict):
        print("\nFormatted fields:")
        formatted_fields = []
        for k, v in extracted_fields.items():
            if v and v != "null" and v != "None":
                formatted_fields.append(f"{k.replace('_', ' ').title()}: {v}")
        print('\n'.join(formatted_fields) if formatted_fields else 'None found.')

if __name__ == "__main__":
    test_email_extraction() 