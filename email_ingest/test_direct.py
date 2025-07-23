#!/usr/bin/env python3

def is_mortgage_email(subject, body):
    subject_lower = (subject or "").lower()
    body_lower = (body or "").lower()
    text = subject_lower + " " + body_lower
    
    # Check for obvious non-mortgage indicators first
    non_mortgage_indicators = [
        ''
    ]
    
    # If any non-mortgage indicators are present, it's likely not a mortgage email
    print(f"DEBUG: Checking non_mortgage_indicators: {non_mortgage_indicators}")
    print(f"DEBUG: text: '{text}'")
    for indicator in non_mortgage_indicators:
        if indicator in text:
            print(f"DEBUG: Found non-mortgage indicator '{indicator}', returning False")
            return False
    print(f"DEBUG: No non-mortgage indicators found, continuing...")
    
    # Strong mortgage indicators that should trigger processing
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
    
    # Check if subject contains strong mortgage indicators (should be processed)
    subject_mortgage_count = sum(1 for keyword in strong_mortgage_indicators if keyword in subject_lower)
    print(f"DEBUG: subject_mortgage_count = {subject_mortgage_count}")
    if subject_mortgage_count >= 1:
        print(f"DEBUG: Returning True due to subject indicators")
        return True
    
    # Also check if subject contains the word "mortgage" (strong indicator)
    print(f"DEBUG: Checking if 'mortgage' in subject_lower: {'mortgage' in subject_lower}")
    if 'mortgage' in subject_lower:
        print(f"DEBUG: Returning True due to 'mortgage' in subject")
        return True
    
    # For body content, require at least 2 mortgage indicators
    body_mortgage_count = sum(1 for keyword in strong_mortgage_indicators if keyword in body_lower)
    print(f"DEBUG: body_mortgage_count = {body_mortgage_count}")
    print(f"DEBUG: Returning {body_mortgage_count >= 2} due to body indicators")
    return body_mortgage_count >= 2

def test():
    test_email_body = """
    Hi there,
    
    I have a borrower who is single, buying SFH in SF CA for 400k, needs a 300k loan. Credit score is high 700s.
    
    Including paystub and 1 bank statements.
    
    Thanks!
    """
    
    test_subject = "inbound mortgage request"
    
    print("Testing direct function...")
    result = is_mortgage_email(test_subject, test_email_body)
    print(f"Result: {result}")

if __name__ == "__main__":
    test() 