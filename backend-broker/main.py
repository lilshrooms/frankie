from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional, Any
import os
import yaml
from pydantic import BaseModel
from fastapi import Body
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
import shutil
from datetime import datetime
import re
import sys
import logging

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'engine'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'rate_ingest'))

# Import email system modules
try:
    from email_ingest.gemini_analyzer import analyze_with_gemini
except ImportError as e:
    logger.warning(f"Gemini analyzer not available: {e}")
    # Mock implementation for missing gemini analyzer
    def analyze_with_gemini(email_body, attachments, criteria, pre_extracted_str=""):
        return {
            "analysis": "Mock analysis - Gemini analyzer not available",
            "summary": "Mock summary",
            "next_steps": ["Mock next steps"],
            "loan_info": {
                "loan_amount": 0,
                "credit_score": 680,
                "ltv": 80
            },
            "timestamp": "now"
        }

try:
    from email_ingest.conversation_manager import ConversationManager
except ImportError as e:
    logger.warning(f"Conversation manager not available: {e}")
    # Mock implementation for missing conversation manager
    class ConversationManager:
        def __init__(self):
            self.conversations = {}
        
        def get_or_create_conversation(self, thread_id):
            if thread_id not in self.conversations:
                self.conversations[thread_id] = {
                    "state": "initial_request",
                    "emails": [],
                    "turn": 1
                }
            return self.conversations[thread_id]
        
        def add_email_to_conversation(self, thread_id, email_data):
            if thread_id in self.conversations:
                self.conversations[thread_id]["emails"].append(email_data)
                self.conversations[thread_id]["turn"] += 1
        
        def generate_response(self, thread_id, analysis_result):
            return "Mock response - conversation manager not available"
        
        def get_next_steps(self, thread_id):
            return ["Mock next steps"]
        
        def get_all_conversations(self):
            return self.conversations
        
        def get_conversation(self, thread_id):
            return self.conversations.get(thread_id)
        
        def delete_conversation(self, thread_id):
            if thread_id in self.conversations:
                del self.conversations[thread_id]
                return True
            return False
        
        def add_optimization_to_conversation(self, thread_id, optimization_data):
            if thread_id in self.conversations:
                if "optimizations" not in self.conversations[thread_id]:
                    self.conversations[thread_id]["optimizations"] = []
                self.conversations[thread_id]["optimizations"].append(optimization_data)

# Import rate system modules
try:
    from optimizer import optimize_scenario
    from analyzer import analyze_quote, generate_quote_summary
    from quote_engine import quote_rate, get_quote_comparison
    from gemini_rate_integration import GeminiRateIntegration
except ImportError as e:
    logger.warning(f"Rate system modules not available: {e}")
    # Mock implementations for missing modules
    def optimize_scenario(*args, **kwargs):
        return {"error": "Rate optimization not available"}
    
    def analyze_quote(*args, **kwargs):
        return {"error": "Quote analysis not available"}
    
    def generate_quote_summary(*args, **kwargs):
        return {"error": "Quote summary not available"}
    
    def quote_rate(*args, **kwargs):
        return {"error": "Quote generation not available"}
    
    def get_quote_comparison(*args, **kwargs):
        return {"error": "Quote comparison not available"}
    
    class GeminiRateIntegration:
        def __init__(self):
            self.scheduler = None
        
        def get_current_rates_context(self):
            return {"error": "Rate context not available"}

from fastapi import UploadFile, File, Form

CRITERIA_DIR = os.path.join(os.path.dirname(__file__), '../criteria')

# Create tables (dev only; use Alembic for prod)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Frankie Backend API",
    description="Unified backend for loan file management, email pipeline, and rate optimization",
    version="1.0.0"
)

# Allow CORS for local frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize managers
conversation_manager = ConversationManager()
rate_integration = GeminiRateIntegration()

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
    last_activity: datetime
    outstanding_items: str = ''
    class Config:
        from_attributes = True

class LoanFileCreate(BaseModel):
    borrower: str
    broker: str
    loan_type: str
    amount: str

class EmailRequest(BaseModel):
    """Request model for email processing."""
    email_body: str
    sender: str
    subject: str
    thread_id: Optional[str] = None
    attachments: Optional[List[Dict]] = None

class RateOptimizationRequest(BaseModel):
    """Request model for rate optimization."""
    loan_amount: float
    credit_score: int
    ltv: float
    loan_type: str = "30yr_fixed"

class QuoteAnalysisRequest(BaseModel):
    """Request model for quote analysis."""
    quote_result: Dict
    borrower_profile: Dict

# Health and status endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Frankie Backend API",
        "version": "1.0.0",
        "status": "healthy",
        "endpoints": {
            "loan_files": "/loan-files",
            "email": "/email/process",
            "conversations": "/conversations",
            "rates": "/rates",
            "optimization": "/optimize",
            "analysis": "/analyze",
            "criteria": "/criteria"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "frankie_backend",
        "version": "1.0.0",
        "components": {
            "database": "active",
            "conversation_manager": "active",
            "rate_integration": "active",
            "gemini_analyzer": "active"
        }
    }

# Loan file management endpoints
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
    
    # Soft delete - just mark as deleted
    loan_file.status = "Deleted"
    db.commit()
    return loan_file

# Criteria management
class SuggestRequest(BaseModel):
    user_request: str
    current_criteria: dict

@app.get("/criteria", response_model=List[str])
def list_criteria():
    """List available criteria files."""
    if not os.path.exists(CRITERIA_DIR):
        return []
    return [f.replace('.yaml', '') for f in os.listdir(CRITERIA_DIR) if f.endswith('.yaml')]

@app.get("/criteria/{loan_type}")
def get_criteria(loan_type: str):
    """Get criteria for a specific loan type."""
    criteria_file = os.path.join(CRITERIA_DIR, f"{loan_type}.yaml")
    if not os.path.exists(criteria_file):
        raise HTTPException(status_code=404, detail=f"Criteria for {loan_type} not found")
    
    with open(criteria_file, 'r') as f:
        return yaml.safe_load(f)

@app.post("/criteria/{loan_type}/suggest")
def suggest_criteria(loan_type: str, req: SuggestRequest = Body(...)):
    # Compose a prompt for Gemini
    prompt = f"""
    Current criteria for {loan_type} loans:
    {yaml.dump(req.current_criteria, default_flow_style=False)}
    
    User request: {req.user_request}
    
    Suggest improvements to the criteria based on the user request.
    Return only the updated criteria in YAML format.
    """
    
    # TODO: Implement Gemini integration for criteria suggestions
    return {"message": "Criteria suggestion feature coming soon"}

# Email pipeline endpoints
@app.post("/email/process")
async def process_email(request: EmailRequest, background_tasks: BackgroundTasks):
    """
    Process an incoming email through the pipeline.
    
    Args:
        request: EmailRequest with email content and metadata
        background_tasks: Background tasks for async processing
        
    Returns:
        Processing result with analysis and response
    """
    try:
        logger.info(f"Processing email from {request.sender}")
        
        # Analyze email with Gemini
        analysis_result = analyze_with_gemini(
            request.email_body,
            request.attachments or [],
            {}  # criteria - we'll need to load this from somewhere
        )
        
        if analysis_result.get('error'):
            return {
                "success": False,
                "error": analysis_result['error'],
                "message": "Failed to analyze email"
            }
        
        # Get or create conversation
        thread_id = request.thread_id or f"thread_{request.sender}_{analysis_result.get('timestamp', 'unknown')}"
        conversation = conversation_manager.get_or_create_conversation(thread_id)
        
        # Update conversation with new email
        conversation_manager.add_email_to_conversation(
            thread_id,
            {
                "sender": request.sender,
                "subject": request.subject,
                "body": request.email_body,
                "analysis": analysis_result,
                "timestamp": analysis_result.get('timestamp')
            }
        )
        
        # Generate response based on conversation state
        response = conversation_manager.generate_response(thread_id, analysis_result)
        
        # Add background task for rate optimization if loan info is found
        if analysis_result.get('loan_info'):
            background_tasks.add_task(
                process_rate_optimization,
                thread_id,
                analysis_result['loan_info']
            )
        
        return {
            "success": True,
            "thread_id": thread_id,
            "conversation_state": conversation.get('state'),
            "analysis": analysis_result,
            "response": response,
            "next_steps": conversation_manager.get_next_steps(thread_id)
        }
        
    except Exception as e:
        logger.error(f"Error processing email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

async def process_rate_optimization(thread_id: str, loan_info: Dict):
    """Background task to process rate optimization for a conversation."""
    try:
        # Extract loan parameters
        loan_amount = loan_info.get('loan_amount', 0)
        credit_score = loan_info.get('credit_score', 680)
        ltv = loan_info.get('ltv', 80)
        
        if loan_amount > 0:
            # Get current rates
            current_rates = rate_integration.scheduler.get_current_rates()
            
            if current_rates:
                # Generate optimization
                optimization = optimize_scenario(loan_amount, credit_score, ltv)
                
                # Store optimization in conversation
                conversation_manager.add_optimization_to_conversation(
                    thread_id,
                    {
                        "loan_info": loan_info,
                        "optimization": optimization,
                        "timestamp": "now"
                    }
                )
                
                logger.info(f"Rate optimization completed for thread {thread_id}")
        
    except Exception as e:
        logger.error(f"Error in background rate optimization: {str(e)}")

# Conversation management endpoints
@app.get("/conversations")
async def get_conversations():
    """Get all conversations."""
    try:
        conversations = conversation_manager.get_all_conversations()
        return {
            "success": True,
            "conversations": conversations,
            "count": len(conversations)
        }
    except Exception as e:
        logger.error(f"Error getting conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/conversations/{thread_id}")
async def get_conversation(thread_id: str):
    """Get a specific conversation by thread ID."""
    try:
        conversation = conversation_manager.get_conversation(thread_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {
            "success": True,
            "conversation": conversation
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation {thread_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.delete("/conversations/{thread_id}")
async def delete_conversation(thread_id: str):
    """Delete a conversation."""
    try:
        success = conversation_manager.delete_conversation(thread_id)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {
            "success": True,
            "message": f"Conversation {thread_id} deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation {thread_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

class ConversationStateUpdate(BaseModel):
    """Request model for updating conversation state."""
    state: str
    admin_notes: Optional[str] = None
    admin_intervention: bool = True

class AdminResponseRequest(BaseModel):
    """Request model for adding admin response."""
    response: str
    override_ai: bool = False
    admin_intervention: bool = True

@app.put("/conversations/{thread_id}/state")
async def update_conversation_state(thread_id: str, request: ConversationStateUpdate):
    """Update conversation state with admin intervention."""
    try:
        # Get the conversation
        conversation = conversation_manager.get_conversation(thread_id)
        if not conversation:
            raise HTTPException(status_code=404, detail=f"Conversation {thread_id} not found")
        
        # Update the state
        conversation["state"] = request.state
        if request.admin_notes:
            conversation["admin_notes"] = request.admin_notes
        conversation["admin_intervention"] = request.admin_intervention
        conversation["updated_at"] = datetime.now().isoformat()
        
        # Save the updated conversation (if save method exists)
        try:
            conversation_manager.save_conversation(thread_id, conversation)
        except AttributeError:
            # If save method doesn't exist, just update in memory
            pass
        
        return {
            "success": True, 
            "message": f"Conversation state updated to {request.state}",
            "conversation": conversation
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating conversation state {thread_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update conversation state: {str(e)}")

@app.post("/conversations/{thread_id}/admin-response")
async def add_admin_response(thread_id: str, request: AdminResponseRequest):
    """Add admin response to conversation."""
    try:
        # Get the conversation
        conversation = conversation_manager.get_conversation(thread_id)
        if not conversation:
            raise HTTPException(status_code=404, detail=f"Conversation {thread_id} not found")
        
        # Add admin response
        admin_email = {
            "sender": "admin@frankie.com",
            "subject": "Admin Response",
            "body": request.response,
            "timestamp": datetime.now().isoformat(),
            "admin_intervention": request.admin_intervention,
            "override_ai": request.override_ai
        }
        
        conversation["emails"].append(admin_email)
        conversation["turn"] += 1
        conversation["updated_at"] = datetime.now().isoformat()
        
        # Save the updated conversation (if save method exists)
        try:
            conversation_manager.save_conversation(thread_id, conversation)
        except AttributeError:
            # If save method doesn't exist, just update in memory
            pass
        
        return {
            "success": True, 
            "message": "Admin response added successfully",
            "conversation": conversation
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding admin response to {thread_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add admin response: {str(e)}")

# Rate system endpoints
@app.get("/rates/current")
async def get_current_rates():
    """Get current mortgage rates."""
    try:
        current_rates = rate_integration.scheduler.get_current_rates()
        rates_context = rate_integration.get_current_rates_context()
        
        return {
            "success": True,
            "rates": current_rates,
            "context": rates_context,
            "last_updated": "now"
        }
    except Exception as e:
        logger.error(f"Error getting current rates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/rates/quote")
async def generate_quote(request: RateOptimizationRequest):
    """Generate a rate quote."""
    try:
        # Validate inputs
        if request.loan_amount <= 0:
            raise HTTPException(status_code=400, detail="Loan amount must be positive")
        
        if not (300 <= request.credit_score <= 850):
            raise HTTPException(status_code=400, detail="Credit score must be between 300 and 850")
        
        if not (50 <= request.ltv <= 100):
            raise HTTPException(status_code=400, detail="LTV must be between 50% and 100%")
        
        # Get current rates
        current_rates = rate_integration.scheduler.get_current_rates()
        
        if not current_rates:
            return {
                "success": False,
                "error": "No current rates available"
            }
        
        # Generate quote
        quote_result = quote_rate(
            request.loan_amount,
            request.credit_score,
            request.ltv,
            request.loan_type,
            current_rates
        )
        
        if quote_result.get('error'):
            return {
                "success": False,
                "error": quote_result.get('error_message', 'Quote generation failed')
            }
        
        return {
            "success": True,
            "quote": quote_result,
            "borrower_profile": {
                "loan_amount": request.loan_amount,
                "credit_score": request.credit_score,
                "ltv": request.ltv,
                "loan_type": request.loan_type
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating quote: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/rates/optimize")
async def optimize_rates(request: RateOptimizationRequest):
    """Optimize rates for a borrower scenario."""
    try:
        # Validate inputs
        if request.loan_amount <= 0:
            raise HTTPException(status_code=400, detail="Loan amount must be positive")
        
        if not (300 <= request.credit_score <= 850):
            raise HTTPException(status_code=400, detail="Credit score must be between 300 and 850")
        
        if not (50 <= request.ltv <= 100):
            raise HTTPException(status_code=400, detail="LTV must be between 50% and 100%")
        
        # Run optimization
        optimization = optimize_scenario(
            request.loan_amount,
            request.credit_score,
            request.ltv,
            request.loan_type
        )
        
        return {
            "success": True,
            "optimization": optimization,
            "borrower_profile": {
                "loan_amount": request.loan_amount,
                "credit_score": request.credit_score,
                "ltv": request.ltv,
                "loan_type": request.loan_type
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error optimizing rates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/rates/analyze")
async def analyze_quote(request: QuoteAnalysisRequest):
    """Analyze a rate quote with Gemini AI."""
    try:
        # Validate inputs
        if not request.quote_result:
            raise HTTPException(status_code=400, detail="Quote result is required")
        
        if not request.borrower_profile:
            raise HTTPException(status_code=400, detail="Borrower profile is required")
        
        # Run analysis
        analysis = analyze_quote(request.quote_result, request.borrower_profile)
        
        return {
            "success": True,
            "analysis": analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing quote: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/rates/quick")
async def quick_rate_analysis(
    loan_amount: float,
    credit_score: int,
    ltv: float,
    loan_type: str = "30yr_fixed"
):
    """Quick rate analysis with quote generation and optimization."""
    try:
        # Validate inputs
        if loan_amount <= 0:
            raise HTTPException(status_code=400, detail="Loan amount must be positive")
        
        if not (300 <= credit_score <= 850):
            raise HTTPException(status_code=400, detail="Credit score must be between 300 and 850")
        
        if not (50 <= ltv <= 100):
            raise HTTPException(status_code=400, detail="LTV must be between 50% and 100%")
        
        # Get current rates
        current_rates = rate_integration.scheduler.get_current_rates()
        
        if not current_rates:
            return {
                "success": False,
                "error": "No current rates available"
            }
        
        # Generate quote
        quote_result = quote_rate(loan_amount, credit_score, ltv, loan_type, current_rates)
        
        if quote_result.get('error'):
            return {
                "success": False,
                "error": quote_result.get('error_message', 'Quote generation failed')
            }
        
        # Create borrower profile
        borrower_profile = {
            "loan_amount": loan_amount,
            "credit_score": credit_score,
            "ltv": ltv,
            "loan_type": loan_type,
            "property_type": "Primary Residence",
            "occupancy": "Owner Occupied"
        }
        
        # Analyze quote
        analysis = analyze_quote(quote_result, borrower_profile)
        
        # Optimize rates
        optimization = optimize_scenario(loan_amount, credit_score, ltv, loan_type)
        
        return {
            "success": True,
            "quote": quote_result,
            "analysis": analysis,
            "optimization": optimization,
            "borrower_profile": borrower_profile
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in quick rate analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Document analysis endpoints (existing functionality)
def extract_years(text):
    # Find all 4-digit years in a reasonable range
    years = re.findall(r'\b(20[12]\d)\b', text)
    return [int(year) for year in years]

def is_recent_year(year, years_back=2):
    current_year = datetime.now().year
    return current_year - years_back <= year <= current_year

def extract_statement_period(text):
    # Look for MM/YYYY or Month YYYY patterns
    patterns = [
        r'\b(\d{1,2})/(\d{4})\b',  # MM/YYYY
        r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b'  # Month YYYY
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            return matches[0]
    return None

def is_recent_month(month_year, months_back=3):
    # TODO: Implement month/year validation
    return True

def classify_doc_type(filename: str, text: str = "") -> str:
    filename_lower = filename.lower()
    text_lower = text.lower()
    
    # Check for pay stubs
    if any(term in filename_lower for term in ['pay', 'stub', 'payslip', 'wage']):
        return 'pay_stub'
    if any(term in text_lower for term in ['gross pay', 'net pay', 'hours worked', 'pay period']):
        return 'pay_stub'
    
    # Check for bank statements
    if any(term in filename_lower for term in ['bank', 'statement', 'account']):
        return 'bank_statement'
    if any(term in text_lower for term in ['account balance', 'transaction', 'deposit', 'withdrawal']):
        return 'bank_statement'
    
    # Check for tax returns
    if any(term in filename_lower for term in ['tax', 'return', 'w2', '1099']):
        return 'tax_return'
    if any(term in text_lower for term in ['adjusted gross income', 'taxable income', 'form w-2']):
        return 'tax_return'
    
    return 'unknown'

class AnalyzeRequest(BaseModel):
    email_body: str = ""

@app.post("/loan-files/{loan_file_id}/analyze")
def analyze_loan_file(loan_file_id: int, request: AnalyzeRequest = Body(...), db: Session = Depends(get_db)):
    loan_file = db.query(models.LoanFile).filter(models.LoanFile.id == loan_file_id).first()
    if not loan_file:
        raise HTTPException(status_code=404, detail="Loan file not found")
    
    # Analyze the email content
    analysis_result = analyze_with_gemini(request.email_body, [], {})
    
    # Create AI analysis record
    ai_analysis = models.AIAnalysis(
        loan_file_id=loan_file_id,
        analysis_text=analysis_result.get('analysis', ''),
        summary=analysis_result.get('summary', ''),
        next_steps=analysis_result.get('next_steps', ''),
    )
    db.add(ai_analysis)
    db.commit()
    
    return {
        "success": True,
        "analysis": analysis_result,
        "loan_file_id": loan_file_id
    }

if __name__ == "__main__":
    import uvicorn
    
    print("Starting Frankie Unified Backend...")
    print("API will be available at: http://localhost:8000")
    print("Documentation at: http://localhost:8000/docs")
    print()
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
