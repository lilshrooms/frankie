import { AppError, withRetry, isOffline, handleOfflineError, formatError } from './errorHandler';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface ApiResponse<T> {
  data: T;
  status: number;
  ok: boolean;
}

class ApiClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retryConfig?: { maxRetries?: number; onRetry?: (error: AppError, retryCount: number) => void }
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    
    const defaultOptions: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    const requestOptions = { ...defaultOptions, ...options };

    const makeRequest = async (): Promise<ApiResponse<T>> => {
      // Check if offline
      if (isOffline()) {
        throw handleOfflineError();
      }

      try {
        const response = await fetch(url, requestOptions);
        
        if (!response.ok) {
          let errorData;
          try {
            errorData = await response.json();
          } catch {
            errorData = { message: `HTTP ${response.status}` };
          }
          
          throw AppError.fromResponse(errorData, response.status);
        }

        const data = await response.json();
        return { data, status: response.status, ok: response.ok };
      } catch (error) {
        if (error instanceof AppError) {
          throw error;
        }
        
        // Handle network errors
        if (error instanceof TypeError && error.message.includes('fetch')) {
          throw AppError.fromNetworkError(error);
        }
        
        // Handle timeout errors
        if (error instanceof TypeError && error.message.includes('timeout')) {
          throw AppError.fromTimeoutError();
        }
        
        // Re-throw as unknown error
        throw new AppError(
          'An unexpected error occurred',
          'UNKNOWN_ERROR',
          false
        );
      }
    };

    // Apply retry logic if configured
    if (retryConfig) {
      return withRetry(makeRequest, retryConfig.maxRetries, retryConfig.onRetry);
    }

    return makeRequest();
  }

  // GET request
  async get<T>(endpoint: string, retryConfig?: { maxRetries?: number; onRetry?: (error: AppError, retryCount: number) => void }): Promise<T> {
    const response = await this.request<T>(endpoint, { method: 'GET' }, retryConfig);
    return response.data;
  }

  // POST request
  async post<T>(endpoint: string, data?: any, retryConfig?: { maxRetries?: number; onRetry?: (error: AppError, retryCount: number) => void }): Promise<T> {
    const response = await this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    }, retryConfig);
    return response.data;
  }

  // PUT request
  async put<T>(endpoint: string, data?: any, retryConfig?: { maxRetries?: number; onRetry?: (error: AppError, retryCount: number) => void }): Promise<T> {
    const response = await this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    }, retryConfig);
    return response.data;
  }

  // DELETE request
  async delete<T>(endpoint: string, retryConfig?: { maxRetries?: number; onRetry?: (error: AppError, retryCount: number) => void }): Promise<T> {
    const response = await this.request<T>(endpoint, { method: 'DELETE' }, retryConfig);
    return response.data;
  }

  // File upload with progress tracking
  async uploadFile<T>(
    endpoint: string,
    file: File,
    onProgress?: (progress: number) => void,
    retryConfig?: { maxRetries?: number; onRetry?: (error: AppError, retryCount: number) => void }
  ): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);

    // Validate file size (10MB limit)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      throw new AppError(
        'File is too large. Please upload a file smaller than 10MB.',
        'FILE_TOO_LARGE',
        false
      );
    }

    // Validate file type
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/gif'];
    if (!allowedTypes.includes(file.type)) {
      throw new AppError(
        'File type not supported. Please upload a PDF or image file.',
        'INVALID_FILE_TYPE',
        false
      );
    }

    const url = `${this.baseURL}${endpoint}`;
    
    const makeUpload = async (): Promise<ApiResponse<T>> => {
      if (isOffline()) {
        throw handleOfflineError();
      }

      return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable && onProgress) {
            const progress = (event.loaded / event.total) * 100;
            onProgress(progress);
          }
        });

        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              const data = JSON.parse(xhr.responseText);
              resolve({ data, status: xhr.status, ok: true });
            } catch {
              reject(new AppError('Invalid response format', 'PARSE_FAILED', false));
            }
          } else {
            let errorData;
            try {
              errorData = JSON.parse(xhr.responseText);
            } catch {
              errorData = { message: `HTTP ${xhr.status}` };
            }
            reject(AppError.fromResponse(errorData, xhr.status));
          }
        });

        xhr.addEventListener('error', () => {
          reject(AppError.fromNetworkError(new Error('Upload failed')));
        });

        xhr.addEventListener('timeout', () => {
          reject(AppError.fromTimeoutError());
        });

        xhr.open('POST', url);
        xhr.timeout = 30000; // 30 second timeout
        xhr.send(formData);
      });
    };

    if (retryConfig) {
      const response = await withRetry(makeUpload, retryConfig.maxRetries, retryConfig.onRetry);
      return response.data;
    }

    const response = await makeUpload();
    return response.data;
  }
}

// Create singleton instance
export const apiClient = new ApiClient();

// Export for testing
export { ApiClient }; 