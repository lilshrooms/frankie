import datetime
from .database import SessionLocal
from .models import LoanFile

def seed_loan_files():
    db = SessionLocal()
    mock_files = [
        LoanFile(
            borrower='Natalie M Tan',
            broker='Ian Tan',
            status='Incomplete',
            last_activity=datetime.datetime(2024, 6, 10, 14, 23),
            outstanding_items='Credit Report, Purchase Agreement',
        ),
        LoanFile(
            borrower='John Smith',
            broker='Rett Johnson',
            status='Pending Docs',
            last_activity=datetime.datetime(2024, 6, 9, 10, 12),
            outstanding_items='Bank Statements',
        ),
        LoanFile(
            borrower='Alice Lee',
            broker='Ian Tan',
            status='Under Review',
            last_activity=datetime.datetime(2024, 6, 8, 16, 45),
            outstanding_items='',
        ),
        LoanFile(
            borrower='Michael Chen',
            broker='Rett Johnson',
            status='Complete',
            last_activity=datetime.datetime(2024, 6, 7, 9, 30),
            outstanding_items='',
        ),
        LoanFile(
            borrower='Priya Patel',
            broker='Ian Tan',
            status='Docs Needed',
            last_activity=datetime.datetime(2024, 6, 6, 11, 0),
            outstanding_items='W-2, Pay Stubs, Appraisal',
        ),
    ]
    db.add_all(mock_files)
    db.commit()
    db.close()
    print('Seeded mock loan files.')

if __name__ == '__main__':
    seed_loan_files() 