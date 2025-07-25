#!/usr/bin/env python3
"""
Migrate existing conversations from JSON to database
"""

import json
import os
import sys
from datetime import datetime

# Add backend-broker to path for database imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend-broker'))

try:
    from database import SessionLocal
    from models import LoanFile, EmailMessage, AIAnalysis, Attachment
    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"Database not available: {e}")
    DATABASE_AVAILABLE = False

def migrate_conversations():
    """Migrate conversations from JSON to database"""
    if not DATABASE_AVAILABLE:
        print("Database not available")
        return
    
    # Load conversations from JSON
    conversations_file = "conversations.json"
    if not os.path.exists(conversations_file):
        print(f"Conversations file {conversations_file} not found")
        return
    
    with open(conversations_file, 'r') as f:
        conversations = json.load(f)
    
    print(f"Found {len(conversations)} conversations to migrate")
    
    db = SessionLocal()
    try:
        migrated_count = 0
        
        for thread_id, conv_data in conversations.items():
            # Check if loan file already exists
            existing_loan = db.query(LoanFile).filter_by(gmail_thread_id=thread_id).first()
            
            if existing_loan:
                print(f"Loan file already exists for thread {thread_id}")
                continue
            
            # Create new loan file
            loan_file = LoanFile(
                gmail_thread_id=thread_id,
                borrower=conv_data.get('borrower_email', 'Unknown'),
                conversation_state=conv_data.get('conversation_state', 'initial_request'),
                conversation_summary=conv_data.get('conversation_summary', ''),
                requested_documents=conv_data.get('requested_documents', []),
                received_documents=conv_data.get('received_documents', []),
                status='Incomplete',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(loan_file)
            db.flush()  # Get the ID
            
            print(f"Created loan file {loan_file.id} for thread {thread_id}")
            migrated_count += 1
        
        db.commit()
        print(f"Successfully migrated {migrated_count} conversations to database")
        
    except Exception as e:
        print(f"Error migrating conversations: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_conversations() 