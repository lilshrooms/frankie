export interface LoanFile {
  id: number;
  borrower: string;
  broker: string;
  status: string;
  last_activity: string;
  outstanding_items: string;
}

const API_BASE_URL = 'http://localhost:8000';

export async function fetchLoanFiles(): Promise<LoanFile[]> {
  const response = await fetch(`${API_BASE_URL}/loan-files`);
  if (!response.ok) {
    throw new Error(`Failed to fetch loan files: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchLoanFile(id: number): Promise<LoanFile> {
  const response = await fetch(`${API_BASE_URL}/loan-files/${id}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch loan file: ${response.statusText}`);
  }
  return response.json();
} 