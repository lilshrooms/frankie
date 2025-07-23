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
    
    # Simplified prompt focused on preliminary qualification
    prompt = f'''
You are a mortgage loan processor helping with preliminary qualification. Your task is to extract key information and provide a high-level assessment.

**BASIC QUALIFICATION CRITERIA:**
- Minimum credit score: 620 (FHA), 680 (Conventional)
- Maximum DTI: 43% (FHA), 45% (Conventional)
- Minimum down payment: 3.5% (FHA), 3% (Conventional)

**PRE-EXTRACTED EMAIL FIELDS (HIGH PRIORITY - USE THESE IF AVAILABLE):**
{pre_extracted_str}

**PRE-EXTRACTED STRUCTURED DATA FROM DOCUMENTS:**
{format_structured_data(all_structured_data)}

**EMAIL BODY:**
{email_body}

**DOCUMENT ANALYSIS:**
{attachments_text}

**TASK:**
1. **Extract key information (PRIORITIZE EMAIL BODY DATA FIRST):**
   - **Credit Score(s)** - Check email body first, then documents
   - **Loan Amount & Purchase Price** - Check email body first, then documents  
   - **Borrower Name(s)**
   - **Monthly Income (gross)**
   - **Monthly Debts (including credit cards)**
   - **Down Payment Amount**
   - **Property Type & Occupancy**

2. **Preliminary Assessment:**
   - Does the borrower meet basic credit score requirements?
   - Can we calculate a preliminary DTI ratio?
   - Are there any obvious red flags?
   - What documents are still needed?

3. **Next Steps:**
   - List 2-3 specific items needed to proceed
   - Suggest loan program if possible (FHA/Conventional)

**CRITICAL: If credit score, loan amount, or purchase price are mentioned in the email body, use those values and do NOT list them as missing items.**

**IMPORTANT:**
- Focus on high-level qualification, not detailed underwriting
- Be concise and clear
- Flag missing critical information
- Provide actionable next steps

Return a brief, structured response with: QUALIFICATION STATUS, KEY FINDINGS, MISSING ITEMS, NEXT STEPS.
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