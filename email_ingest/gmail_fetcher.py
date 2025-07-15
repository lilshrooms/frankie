import os
import base64
import email
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv
from email_ingest.attachment_parser import parse_attachments
from email_ingest.gemini_analyzer import analyze_with_gemini
import yaml

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

def fetch_unread_emails():
    service = get_gmail_service()
    results = service.users().messages().list(userId='me', labelIds=['UNREAD'], maxResults=10).execute()
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

if __name__ == '__main__':
    emails = fetch_unread_emails()
    # Load criteria (for now, use conventional.yaml)
    with open('criteria/conventional.yaml', 'r') as f:
        criteria = yaml.safe_load(f)
    for email_data in emails:
        print(f"Subject: {email_data['subject']}")
        print(f"From: {email_data['from']}")
        print(f"Body: {email_data['body'][:100]}...")
        print(f"Attachments: {[a['filename'] for a in email_data['attachments']]}")
        # Parse attachments
        parsed_attachments = parse_attachments(email_data['attachments'])
        extracted_text = email_data['body'] + '\n' + '\n'.join([a['text'] or '' for a in parsed_attachments])
        # Analyze with Gemini
        analysis = analyze_with_gemini(extracted_text, criteria)
        print(f"Gemini Analysis: {analysis}")
        print('---') 