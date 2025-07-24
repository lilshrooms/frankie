import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  TrendingUp, 
  Calculator, 
  Zap, 
  BarChart3, 
  RefreshCw, 
  DollarSign,
  Clock,
  FileText,
  CheckCircle,
  AlertCircle,
  ArrowUpRight
} from 'lucide-react';
import './RateOptimizationDashboard.css';
import { 
  getCurrentRates, 
  generateQuote, 
  optimizeRates, 
  analyzeQuote, 
  quickRateAnalysis,
  RateOption,
  CurrentRates
} from '../api/rateSystem';

interface RateOptimizationDashboardProps {
  onSelectBorrower?: (borrowerData: any) => void;
}

const RateOptimizationDashboard: React.FC<RateOptimizationDashboardProps> = ({ onSelectBorrower }) => {
  const [currentRates, setCurrentRates] = useState<CurrentRates | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('quote');
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [borrowerData, setBorrowerData] = useState({
    loan_amount: 500000,
    credit_score: 720,
    ltv: 80,
    loan_type: '30yr_fixed'
  });



  const loadCurrentRates = useCallback(async () => {
    try {
      const response = await getCurrentRates();
      if (response.success && response.rates) {
        setCurrentRates(response.rates);
      } else {
        console.error('Failed to load current rates', 'No rates data available.');
      }
    } catch (error) {
      console.error('Failed to load current rates', 'Please try refreshing the page.');
    }
  }, []);

  useEffect(() => {
    loadCurrentRates();
  }, [loadCurrentRates]);

  const handleInputChange = (field: string, value: any) => {
    setBorrowerData(prev => ({ ...prev, [field]: value }));
  };

  const generateRateQuote = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await generateQuote({
        loan_amount: borrowerData.loan_amount,
        credit_score: borrowerData.credit_score,
        ltv: borrowerData.ltv,
        loan_type: borrowerData.loan_type
      });
      
      if (result.success && result.quote) {
        console.log('Quote result:', result); // Debug log
        setResults({ type: 'quote', data: result });
        setActiveTab('quote');
      } else {
        console.error('Quote generation failed:', result.error);
        setError(result.error || 'Failed to generate quote');
      }
    } catch (error) {
      console.error('Error generating quote:', error);
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const optimizeBorrowerRates = async () => {
    setLoading(true);
    try {
      const result = await optimizeRates({
        loan_amount: borrowerData.loan_amount,
        credit_score: borrowerData.credit_score,
        ltv: borrowerData.ltv,
        loan_type: borrowerData.loan_type
      });
      setResults({ type: 'optimization', data: result });
      setActiveTab('optimization');
    } catch (error) {
      console.error('Error optimizing rates:', error);
    } finally {
      setLoading(false);
    }
  };

  const analyzeRateQuote = async () => {
    setLoading(true);
    try {
      const result = await analyzeQuote(results?.data?.quote || {}, borrowerData);
      setResults({ type: 'analysis', data: result });
      setActiveTab('analysis');
    } catch (error) {
      console.error('Error analyzing quote:', error);
    } finally {
      setLoading(false);
    }
  };

  const performQuickAnalysis = async () => {
    setLoading(true);
    try {
      const result = await quickRateAnalysis({
        loan_amount: borrowerData.loan_amount,
        credit_score: borrowerData.credit_score,
        ltv: borrowerData.ltv,
        loan_type: borrowerData.loan_type
      });
      setResults({ type: 'quick', data: result });
      setActiveTab('quick');
    } catch (error) {
      console.error('Error performing quick analysis:', error);
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

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        duration: 0.6,
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.5 }
    }
  };

  const cardVariants = {
    hidden: { opacity: 0, scale: 0.95 },
    visible: {
      opacity: 1,
      scale: 1,
      transition: { duration: 0.3 }
    },
    hover: {
      scale: 1.02,
      transition: { duration: 0.2 }
    }
  };

  return (
    <motion.div 
      className="rate-optimization-dashboard"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      <motion.div className="dashboard-header" variants={itemVariants}>
        <div className="header-content">
          <h2>
            Rate Optimization Dashboard
          </h2>
          <p>Generate quotes, optimize rates, and analyze borrower scenarios with AI assistance.</p>
        </div>
        <div className="header-actions">
                    <motion.button
            onClick={loadCurrentRates}
            className="refresh-btn"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <RefreshCw size={20} />
            Refresh Rates
          </motion.button>
        </div>
      </motion.div>

      <div className="dashboard-layout">
        {/* Current Rates Panel */}
        <motion.div className="rates-panel" variants={itemVariants}>
          <div className="panel-header">
            <TrendingUp size={24} className="text-green-500" />
            <h3>Current Market Rates</h3>
          </div>
          
          <AnimatePresence mode="wait">
            {currentRates ? (
              <motion.div 
                className="rates-container"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.3 }}
              >
                {Object.entries(currentRates).map(([loanType, rateOptions]: [string, RateOption[]]) => (
                  <motion.div key={loanType} className="loan-type-section" variants={itemVariants}>
                    <h4 className="loan-type-title">
                      {loanType.replace(/_/g, ' ').toUpperCase()}
                    </h4>
                    <div className="rate-options">
                      {rateOptions.map((option, index) => (
                        <motion.div 
                          key={index} 
                          className="rate-option-card"
                          variants={cardVariants}
                          whileHover="hover"
                          layout
                        >
                          <div className="rate-header">
                            <div className="rate-value">
                              <DollarSign size={20} className="text-green-500" />
                              {formatPercentage(option.rate)}
                            </div>
                            <div className="rate-apr">
                              APR: {formatPercentage(option.apr)}
                            </div>
                          </div>
                          <div className="rate-details">
                            <div className="rate-fee">
                              <FileText size={16} />
                              Fees: {formatCurrency(option.fees)}
                            </div>
                            <div className="rate-lock">
                              <Clock size={16} />
                              {option.lock_period} day lock
                            </div>
                          </div>
                          <div className="rate-source">
                            Source: {option.source}
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </motion.div>
                ))}
              </motion.div>
            ) : (
              <motion.div 
                className="loading"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <RefreshCw className="animate-spin" size={24} />
                Loading current rates...
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Borrower Input Panel */}
        <motion.div className="input-panel" variants={itemVariants}>
          <div className="panel-header">
            <Calculator size={24} className="text-blue-500" />
            <h3>Borrower Scenario</h3>
          </div>
          
          <div className="input-grid">
            <motion.div className="input-field" variants={itemVariants}>
              <label>Loan Amount</label>
              <div className="input-wrapper">
                <DollarSign size={20} className="input-icon" />
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
            </motion.div>
            
            <motion.div className="input-field" variants={itemVariants}>
              <label>Credit Score</label>
              <div className="input-wrapper">
                <BarChart3 size={20} className="input-icon" />
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
            </motion.div>
            
            <motion.div className="input-field" variants={itemVariants}>
              <label>LTV (%)</label>
              <div className="input-wrapper">
                <TrendingUp size={20} className="input-icon" />
                <input
                  type="number"
                  value={borrowerData.ltv}
                  onChange={(e) => handleInputChange('ltv', parseFloat(e.target.value) || 0)}
                  className="form-input"
                  min="50"
                  max="100"
                  step="5"
                />
              </div>
            </motion.div>
            
            <motion.div className="input-field" variants={itemVariants}>
              <label>Loan Type</label>
              <div className="input-wrapper">
                <FileText size={20} className="input-icon" />
                <select
                  value={borrowerData.loan_type}
                  onChange={(e) => handleInputChange('loan_type', e.target.value)}
                  className="form-select"
                >
                  {currentRates ? (
                    Object.keys(currentRates).map(loanType => (
                      <option key={loanType} value={loanType}>
                        {loanType.replace(/_/g, ' ').toUpperCase()}
                      </option>
                    ))
                  ) : (
                    <>
                      <option value="30yr_fixed">30YR FIXED</option>
                      <option value="15yr_fixed">15YR FIXED</option>
                      <option value="fha_30yr">FHA 30YR</option>
                      <option value="va_30yr">VA 30YR</option>
                    </>
                  )}
                </select>
              </div>
            </motion.div>
          </div>
        </motion.div>

        {/* Action Tabs */}
        <motion.div className="action-tabs" variants={itemVariants}>
          <motion.button
            className={`tab-button ${activeTab === 'quote' ? 'active' : ''}`}
            onClick={() => setActiveTab('quote')}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Calculator size={16} />
            Generate Quote
          </motion.button>
          
          <motion.button
            className={`tab-button ${activeTab === 'optimization' ? 'active' : ''}`}
            onClick={() => setActiveTab('optimization')}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Zap size={16} />
            Optimize Rates
          </motion.button>
          
          <motion.button
            className={`tab-button ${activeTab === 'analysis' ? 'active' : ''}`}
            onClick={() => setActiveTab('analysis')}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <BarChart3 size={16} />
            AI Analysis
          </motion.button>
          
          <motion.button
            className={`tab-button ${activeTab === 'quick' ? 'active' : ''}`}
            onClick={() => setActiveTab('quick')}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <ArrowUpRight size={16} />
            Quick Analysis
          </motion.button>
        </motion.div>

        {/* Results Panel */}
        <motion.div className="results-panel" variants={itemVariants}>
          <div className="tab-content">
            <div className="tab-header">
              <h3>
                {activeTab === 'quote' && <Calculator size={20} />}
                {activeTab === 'optimization' && <Zap size={20} />}
                {activeTab === 'analysis' && <BarChart3 size={20} />}
                {activeTab === 'quick' && <ArrowUpRight size={20} />}
                {activeTab === 'quote' && 'Rate Quote'}
                {activeTab === 'optimization' && 'Rate Optimization'}
                {activeTab === 'analysis' && 'AI Analysis'}
                {activeTab === 'quick' && 'Quick Analysis'}
              </h3>
              
              <motion.button
                onClick={
                  activeTab === 'quote' ? generateRateQuote :
                  activeTab === 'optimization' ? optimizeBorrowerRates :
                  activeTab === 'analysis' ? analyzeRateQuote :
                  performQuickAnalysis
                }
                className="btn btn-primary"
                disabled={loading}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                {loading ? (
                  <RefreshCw className="animate-spin" size={16} />
                ) : (
                  <>
                    {activeTab === 'quote' && <Calculator size={16} />}
                    {activeTab === 'optimization' && <Zap size={16} />}
                    {activeTab === 'analysis' && <BarChart3 size={16} />}
                    {activeTab === 'quick' && <ArrowUpRight size={16} />}
                  </>
                )}
                {loading ? 'Processing...' : 'Generate'}
              </motion.button>
            </div>

            {/* Error Display */}
            {error && (
              <motion.div 
                className="error"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
              >
                <AlertCircle size={16} />
                {error}
              </motion.div>
            )}

            <AnimatePresence mode="wait">
              {results && results.type === activeTab && (
                <motion.div
                  key={activeTab}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.3 }}
                >
                  {/* Quote Results */}
                  {activeTab === 'quote' && results.data?.success && (
                    <div className="quote-results">
                      <motion.div className="quote-summary" variants={cardVariants}>
                        <div className="quote-rate">
                          <div className="rate-label">Rate</div>
                          <div className="rate-value">
                            {formatPercentage(results.data.quote.final_rate)}
                          </div>
                        </div>
                        <div className="quote-payment">
                          <div className="payment-label">Monthly Payment</div>
                          <div className="payment-value">
                            {formatCurrency(results.data.quote.monthly_payment)}
                          </div>
                        </div>
                      </motion.div>
                      
                      <motion.div className="quote-details" variants={cardVariants}>
                        <h4>Quote Breakdown</h4>
                        <div className="breakdown-grid">
                          <div className="breakdown-item">
                            <span>Base Rate</span>
                            <span>{formatPercentage(results.data.quote.base_rate)}</span>
                          </div>
                          <div className="breakdown-item">
                            <span>Final Rate</span>
                            <span>{formatPercentage(results.data.quote.final_rate)}</span>
                          </div>
                          <div className="breakdown-item">
                            <span>APR</span>
                            <span>{formatPercentage(results.data.quote.final_apr)}</span>
                          </div>
                          <div className="breakdown-item">
                            <span>Total Interest</span>
                            <span>{formatCurrency(results.data.quote.total_interest)}</span>
                          </div>
                        </div>
                      </motion.div>
                      
                      <motion.div className="eligibility-status" variants={cardVariants}>
                        <h4>Eligibility Status</h4>
                        <div className={`status-badge ${results.data.quote.is_eligible ? 'approved' : 'denied'}`}>
                          {results.data.quote.is_eligible ? (
                            <>
                              <CheckCircle size={16} />
                              Approved
                            </>
                          ) : (
                            <>
                              <AlertCircle size={16} />
                              Denied
                            </>
                          )}
                        </div>
                        {results.data.quote.eligibility_reasons && (
                          <ul className="eligibility-reasons">
                            {results.data.quote.eligibility_reasons.map((reason: string, index: number) => (
                              <li key={index}>{reason}</li>
                            ))}
                          </ul>
                        )}
                      </motion.div>
                    </div>
                  )}

                  {/* Optimization Results */}
                  {activeTab === 'optimization' && results.data?.success && (
                    <div className="optimization-results">
                      <motion.div className="optimization-summary" variants={cardVariants}>
                        <h4>Optimization Summary</h4>
                        <div className="summary-stats">
                          <div className="stat-item">
                            <div className="stat-label">Current Rate</div>
                            <div className="stat-value">
                              {formatPercentage(results.data.optimization.current_rate)}
                            </div>
                          </div>
                          <div className="stat-item">
                            <div className="stat-label">Optimized Rate</div>
                            <div className="stat-value">
                              {formatPercentage(results.data.optimization.optimized_rate)}
                            </div>
                          </div>
                          <div className="stat-item">
                            <div className="stat-label">Monthly Savings</div>
                            <div className="stat-value">
                              {formatCurrency(results.data.optimization.monthly_savings)}
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    </div>
                  )}

                  {/* Analysis Results */}
                  {activeTab === 'analysis' && results.data?.success && (
                    <div className="analysis-results">
                      <motion.div className="analysis-explanation" variants={cardVariants}>
                        <h4>AI Analysis</h4>
                        <p>{results.data.analysis.explanation}</p>
                      </motion.div>
                      
                      <motion.div className="improvement-suggestions" variants={cardVariants}>
                        <h4>Improvement Suggestions</h4>
                        {results.data.analysis.improvement_suggestions?.map((suggestion: string, index: number) => (
                          <div key={index} className="suggestion-item">
                            <div className="suggestion-text">{suggestion}</div>
                          </div>
                        ))}
                      </motion.div>
                    </div>
                  )}

                  {/* Quick Analysis Results */}
                  {activeTab === 'quick' && results.data?.success && (
                    <div className="quick-analysis-results">
                      <motion.div className="quick-summary" variants={cardVariants}>
                        <h4>Quick Analysis Summary</h4>
                        <div className="summary-cards">
                          <div className="summary-card">
                            <h5>Rate Analysis</h5>
                            <div className="card-content">
                              <div>Current Rate: {formatPercentage(results.data.quote.final_rate)}</div>
                              <div>APR: {formatPercentage(results.data.quote.final_apr)}</div>
                              <div className={`status ${results.data.quote.is_eligible ? 'approved' : 'denied'}`}>
                                {results.data.quote.is_eligible ? 'Eligible' : 'Not Eligible'}
                              </div>
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
};

export default RateOptimizationDashboard; 