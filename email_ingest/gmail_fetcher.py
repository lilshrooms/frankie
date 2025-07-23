import os
import base64
import email
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv
from attachment_parser import parse_attachments
from gemini_analyzer import analyze_with_gemini
import yaml
from rag_pipeline import build_rag_index, retrieve_relevant_chunks, prepare_gemini_prompt
import re
from typing import Dict

def _parse_analysis_for_response(analysis: str, gemini_fields: Dict) -> Dict:
    """Parse Gemini analysis to extract structured information for response generation"""
    analysis_data = {
        'key_findings': analysis,
        'qualification_status': 'Under review',
        'missing_items': 'Additional documents may be required',
        'next_steps': 'Please provide requested documents'
    }
    
    # Try to extract qualification status
    if 'QUALIFICATION STATUS' in analysis:
        lines = analysis.split('\n')
        for i, line in enumerate(lines):
            if 'QUALIFICATION STATUS' in line and i + 1 < len(lines):
                status = lines[i + 1].strip()
                if status and not status.startswith('**'):
                    analysis_data['qualification_status'] = status
                    break
    
    # Try to extract missing items
    if 'MISSING ITEMS' in analysis:
        missing_start = analysis.find('MISSING ITEMS')
        missing_end = analysis.find('NEXT STEPS') if 'NEXT STEPS' in analysis else len(analysis)
        missing_section = analysis[missing_start:missing_end]
        
        # Extract bullet points
        missing_items = []
        for line in missing_section.split('\n'):
            line = line.strip()
            if line.startswith('*') or line.startswith('-') or line.startswith('•'):
                item = line.lstrip('* - •').strip()
                if item and len(item) > 5:
                    missing_items.append(item)
        
        if missing_items:
            analysis_data['missing_items'] = '\n'.join(f"• {item}" for item in missing_items)
    
    # Try to extract next steps
    if 'NEXT STEPS' in analysis:
        next_start = analysis.find('NEXT STEPS')
        next_section = analysis[next_start:]
        
        # Extract numbered steps
        next_steps = []
        for line in next_section.split('\n'):
            line = line.strip()
            if line.startswith('1.') or line.startswith('2.') or line.startswith('3.'):
                step = line.split('.', 1)[1].strip() if '.' in line else line
                if step and len(step) > 5:
                    next_steps.append(step)
        
        if next_steps:
            analysis_data['next_steps'] = '\n'.join(f"{i+1}. {step}" for i, step in enumerate(next_steps))
    
    return analysis_data

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
    
    # Get emails from the last 6 hours (including read ones for testing)
    import datetime
    six_hours_ago = datetime.datetime.now() - datetime.timedelta(hours=6)
    date_query = six_hours_ago.strftime('%Y/%m/%d')
    
    # Query for recent emails (including read ones for testing)
    query = f'after:{date_query}'
    results = service.users().messages().list(userId='me', q=query, maxResults=50).execute()
    messages = results.get('messages', [])
    
    if not messages:
        print("No unread emails found from the last 24 hours.")
        return []
    
    print(f"Found {len(messages)} unread emails from the last 24 hours.")
    
    emails = []
    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
        payload = msg_data['payload']
        headers = payload.get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), None)
        from_email = next((h['value'] for h in headers if h['name'] == 'From'), None)
        
        # Get email date
        date_header = next((h['value'] for h in headers if h['name'] == 'Date'), None)
        
        # FIXED: Handle multipart/alternative structure for email body extraction
        body = ''
        if 'data' in payload.get('body', {}):
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        elif 'parts' in payload:
            for part in payload['parts']:
                # Handle multipart/alternative structure
                if part['mimeType'] == 'multipart/alternative' and 'parts' in part:
                    for subpart in part['parts']:
                        if subpart['mimeType'] == 'text/plain' and 'data' in subpart['body']:
                            body = base64.urlsafe_b64decode(subpart['body']['data']).decode('utf-8')
                            break
                        elif subpart['mimeType'] == 'text/html' and 'data' in subpart['body'] and not body:
                            html_body = base64.urlsafe_b64decode(subpart['body']['data']).decode('utf-8')
                            import re
                            body = re.sub(r'<[^>]+>', '', html_body)
                            body = re.sub(r'\s+', ' ', body).strip()
                            break
                    if body:
                        break
                # Handle direct text parts
                elif part['mimeType'] == 'text/plain' and 'data' in part['body']:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
                elif part['mimeType'] == 'text/html' and 'data' in part['body'] and not body:
                    html_body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    import re
                    body = re.sub(r'<[^>]+>', '', html_body)
                    body = re.sub(r'\s+', ' ', body).strip()
                    break
        
        attachments = []
        if 'parts' in payload:
            for part in payload['parts']:
                filename = part.get('filename')
                if filename and 'attachmentId' in part['body']:
                    att_id = part['body']['attachmentId']
                    att = service.users().messages().attachments().get(userId='me', messageId=msg['id'], id=att_id).execute()
                    file_data = base64.urlsafe_b64decode(att['data'])
                    attachments.append({'filename': filename, 'data': file_data})
        
        emails.append({
            'id': msg['id'], 
            'thread_id': msg.get('threadId'),  # Add thread ID for conversation tracking
            'subject': subject, 
            'from': from_email, 
            'body': body, 
            'attachments': attachments,
            'date': date_header
        })
        

    
    return emails

def mark_email_as_read(email_id):
    """Mark an email as read after processing"""
    try:
        service = get_gmail_service()
        service.users().messages().modify(
            userId='me', 
            id=email_id, 
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        print(f"Marked email {email_id} as read")
    except Exception as e:
        print(f"Error marking email as read: {e}")

def parse_attachment(att):
    # Use your existing logic to parse PDFs/images
    from email_ingest.attachment_parser import parse_pdf, parse_image
    filename = att['filename']
    data = att['data']
    if filename.lower().endswith('.pdf'):
        parsed_data = parse_pdf(data)
        return parsed_data.get('text', '')  # Extract text from the dictionary
    elif filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
        parsed_data = parse_image(data)
        return parsed_data.get('text', '')  # Extract text from the dictionary
    else:
        return ''

MORTGAGE_KEYWORDS = [
    "mortgage loan", "loan request", "home loan", "mortgage application", "loan application",
    "pre-approval", "prequalification", "underwriting", "borrower", "property address",
    "closing disclosure", "settlement statement", "good faith estimate", "loan estimate",
    "down payment", "earnest money", "appraisal", "credit report", "credit score",
    "income verification", "bank statement", "W-2", "pay stub", "asset statement",
    "purchase contract", "sales contract", "real estate agent", "MLS", "property tax",
    "FHA", "VA", "USDA", "conventional", "jumbo", "non-QM", "conforming",
    "commitment letter", "clear to close", "HELOC", "home equity"
]

def is_mortgage_email(subject, body):
    subject_lower = (subject or "").lower()
    body_lower = (body or "").lower()
    text = subject_lower + " " + body_lower
    
    # Check for obvious non-mortgage indicators first
    non_mortgage_indicators = [
        # Add actual non-mortgage indicators here if needed
    ]
    
    # If any non-mortgage indicators are present, it's likely not a mortgage email
    if any(indicator in text for indicator in non_mortgage_indicators):
        return False
    
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
    if subject_mortgage_count >= 1:
        return True
    
    # Also check if subject contains the word "mortgage" (strong indicator)
    if 'mortgage' in subject_lower:
        return True
    
    # For body content, require at least 2 mortgage indicators
    body_mortgage_count = sum(1 for keyword in strong_mortgage_indicators if keyword in body_lower)
    return body_mortgage_count >= 2

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
    # FRESH START: Simple extraction with strict anti-hallucination
    if not email_body or len(email_body.strip()) < 5:
        print(f"Email body too short ({len(email_body)} chars), skipping")
        return {}
    
    # Check for AI response content
    if 'PRELIMINARY LOAN ASSESSMENT' in email_body or 'QUALIFICATION STATUS' in email_body:
        print(f"Email contains AI response, skipping")
        return {}
    
    prompt = f'''
Extract ONLY explicitly stated information from this email. DO NOT make up or infer anything.

Email: {email_body}

Return JSON with ONLY information that is explicitly stated:
{{
  "credit_score": null,
  "loan_amount": null, 
  "purchase_price": null,
  "property_type": null,
  "occupancy": null,
  "borrower_name": null,
  "property_location": null,
  "monthly_income": null,
  "monthly_debts": null,
  "down_payment": null,
  "loan_type": null
}}

If nothing is stated, return empty {{}}.
'''
    from gemini_analyzer import GEMINI_API_URL
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

def send_email_response(to_email, original_subject, analysis):
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    import base64, os, email
    import re
    
    GMAIL_CLIENT_ID = os.getenv('GMAIL_CLIENT_ID')
    GMAIL_CLIENT_SECRET = os.getenv('GMAIL_CLIENT_SECRET')
    GMAIL_REFRESH_TOKEN = os.getenv('GMAIL_REFRESH_TOKEN')
    GMAIL_USER_EMAIL = os.getenv('GMAIL_USER_EMAIL')
    
    creds = Credentials(
        None,
        refresh_token=GMAIL_REFRESH_TOKEN,
        client_id=GMAIL_CLIENT_ID,
        client_secret=GMAIL_CLIENT_SECRET,
        token_uri='https://oauth2.googleapis.com/token',
        scopes=['https://mail.google.com/']
    )
    service = build('gmail', 'v1', credentials=creds)
    
    # Parse the analysis to extract key sections
    qualification_status = ""
    key_findings = ""
    missing_items = ""
    next_steps = ""
    
    # Extract sections from the analysis
    lines = analysis.split('\n')
    current_section = ""
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if 'QUALIFICATION STATUS' in line.upper():
            current_section = "qualification"
        elif 'KEY FINDINGS' in line.upper():
            current_section = "findings"
        elif 'MISSING ITEMS' in line.upper():
            current_section = "missing"
        elif 'NEXT STEPS' in line.upper():
            current_section = "steps"
        elif line.startswith('-') or line.startswith('•'):
            if current_section == "qualification":
                qualification_status += line + '\n'
            elif current_section == "findings":
                key_findings += line + '\n'
            elif current_section == "missing":
                missing_items += line + '\n'
            elif current_section == "steps":
                next_steps += line + '\n'
        elif current_section and not line.startswith('#'):
            # Add non-header lines to current section
            if current_section == "qualification":
                qualification_status += line + '\n'
            elif current_section == "findings":
                key_findings += line + '\n'
            elif current_section == "missing":
                missing_items += line + '\n'
            elif current_section == "steps":
                next_steps += line + '\n'
    
    # Create a clean, concise email body
    subject = f"Re: {original_subject} — Preliminary Loan Assessment"
    
    body = f"""PRELIMINARY LOAN ASSESSMENT

QUALIFICATION STATUS:
{qualification_status.strip() or "Analysis in progress"}

KEY FINDINGS:
{key_findings.strip() or "Processing documents"}

MISSING ITEMS:
{missing_items.strip() or "None identified"}

NEXT STEPS:
{next_steps.strip() or "Awaiting additional documents"}

---
This is an automated preliminary assessment. Please contact us for detailed underwriting.
"""
    
    message = email.message.EmailMessage()
    message.set_content(body)
    message['To'] = to_email
    message['From'] = GMAIL_USER_EMAIL
    message['Subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    send_message = {'raw': raw}
    service.users().messages().send(userId='me', body=send_message).execute()

if __name__ == '__main__':
    # Initialize conversation manager
    from conversation_manager import ConversationManager
    conversation_manager = ConversationManager()
    
    emails = fetch_recent_emails()
    # Load criteria (for now, use conventional.yaml)
    with open('../criteria/conventional.yaml', 'r') as f:
        criteria = yaml.safe_load(f)
    
    for email_data in emails:
        print(f"\n---\nChecking email: Subject: {email_data['subject']} | From: {email_data['from']}")
        print(f"Body preview: {email_data['body'][:120].replace('\n', ' ')}")
        print(f"Body length: {len(email_data['body'])}")
        
        # Get or create conversation context
        thread_id = email_data.get('thread_id', 'unknown')
        borrower_email = email_data['from']
        conversation_context = conversation_manager.get_or_create_conversation(thread_id, borrower_email)
        
        print(f"[CONVERSATION] Turn {conversation_context.conversation_turn} | State: {conversation_context.conversation_state}")
        
        is_mortgage = is_mortgage_email(email_data['subject'], email_data['body'])
        if not is_mortgage:
            print(f"[SKIP] Not a mortgage-related email.\n")
            mark_email_as_read(email_data['id'])
            continue
        print(f"[PROCESS] Identified as mortgage-related. Proceeding with analysis and response.")
        
        # FIXED: Check for AI response emails to prevent processing loops
        email_body = email_data['body'] or ""
        if ('PRELIMINARY LOAN ASSESSMENT' in email_body or 
            'QUALIFICATION STATUS' in email_body or
            'This is an automated preliminary assessment' in email_body):
            print(f"[SKIP] Email contains AI response content, skipping to prevent processing loop")
            mark_email_as_read(email_data['id'])
            continue
        
        # Additional safety check for email addresses
        from_email = email_data['from'] or ""
        if any(non_mortgage in from_email.lower() for non_mortgage in ['noreply', 'no-reply', 'reddit', 'google', 'yc', 'ycombinator', 'newsletter', 'alert']):
            print(f"[SKIP] Email from non-mortgage source: {from_email}")
            continue
        
        # Parse attachments
        from attachment_parser import parse_attachments
        parsed_attachments = parse_attachments(email_data['attachments'])
        
        print(f"Processing {len(parsed_attachments)} attachments:")
        for attachment in parsed_attachments:
            print(f"  - {attachment['filename']}: {attachment.get('document_type', 'unknown')}")
            if attachment.get('text'):
                ocr_status = " (OCR used)" if attachment.get('used_ocr', False) else ""
                print(f"    Text length: {len(attachment['text'])} characters{ocr_status}")
            else:
                print(f"    WARNING: No text extracted from {attachment['filename']}")
        
        # Determine conversation state based on content
        new_state = conversation_manager.determine_conversation_state(
            email_body, 
            [att['filename'] for att in parsed_attachments], 
            conversation_context
        )
        
        if new_state != conversation_context.conversation_state:
            print(f"[STATE CHANGE] {conversation_context.conversation_state} → {new_state}")
            conversation_context.conversation_state = new_state
        
        # Extract document types from new attachments
        new_document_types = conversation_manager.extract_document_types(
            [att['filename'] for att in parsed_attachments]
        )
        
        # Step 1: Extract fields from email body using Gemini
        gemini_fields = extract_fields_with_gemini(email_data['body'])
        print(f"Gemini Body Extraction: {gemini_fields}")
        
        # Step 2: Analyze with conversation context
        if gemini_fields and isinstance(gemini_fields, dict):
            formatted_fields = []
            for k, v in gemini_fields.items():
                if v and v != "null" and v != "None":
                    formatted_fields.append(f"{k.replace('_', ' ').title()}: {v}")
            pre_extracted_str = '\n'.join(formatted_fields) if formatted_fields else 'None found.'
        else:
            pre_extracted_str = 'None found.'
        
        print(f"Formatted extracted fields: {pre_extracted_str}")
        
        # Use conversation-aware analysis
        analysis = analyze_with_gemini(
            email_body, 
            parsed_attachments, 
            criteria, 
            pre_extracted_str,
            conversation_context
        )
        print(f"Gemini Analysis: {analysis}")
        
        # Extract borrower name from email or analysis
        borrower_name = gemini_fields.get('borrower_name', 'Borrower')
        if not borrower_name or borrower_name == 'None':
            # Try to extract from email address
            from_email = email_data['from']
            if '<' in from_email and '>' in from_email:
                borrower_name = from_email.split('<')[0].strip()
            else:
                borrower_name = from_email.split('@')[0].replace('.', ' ').title()
        
        # Parse analysis to extract key information
        analysis_data = _parse_analysis_for_response(analysis, gemini_fields)
        
        # Generate response based on conversation state
        response = conversation_manager.generate_response_based_on_state(conversation_context, {
            'borrower_name': borrower_name,
            'loan_amount': gemini_fields.get('loan_amount', 'N/A'),
            'property_value': gemini_fields.get('property_value', 'N/A'),
            'credit_score': gemini_fields.get('credit_score', 'N/A'),
            'property_type': gemini_fields.get('property_type', 'N/A'),
            'property_location': gemini_fields.get('property_location', 'N/A'),
            'monthly_income': gemini_fields.get('monthly_income', 'N/A'),
            'employer': gemini_fields.get('employer', 'N/A'),
            'bank_balance': gemini_fields.get('bank_balance', 'N/A'),
            'down_payment': gemini_fields.get('down_payment', 'N/A'),
            'key_findings': analysis_data.get('key_findings', analysis),
            'qualification_status': analysis_data.get('qualification_status', 'Under review'),
            'missing_items': analysis_data.get('missing_items', 'Additional documents may be required'),
            'next_steps': analysis_data.get('next_steps', 'Please provide requested documents'),
            'documents_received': new_document_types
        })
        
        # Update conversation state
        conversation_manager.update_conversation_state(
            conversation_context,
            new_state,
            new_document_types,
            analysis[:500] + "..." if len(analysis) > 500 else analysis  # Truncate for summary
        )
        
        # Send response email
        print(f"[EMAIL] Sending response to: {email_data['from']} | Subject: Re: {email_data['subject']}")
        send_email_response(email_data['from'], email_data['subject'], response)
        
        # Mark email as read after processing
        mark_email_as_read(email_data['id'])
        print('---') 