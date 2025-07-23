#!/usr/bin/env python3
"""
Rate Optimizer API
Provides API endpoints for rate optimization functionality.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
from optimizer import optimize_scenario
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Frankie Rate Optimizer API",
    description="API for optimizing mortgage rates and loan scenarios",
    version="1.0.0"
)


class OptimizationRequest(BaseModel):
    """Request model for rate optimization."""
    loan_amount: float
    credit_score: int
    ltv: float
    loan_type: str = "30yr_fixed"


class OptimizationResponse(BaseModel):
    """Response model for rate optimization."""
    success: bool
    current_scenario: Optional[Dict] = None
    optimizations: Optional[Dict] = None
    summary: Optional[Dict] = None
    error_message: Optional[str] = None


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Frankie Rate Optimizer API",
        "version": "1.0.0",
        "endpoints": {
            "/optimize": "POST - Optimize loan scenario",
            "/health": "GET - Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "rate_optimizer",
        "version": "1.0.0"
    }


@app.post("/optimize", response_model=OptimizationResponse)
async def optimize_loan_scenario(request: OptimizationRequest):
    """
    Optimize a loan scenario to find potential savings.
    
    Args:
        request: OptimizationRequest containing loan parameters
        
    Returns:
        OptimizationResponse with optimization results
    """
    try:
        logger.info(f"Optimizing scenario: ${request.loan_amount:,}, "
                   f"credit {request.credit_score}, LTV {request.ltv}%")
        
        # Validate inputs
        if request.loan_amount <= 0:
            raise HTTPException(status_code=400, detail="Loan amount must be positive")
        
        if not (300 <= request.credit_score <= 850):
            raise HTTPException(status_code=400, detail="Credit score must be between 300 and 850")
        
        if not (50 <= request.ltv <= 100):
            raise HTTPException(status_code=400, detail="LTV must be between 50% and 100%")
        
        # Run optimization
        result = optimize_scenario(
            request.loan_amount,
            request.credit_score,
            request.ltv,
            request.loan_type
        )
        
        if result.get('error'):
            return OptimizationResponse(
                success=False,
                error_message=result['message']
            )
        
        # Extract components
        current_scenario = result.get('current_scenario')
        optimizations = {
            "credit_score_optimizations": result.get('credit_score_optimizations', []),
            "ltv_optimizations": result.get('ltv_optimizations', []),
            "loan_amount_optimizations": result.get('loan_amount_optimizations', []),
            "loan_type_optimizations": result.get('loan_type_optimizations', [])
        }
        summary = result.get('summary', {})
        
        logger.info(f"Optimization completed successfully. "
                   f"Total potential savings: ${summary.get('total_potential_savings', 0):,.2f}")
        
        return OptimizationResponse(
            success=True,
            current_scenario=current_scenario,
            optimizations=optimizations,
            summary=summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error optimizing scenario: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/optimize/quick")
async def quick_optimize(
    loan_amount: float,
    credit_score: int,
    ltv: float,
    loan_type: str = "30yr_fixed"
):
    """
    Quick optimization endpoint with query parameters.
    
    Args:
        loan_amount: Loan amount
        credit_score: Credit score
        ltv: Loan-to-value ratio
        loan_type: Loan type
        
    Returns:
        Quick optimization summary
    """
    try:
        # Validate inputs
        if loan_amount <= 0:
            raise HTTPException(status_code=400, detail="Loan amount must be positive")
        
        if not (300 <= credit_score <= 850):
            raise HTTPException(status_code=400, detail="Credit score must be between 300 and 850")
        
        if not (50 <= ltv <= 100):
            raise HTTPException(status_code=400, detail="LTV must be between 50% and 100%")
        
        # Run optimization
        result = optimize_scenario(loan_amount, credit_score, ltv, loan_type)
        
        if result.get('error'):
            return {
                "success": False,
                "error": result['message']
            }
        
        # Return quick summary
        current = result['current_scenario']
        summary = result['summary']
        
        return {
            "success": True,
            "current_rate": current['final_rate'],
            "current_monthly_payment": current['monthly_payment'],
            "total_potential_savings": summary['total_potential_savings'],
            "top_recommendations": summary['recommendations'][:3],
            "quick_wins_count": len(summary.get('quick_wins', [])),
            "long_term_improvements_count": len(summary.get('long_term_improvements', []))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in quick optimize: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    print("Starting Rate Optimizer API...")
    print("API will be available at: http://localhost:8001")
    print("Documentation at: http://localhost:8001/docs")
    print()
    
    uvicorn.run(
        "optimizer_api:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    ) 