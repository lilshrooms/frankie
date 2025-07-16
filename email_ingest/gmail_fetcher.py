import os
import base64
import email
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv
from email_ingest.attachment_parser import parse_attachments
from email_ingest.gemini_analyzer import analyze_with_gemini
import yaml
from email_ingest.rag_pipeline import build_rag_index, retrieve_relevant_chunks, prepare_gemini_prompt
import re

# Load environment variables
load_dotenv()

GMAIL_CLIENT_ID = os.getenv('GMAIL_CLIENT_ID')
GMAIL_CLIENT_SECRET = os.getenv('GMAIL_CLIENT_SECRET')
GMAIL_REFRESH_TOKEN = os.getenv('GMAIL_REFRESH_TOKEN')
GMAIL_USER_EMAIL = os.getenv('GMAIL_USER_EMAIL')

SCOPES = ['https://mail.google.com/']

def get_gmail_service():
    creds = Credentials(
        None,
        refresh_token=GMAIL_REFRESH_TOKEN,
        client_id=GMAIL_CLIENT_ID,
        client_secret=GMAIL_CLIENT_SECRET,
        token_uri='https://oauth2.googleapis.com/token',
        scopes=SCOPES
    )
    service = build('gmail', 'v1', credentials=creds)
    return service

def fetch_recent_emails():
    service = get_gmail_service()
    results = service.users().messages().list(userId='me', maxResults=20).execute()
    messages = results.get('messages', [])
    emails = []
    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
        payload = msg_data['payload']
        headers = payload.get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), None)
        from_email = next((h['value'] for h in headers if h['name'] == 'From'), None)
        body = ''
        if 'data' in payload.get('body', {}):
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        elif 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
        attachments = []
        if 'parts' in payload:
            for part in payload['parts']:
                filename = part.get('filename')
                if filename and 'attachmentId' in part['body']:
                    att_id = part['body']['attachmentId']
                    att = service.users().messages().attachments().get(userId='me', messageId=msg['id'], id=att_id).execute()
                    file_data = base64.urlsafe_b64decode(att['data'])
                    attachments.append({'filename': filename, 'data': file_data})
        emails.append({'id': msg['id'], 'subject': subject, 'from': from_email, 'body': body, 'attachments': attachments})
    return emails

def parse_attachment(att):
    # Use your existing logic to parse PDFs/images
    from email_ingest.attachment_parser import parse_pdf, parse_image
    filename = att['filename']
    data = att['data']
    if filename.lower().endswith('.pdf'):
        return parse_pdf(data)
    elif filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
        return parse_image(data)
    else:
        return ''

MORTGAGE_KEYWORDS = [
    "mortgage", "loan request", "home loan", "purchase", "refinance",
    "pre-approval", "prequal", "pre-qual", "prequalification", "pre-qualification",
    "underwrite", "underwriting", "borrower", "property address", "escrow",
    "closing disclosure", "CD", "HUD", "settlement statement", "GFE", "good faith estimate",
    "lender", "title company", "down payment", "earnest money", "appraisal",
    "loan estimate", "LE", "interest rate", "APR", "annual percentage rate",
    "principal", "PITI", "DTI", "debt to income", "credit report", "credit score",
    "income verification", "bank statement", "W-2", "pay stub", "asset statement",
    "purchase contract", "sales contract", "offer letter", "real estate agent",
    "listing", "MLS", "property tax", "insurance binder", "hazard insurance",
    "FHA", "VA", "USDA", "conventional", "jumbo", "non-QM", "conforming",
    "high-balance", "cash to close", "funding", "commitment letter", "clear to close",
    "CTC", "closing date", "funded", "draw", "HELOC", "home equity", "second mortgage"
]

def is_mortgage_email(subject, body):
    text = (subject or "") + " " + (body or "")
    text = text.lower()
    return any(keyword in text for keyword in MORTGAGE_KEYWORDS)

def extract_fields_from_body(body):
    fields = {}
    patterns = {
        "credit_score": r"credit score[:\s]*([0-9]{3})",
        "loan_amount": r"loan amount[:\s]*\$?([0-9,]+)",
        "purchase_price": r"(purchase price|home price|sales price)[:\s]*\$?([0-9,]+)",
        "property_type": r"property type[:\s]*([\w\s-]+)",
        "occupancy_type": r"occupancy type[:\s]*([\w\s-]+)",
        "monthly_debts": r"monthly debts?[:\s]*\$?([0-9,]+)",
    }
    for field, pattern in patterns.items():
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            fields[field] = match.group(1)
    return fields

def extract_fields_with_gemini(email_body):
    # Use Gemini to extract key fields from the email body only
    prompt = '''
Extract the following fields from the email body below if present:
- Credit Score
- Loan Amount
- Purchase Price
- Property Type
- Occupancy Type
- Monthly Debts
- Monthly Income
- Employer(s)
- Any other relevant details

Return your answer as a JSON object with keys for each field. If a field is not present, use null.

EMAIL BODY:
'''
    prompt += email_body
    from email_ingest.gemini_analyzer import GEMINI_API_URL
    import os, requests
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(GEMINI_API_URL, json=data)
    if response.status_code == 200:
        result = response.json()
        text = result['candidates'][0]['content']['parts'][0]['text']
        # Try to parse JSON from Gemini's response
        import json
        try:
            return json.loads(text)
        except Exception:
            return {"raw": text}
    else:
        return {"error": f"Error: {response.status_code} {response.text}"}

if __name__ == '__main__':
    emails = fetch_recent_emails()
    # Load criteria (for now, use conventional.yaml)
    with open('criteria/conventional.yaml', 'r') as f:
        criteria = yaml.safe_load(f)
    for email_data in emails:
        if not is_mortgage_email(email_data['subject'], email_data['body']):
            print(f"Skipping non-mortgage email: {email_data['subject']}")
            continue
        print(f"Subject: {email_data['subject']}")
        print(f"From: {email_data['from']}")
        print(f"Body: {email_data['body'][:100]}...")
        print(f"Attachments: {[a['filename'] for a in email_data['attachments']]}")
        # Step 1: Extract fields from email body using Gemini
        gemini_fields = extract_fields_with_gemini(email_data['body'])
        print(f"Gemini Body Extraction: {gemini_fields}")
        # Build RAG index from attachments
        rag_chunks = build_rag_index(email_data['attachments'], parse_attachment)
        if rag_chunks:
            query = "What is the borrower's total income?"
            relevant_chunks = retrieve_relevant_chunks(rag_chunks, query)
            prompt = prepare_gemini_prompt(relevant_chunks, query)
            print(f"Gemini Prompt:\n{prompt}\n---")
        else:
            print("No text chunks found in attachments. Skipping RAG retrieval.")
        # Parse attachments
        parsed_attachments = parse_attachments(email_data['attachments'])
        email_body = email_data['body']
        attachments_text = '\n'.join([a['text'] or '' for a in parsed_attachments])
        # Step 2: Full analysis with Gemini, passing extracted fields as context
        pre_extracted_str = '\n'.join([f'{k.replace('_', ' ').title()}: {v}' for k, v in gemini_fields.items()]) if gemini_fields else 'None found.'
        analysis = analyze_with_gemini(email_body, attachments_text, criteria, pre_extracted_str)
        print(f"Gemini Analysis: {analysis}")
        print('---') 