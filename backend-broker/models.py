from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class LoanFile(Base):
    __tablename__ = 'loan_files'
    id = Column(Integer, primary_key=True, index=True)
    borrower = Column(String, index=True)
    broker = Column(String, index=True)
    status = Column(String, default='Incomplete')
    last_activity = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    outstanding_items = Column(Text)  # Comma-separated or JSON string
    emails = relationship('EmailMessage', back_populates='loan_file')
    analyses = relationship('AIAnalysis', back_populates='loan_file')
    actions = relationship('UserAction', back_populates='loan_file')
    attachments = relationship('Attachment', back_populates='loan_file')

class EmailMessage(Base):
    __tablename__ = 'email_messages'
    id = Column(Integer, primary_key=True, index=True)
    loan_file_id = Column(Integer, ForeignKey('loan_files.id'))
    sender = Column(String)
    recipient = Column(String)
    subject = Column(String)
    body = Column(Text)
    timestamp = Column(DateTime, default=func.now())
    attachments = Column(Text)  # Comma-separated or JSON string
    loan_file = relationship('LoanFile', back_populates='emails')

class AIAnalysis(Base):
    __tablename__ = 'ai_analyses'
    id = Column(Integer, primary_key=True, index=True)
    loan_file_id = Column(Integer, ForeignKey('loan_files.id'))
    analysis_text = Column(Text)
    summary = Column(Text)
    next_steps = Column(Text)
    created_at = Column(DateTime, default=func.now())
    loan_file = relationship('LoanFile', back_populates='analyses')

class UserAction(Base):
    __tablename__ = 'user_actions'
    id = Column(Integer, primary_key=True, index=True)
    loan_file_id = Column(Integer, ForeignKey('loan_files.id'))
    user_id = Column(String)
    action_type = Column(String)
    details = Column(Text)
    timestamp = Column(DateTime, default=func.now())
    loan_file = relationship('LoanFile', back_populates='actions')

class Attachment(Base):
    __tablename__ = 'attachments'
    id = Column(Integer, primary_key=True, index=True)
    loan_file_id = Column(Integer, ForeignKey('loan_files.id'))
    filename = Column(String)
    file_url = Column(String)
    uploaded_by = Column(String)
    uploaded_at = Column(DateTime, default=func.now())
    doc_type = Column(String, default='Unknown')  # New field for document type
    loan_file = relationship('LoanFile', back_populates='attachments') 