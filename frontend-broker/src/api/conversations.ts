export interface EmailMessage {
  sender: string;
  subject: string;
  body: string;
  timestamp: string;
  analysis?: any;
}

export interface Conversation {
  thread_id: string;
  state: 'initial_request' | 'waiting_docs' | 'underwriting' | 'complete';
  emails: EmailMessage[];
  turn: number;
  summary?: string;
  optimizations?: any[];
  created_at: string;
  updated_at: string;
}

export interface EmailProcessingRequest {
  email_body: string;
  sender: string;
  subject: string;
  thread_id?: string;
  attachments?: Array<{
    filename: string;
    content: string;
    type: string;
  }>;
}

export interface EmailProcessingResult {
  success: boolean;
  thread_id: string;
  conversation_state: string;
  analysis: any;
  response: string;
  next_steps: string[];
  error?: string;
}

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Get all conversations
export async function getConversations(): Promise<{ success: boolean; conversations: Conversation[]; count: number }> {
  const response = await fetch(`${API_BASE_URL}/conversations`);
  if (!response.ok) {
    throw new Error(`Failed to fetch conversations: ${response.statusText}`);
  }
  return response.json();
}

// Get specific conversation by thread ID
export async function getConversation(threadId: string): Promise<{ success: boolean; conversation: Conversation }> {
  const response = await fetch(`${API_BASE_URL}/conversations/${threadId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch conversation: ${response.statusText}`);
  }
  return response.json();
}

// Delete conversation
export async function deleteConversation(threadId: string): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${API_BASE_URL}/conversations/${threadId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to delete conversation: ${response.statusText}`);
  }
  return response.json();
}

// Process email through pipeline
export async function processEmail(request: EmailProcessingRequest): Promise<EmailProcessingResult> {
  const response = await fetch(`${API_BASE_URL}/email/process`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to process email: ${response.statusText}`);
  }
  
  return response.json();
}

// Update conversation state (admin intervention)
export async function updateConversationState(threadId: string, newState: string, adminNotes?: string): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${API_BASE_URL}/conversations/${threadId}/state`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      state: newState, 
      admin_notes: adminNotes,
      admin_intervention: true 
    }),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to update conversation state: ${response.statusText}`);
  }
  
  return response.json();
}

// Add admin response to conversation
export async function addAdminResponse(threadId: string, response: string, overrideAI?: boolean): Promise<{ success: boolean; message: string }> {
  const responseData = await fetch(`${API_BASE_URL}/conversations/${threadId}/admin-response`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      response, 
      override_ai: overrideAI || false,
      admin_intervention: true 
    }),
  });
  
  if (!responseData.ok) {
    throw new Error(`Failed to add admin response: ${responseData.statusText}`);
  }
  
  return responseData.json();
} 