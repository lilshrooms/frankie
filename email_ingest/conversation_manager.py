#!/usr/bin/env python3
"""
Conversation Manager for Multi-Turn Email Conversations
Handles conversation tracking, context management, and state transitions
"""

import json
import re
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

@dataclass
class ConversationContext:
    """Represents the current state of a conversation"""
    loan_file_id: Optional[int] = None
    gmail_thread_id: Optional[str] = None
    borrower_email: Optional[str] = None
    conversation_state: str = 'initial_request'  # initial_request, waiting_docs, underwriting, complete
    conversation_summary: str = ""
    requested_documents: List[str] = None
    received_documents: List[str] = None
    conversation_turn: int = 1
    previous_analyses: List[Dict] = None
    
    def __post_init__(self):
        if self.requested_documents is None:
            self.requested_documents = []
        if self.received_documents is None:
            self.received_documents = []
        if self.previous_analyses is None:
            self.previous_analyses = []

class ConversationManager:
    """Manages multi-turn conversations for loan applications"""
    
    def __init__(self, db_session=None, persistence_file="conversations.json"):
        self.db_session = db_session
        self.persistence_file = persistence_file
        self.conversation_cache = {}  # thread_id -> ConversationContext
        self._load_conversations()
    
    def _load_conversations(self):
        """Load conversations from persistence file"""
        if os.path.exists(self.persistence_file):
            try:
                with open(self.persistence_file, 'r') as f:
                    data = json.load(f)
                    for thread_id, conv_data in data.items():
                        context = ConversationContext(**conv_data)
                        self.conversation_cache[thread_id] = context
                print(f"Loaded {len(self.conversation_cache)} conversations from {self.persistence_file}")
            except Exception as e:
                print(f"Error loading conversations: {e}")
    
    def _save_conversations(self):
        """Save conversations to persistence file"""
        try:
            data = {}
            for thread_id, context in self.conversation_cache.items():
                data[thread_id] = asdict(context)
            
            with open(self.persistence_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving conversations: {e}")
    
    def get_or_create_conversation(self, gmail_thread_id: str, borrower_email: str) -> ConversationContext:
        """Get existing conversation or create new one"""
        if gmail_thread_id in self.conversation_cache:
            context = self.conversation_cache[gmail_thread_id]
            print(f"[CONVERSATION] Found existing conversation: Turn {context.conversation_turn} | State: {context.conversation_state}")
            return context
        
        # Try to find existing conversation in database
        if self.db_session:
            from models import LoanFile
            existing_loan = self.db_session.query(LoanFile).filter_by(
                gmail_thread_id=gmail_thread_id
            ).first()
            
            if existing_loan:
                context = ConversationContext(
                    loan_file_id=existing_loan.id,
                    gmail_thread_id=gmail_thread_id,
                    borrower_email=borrower_email,
                    conversation_state=existing_loan.conversation_state,
                    conversation_summary=existing_loan.conversation_summary or "",
                    requested_documents=existing_loan.requested_documents or [],
                    received_documents=existing_loan.received_documents or [],
                    conversation_turn=len(existing_loan.analyses) + 1
                )
                self.conversation_cache[gmail_thread_id] = context
                self._save_conversations()
                return context
        
        # Create new conversation
        context = ConversationContext(
            gmail_thread_id=gmail_thread_id,
            borrower_email=borrower_email,
            conversation_state='initial_request'
        )
        self.conversation_cache[gmail_thread_id] = context
        self._save_conversations()
        print(f"[CONVERSATION] Created new conversation: Turn {context.conversation_turn} | State: {context.conversation_state}")
        return context
    
    def update_conversation_state(self, context: ConversationContext, new_state: str, 
                                new_documents: List[str] = None, analysis_summary: str = None):
        """Update conversation state and track new information"""
        old_state = context.conversation_state
        context.conversation_state = new_state
        context.conversation_turn += 1
        
        if new_documents:
            context.received_documents.extend(new_documents)
        
        if analysis_summary:
            context.conversation_summary = analysis_summary
        
        print(f"[CONVERSATION] Updated state: {old_state} → {new_state} | Turn: {context.conversation_turn}")
        print(f"[CONVERSATION] Documents received: {context.received_documents}")
        
        # Update database if available
        if self.db_session and context.loan_file_id:
            from models import LoanFile
            loan_file = self.db_session.query(LoanFile).filter_by(id=context.loan_file_id).first()
            if loan_file:
                loan_file.conversation_state = new_state
                loan_file.conversation_summary = context.conversation_summary
                loan_file.received_documents = context.received_documents
                loan_file.last_activity = datetime.now()
                self.db_session.commit()
        
        # Save to persistence file
        self._save_conversations()
    
    def determine_conversation_state(self, email_body: str, attachments: List[str], 
                                   context: ConversationContext) -> str:
        """Determine the current state based on email content and context"""
        
        # Check if this is a response to a request for documents
        if context.conversation_state == 'waiting_docs':
            if attachments:
                return 'underwriting'  # Documents provided, move to underwriting
            elif any(phrase in email_body.lower() for phrase in ['here are', 'attached', 'sending', 'find attached']):
                return 'underwriting'  # Mentioned documents, move to underwriting
        
        # Check if this is initial request
        if context.conversation_state == 'initial_request':
            if any(phrase in email_body.lower() for phrase in ['loan', 'mortgage', 'refinance', 'purchase']):
                return 'waiting_docs'  # Initial loan request, need documents
        
        # Check if this is asking for more information
        if any(phrase in email_body.lower() for phrase in ['need more', 'additional', 'missing', 'require']):
            return 'waiting_docs'
        
        return context.conversation_state
    
    def build_conversation_context_for_gemini(self, context: ConversationContext, 
                                            current_email_body: str, 
                                            current_attachments: List[str]) -> str:
        """Build context string for Gemini to understand conversation history"""
        
        context_parts = []
        
        # Add conversation summary
        if context.conversation_summary:
            context_parts.append(f"CONVERSATION HISTORY:\n{context.conversation_summary}")
        
        # Add requested documents
        if context.requested_documents:
            context_parts.append(f"PREVIOUSLY REQUESTED DOCUMENTS:\n{', '.join(context.requested_documents)}")
        
        # Add received documents
        if context.received_documents:
            context_parts.append(f"PREVIOUSLY RECEIVED DOCUMENTS:\n{', '.join(context.received_documents)}")
        
        # Add current turn info
        context_parts.append(f"CURRENT EMAIL (Turn {context.conversation_turn}):\n{current_email_body}")
        
        if current_attachments:
            context_parts.append(f"NEW ATTACHMENTS:\n{', '.join(current_attachments)}")
        
        return "\n\n".join(context_parts)
    
    def generate_response_based_on_state(self, context: ConversationContext, 
                                       analysis_result: Dict) -> str:
        """Generate appropriate response based on conversation state"""
        
        if context.conversation_state == 'initial_request':
            return self._generate_initial_response(analysis_result)
        elif context.conversation_state == 'waiting_docs':
            return self._generate_document_request_response(analysis_result)
        elif context.conversation_state == 'underwriting':
            return self._generate_underwriting_response(analysis_result)
        else:
            return self._generate_generic_response(analysis_result)
    
    def _generate_initial_response(self, analysis_result: Dict) -> str:
        """Generate response for initial loan request"""
        loan_amount = analysis_result.get('loan_amount', 'N/A')
        property_value = analysis_result.get('property_value', 'N/A')
        credit_score = analysis_result.get('credit_score', 'N/A')
        
        return f"""Thank you for your loan request for ${loan_amount} on a ${property_value} property.

PRELIMINARY ASSESSMENT:
Based on your credit score of {credit_score}, we can proceed with your application.

REQUIRED DOCUMENTS:
To complete your application, please provide:
- Recent pay stubs (last 2 months)
- Bank statements (last 2 months) 
- W-2 forms (last 2 years)
- Tax returns (last 2 years)
- Driver's license or ID
- Proof of funds for down payment

Please reply to this email with the requested documents attached.

---
This is an automated preliminary assessment. Please contact us for detailed underwriting."""
    
    def _generate_document_request_response(self, analysis_result: Dict) -> str:
        """Generate response when requesting additional documents"""
        missing_items = analysis_result.get('missing_items', 'Additional documents')
        
        return f"""Thank you for the documents provided.

ADDITIONAL DOCUMENTS NEEDED:
{missing_items}

Please reply to this email with the requested documents attached.

---
This is an automated preliminary assessment. Please contact us for detailed underwriting."""
    
    def _generate_underwriting_response(self, analysis_result: Dict) -> str:
        """Generate response for underwriting analysis"""
        key_findings = analysis_result.get('key_findings', 'Processing documents')
        qualification_status = analysis_result.get('qualification_status', 'Under review')
        next_steps = analysis_result.get('next_steps', 'Awaiting additional documents')
        
        return f"""DOCUMENT ANALYSIS COMPLETE

QUALIFICATION STATUS:
{qualification_status}

KEY FINDINGS:
{key_findings}

NEXT STEPS:
{next_steps}

---
This is an automated preliminary assessment. Please contact us for detailed underwriting."""
    
    def _generate_generic_response(self, analysis_result: Dict) -> str:
        """Generate generic response"""
        return f"""Thank you for your email.

{analysis_result.get('summary', 'Processing your request...')}

---
This is an automated preliminary assessment. Please contact us for detailed underwriting."""
    
    def extract_document_types(self, attachments: List[str]) -> List[str]:
        """Extract document types from attachment filenames"""
        document_types = []
        
        for attachment in attachments:
            filename = attachment.lower()
            if any(word in filename for word in ['pay', 'stub', 'wage']):
                document_types.append('pay_stub')
            elif any(word in filename for word in ['bank', 'statement', 'account']):
                document_types.append('bank_statement')
            elif any(word in filename for word in ['w2', 'w-2']):
                document_types.append('w2')
            elif any(word in filename for word in ['tax', 'return', '1040']):
                document_types.append('tax_return')
            elif any(word in filename for word in ['license', 'id', 'passport']):
                document_types.append('identification')
            else:
                document_types.append('other')
        
        return document_types 