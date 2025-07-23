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
        borrower_name = analysis_result.get('borrower_name', 'Borrower')
        
        return f"""Hi {borrower_name},

Thank you for your loan request! We're excited to help you get into your new home faster.

**LOAN SUMMARY:**
• Loan Amount: ${loan_amount:,}
• Property Value: ${property_value:,}
• Credit Score: {credit_score}
• Property Type: {analysis_result.get('property_type', 'N/A')}
• Location: {analysis_result.get('property_location', 'N/A')}

**FAST TRACK TO APPROVAL:**
To get you approved quickly, please provide these documents:

**REQUIRED DOCUMENTS:**
□ Recent pay stubs (last 2 months)
□ Bank statements (last 2 months)
□ W-2 forms (last 2 years)
□ Tax returns (last 2 years)
□ Proof of funds for down payment

**QUICK RESPONSE NEEDED:**
1. Gather the documents above
2. Reply to this email with all documents attached
3. We'll provide your preliminary decision in 5 minutes

**Reply now to get started on your home journey!**

---
*This is an automated preliminary assessment. For detailed underwriting, please contact our loan officers.*"""
    
    def _generate_document_request_response(self, analysis_result: Dict) -> str:
        """Generate response when requesting additional documents"""
        missing_items = analysis_result.get('missing_items', 'Additional documents')
        borrower_name = analysis_result.get('borrower_name', 'Borrower')
        
        # Extract key facts from analysis
        key_facts = self._extract_key_facts_from_analysis(analysis_result)
        
        return f"""Hi {borrower_name},

Great progress! We're almost there. Here's what we have so far:

**KEY FACTS:**
{key_facts}

**DOCUMENTS RECEIVED:**
{', '.join(analysis_result.get('documents_received', ['None specified']))}

**FINAL DOCUMENTS NEEDED:**
{missing_items}

**QUICK COMPLETION:**
1. Provide the missing documents above
2. Reply to this email with all documents attached
3. We'll give you a decision in 5 minutes

**Your dream home is waiting - let's complete this together!**

---
*This is an automated preliminary assessment. For detailed underwriting, please contact our loan officers.*"""
    
    def _generate_underwriting_response(self, analysis_result: Dict) -> str:
        """Generate response for underwriting analysis"""
        key_findings = analysis_result.get('key_findings', 'Processing documents')
        qualification_status = analysis_result.get('qualification_status', 'Under review')
        next_steps = analysis_result.get('next_steps', 'Awaiting additional documents')
        borrower_name = analysis_result.get('borrower_name', 'Borrower')
        
        # Extract key facts from analysis
        key_facts = self._extract_key_facts_from_analysis(analysis_result)
        
        # Determine if we have all documents
        all_docs_received = len(analysis_result.get('documents_received', [])) >= 6  # Assuming 6 core documents
        
        if all_docs_received:
            return self._generate_complete_analysis_response(analysis_result, key_facts, qualification_status, key_findings)
        else:
            return self._generate_partial_analysis_response(analysis_result, key_facts, qualification_status, key_findings, next_steps)
    
    def _generate_complete_analysis_response(self, analysis_result: Dict, key_facts: str, qualification_status: str, key_findings: str) -> str:
        """Generate response when all documents are received"""
        borrower_name = analysis_result.get('borrower_name', 'Borrower')
        
        # Determine if this is a success or failure
        is_success = any(word in qualification_status.lower() for word in ['approved', 'qualify', 'eligible', 'strong'])
        is_failure = any(word in qualification_status.lower() for word in ['denied', 'not qualify', 'ineligible', 'insufficient'])
        
        if is_success:
            return f"""Hi {borrower_name},

**PRELIMINARY APPROVAL**

**LOAN SUMMARY:**
{key_facts}

**QUALIFICATION STATUS:**
{qualification_status}

**KEY FINDINGS:**
{key_findings}

**NEXT STEPS:**
1. A loan officer will contact you within 5 minutes
2. Complete the formal application process
3. Schedule property appraisal
4. Finalize loan terms and closing

**Congratulations!** Your application looks strong and we're ready to move forward.

**Your new home is within reach - let's make it happen!**

---
*This is a preliminary approval. Final terms subject to full underwriting review.*"""
        
        elif is_failure:
            return f"""Hi {borrower_name},

**PRELIMINARY DECISION**

**LOAN SUMMARY:**
{key_facts}

**QUALIFICATION STATUS:**
{qualification_status}

**KEY FINDINGS:**
{key_findings}

**NEXT STEPS:**
1. A loan officer will contact you within 5 minutes to discuss alternatives
2. We may be able to help with different loan programs
3. Consider addressing the issues identified above

**Don't give up on your dream home!** We're here to help find a solution that works for you.

---
*This is a preliminary decision. Please contact us to discuss options.*"""
        
        else:
            return f"""Hi {borrower_name},

**ANALYSIS COMPLETE**

**LOAN SUMMARY:**
{key_facts}

**QUALIFICATION STATUS:**
{qualification_status}

**KEY FINDINGS:**
{key_findings}

**NEXT STEPS:**
1. We will review your application within 5 minutes
2. You'll receive a detailed decision shortly
3. We may request additional information to help us help you

**Stay tuned - we're working fast to get you into your home!**

---
*This is a preliminary assessment. Final decision pending full review.*"""
    
    def _generate_partial_analysis_response(self, analysis_result: Dict, key_facts: str, qualification_status: str, key_findings: str, next_steps: str) -> str:
        """Generate response when some documents are still missing"""
        borrower_name = analysis_result.get('borrower_name', 'Borrower')
        
        return f"""Hi {borrower_name},

**PARTIAL ANALYSIS COMPLETE**

**LOAN SUMMARY:**
{key_facts}

**CURRENT STATUS:**
{qualification_status}

**KEY FINDINGS:**
{key_findings}

**MISSING DOCUMENTS:**
{next_steps}

**QUICK COMPLETION:**
1. Provide the missing documents above
2. Reply to this email with all documents attached
3. We'll complete the full analysis in 5 minutes

**Your dream home is waiting - let's complete this together!**

---
*This is a partial assessment. Complete analysis pending missing documents.*"""
    
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
            elif any(word in filename for word in ['funds', 'down', 'payment', 'proof']):
                document_types.append('proof_of_funds')
            else:
                document_types.append('other')
        
        return document_types
    
    def _extract_key_facts_from_analysis(self, analysis_result: Dict) -> str:
        """Extract and format key facts from analysis result"""
        facts = []
        
        # Basic loan info
        if analysis_result.get('loan_amount'):
            try:
                loan_amount = int(analysis_result['loan_amount'])
                facts.append(f"• Loan Amount: ${loan_amount:,}")
            except (ValueError, TypeError):
                facts.append(f"• Loan Amount: {analysis_result['loan_amount']}")
        
        if analysis_result.get('property_value'):
            try:
                property_value = int(analysis_result['property_value'])
                facts.append(f"• Property Value: ${property_value:,}")
            except (ValueError, TypeError):
                facts.append(f"• Property Value: {analysis_result['property_value']}")
        
        if analysis_result.get('credit_score'):
            facts.append(f"• Credit Score: {analysis_result['credit_score']}")
        
        if analysis_result.get('property_type'):
            facts.append(f"• Property Type: {analysis_result['property_type']}")
        
        if analysis_result.get('property_location'):
            facts.append(f"• Location: {analysis_result['property_location']}")
        
        # Income info
        if analysis_result.get('monthly_income'):
            try:
                monthly_income = int(analysis_result['monthly_income'])
                facts.append(f"• Monthly Income: ${monthly_income:,}")
            except (ValueError, TypeError):
                facts.append(f"• Monthly Income: {analysis_result['monthly_income']}")
        
        if analysis_result.get('employer'):
            facts.append(f"• Employer: {analysis_result['employer']}")
        
        # Asset info
        if analysis_result.get('bank_balance'):
            try:
                bank_balance = int(analysis_result['bank_balance'])
                facts.append(f"• Bank Balance: ${bank_balance:,}")
            except (ValueError, TypeError):
                facts.append(f"• Bank Balance: {analysis_result['bank_balance']}")
        
        # Down payment
        if analysis_result.get('down_payment'):
            try:
                down_payment = int(analysis_result['down_payment'])
                facts.append(f"• Down Payment: ${down_payment:,}")
            except (ValueError, TypeError):
                facts.append(f"• Down Payment: {analysis_result['down_payment']}")
        
        if not facts:
            return "• Basic loan information provided"
        
        return "\n".join(facts) 