import os
import requests
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
# Update to Gemini 2.5 Pro model and v1 endpoint
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1/models/gemini-2.5-pro:generateContent?key=' + GEMINI_API_KEY

def analyze_with_gemini(email_body: str, attachments_text: str, criteria: dict) -> str:
    prompt = f'''
You are an AI loan underwriter. Use the following underwriting criteria:
{criteria}

Here is the information extracted from the broker's email body:
{email_body}

Here is the information extracted from the attachments:
{attachments_text}

Please extract and summarize all relevant borrower and loan details (credit score, loan amount, purchase price, etc.) from both the email body and attachments. Then determine if the applicant meets the criteria. If information is missing, specify what is needed.
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