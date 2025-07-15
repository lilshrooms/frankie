import os
import requests
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=' + GEMINI_API_KEY

def analyze_with_gemini(extracted_text: str, criteria: dict) -> str:
    prompt = f"""
You are an AI loan underwriter. Use the following underwriting criteria:
{criteria}

Here is the information extracted from the broker's email and attachments:
{extracted_text}

Please determine if the applicant meets the criteria. If information is missing, specify what is needed.
"""
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    response = requests.post(GEMINI_API_URL, json=data)
    if response.status_code == 200:
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    else:
        return f"Error: {response.status_code} {response.text}" 