#!/usr/bin/env python3
"""
Test Supabase Connection
Verifies that the Supabase database connection is working correctly
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database import Base, SessionLocal
import models
from datetime import datetime

def test_connection():
    """Test basic database connection"""
    print("🔍 Testing Supabase connection...")
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set!")
        return False
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL: {version}")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_tables():
    """Test that all tables exist"""
    print("📋 Testing table structure...")
    
    database_url = os.getenv('DATABASE_URL')
    engine = create_engine(database_url)
    
    try:
        # Check if tables exist
        with engine.connect() as conn:
            tables = ['loan_files', 'email_messages', 'ai_analyses', 'user_actions', 'attachments']
            for table in tables:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.fetchone()[0]
                print(f"✅ Table {table}: {count} records")
        return True
    except Exception as e:
        print(f"❌ Table test failed: {e}")
        return False

def test_crud_operations():
    """Test Create, Read, Update, Delete operations"""
    print("🔄 Testing CRUD operations...")
    
    database_url = os.getenv('DATABASE_URL')
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Test CREATE
        print("Testing CREATE...")
        test_loan = models.LoanFile(
            borrower="Test Borrower",
            broker="Test Broker",
            status="test",
            outstanding_items="Test migration",
            created_at=datetime.now()
        )
        session.add(test_loan)
        session.commit()
        print(f"✅ Created loan file with ID: {test_loan.id}")
        
        # Test READ
        print("Testing READ...")
        loan = session.query(models.LoanFile).filter_by(id=test_loan.id).first()
        if loan:
            print(f"✅ Read loan file: {loan.borrower}")
        else:
            print("❌ Failed to read loan file")
            return False
        
        # Test UPDATE
        print("Testing UPDATE...")
        loan.status = "updated"
        session.commit()
        updated_loan = session.query(models.LoanFile).filter_by(id=test_loan.id).first()
        if updated_loan.status == "updated":
            print("✅ Updated loan file successfully")
        else:
            print("❌ Failed to update loan file")
            return False
        
        # Test DELETE
        print("Testing DELETE...")
        session.delete(loan)
        session.commit()
        deleted_loan = session.query(models.LoanFile).filter_by(id=test_loan.id).first()
        if deleted_loan is None:
            print("✅ Deleted loan file successfully")
        else:
            print("❌ Failed to delete loan file")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ CRUD test failed: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def test_api_endpoints():
    """Test that API endpoints work with Supabase"""
    print("🌐 Testing API endpoints...")
    
    try:
        import requests
        
        # Test health endpoint
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print("❌ Health endpoint failed")
            return False
        
        # Test loan files endpoint
        response = requests.get("http://localhost:8000/loan-files")
        if response.status_code == 200:
            print("✅ Loan files endpoint working")
        else:
            print("❌ Loan files endpoint failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Frankie Supabase Connection Test")
    print("=" * 40)
    
    # Check if DATABASE_URL is set
    if not os.getenv('DATABASE_URL'):
        print("❌ DATABASE_URL environment variable not set!")
        print("Please set it to your Supabase PostgreSQL connection string")
        print("Example: export DATABASE_URL='postgresql://postgres:password@db.xxx.supabase.co:5432/postgres'")
        sys.exit(1)
    
    # Run tests
    tests = [
        ("Connection", test_connection),
        ("Tables", test_tables),
        ("CRUD Operations", test_crud_operations),
        ("API Endpoints", test_api_endpoints)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} Test ---")
        if test_func():
            passed += 1
            print(f"✅ {test_name} test passed")
        else:
            print(f"❌ {test_name} test failed")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Supabase integration is working correctly.")
        print("\nYour Frankie backend is ready to use with Supabase!")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 