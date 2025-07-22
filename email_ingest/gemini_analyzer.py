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
    
    # Enhanced prompt with structured data and tables
    prompt = f'''
You are an AI loan underwriter with expertise in mortgage underwriting. Your task is to analyze loan applications and extract key information with high accuracy.

**UNDERWRITING CRITERIA:**
{criteria}

**PRE-EXTRACTED EMAIL FIELDS:**
{pre_extracted_str}

**PRE-EXTRACTED STRUCTURED DATA FROM DOCUMENTS:**
{format_structured_data(all_structured_data)}

**EXTRACTED TABLES:**
{format_tables(all_tables)}

**EMAIL BODY:**
{email_body}

**DOCUMENT ANALYSIS:**
{attachments_text}

**TASK:**
1. **Extract and validate** the following fields if present:
   - Borrower Name(s)
   - Credit Score(s)
   - Loan Amount
   - Purchase Price
   - Property Type
   - Occupancy Type
   - Monthly Debts (including credit card minimum payments)
   - Monthly Income (gross and net)
   - Employer(s) and job title(s)
   - Down Payment Amount
   - Property Address
   - Credit card balances and minimum payments (for DTI calculation)
   - Any other relevant financial information

2. **For credit card statements specifically:**
   - Extract all credit card balances
   - Calculate total monthly credit card payments (minimum payments)
   - Note credit utilization ratios
   - Flag any late payments or high utilization
   - Include in monthly debt calculations for DTI

3. **For each field:**
   - Provide the exact value found
   - Indicate the source (Email Body, Document Type, or Table)
   - Note any discrepancies between sources
   - Flag any missing critical information

4. **Provide underwriting analysis:**
   - Compare extracted data against the underwriting criteria
   - Calculate preliminary DTI ratio using income and debt data
   - Identify any red flags or missing requirements
   - Flag high credit utilization or late payments
   - Suggest next steps for the loan officer

**IMPORTANT:**
- Use the structured data and tables as your primary source when available
- Cross-reference information across multiple documents
- Be precise with numbers and dates
- Flag any inconsistencies or missing critical data

Return your analysis as a structured Markdown response with clear sections for extracted data, validation, and recommendations.
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