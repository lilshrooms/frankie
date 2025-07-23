import React, { useState, useEffect, useCallback } from 'react';
import { getCurrentRates, generateQuote, optimizeRates, analyzeQuote, quickRateAnalysis } from '../api/rateSystem';
import { useToast } from './ToastContainer';
import { FaCalculator, FaChartLine, FaLightbulb, FaDownload } from 'react-icons/fa';
import './RateOptimizationDashboard.css';

interface RateOptimizationDashboardProps {
  onSelectBorrower?: (borrowerData: any) => void;
}

const RateOptimizationDashboard: React.FC<RateOptimizationDashboardProps> = ({ onSelectBorrower }) => {
  const { showSuccess, showError } = useToast();
  const [currentRates, setCurrentRates] = useState<any>(null);
  const [borrowerData, setBorrowerData] = useState({
    loan_amount: 300000,
    credit_score: 720,
    ltv: 80,
    loan_type: 'conventional'
  });
  const [quoteResult, setQuoteResult] = useState<any>(null);
  const [optimizationResult, setOptimizationResult] = useState<any>(null);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'quote' | 'optimize' | 'analyze' | 'quick'>('quote');

  const loadCurrentRates = useCallback(async () => {
    try {
      const rates = await getCurrentRates();
      setCurrentRates(rates);
    } catch (error) {
      showError('Failed to load current rates', 'Please try refreshing the page.');
    }
  }, [showError]);

  useEffect(() => {
    loadCurrentRates();
  }, [loadCurrentRates]);

  const handleInputChange = (field: string, value: any) => {
    setBorrowerData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const generateRateQuote = async () => {
    setLoading(true);
    try {
      const result = await generateQuote(borrowerData);
      if (result.success) {
        setQuoteResult(result.quote);
        showSuccess('Quote Generated', 'Rate quote has been calculated successfully.');
      } else {
        showError('Quote Failed', result.error || 'Failed to generate quote.');
      }
    } catch (error) {
      showError('Quote Error', 'Failed to generate rate quote.');
    } finally {
      setLoading(false);
    }
  };

  const optimizeBorrowerRates = async () => {
    setLoading(true);
    try {
      const result = await optimizeRates(borrowerData);
      if (result.success) {
        setOptimizationResult(result.optimization);
        showSuccess('Optimization Complete', 'Rate optimization analysis is ready.');
      } else {
        showError('Optimization Failed', result.error || 'Failed to optimize rates.');
      }
    } catch (error) {
      showError('Optimization Error', 'Failed to optimize rates.');
    } finally {
      setLoading(false);
    }
  };

  const analyzeRateQuote = async () => {
    if (!quoteResult) {
      showError('No Quote Available', 'Please generate a quote first.');
      return;
    }

    setLoading(true);
    try {
      const result = await analyzeQuote(quoteResult, borrowerData);
      if (result.success) {
        setAnalysisResult(result.analysis);
        showSuccess('Analysis Complete', 'AI analysis of the rate quote is ready.');
      } else {
        showError('Analysis Failed', result.error || 'Failed to analyze quote.');
      }
    } catch (error) {
      showError('Analysis Error', 'Failed to analyze rate quote.');
    } finally {
      setLoading(false);
    }
  };

  const performQuickAnalysis = async () => {
    setLoading(true);
    try {
      const result = await quickRateAnalysis(borrowerData);
      if (result.success) {
        setQuoteResult(result.quote);
        setOptimizationResult(result.optimization);
        setAnalysisResult(result.analysis);
        showSuccess('Quick Analysis Complete', 'Complete rate analysis is ready.');
      } else {
        showError('Quick Analysis Failed', result.error || 'Failed to perform quick analysis.');
      }
    } catch (error) {
      showError('Quick Analysis Error', 'Failed to perform quick analysis.');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatPercentage = (rate: number) => {
    return `${(rate * 100).toFixed(3)}%`;
  };

  return (
    <div className="rate-optimization-dashboard">
      <div className="dashboard-header">
        <h2>Rate Optimization Dashboard</h2>
        <p>Generate quotes, optimize rates, and analyze borrower scenarios with AI assistance.</p>
      </div>

      <div className="dashboard-layout">
        {/* Current Rates Panel */}
        <div className="rates-panel">
          <h3>Current Market Rates</h3>
          {currentRates ? (
            <div className="rates-grid">
              {Object.entries(currentRates).map(([loanType, rate]: [string, any]) => (
                <div key={loanType} className="rate-card">
                  <div className="rate-type">{loanType.replace(/_/g, ' ').toUpperCase()}</div>
                  <div className="rate-value">{formatPercentage(rate)}</div>
                </div>
              ))}
            </div>
          ) : (
            <div className="loading">Loading current rates...</div>
          )}
          <button onClick={loadCurrentRates} className="btn btn-secondary">
            <FaDownload /> Refresh Rates
          </button>
        </div>

        {/* Borrower Input Panel */}
        <div className="input-panel">
          <h3>Borrower Scenario</h3>
          <div className="input-grid">
            <div className="input-field">
              <label>Loan Amount</label>
              <input
                type="number"
                value={borrowerData.loan_amount}
                onChange={(e) => handleInputChange('loan_amount', parseInt(e.target.value) || 0)}
                className="form-input"
                min="50000"
                max="2000000"
                step="10000"
              />
            </div>
            <div className="input-field">
              <label>Credit Score</label>
              <input
                type="number"
                value={borrowerData.credit_score}
                onChange={(e) => handleInputChange('credit_score', parseInt(e.target.value) || 0)}
                className="form-input"
                min="300"
                max="850"
                step="10"
              />
            </div>
            <div className="input-field">
              <label>LTV (%)</label>
              <input
                type="number"
                value={borrowerData.ltv}
                onChange={(e) => handleInputChange('ltv', parseInt(e.target.value) || 0)}
                className="form-input"
                min="3"
                max="100"
                step="1"
              />
            </div>
            <div className="input-field">
              <label>Loan Type</label>
              <select
                value={borrowerData.loan_type}
                onChange={(e) => handleInputChange('loan_type', e.target.value)}
                className="form-select"
              >
                <option value="conventional">Conventional</option>
                <option value="fha">FHA</option>
                <option value="va">VA</option>
                <option value="usda">USDA</option>
              </select>
            </div>
          </div>
        </div>

        {/* Action Tabs */}
        <div className="action-tabs">
          <button
            className={`tab-button ${activeTab === 'quote' ? 'active' : ''}`}
            onClick={() => setActiveTab('quote')}
          >
            <FaCalculator /> Generate Quote
          </button>
          <button
            className={`tab-button ${activeTab === 'optimize' ? 'active' : ''}`}
            onClick={() => setActiveTab('optimize')}
          >
            <FaLightbulb /> Optimize Rates
          </button>
          <button
            className={`tab-button ${activeTab === 'analyze' ? 'active' : ''}`}
            onClick={() => setActiveTab('analyze')}
          >
            <FaChartLine /> AI Analysis
          </button>
          <button
            className={`tab-button ${activeTab === 'quick' ? 'active' : ''}`}
            onClick={() => setActiveTab('quick')}
          >
            <FaChartLine /> Quick Analysis
          </button>
        </div>

        {/* Results Panel */}
        <div className="results-panel">
          {activeTab === 'quote' && (
            <div className="tab-content">
              <div className="tab-header">
                <h3>Rate Quote</h3>
                <button
                  onClick={generateRateQuote}
                  className="btn btn-primary"
                  disabled={loading}
                >
                  {loading ? 'Generating...' : 'Generate Quote'}
                </button>
              </div>
              
              {quoteResult && (
                <div className="quote-results">
                  <div className="quote-summary">
                    <div className="quote-rate">
                      <span className="rate-label">Your Rate:</span>
                      <span className="rate-value">{formatPercentage(quoteResult.adjusted_rate)}</span>
                    </div>
                    <div className="quote-payment">
                      <span className="payment-label">Monthly Payment:</span>
                      <span className="payment-value">{formatCurrency(quoteResult.monthly_payment)}</span>
                    </div>
                  </div>
                  
                  <div className="quote-details">
                    <h4>Rate Breakdown</h4>
                    <div className="breakdown-grid">
                      <div className="breakdown-item">
                        <span>Base Rate:</span>
                        <span>{formatPercentage(quoteResult.base_rate)}</span>
                      </div>
                      <div className="breakdown-item">
                        <span>Credit Adjustment:</span>
                        <span>{formatPercentage(quoteResult.llpas.credit_score_adjustment)}</span>
                      </div>
                      <div className="breakdown-item">
                        <span>LTV Adjustment:</span>
                        <span>{formatPercentage(quoteResult.llpas.ltv_adjustment)}</span>
                      </div>
                      <div className="breakdown-item">
                        <span>Total Adjustment:</span>
                        <span>{formatPercentage(quoteResult.llpas.total_adjustment)}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="eligibility-status">
                    <h4>Eligibility</h4>
                    <div className={`status-badge ${quoteResult.eligibility.approved ? 'approved' : 'denied'}`}>
                      {quoteResult.eligibility.approved ? 'Approved' : 'Not Approved'}
                    </div>
                    {quoteResult.eligibility.reasons.length > 0 && (
                      <ul className="eligibility-reasons">
                        {quoteResult.eligibility.reasons.map((reason: string, index: number) => (
                          <li key={index}>{reason}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'optimize' && (
            <div className="tab-content">
              <div className="tab-header">
                <h3>Rate Optimization</h3>
                <button
                  onClick={optimizeBorrowerRates}
                  className="btn btn-primary"
                  disabled={loading}
                >
                  {loading ? 'Optimizing...' : 'Optimize Rates'}
                </button>
              </div>
              
              {optimizationResult && (
                <div className="optimization-results">
                  <div className="optimization-summary">
                    <h4>Optimization Summary</h4>
                    <div className="summary-stats">
                      <div className="stat-item">
                        <span className="stat-label">Best Optimization:</span>
                        <span className="stat-value">{optimizationResult.summary.best_optimization}</span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-label">Total Savings:</span>
                        <span className="stat-value">{formatCurrency(optimizationResult.summary.total_potential_savings)}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="optimization-details">
                    <h4>Optimization Options</h4>
                    {Object.entries(optimizationResult.optimizations).map(([type, opt]: [string, any]) => (
                      <div key={type} className="optimization-option">
                        <h5>{type.replace(/_/g, ' ').toUpperCase()}</h5>
                        <div className="option-details">
                          <div className="option-change">
                            <span>Current: {opt.current}</span>
                            <span>Recommended: {opt.recommended}</span>
                          </div>
                          <div className="option-benefits">
                            <div>Rate Improvement: {formatPercentage(opt.rate_improvement)}</div>
                            <div>Monthly Savings: {formatCurrency(opt.monthly_savings)}</div>
                          </div>
                          <div className="option-feasibility">
                            <strong>Feasibility:</strong> {opt.feasibility}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'analyze' && (
            <div className="tab-content">
              <div className="tab-header">
                <h3>AI Analysis</h3>
                <button
                  onClick={analyzeRateQuote}
                  className="btn btn-primary"
                  disabled={loading || !quoteResult}
                >
                  {loading ? 'Analyzing...' : 'Analyze Quote'}
                </button>
              </div>
              
              {analysisResult && (
                <div className="analysis-results">
                  <div className="analysis-explanation">
                    <h4>AI Explanation</h4>
                    <p>{analysisResult.explanation}</p>
                  </div>
                  
                  <div className="improvement-suggestions">
                    <h4>Improvement Suggestions</h4>
                    {analysisResult.improvement_suggestions.map((suggestion: any, index: number) => (
                      <div key={index} className="suggestion-item">
                        <div className="suggestion-text">{suggestion.suggestion}</div>
                        <div className="suggestion-impact">Impact: {suggestion.impact}</div>
                        <div className="suggestion-action">Action: {suggestion.action}</div>
                      </div>
                    ))}
                  </div>
                  
                  <div className="rate-breakdown">
                    <h4>Rate Breakdown</h4>
                    <div className="breakdown-details">
                      <div className="breakdown-base">
                        Base Rate: {formatPercentage(analysisResult.rate_breakdown.base_rate)}
                      </div>
                      {analysisResult.rate_breakdown.adjustments.map((adj: any, index: number) => (
                        <div key={index} className="breakdown-adjustment">
                          {adj.type}: {formatPercentage(adj.amount)} ({adj.reason})
                        </div>
                      ))}
                      <div className="breakdown-final">
                        Final Rate: {formatPercentage(analysisResult.rate_breakdown.final_rate)}
                      </div>
                    </div>
                  </div>
                  
                  <div className="market-context">
                    <h4>Market Context</h4>
                    <p>{analysisResult.market_context}</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'quick' && (
            <div className="tab-content">
              <div className="tab-header">
                <h3>Quick Analysis</h3>
                <button
                  onClick={performQuickAnalysis}
                  className="btn btn-primary"
                  disabled={loading}
                >
                  {loading ? 'Analyzing...' : 'Run Quick Analysis'}
                </button>
              </div>
              
              {quoteResult && optimizationResult && analysisResult && (
                <div className="quick-analysis-results">
                  <div className="quick-summary">
                    <h4>Complete Analysis Summary</h4>
                    <div className="summary-cards">
                      <div className="summary-card">
                        <h5>Current Quote</h5>
                        <div className="card-content">
                          <div>Rate: {formatPercentage(quoteResult.adjusted_rate)}</div>
                          <div>Payment: {formatCurrency(quoteResult.monthly_payment)}</div>
                          <div className={`status ${quoteResult.eligibility.approved ? 'approved' : 'denied'}`}>
                            {quoteResult.eligibility.approved ? 'Approved' : 'Not Approved'}
                          </div>
                        </div>
                      </div>
                      
                      <div className="summary-card">
                        <h5>Optimization Potential</h5>
                        <div className="card-content">
                          <div>Best Option: {optimizationResult.summary.best_optimization}</div>
                          <div>Total Savings: {formatCurrency(optimizationResult.summary.total_potential_savings)}</div>
                          <div>Actions: {optimizationResult.summary.recommended_actions.length}</div>
                        </div>
                      </div>
                      
                      <div className="summary-card">
                        <h5>AI Insights</h5>
                        <div className="card-content">
                          <div>Suggestions: {analysisResult.improvement_suggestions.length}</div>
                          <div>Market Context: Available</div>
                          <div>Rate Breakdown: Complete</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RateOptimizationDashboard; 