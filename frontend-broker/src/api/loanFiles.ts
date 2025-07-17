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

export async function createLoanFile({
  borrower,
  broker,
  loanType,
  amount,
  document,
}: {
  borrower: string;
  broker: string;
  loanType: string;
  amount: string;
  document?: File | null;
}): Promise<LoanFile> {
  const formData = new FormData();
  formData.append('borrower', borrower);
  formData.append('broker', broker);
  formData.append('loan_type', loanType);
  formData.append('amount', amount);
  if (document) {
    formData.append('document', document);
  }
  const response = await fetch(`${API_BASE_URL}/loan-files`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) {
    throw new Error(`Failed to create loan file: ${response.statusText}`);
  }
  return response.json();
}

export async function softDeleteLoanFile(id: number): Promise<LoanFile> {
  const response = await fetch(`${API_BASE_URL}/loan-files/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to delete loan file: ${response.statusText}`);
  }
  return response.json();
} 