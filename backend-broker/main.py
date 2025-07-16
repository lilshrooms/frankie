from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
import yaml
from pydantic import BaseModel
from fastapi import Body
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from . import models
from email_ingest.gemini_analyzer import analyze_with_gemini

CRITERIA_DIR = os.path.join(os.path.dirname(__file__), '../criteria')

# Create tables (dev only; use Alembic for prod)
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Allow CORS for local frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic schemas for API
class LoanFileOut(BaseModel):
    id: int
    borrower: str
    broker: str
    status: str
    last_activity: str
    outstanding_items: str = ''
    class Config:
        orm_mode = True

@app.get("/loan-files", response_model=List[LoanFileOut])
def list_loan_files(db: Session = Depends(get_db)):
    return db.query(models.LoanFile).all()

@app.get("/loan-files/{loan_file_id}", response_model=LoanFileOut)
def get_loan_file(loan_file_id: int, db: Session = Depends(get_db)):
    loan_file = db.query(models.LoanFile).filter(models.LoanFile.id == loan_file_id).first()
    if not loan_file:
        raise HTTPException(status_code=404, detail="Loan file not found")
    return loan_file

class SuggestRequest(BaseModel):
    user_request: str
    current_criteria: dict

@app.get("/criteria", response_model=List[str])
def list_criteria():
    files = [f for f in os.listdir(CRITERIA_DIR) if f.endswith('.yaml')]
    return files

@app.get("/criteria/{loan_type}")
def get_criteria(loan_type: str):
    path = os.path.join(CRITERIA_DIR, f"{loan_type}.yaml")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Criteria not found")
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    return data

@app.post("/criteria/{loan_type}/suggest")
def suggest_criteria(loan_type: str, req: SuggestRequest = Body(...)):
    # Compose a prompt for Gemini
    prompt = f"""
You are an AI assistant for loan underwriting. Here are the current criteria for {loan_type} loans:
{req.current_criteria}

A loan officer has requested: '{req.user_request}'

Suggest specific changes to the criteria as a YAML dictionary. Only include changed fields."
"""
    suggestion = analyze_with_gemini("", {"prompt": prompt})
    # Try to parse the YAML from Gemini's response
    try:
        suggested_criteria = yaml.safe_load(suggestion)
    except Exception:
        suggested_criteria = {"error": "Could not parse suggestion as YAML", "raw": suggestion}
    return {"suggested_criteria": suggested_criteria, "raw": suggestion}
