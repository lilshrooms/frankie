import os
import requests
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
# Update to Gemini 2.5 Pro model and v1 endpoint
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1/models/gemini-2.5-pro:generateContent?key=' + GEMINI_API_KEY

def format_structured_data(structured_data: Dict) -> str:
    """Format structured data for Gemini prompt"""
    if not structured_data:
        return "No structured data extracted"
    
    formatted = "**Pre-extracted Structured Data:**\n"
    for field, value in structured_data.items():
        formatted += f"- {field.replace('_', ' ').title()}: {value}\n"
    return formatted

def format_tables(tables: List) -> str:
    """Format tables for Gemini prompt"""
    if not tables:
        return "No tables found"
    
    formatted = "**Extracted Tables:**\n"
    for i, table in enumerate(tables):
        formatted += f"\nTable {i+1}:\n"
        for row in table:
            if row:  # Filter out empty rows
                formatted += "| " + " | ".join(str(cell) if cell else "" for cell in row) + " |\n"
    return formatted

def analyze_with_gemini(email_body: str, attachments_data: List[Dict], criteria: dict, pre_extracted_str: str) -> str:
    # Prepare enhanced attachment information
    attachments_text = ""
    all_structured_data = {}
    all_tables = []
    
    for attachment in attachments_data:
        if attachment.get('text'):
            attachments_text += f"\n**File: {attachment['filename']}**\n"
            attachments_text += f"**Document Type: {attachment['document_type']}**\n"
            attachments_text += f"**Text Content:**\n{attachment['text']}\n"
            
            # Add structured data
            if attachment.get('structured_data'):
                structured_text = format_structured_data(attachment['structured_data'])
                attachments_text += f"\n{structured_text}\n"
                all_structured_data.update(attachment['structured_data'])
            
            # Add tables
            if attachment.get('tables'):
                tables_text = format_tables(attachment['tables'])
                attachments_text += f"\n{tables_text}\n"
                all_tables.extend(attachment['tables'])
    
    # FRESH START: Simple, clear analysis prompt
    prompt = f'''
Analyze this mortgage loan request. Use ONLY information that is explicitly provided.

**EMAIL BODY:**
{email_body}

**EXTRACTED EMAIL FIELDS:**
{pre_extracted_str}

**DOCUMENT ANALYSIS:**
{attachments_text}

**TASK:**
1. List ONLY information that is explicitly stated
2. Identify what is missing
3. Provide next steps

**CRITICAL: DO NOT make up or infer any information. If something is not stated, mark it as missing.**

Return a structured response with:
- QUALIFICATION STATUS
- KEY FINDINGS (only stated facts)
- MISSING ITEMS
- NEXT STEPS
'''
    
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        response = requests.post(GEMINI_API_URL, json=data, timeout=60)
        if response.status_code == 200:
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Error: {response.status_code} {response.text}"
    except requests.exceptions.Timeout:
        return "Error: Request timed out. Please try again."
    except Exception as e:
        return f"Error: {str(e)}" 