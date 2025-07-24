export interface RateQuote {
  loan_amount: number;
  credit_score: number;
  ltv: number;
  loan_type: string;
  base_rate: number;
  adjusted_rate: number;
  monthly_payment: number;
  total_interest: number;
  llpas: {
    credit_score_adjustment: number;
    ltv_adjustment: number;
    total_adjustment: number;
  };
  eligibility: {
    approved: boolean;
    reasons: string[];
  };
}

export interface RateOptimization {
  current_scenario: RateQuote;
  optimizations: {
    credit_score: {
      current: number;
      recommended: number;
      rate_improvement: number;
      monthly_savings: number;
      feasibility: string;
      roi_analysis: string;
    };
    ltv: {
      current: number;
      recommended: number;
      rate_improvement: number;
      monthly_savings: number;
      down_payment_increase: number;
      feasibility: string;
      roi_analysis: string;
    };
    loan_amount: {
      current: number;
      recommended: number;
      rate_improvement: number;
      monthly_savings: number;
      feasibility: string;
      roi_analysis: string;
    };
  };
  summary: {
    best_optimization: string;
    total_potential_savings: number;
    recommended_actions: string[];
  };
}

export interface RateAnalysis {
  explanation: string;
  improvement_suggestions: Array<{
    suggestion: string;
    impact: string;
    action: string;
  }>;
  rate_breakdown: {
    base_rate: number;
    adjustments: Array<{
      type: string;
      amount: number;
      reason: string;
    }>;
    final_rate: number;
  };
  market_context: string;
}

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Get current mortgage rates
export async function getCurrentRates() {
  const response = await fetch(`${API_BASE_URL}/rates/current`);
  if (!response.ok) {
    throw new Error(`Failed to fetch current rates: ${response.statusText}`);
  }
  return response.json();
}

// Rate option interface for the new format
export interface RateOption {
  rate: number;
  apr: number;
  fees: number;
  lock_period: number;
  source: string;
}

export interface CurrentRates {
  [loanType: string]: RateOption[];
}

// Generate rate quote
export async function generateQuote(params: {
  loan_amount: number;
  credit_score: number;
  ltv: number;
  loan_type: string;
}): Promise<{ success: boolean; quote?: RateQuote; error?: string }> {
  const response = await fetch(`${API_BASE_URL}/rates/quote`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to generate quote: ${response.statusText}`);
  }
  
  return response.json();
}

// Optimize rates for borrower scenario
export async function optimizeRates(params: {
  loan_amount: number;
  credit_score: number;
  ltv: number;
  loan_type: string;
}): Promise<{ success: boolean; optimization?: RateOptimization; error?: string }> {
  const response = await fetch(`${API_BASE_URL}/rates/optimize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to optimize rates: ${response.statusText}`);
  }
  
  return response.json();
}

// Analyze rate quote with AI
export async function analyzeQuote(quote: RateQuote, borrowerProfile: any): Promise<{ success: boolean; analysis?: RateAnalysis; error?: string }> {
  const response = await fetch(`${API_BASE_URL}/rates/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ quote_result: quote, borrower_profile: borrowerProfile }),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to analyze quote: ${response.statusText}`);
  }
  
  return response.json();
}

// Quick rate analysis (quote + optimization + analysis)
export async function quickRateAnalysis(params: {
  loan_amount: number;
  credit_score: number;
  ltv: number;
  loan_type: string;
}): Promise<{
  success: boolean;
  quote?: RateQuote;
  optimization?: RateOptimization;
  analysis?: RateAnalysis;
  borrower_profile?: any;
  error?: string;
}> {
  const response = await fetch(`${API_BASE_URL}/rates/quick?${new URLSearchParams({
    loan_amount: params.loan_amount.toString(),
    credit_score: params.credit_score.toString(),
    ltv: params.ltv.toString(),
    loan_type: params.loan_type,
  })}`);
  
  if (!response.ok) {
    throw new Error(`Failed to perform quick rate analysis: ${response.statusText}`);
  }
  
  return response.json();
} 