import os
import requests
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
# Update to Gemini 2.5 Pro model and v1 endpoint
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1/models/gemini-2.5-pro:generateContent?key=' + GEMINI_API_KEY

def analyze_with_gemini(email_body: str, attachments_text: str, criteria: dict, pre_extracted_str: str) -> str:
    prompt = f'''
You are an AI loan underwriter. Use the following underwriting criteria:
{criteria}

The following fields were pre-extracted from the email body:
{pre_extracted_str}

Extract and list the following fields if present in the email body or attachments:
- Credit Score
- Loan Amount
- Purchase Price
- Property Type
- Occupancy Type
- Monthly Debts
- Monthly Income
- Employer(s)
- Any other relevant details

For each field, indicate the value, the source (Email Body or Attachment), and any notes.

Here is the information extracted from the broker's email body:
{email_body}

Here is the information extracted from the attachments:
{attachments_text}

Return your answer as a Markdown table with columns: Field, Value, Source, Notes. Then provide your underwriting analysis and next steps.
'''
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    response = requests.post(GEMINI_API_URL, json=data)
    if response.status_code == 200:
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    else:
        return f"Error: {response.status_code} {response.text}" 