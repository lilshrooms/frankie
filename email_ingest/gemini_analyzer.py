import os
import requests
from dotenv import load_dotenv
from typing import List, Dict, Optional
from conversation_manager import ConversationContext

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

def analyze_with_gemini(email_body: str, attachments_data: List[Dict], criteria: dict, 
                       pre_extracted_str: str, conversation_context: Optional[ConversationContext] = None) -> str:
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
    
    # Build conversation context if available
    conversation_text = ""
    if conversation_context:
        conversation_text = f"""
**CONVERSATION CONTEXT:**
- Conversation Turn: {conversation_context.conversation_turn}
- Current State: {conversation_context.conversation_state}
- Previous Documents Received: {', '.join(conversation_context.received_documents) if conversation_context.received_documents else 'None'}
- Conversation Summary: {conversation_context.conversation_summary if conversation_context.conversation_summary else 'Initial request'}
"""
    
    # Enhanced prompt with conversation context
    prompt = f'''
Analyze this mortgage loan request. Use ONLY information that is explicitly provided.

{conversation_text}

**CURRENT EMAIL BODY:**
{email_body}

**EXTRACTED EMAIL FIELDS:**
{pre_extracted_str}

**DOCUMENT ANALYSIS:**
{attachments_text}

**TASK:**
1. List ONLY information that is explicitly stated
2. Identify what is missing based on conversation context
3. Provide next steps considering previous interactions
4. Update conversation summary with new information

**CRITICAL: DO NOT make up or infer any information. If something is not stated, mark it as missing.**

Return a structured response with:
- QUALIFICATION STATUS
- KEY FINDINGS (only stated facts)
- MISSING ITEMS
- NEXT STEPS
- CONVERSATION SUMMARY (brief summary of all information gathered so far)
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

def analyze_conversation_context(email_body: str, attachments_data: List[Dict], 
                               conversation_context: ConversationContext) -> Dict:
    """Analyze email in the context of ongoing conversation"""
    
    # Build context-aware prompt
    context_prompt = f"""
You are analyzing an email in an ongoing mortgage loan conversation.

**CONVERSATION HISTORY:**
- Turn: {conversation_context.conversation_turn}
- State: {conversation_context.conversation_state}
- Previously received: {', '.join(conversation_context.received_documents) if conversation_context.received_documents else 'None'}
- Summary: {conversation_context.conversation_summary if conversation_context.conversation_summary else 'Initial request'}

**CURRENT EMAIL:**
{email_body}

**NEW ATTACHMENTS:**
{len(attachments_data)} attachments provided

**TASK:**
1. Extract any new information provided
2. Identify what documents were sent
3. Determine if this addresses previous requests
4. Suggest next steps

Return JSON format:
{{
    "new_information": "list of new facts provided",
    "documents_received": ["list", "of", "document", "types"],
    "addresses_previous_requests": true/false,
    "missing_items": ["list", "of", "still", "missing", "items"],
    "next_state": "suggested next conversation state",
    "response_type": "document_request/underwriting/complete"
}}
"""
    
    data = {
        "contents": [{"parts": [{"text": context_prompt}]}]
    }
    
    try:
        response = requests.post(GEMINI_API_URL, json=data, timeout=60)
        if response.status_code == 200:
            result = response.json()
            response_text = result['candidates'][0]['content']['parts'][0]['text']
            
            # Try to parse JSON response
            import json
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                # Fallback to text parsing
                return {
                    "new_information": "Unable to parse structured response",
                    "documents_received": [],
                    "addresses_previous_requests": False,
                    "missing_items": ["Unable to determine"],
                    "next_state": conversation_context.conversation_state,
                    "response_type": "generic"
                }
        else:
            return {"error": f"API Error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"} 