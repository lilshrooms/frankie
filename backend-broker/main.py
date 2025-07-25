from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks, Header
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
import secrets

# Import security module
try:
    from security import security_health, audit_logger, pii_encryption, session_manager
except ImportError as e:
    logger.warning(f"Security module not available: {e}")
    # Mock security implementations
    def security_health():
        return {"security_score": 0, "error": "Security module not available"}
    audit_logger = None
    pii_encryption = None
    session_manager = None

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Key for Gmail Add-on (in production, use environment variables)
GMAIL_ADDON_API_KEY = os.getenv("GMAIL_ADDON_API_KEY", "frankie-gmail-addon-key-2025")

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
    def optimize_scenario(loan_amount, credit_score, ltv, loan_type, current_rates):
        """Mock rate optimization function."""
        # Get current quote
        current_quote = quote_rate(loan_amount, credit_score, ltv, loan_type, current_rates)
        
        # Mock optimization suggestions
        optimizations = {
            "credit_score": {
                "current": credit_score,
                "recommended": min(credit_score + 20, 850),
                "rate_improvement": 0.00125 if credit_score < 680 else 0.0,
                "monthly_savings": 50 if credit_score < 680 else 0,
                "feasibility": "Moderate - requires credit improvement",
                "roi_analysis": "20-point credit score improvement could save $50/month"
            },
            "ltv": {
                "current": ltv,
                "recommended": max(ltv - 5, 50),
                "rate_improvement": 0.0025 if ltv > 80 else 0.0,
                "monthly_savings": 100 if ltv > 80 else 0,
                "down_payment_increase": (loan_amount * 0.05) if ltv > 80 else 0,
                "feasibility": "High - increase down payment",
                "roi_analysis": "5% additional down payment could save $100/month"
            },
            "loan_amount": {
                "current": loan_amount,
                "recommended": loan_amount * 0.95,
                "rate_improvement": 0.0005,
                "monthly_savings": 25,
                "feasibility": "Low - requires additional savings",
                "roi_analysis": "5% reduction in loan amount could save $25/month"
            }
        }
        
        # Determine best optimization
        best_optimization = "credit_score" if credit_score < 680 else "ltv" if ltv > 80 else "loan_amount"
        total_savings = sum(opt["monthly_savings"] for opt in optimizations.values())
        
        return {
            "current_scenario": current_quote,
            "optimizations": optimizations,
            "summary": {
                "best_optimization": best_optimization,
                "total_potential_savings": total_savings,
                "recommended_actions": [
                    "Improve credit score if below 680",
                    "Increase down payment if LTV > 80%",
                    "Consider reducing loan amount if possible"
                ]
            }
        }
    
    def analyze_quote(quote_result, borrower_profile):
        """Mock quote analysis function."""
        return {
            "explanation": f"Your rate of {quote_result['adjusted_rate']:.3%} is based on a base rate of {quote_result['base_rate']:.3%} with adjustments for your credit score ({borrower_profile['credit_score']}) and LTV ({borrower_profile['ltv']}%).",
            "improvement_suggestions": [
                {
                    "suggestion": "Improve your credit score",
                    "impact": "Could reduce your rate by 0.125%",
                    "action": "Pay bills on time and reduce credit utilization"
                },
                {
                    "suggestion": "Increase your down payment",
                    "impact": "Could reduce your rate by 0.25%",
                    "action": "Save additional funds for down payment"
                }
            ],
            "rate_breakdown": {
                "base_rate": quote_result["base_rate"],
                "adjustments": [
                    {
                        "type": "Credit Score Adjustment",
                        "amount": quote_result["llpas"]["credit_score_adjustment"],
                        "reason": f"Credit score of {borrower_profile['credit_score']}"
                    },
                    {
                        "type": "LTV Adjustment", 
                        "amount": quote_result["llpas"]["ltv_adjustment"],
                        "reason": f"LTV of {borrower_profile['ltv']}%"
                    }
                ],
                "final_rate": quote_result["adjusted_rate"]
            },
            "market_context": "Current market rates are competitive. Your rate reflects current market conditions and your specific borrower profile."
        }
    
    def generate_quote_summary(*args, **kwargs):
        return {"error": "Quote summary not available"}
    
    def quote_rate(loan_amount, credit_score, ltv, loan_type, current_rates):
        """Mock quote rate function."""
        # Get base rate for loan type
        base_rate = current_rates.get(loan_type, 0.0675)
        
        # Calculate LLPAs
        credit_adjustment = 0.0
        if credit_score < 680:
            credit_adjustment = 0.00125  # 0.125%
        
        ltv_adjustment = 0.0
        if ltv > 80:
            ltv_adjustment = 0.0025  # 0.25%
        
        total_adjustment = credit_adjustment + ltv_adjustment
        adjusted_rate = base_rate + total_adjustment
        
        # Calculate monthly payment (simplified)
        monthly_rate = adjusted_rate / 12
        num_payments = 360  # 30 years
        monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
        
        # Calculate total interest
        total_interest = (monthly_payment * num_payments) - loan_amount
        
        return {
            "loan_amount": loan_amount,
            "credit_score": credit_score,
            "ltv": ltv,
            "loan_type": loan_type,
            "base_rate": base_rate,
            "adjusted_rate": adjusted_rate,
            "monthly_payment": monthly_payment,
            "total_interest": total_interest,
            "llpas": {
                "credit_score_adjustment": credit_adjustment,
                "ltv_adjustment": ltv_adjustment,
                "total_adjustment": total_adjustment
            },
            "eligibility": {
                "approved": True,
                "reasons": ["Loan meets basic eligibility criteria"]
            }
        }
    
    def get_quote_comparison(*args, **kwargs):
        return {"error": "Quote comparison not available"}
    
    class GeminiRateIntegration:
        def __init__(self):
            self.scheduler = MockRateScheduler()
        
        def get_current_rates_context(self):
            return {
                "market_summary": "Current market rates are stable with slight variations",
                "trend": "Rates have been relatively flat over the past week",
                "recommendation": "Good time for borrowers to lock rates"
            }
    
    class MockRateScheduler:
        def get_current_rates(self):
            # Return simple rate object for frontend compatibility
            return {
                "30yr_fixed": 0.0675,  # 6.75%
                "15yr_fixed": 0.0625,  # 6.25%
                "fha_30yr": 0.0650,    # 6.50%
                "va_30yr": 0.0640,     # 6.40%
                "usda_30yr": 0.0660    # 6.60%
            }
        
        def get_detailed_rates(self):
            # Return detailed rate array for internal use
            return [
                {
                    "loan_type": "30yr_fixed",
                    "rate": 6.75,
                    "apr": 6.85,
                    "lock_period": 30,
                    "source": "mock",
                    "timestamp": datetime.now().isoformat(),
                    "fees": 1000
                },
                {
                    "loan_type": "15yr_fixed", 
                    "rate": 6.25,
                    "apr": 6.35,
                    "lock_period": 30,
                    "source": "mock",
                    "timestamp": datetime.now().isoformat(),
                    "fees": 800
                }
            ]

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
    """Health check endpoint with component status."""
    try:
        # Test database connection
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_status = "active"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "error"
    
    # Test conversation manager
    try:
        conversation_manager.get_all_conversations()
        conv_status = "active"
    except Exception as e:
        logger.error(f"Conversation manager health check failed: {e}")
        conv_status = "error"
    
    # Test rate integration
    try:
        rate_integration.get_current_rates_context()
        rate_status = "active"
    except Exception as e:
        logger.error(f"Rate integration health check failed: {e}")
        rate_status = "error"
    
    # Test Gemini analyzer
    try:
        analyze_with_gemini("test", [], {})
        gemini_status = "active"
    except Exception as e:
        logger.error(f"Gemini analyzer health check failed: {e}")
        gemini_status = "error"
    
    # Test security module
    try:
        security_status = "active" if security_health else "error"
    except Exception as e:
        logger.error(f"Security module health check failed: {e}")
        security_status = "error"
    
    return {
        "status": "healthy",
        "service": "frankie_backend",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "database": db_status,
            "conversation_manager": conv_status,
            "rate_integration": rate_status,
            "gemini_analyzer": gemini_status,
            "security": security_status
        }
    }

@app.get("/security/health")
async def security_health_check():
    """Security health check endpoint for compliance monitoring."""
    try:
        if security_health:
            security_status = security_health.run_security_checks()
        else:
            security_status = {
                "security_score": 0,
                "error": "Security module not available",
                "encryption_enabled": False,
                "mfa_required": False,
                "audit_logging": False,
                "access_control": False
            }
        
        return {
            "status": "security_check_complete",
            "timestamp": datetime.utcnow().isoformat(),
            "security_status": security_status
        }
    except Exception as e:
        logger.error(f"Security health check failed: {e}")
        return {
            "status": "security_check_failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
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
        
        # Convert array format to object format for frontend compatibility
        if isinstance(current_rates, list):
            # Convert array of rate objects to grouped format for frontend
            # Group rates by loan type and include all options
            rates_dict = {}
            for rate_obj in current_rates:
                loan_type = rate_obj.get('loan_type', '30yr_fixed')
                rate_value = rate_obj.get('rate', 0) / 100  # Convert percentage to decimal
                
                if loan_type not in rates_dict:
                    rates_dict[loan_type] = []
                
                rates_dict[loan_type].append({
                    "rate": rate_value,
                    "apr": rate_obj.get('apr', 0) / 100,
                    "fees": rate_obj.get('fees', 0),
                    "lock_period": rate_obj.get('lock_period', 30),
                    "source": rate_obj.get('source', 'unknown')
                })
            
            # Sort rates within each loan type (lowest first)
            for loan_type in rates_dict:
                rates_dict[loan_type].sort(key=lambda x: x['rate'])
            
            current_rates = rates_dict
        
        return {
            "success": True,
            "rates": current_rates,
            "context": rates_context,
            "last_updated": datetime.now().isoformat()
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
async def analyze_rate_quote(request: QuoteAnalysisRequest):
    """Analyze a rate quote with Gemini AI."""
    try:
        # Validate inputs
        if not request.quote_result:
            raise HTTPException(status_code=400, detail="Quote result is required")
        
        if not request.borrower_profile:
            raise HTTPException(status_code=400, detail="Borrower profile is required")
        
        # Run analysis
        analysis_result = analyze_quote(request.quote_result, request.borrower_profile)
        
        return {
            "success": True,
            "analysis": analysis_result
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

# API Key authentication for Gmail Add-on
async def verify_api_key(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(
            status_code=401, 
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Extract API key from "Bearer <key>" format
    if authorization.startswith("Bearer "):
        api_key = authorization[7:]
    else:
        api_key = authorization
    
    if api_key != GMAIL_ADDON_API_KEY:
        raise HTTPException(
            status_code=401, 
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return api_key

# Document processing endpoint for Gmail Add-on
class DocumentProcessRequest(BaseModel):
    """Request model for document processing from Gmail Add-on."""
    attachments: List[Dict[str, Any]]
    thread_id: Optional[str] = None

@app.post("/documents/process")
async def process_documents(
    request: DocumentProcessRequest,
    api_key: str = Depends(verify_api_key)
):
    """Process documents from Gmail attachments."""
    try:
        results = []
        
        for attachment in request.attachments:
            try:
                # Decode base64 data
                import base64
                file_data = base64.b64decode(attachment.get('data', ''))
                filename = attachment.get('name', 'unknown')
                content_type = attachment.get('contentType', 'application/octet-stream')
                
                # Process based on content type
                if 'pdf' in content_type.lower():
                    # Process PDF
                    result = {
                        "filename": filename,
                        "type": "pdf",
                        "processed": True,
                        "extracted_text": "PDF content extracted",  # Mock for now
                        "document_type": classify_doc_type(filename),
                        "status": "success"
                    }
                elif 'image' in content_type.lower():
                    # Process image (OCR)
                    result = {
                        "filename": filename,
                        "type": "image",
                        "processed": True,
                        "extracted_text": "Image content extracted via OCR",  # Mock for now
                        "document_type": classify_doc_type(filename),
                        "status": "success"
                    }
                else:
                    result = {
                        "filename": filename,
                        "type": "unknown",
                        "processed": False,
                        "error": "Unsupported file type",
                        "status": "error"
                    }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing attachment {attachment.get('name', 'unknown')}: {str(e)}")
                results.append({
                    "filename": attachment.get('name', 'unknown'),
                    "type": "error",
                    "processed": False,
                    "error": str(e),
                    "status": "error"
                })
        
        return {
            "success": True,
            "results": results,
            "thread_id": request.thread_id,
            "total_processed": len([r for r in results if r.get("processed", False)]),
            "total_errors": len([r for r in results if r.get("status") == "error"])
        }
        
    except Exception as e:
        logger.error(f"Error in document processing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

# Loan file creation endpoint for Gmail Add-on
class GmailLoanFileRequest(BaseModel):
    """Request model for creating loan files from Gmail Add-on."""
    borrower: str
    broker: str
    loan_type: str
    amount: str
    thread_id: Optional[str] = None
    email_summary: Optional[str] = None

@app.post("/loan-files/gmail")
async def create_loan_file_from_gmail(
    request: GmailLoanFileRequest,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Create a loan file from Gmail Add-on."""
    try:
        # Create the LoanFile
        loan_file = models.LoanFile(
            borrower=request.borrower,
            broker=request.broker,
            loan_type=request.loan_type,
            amount=request.amount,
            status="new",
            last_activity=datetime.now(),
            outstanding_items="Initial setup required",
            gmail_thread_id=request.thread_id,
            email_summary=request.email_summary
        )
        
        db.add(loan_file)
        db.commit()
        db.refresh(loan_file)
        
        return {
            "success": True,
            "loan_file": {
                "id": loan_file.id,
                "borrower": loan_file.borrower,
                "broker": loan_file.broker,
                "status": loan_file.status,
                "last_activity": loan_file.last_activity,
                "outstanding_items": loan_file.outstanding_items
            },
            "thread_id": request.thread_id
        }
        
    except Exception as e:
        logger.error(f"Error creating loan file from Gmail: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create loan file: {str(e)}")

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
