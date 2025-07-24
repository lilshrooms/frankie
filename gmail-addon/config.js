/**
 * Frankie Gmail Add-on Configuration
 * Update these values for your deployment
 */

const CONFIG = {
  // Frankie Backend API Configuration
  FRANKIE_API_BASE: 'http://localhost:8000', // Update with your domain for production
  FRANKIE_API_KEY: 'frankie-gmail-addon-key-2024', // API key for Gmail Add-on
  
  // Gmail Add-on Configuration
  ADDON_NAME: 'Frankie AI Assistant',
  ADDON_VERSION: '1.0.0',
  
  // UI Configuration
  PRIMARY_COLOR: '#1e293b',
  SECONDARY_COLOR: '#3b82f6',
  SUCCESS_COLOR: '#10b981',
  ERROR_COLOR: '#ef4444',
  WARNING_COLOR: '#f59e0b',
  
  // Feature Flags
  ENABLE_EMAIL_ANALYSIS: true,
  ENABLE_RATE_QUOTES: true,
  ENABLE_DOCUMENT_PROCESSING: true,
  ENABLE_LOAN_FILE_CREATION: true,
  
  // API Endpoints
  ENDPOINTS: {
    EMAIL_PROCESS: '/email/process',
    RATE_QUOTE: '/rates/quote',
    LOAN_FILES: '/loan-files/gmail',
    DOCUMENT_PROCESS: '/documents/process'
  },
  
  // Default Values
  DEFAULTS: {
    LOAN_AMOUNT: 500000,
    CREDIT_SCORE: 720,
    LTV: 80,
    LOAN_TYPE: '30yr_fixed'
  },
  
  // Error Messages
  ERRORS: {
    API_CONNECTION: 'Failed to connect to Frankie API',
    EMAIL_PROCESSING: 'Failed to process email',
    RATE_GENERATION: 'Failed to generate rate quote',
    DOCUMENT_PROCESSING: 'Failed to process documents',
    LOAN_FILE_CREATION: 'Failed to create loan file'
  }
};

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
  module.exports = CONFIG;
} 