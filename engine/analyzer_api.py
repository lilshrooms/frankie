#!/usr/bin/env python3
"""
Gemini Rate Analyzer API
Provides API endpoints for rate quote analysis with Gemini AI.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
from analyzer import analyze_quote, generate_quote_summary
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Frankie Rate Analyzer API",
    description="API for analyzing mortgage rate quotes with Gemini AI",
    version="1.0.0"
)


class QuoteAnalysisRequest(BaseModel):
    """Request model for quote analysis."""
    quote_result: Dict
    borrower_profile: Dict


class QuoteAnalysisResponse(BaseModel):
    """Response model for quote analysis."""
    success: bool
    explanation: Optional[str] = None
    improvement_suggestions: Optional[list] = None
    rate_breakdown: Optional[Dict] = None
    market_context: Optional[str] = None
    error_message: Optional[str] = None


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Frankie Rate Analyzer API",
        "version": "1.0.0",
        "endpoints": {
            "/analyze": "POST - Analyze rate quote with Gemini AI",
            "/analyze/summary": "POST - Generate formatted summary",
            "/health": "GET - Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "rate_analyzer",
        "version": "1.0.0"
    }


@app.post("/analyze", response_model=QuoteAnalysisResponse)
async def analyze_rate_quote(request: QuoteAnalysisRequest):
    """
    Analyze a rate quote using Gemini AI.
    
    Args:
        request: QuoteAnalysisRequest containing quote result and borrower profile
        
    Returns:
        QuoteAnalysisResponse with analysis results
    """
    try:
        logger.info(f"Analyzing quote for borrower with credit score {request.borrower_profile.get('credit_score')}")
        
        # Validate inputs
        if not request.quote_result:
            raise HTTPException(status_code=400, detail="Quote result is required")
        
        if not request.borrower_profile:
            raise HTTPException(status_code=400, detail="Borrower profile is required")
        
        # Run analysis
        result = analyze_quote(request.quote_result, request.borrower_profile)
        
        if not result.get('success'):
            return QuoteAnalysisResponse(
                success=False,
                error_message=result.get('error', 'Analysis failed')
            )
        
        logger.info("Quote analysis completed successfully")
        
        return QuoteAnalysisResponse(
            success=True,
            explanation=result.get('explanation'),
            improvement_suggestions=result.get('improvement_suggestions'),
            rate_breakdown=result.get('rate_breakdown'),
            market_context=result.get('market_context')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing quote: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/analyze/summary")
async def generate_analysis_summary(request: QuoteAnalysisRequest):
    """
    Generate a formatted summary of the quote analysis.
    
    Args:
        request: QuoteAnalysisRequest containing quote result and borrower profile
        
    Returns:
        str: Formatted summary
    """
    try:
        logger.info(f"Generating summary for borrower with credit score {request.borrower_profile.get('credit_score')}")
        
        # Validate inputs
        if not request.quote_result:
            raise HTTPException(status_code=400, detail="Quote result is required")
        
        if not request.borrower_profile:
            raise HTTPException(status_code=400, detail="Borrower profile is required")
        
        # Generate summary
        summary = generate_quote_summary(request.quote_result, request.borrower_profile)
        
        logger.info("Summary generation completed successfully")
        
        return {
            "success": True,
            "summary": summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/analyze/quick")
async def quick_analyze(
    loan_amount: float,
    credit_score: int,
    ltv: float,
    loan_type: str = "30yr_fixed"
):
    """
    Quick analysis endpoint that generates quote and analyzes it.
    
    Args:
        loan_amount: Loan amount
        credit_score: Credit score
        ltv: Loan-to-value ratio
        loan_type: Loan type
        
    Returns:
        Quick analysis summary
    """
    try:
        # Validate inputs
        if loan_amount <= 0:
            raise HTTPException(status_code=400, detail="Loan amount must be positive")
        
        if not (300 <= credit_score <= 850):
            raise HTTPException(status_code=400, detail="Credit score must be between 300 and 850")
        
        if not (50 <= ltv <= 100):
            raise HTTPException(status_code=400, detail="LTV must be between 50% and 100%")
        
        # Import quote engine
        from quote_engine import quote_rate
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ingest'))
        from gemini_rate_integration import GeminiRateIntegration
        
        # Get current rates
        rate_integration = GeminiRateIntegration()
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
        
        if not analysis.get('success'):
            return {
                "success": False,
                "error": analysis.get('error', 'Analysis failed')
            }
        
        # Return quick summary
        return {
            "success": True,
            "quote": {
                "final_rate": quote_result['final_rate'],
                "monthly_payment": quote_result['monthly_payment'],
                "total_interest": quote_result['total_interest']
            },
            "explanation": analysis.get('explanation'),
            "improvement_suggestions": analysis.get('improvement_suggestions', [])[:2],
            "market_context": analysis.get('market_context')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in quick analyze: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    print("Starting Rate Analyzer API...")
    print("API will be available at: http://localhost:8002")
    print("Documentation at: http://localhost:8002/docs")
    print()
    
    uvicorn.run(
        "analyzer_api:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    ) 