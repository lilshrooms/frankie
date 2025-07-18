from fastapi import FastAPI, HTTPException, Depends, status
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
from fastapi import UploadFile, File, Form
import shutil
from datetime import datetime
import re

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
    last_activity: datetime  # <-- change from str to datetime
    outstanding_items: str = ''
    class Config:
        orm_mode = True  # or 'from_attributes = True' for Pydantic v2

class LoanFileCreate(BaseModel):
    borrower: str
    broker: str
    loan_type: str
    amount: str

@app.get("/loan-files", response_model=List[LoanFileOut])
def list_loan_files(db: Session = Depends(get_db)):
    return db.query(models.LoanFile).all()

@app.get("/loan-files/{loan_file_id}", response_model=LoanFileOut)
def get_loan_file(loan_file_id: int, db: Session = Depends(get_db)):
    loan_file = db.query(models.LoanFile).filter(models.LoanFile.id == loan_file_id).first()
    if not loan_file:
        raise HTTPException(status_code=404, detail="Loan file not found")
    return loan_file

@app.post("/loan-files", response_model=LoanFileOut)
def create_loan_file(
    borrower: str = Form(...),
    broker: str = Form(...),
    loan_type: str = Form(...),
    amount: str = Form(...),
    document: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    # Create the LoanFile
    loan_file = models.LoanFile(
        borrower=borrower,
        broker=broker,
        status="Incomplete",
        last_activity=datetime.utcnow(),
        outstanding_items="",
    )
    db.add(loan_file)
    db.commit()
    db.refresh(loan_file)

    # Handle document upload
    if document:
        upload_dir = os.path.join(os.path.dirname(__file__), "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, f"loanfile_{loan_file.id}_{document.filename}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(document.file, buffer)
        attachment = models.Attachment(
            loan_file_id=loan_file.id,
            filename=document.filename,
            file_url=file_path,
            uploaded_by=broker,
        )
        db.add(attachment)
        db.commit()

    return loan_file

@app.delete("/loan-files/{loan_file_id}", response_model=LoanFileOut, status_code=status.HTTP_200_OK)
def soft_delete_loan_file(loan_file_id: int, db: Session = Depends(get_db)):
    loan_file = db.query(models.LoanFile).filter(models.LoanFile.id == loan_file_id).first()
    if not loan_file:
        raise HTTPException(status_code=404, detail="Loan file not found")
    loan_file.status = "deleted"
    db.commit()
    db.refresh(loan_file)
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

import pdfplumber
from PIL import Image
import pytesseract
import io

def extract_years(text):
    # Find all 4-digit years in a reasonable range
    years = re.findall(r'(20[0-2][0-9])', text)
    return [int(y) for y in years if 2000 <= int(y) <= datetime.now().year]

def is_recent_year(year, years_back=2):
    current_year = datetime.now().year
    return current_year - year < years_back

def extract_statement_period(text):
    # Look for MM/YYYY or Month YYYY patterns
    matches = re.findall(r'(0[1-9]|1[0-2])[\-/](20[0-2][0-9])', text)
    return [f"{m[0]}/{m[1]}" for m in matches]

def is_recent_month(month_year, months_back=3):
    try:
        dt = datetime.strptime(month_year, "%m/%Y")
        now = datetime.now()
        diff = (now.year - dt.year) * 12 + (now.month - dt.month)
        return diff < months_back
    except Exception:
        return False

def classify_doc_type(filename: str, text: str = "") -> str:
    name = filename.lower()
    text = (text or "").lower()
    if "w2" in name: return "W2"
    if "1099" in name: return "1099"
    if "paystub" in name or "pay-stub" in name: return "Paystub"
    if "bank" in name or "statement" in name: return "Bank Statement"
    if "appraisal" in name: return "Appraisal"
    if "tax" in name: return "Tax Document"
    if "id" in name or "driver" in name or "passport" in name: return "ID"
    if "wage and tax statement" in text and "form w-2" in text: return "W2"
    if "statement period" in text and "account number" in text: return "Bank Statement"
    if "appraisal report" in text: return "Appraisal"
    if "irs form 1099" in text: return "1099"
    if "pay period" in text and "net pay" in text: return "Paystub"
    if "social security number" in text and "date of birth" in text: return "ID"
    return "Unknown"

@app.post("/loan-files/{loan_file_id}/analyze")
def analyze_loan_file(loan_file_id: int, db: Session = Depends(get_db)):
    # 1. Fetch loan file and attachments
    loan_file = db.query(models.LoanFile).filter(models.LoanFile.id == loan_file_id).first()
    if not loan_file:
        raise HTTPException(status_code=404, detail="Loan file not found")
    attachments = db.query(models.Attachment).filter(models.Attachment.loan_file_id == loan_file_id).all()
    if not attachments:
        raise HTTPException(status_code=404, detail="No attachments found for this loan file")

    # 2. For each attachment: parse PDF or image
    extracted_texts = []
    for att in attachments:
        file_path = att.file_url if isinstance(att.file_url, str) else str(att.file_url)
        if file_path.lower().endswith('.pdf'):
            try:
                with pdfplumber.open(file_path) as pdf:
                    text = "".join([page.extract_text() or "" for page in pdf.pages])
                extracted_texts.append(text)
            except Exception as e:
                extracted_texts.append(f"[PDF parse error: {e}]")
        elif file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
            try:
                with Image.open(file_path) as img:
                    text = pytesseract.image_to_string(img)
                extracted_texts.append(text)
            except Exception as e:
                extracted_texts.append(f"[Image OCR error: {e}]")
        else:
            extracted_texts.append(f"[Unsupported file type: {file_path}]")

    # 3. Combine all extracted text
    attachments_text = "\n\n".join(extracted_texts)

    # 4. Run Gemini analysis
    from email_ingest.gemini_analyzer import analyze_with_gemini
    # For now, use empty strings for email_body, criteria, pre_extracted_str
    analysis_result = analyze_with_gemini("", attachments_text, {}, "")

    # 5. Store result in AIAnalysis table
    analysis = models.AIAnalysis(
        loan_file_id=loan_file.id,
        analysis_text=analysis_result,
        summary=analysis_result[:200],  # First 200 chars as summary
        next_steps="",  # Could extract next steps from analysis_result
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    # 6. Return result
    checklist = []
    for att, text in zip(attachments, extracted_texts):
        filename = att.filename if isinstance(att.filename, str) else str(att.filename)
        doc_type = classify_doc_type(filename, text)
        # Recency check for W2
        if doc_type == "W2":
            years = extract_years(text)
            if years and any(is_recent_year(y, 2) for y in years):
                recency = f"Recent W2 ({max(years)})"
            else:
                recency = f"No recent W2 ({years if years else 'none found'})"
        # Recency check for Bank Statement
        elif doc_type == "Bank Statement":
            periods = extract_statement_period(text)
            if periods and any(is_recent_month(p, 3) for p in periods):
                recency = f"Recent Bank Statement ({max(periods)})"
            else:
                recency = f"No recent Bank Statement ({periods if periods else 'none found'})"
        else:
            recency = "N/A"
        checklist.append({
            "filename": filename,
            "doc_type": doc_type,
            "recency": recency
        })

    return {
        "loan_file_id": loan_file.id,
        "analysis_id": analysis.id,
        "analysis_text": analysis.analysis_text,
        "summary": analysis.summary,
        "next_steps": analysis.next_steps,
        "checklist": checklist
    }
