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

if __name__ == '__main__':
    emails = fetch_recent_emails()
    # Load criteria (for now, use conventional.yaml)
    with open('criteria/conventional.yaml', 'r') as f:
        criteria = yaml.safe_load(f)
    for email_data in emails:
        print(f"Subject: {email_data['subject']}")
        print(f"From: {email_data['from']}")
        print(f"Body: {email_data['body'][:100]}...")
        print(f"Attachments: {[a['filename'] for a in email_data['attachments']]}")
        # Build RAG index from attachments
        rag_chunks = build_rag_index(email_data['attachments'], parse_attachment)
        if rag_chunks:
            # Example query: "What is the borrower's total income?"
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
        # Analyze with Gemini, passing both body and attachments text
        analysis = analyze_with_gemini(email_body, attachments_text, criteria)
        print(f"Gemini Analysis: {analysis}")
        print('---') 