export interface ErrorWithRetry extends Error {
  retryCount?: number;
  maxRetries?: number;
  retryAfter?: number;
}

export interface ErrorResponse {
  message: string;
  code?: string;
  details?: any;
}

// Human-readable error messages mapped to error types
const ERROR_MESSAGES = {
  // Network errors
  'NETWORK_ERROR': 'Connection lost. Please check your internet connection.',
  'TIMEOUT': 'Request timed out. Please try again.',
  'OFFLINE': 'You appear to be offline. Please check your connection.',
  
  // HTTP errors
  '400': 'Invalid request. Please check your input and try again.',
  '401': 'Your session has expired. Please log in again.',
  '403': 'You don\'t have permission to perform this action.',
  '404': 'The requested resource was not found.',
  '409': 'This resource already exists.',
  '422': 'Invalid data provided. Please check your input.',
  '429': 'Too many requests. Please wait a moment and try again.',
  '500': 'Server error. Please try again later.',
  '502': 'Service temporarily unavailable. Please try again.',
  '503': 'Service is currently down for maintenance.',
  
  // File upload errors
  'FILE_TOO_LARGE': 'File is too large. Please upload a smaller file.',
  'INVALID_FILE_TYPE': 'File type not supported. Please upload a PDF or image.',
  'FILE_CORRUPTED': 'File appears to be corrupted. Please try a different file.',
  'UPLOAD_FAILED': 'Failed to upload file. Please try again.',
  
  // Document processing errors
  'OCR_FAILED': 'Could not extract text from image. Please upload a clearer version.',
  'PARSE_FAILED': 'Could not process document. Please check the file format.',
  'GEMINI_ERROR': 'AI analysis failed. Please try again.',
  'GEMINI_QUOTA': 'AI analysis temporarily unavailable due to high usage.',
  
  // Business logic errors
  'DUPLICATE_LOAN': 'A loan file for this borrower already exists.',
  'INVALID_STATUS': 'Cannot perform this action with the current status.',
  'MISSING_DOCS': 'Required documents are missing.',
  
  // Generic errors
  'UNKNOWN_ERROR': 'An unexpected error occurred. Please try again.',
  'VALIDATION_ERROR': 'Please check your input and try again.',
} as const;

// Auto-retry configuration
export const RETRY_CONFIG = {
  maxRetries: 3,
  baseDelay: 1000, // 1 second
  maxDelay: 10000, // 10 seconds
  backoffMultiplier: 2,
};

export class AppError extends Error {
  public code: string;
  public retryCount: number;
  public maxRetries: number;
  public retryAfter?: number;
  public isRetryable: boolean;

  constructor(
    message: string,
    code: string = 'UNKNOWN_ERROR',
    isRetryable: boolean = false,
    retryCount: number = 0,
    maxRetries: number = RETRY_CONFIG.maxRetries
  ) {
    super(message);
    this.name = 'AppError';
    this.code = code;
    this.retryCount = retryCount;
    this.maxRetries = maxRetries;
    this.isRetryable = isRetryable;
  }

  static fromResponse(response: ErrorResponse, statusCode?: number): AppError {
    const code = response.code || statusCode?.toString() || 'UNKNOWN_ERROR';
    const message = ERROR_MESSAGES[code as keyof typeof ERROR_MESSAGES] || response.message || ERROR_MESSAGES.UNKNOWN_ERROR;
    const isRetryable = isRetryableError(statusCode, code);
    
    return new AppError(message, code, isRetryable);
  }

  static fromNetworkError(error: Error): AppError {
    return new AppError(
      ERROR_MESSAGES.NETWORK_ERROR,
      'NETWORK_ERROR',
      true
    );
  }

  static fromTimeoutError(): AppError {
    return new AppError(
      ERROR_MESSAGES.TIMEOUT,
      'TIMEOUT',
      true
    );
  }
}

// Determine if an error is retryable
export function isRetryableError(statusCode?: number, code?: string): boolean {
  if (code === 'NETWORK_ERROR' || code === 'TIMEOUT') return true;
  
  // Retryable HTTP status codes
  const retryableStatusCodes = [408, 429, 500, 502, 503, 504];
  if (statusCode && retryableStatusCodes.includes(statusCode)) return true;
  
  return false;
}

// Calculate retry delay with exponential backoff
export function calculateRetryDelay(retryCount: number): number {
  const delay = RETRY_CONFIG.baseDelay * Math.pow(RETRY_CONFIG.backoffMultiplier, retryCount);
  return Math.min(delay, RETRY_CONFIG.maxDelay);
}

// Auto-retry wrapper for async functions
export async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries: number = RETRY_CONFIG.maxRetries,
  onRetry?: (error: AppError, retryCount: number) => void
): Promise<T> {
  let lastError: AppError;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      const appError = error instanceof AppError ? error : AppError.fromNetworkError(error as Error);
      appError.retryCount = attempt;
      appError.maxRetries = maxRetries;
      
      lastError = appError;

      // Don't retry if error is not retryable or we've exhausted retries
      if (!appError.isRetryable || attempt >= maxRetries) {
        throw appError;
      }

      // Call retry callback if provided
      if (onRetry) {
        onRetry(appError, attempt);
      }

      // Wait before retrying
      const delay = calculateRetryDelay(attempt);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  throw lastError!;
}

// Format error for display
export function formatError(error: Error | AppError): { title: string; message?: string } {
  if (error instanceof AppError) {
    return {
      title: error.message,
      message: error.retryCount > 0 ? `Retry ${error.retryCount}/${error.maxRetries} failed` : undefined
    };
  }

  return {
    title: ERROR_MESSAGES.UNKNOWN_ERROR,
    message: error.message
  };
}

// Check if user is offline
export function isOffline(): boolean {
  return !navigator.onLine;
}

// Handle offline state
export function handleOfflineError(): AppError {
  return new AppError(
    ERROR_MESSAGES.OFFLINE,
    'OFFLINE',
    true
  );
} 