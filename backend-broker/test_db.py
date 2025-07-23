#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
import models

def main():
    db = SessionLocal()
    try:
        # Check loan files
        loan_files = db.query(models.LoanFile).all()
        print(f"Found {len(loan_files)} loan files")
        for lf in loan_files:
            print(f"  Loan File ID: {lf.id}, Borrower: {lf.borrower}, Status: {lf.status}")
        
        # Check email messages
        emails = db.query(models.EmailMessage).all()
        print(f"\nFound {len(emails)} email messages")
        for email in emails:
            print(f"  Email ID: {email.id}, Loan File: {email.loan_file_id}")
            print(f"    Subject: {email.subject}")
            print(f"    Body preview: {email.body[:100] if email.body else 'None'}...")
            print()
            
    finally:
        db.close()

if __name__ == "__main__":
    main() 