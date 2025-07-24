#!/usr/bin/env python3
"""
Frankie Database Migration Script
Migrates from SQLite to Supabase PostgreSQL
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database import Base, SessionLocal
import models
import json
from datetime import datetime

def create_supabase_engine():
    """Create Supabase PostgreSQL engine"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set!")
        print("Please set it to your Supabase PostgreSQL connection string")
        print("Example: postgresql://postgres:password@db.xxx.supabase.co:5432/postgres")
        sys.exit(1)
    
    try:
        engine = create_engine(database_url)
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Successfully connected to Supabase!")
        return engine
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        sys.exit(1)

def create_sqlite_engine():
    """Create local SQLite engine for reading existing data"""
    try:
        engine = create_engine('sqlite:///./frankie.db')
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Successfully connected to local SQLite database!")
        return engine
    except Exception as e:
        print(f"❌ Failed to connect to local SQLite: {e}")
        sys.exit(1)

def migrate_schema(supabase_engine):
    """Create tables in Supabase"""
    print("📋 Creating tables in Supabase...")
    try:
        Base.metadata.create_all(bind=supabase_engine)
        print("✅ Tables created successfully!")
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        sys.exit(1)

def migrate_data(sqlite_engine, supabase_engine):
    """Migrate data from SQLite to Supabase"""
    print("🔄 Migrating data...")
    
    # Create sessions
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    SupabaseSession = sessionmaker(bind=supabase_engine)
    
    sqlite_session = SQLiteSession()
    supabase_session = SupabaseSession()
    
    try:
        # Migrate LoanFiles
        print("Migrating loan files...")
        loan_files = sqlite_session.query(models.LoanFile).all()
        for loan_file in loan_files:
            new_loan_file = models.LoanFile(
                id=loan_file.id,
                borrower=loan_file.borrower,
                broker=loan_file.broker,
                status=loan_file.status,
                last_activity=loan_file.last_activity,
                created_at=loan_file.created_at,
                updated_at=loan_file.updated_at,
                outstanding_items=loan_file.outstanding_items,
                gmail_thread_id=getattr(loan_file, 'gmail_thread_id', None),
                conversation_state=getattr(loan_file, 'conversation_state', 'initial_request'),
                conversation_summary=getattr(loan_file, 'conversation_summary', None),
                requested_documents=getattr(loan_file, 'requested_documents', None),
                received_documents=getattr(loan_file, 'received_documents', None)
            )
            supabase_session.add(new_loan_file)
        
        # Migrate EmailMessages
        print("Migrating email messages...")
        email_messages = sqlite_session.query(models.EmailMessage).all()
        for email in email_messages:
            new_email = models.EmailMessage(
                id=email.id,
                loan_file_id=email.loan_file_id,
                sender=email.sender,
                recipient=email.recipient,
                subject=email.subject,
                body=email.body,
                timestamp=email.timestamp,
                attachments=email.attachments,
                gmail_message_id=getattr(email, 'gmail_message_id', None),
                gmail_thread_id=getattr(email, 'gmail_thread_id', None),
                is_processed=getattr(email, 'is_processed', False)
            )
            supabase_session.add(new_email)
        
        # Migrate AIAnalyses
        print("Migrating AI analyses...")
        ai_analyses = sqlite_session.query(models.AIAnalysis).all()
        for analysis in ai_analyses:
            new_analysis = models.AIAnalysis(
                id=analysis.id,
                loan_file_id=analysis.loan_file_id,
                analysis_text=analysis.analysis_text,
                summary=analysis.summary,
                next_steps=analysis.next_steps,
                created_at=analysis.created_at,
                conversation_turn=getattr(analysis, 'conversation_turn', 1),
                context_summary=getattr(analysis, 'context_summary', None),
                new_information=getattr(analysis, 'new_information', None)
            )
            supabase_session.add(new_analysis)
        
        # Migrate UserActions
        print("Migrating user actions...")
        user_actions = sqlite_session.query(models.UserAction).all()
        for action in user_actions:
            new_action = models.UserAction(
                id=action.id,
                loan_file_id=action.loan_file_id,
                user_id=action.user_id,
                action_type=action.action_type,
                details=action.details,
                timestamp=action.timestamp
            )
            supabase_session.add(new_action)
        
        # Migrate Attachments
        print("Migrating attachments...")
        attachments = sqlite_session.query(models.Attachment).all()
        for attachment in attachments:
            new_attachment = models.Attachment(
                id=attachment.id,
                loan_file_id=attachment.loan_file_id,
                filename=attachment.filename,
                file_url=attachment.file_url,
                uploaded_by=attachment.uploaded_by,
                uploaded_at=attachment.uploaded_at,
                doc_type=attachment.doc_type,
                email_message_id=getattr(attachment, 'email_message_id', None)
            )
            supabase_session.add(new_attachment)
        
        # Commit all changes
        supabase_session.commit()
        print("✅ Data migration completed successfully!")
        
        # Print summary
        print(f"📊 Migration Summary:")
        print(f"   - Loan Files: {len(loan_files)}")
        print(f"   - Email Messages: {len(email_messages)}")
        print(f"   - AI Analyses: {len(ai_analyses)}")
        print(f"   - User Actions: {len(user_actions)}")
        print(f"   - Attachments: {len(attachments)}")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        supabase_session.rollback()
        sys.exit(1)
    finally:
        sqlite_session.close()
        supabase_session.close()

def verify_migration(supabase_engine):
    """Verify the migration was successful"""
    print("🔍 Verifying migration...")
    
    SupabaseSession = sessionmaker(bind=supabase_engine)
    session = SupabaseSession()
    
    try:
        # Check table counts
        loan_files_count = session.query(models.LoanFile).count()
        email_messages_count = session.query(models.EmailMessage).count()
        ai_analyses_count = session.query(models.AIAnalysis).count()
        user_actions_count = session.query(models.UserAction).count()
        attachments_count = session.query(models.Attachment).count()
        
        print(f"✅ Verification complete:")
        print(f"   - Loan Files: {loan_files_count}")
        print(f"   - Email Messages: {email_messages_count}")
        print(f"   - AI Analyses: {ai_analyses_count}")
        print(f"   - User Actions: {user_actions_count}")
        print(f"   - Attachments: {attachments_count}")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        sys.exit(1)
    finally:
        session.close()

def main():
    """Main migration function"""
    print("🚀 Frankie Database Migration to Supabase")
    print("=" * 50)
    
    # Check if DATABASE_URL is set
    if not os.getenv('DATABASE_URL'):
        print("❌ DATABASE_URL environment variable not set!")
        print("Please set it to your Supabase PostgreSQL connection string")
        print("Example: export DATABASE_URL='postgresql://postgres:password@db.xxx.supabase.co:5432/postgres'")
        sys.exit(1)
    
    # Create engines
    supabase_engine = create_supabase_engine()
    sqlite_engine = create_sqlite_engine()
    
    # Run migration
    migrate_schema(supabase_engine)
    migrate_data(sqlite_engine, supabase_engine)
    verify_migration(supabase_engine)
    
    print("\n🎉 Migration completed successfully!")
    print("Your Frankie database is now running on Supabase!")
    print("\nNext steps:")
    print("1. Update your backend to use the new DATABASE_URL")
    print("2. Test the application with the new database")
    print("3. Deploy to production with the Supabase connection")

if __name__ == "__main__":
    main() 