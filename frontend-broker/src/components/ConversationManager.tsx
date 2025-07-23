import React, { useState, useEffect, useCallback } from 'react';
import { getConversations, getConversation, updateConversationState, addAdminResponse } from '../api/conversations';
import { useToast } from './ToastContainer';
import { FaEdit } from 'react-icons/fa';
import './ConversationManager.css';

interface ConversationManagerProps {
  onSelectConversation?: (conversation: any) => void;
}

const ConversationManager: React.FC<ConversationManagerProps> = ({ onSelectConversation }) => {
  const { showSuccess, showError } = useToast();
  const [conversations, setConversations] = useState<any[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [adminResponse, setAdminResponse] = useState('');
  const [adminNotes, setAdminNotes] = useState('');
  const [newState, setNewState] = useState('');
  const [showAdminPanel, setShowAdminPanel] = useState(false);
  const [saving, setSaving] = useState(false);

  const loadConversations = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await getConversations();
      setConversations(result.conversations);
    } catch (err) {
      setError('Failed to load conversations');
      showError('Failed to load conversations', 'Please try refreshing the page.');
    } finally {
      setLoading(false);
    }
  }, [showError]);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  const handleSelectConversation = async (threadId: string) => {
    try {
      const result = await getConversation(threadId);
      setSelectedConversation(result.conversation);
      setShowAdminPanel(false);
      if (onSelectConversation) {
        onSelectConversation(result.conversation);
      }
    } catch (err) {
      showError('Failed to load conversation', 'Please try selecting a different conversation.');
    }
  };

  const handleStateChange = async () => {
    if (!selectedConversation || !newState) {
      showError('Invalid State Change', 'Please select a new state.');
      return;
    }

    setSaving(true);
    try {
      await updateConversationState(selectedConversation.thread_id, newState, adminNotes);
      showSuccess('State Updated', 'Conversation state has been updated successfully.');
      
      // Reload the conversation
      await handleSelectConversation(selectedConversation.thread_id);
      await loadConversations();
      
      setNewState('');
      setAdminNotes('');
      setShowAdminPanel(false);
    } catch (err) {
      showError('Failed to update state', 'Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleAdminResponse = async () => {
    if (!selectedConversation || !adminResponse.trim()) {
      showError('Invalid Response', 'Please enter an admin response.');
      return;
    }

    setSaving(true);
    try {
      await addAdminResponse(selectedConversation.thread_id, adminResponse, true);
      showSuccess('Response Added', 'Admin response has been added to the conversation.');
      
      // Reload the conversation
      await handleSelectConversation(selectedConversation.thread_id);
      await loadConversations();
      
      setAdminResponse('');
      setShowAdminPanel(false);
    } catch (err) {
      showError('Failed to add response', 'Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const getStateColor = (state: string) => {
    switch (state) {
      case 'initial_request': return '#ffc107';
      case 'waiting_docs': return '#17a2b8';
      case 'underwriting': return '#28a745';
      case 'complete': return '#6c757d';
      default: return '#6c757d';
    }
  };

  const getStateLabel = (state: string) => {
    switch (state) {
      case 'initial_request': return 'Initial Request';
      case 'waiting_docs': return 'Waiting for Docs';
      case 'underwriting': return 'Underwriting';
      case 'complete': return 'Complete';
      default: return state;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getLatestEmail = (conversation: any) => {
    if (!conversation.emails || conversation.emails.length === 0) return null;
    return conversation.emails[conversation.emails.length - 1];
  };

  return (
    <div className="conversation-manager">
      <div className="conversation-header">
        <h2>Email Conversations</h2>
        <p>Monitor and manage email-based loan requests processed by Gemini AI.</p>
      </div>

      <div className="conversation-layout">
        {/* Conversation List */}
        <div className="conversation-list">
          <div className="list-header">
            <h3>Active Conversations ({conversations.length})</h3>
            <button 
              onClick={loadConversations}
              className="btn btn-secondary"
              disabled={loading}
            >
              {loading ? 'Loading...' : 'Refresh'}
            </button>
          </div>

          {error && <div className="error-message">{error}</div>}

          {loading ? (
            <div className="loading">Loading conversations...</div>
          ) : conversations.length === 0 ? (
            <div className="no-conversations">
              <p>No conversations found.</p>
            </div>
          ) : (
            <div className="conversation-items">
              {conversations.map((conversation) => {
                const latestEmail = getLatestEmail(conversation);
                return (
                  <div
                    key={conversation.thread_id}
                    className={`conversation-item ${selectedConversation?.thread_id === conversation.thread_id ? 'selected' : ''}`}
                    onClick={() => handleSelectConversation(conversation.thread_id)}
                  >
                    <div className="conversation-header">
                      <div className="conversation-state">
                        <span 
                          className="state-badge"
                          style={{ backgroundColor: getStateColor(conversation.state) }}
                        >
                          {getStateLabel(conversation.state)}
                        </span>
                      </div>
                      <div className="conversation-meta">
                        <span className="turn-count">Turn {conversation.turn}</span>
                        <span className="date">{formatDate(conversation.updated_at)}</span>
                      </div>
                    </div>
                    
                    {latestEmail && (
                      <div className="conversation-preview">
                        <div className="email-sender">{latestEmail.sender}</div>
                        <div className="email-subject">{latestEmail.subject}</div>
                        <div className="email-body">
                          {latestEmail.body.substring(0, 100)}...
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Conversation Details */}
        <div className="conversation-details">
          {selectedConversation ? (
            <>
              <div className="details-header">
                <h3>Conversation Details</h3>
                <div className="header-actions">
                  <button
                    onClick={() => setShowAdminPanel(!showAdminPanel)}
                    className="btn btn-primary"
                  >
                    <FaEdit /> Admin Actions
                  </button>
                </div>
              </div>

              <div className="conversation-info">
                <div className="info-grid">
                  <div className="info-item">
                    <label>Thread ID:</label>
                    <span>{selectedConversation.thread_id}</span>
                  </div>
                  <div className="info-item">
                    <label>State:</label>
                    <span 
                      className="state-badge"
                      style={{ backgroundColor: getStateColor(selectedConversation.state) }}
                    >
                      {getStateLabel(selectedConversation.state)}
                    </span>
                  </div>
                  <div className="info-item">
                    <label>Turn:</label>
                    <span>{selectedConversation.turn}</span>
                  </div>
                  <div className="info-item">
                    <label>Created:</label>
                    <span>{formatDate(selectedConversation.created_at)}</span>
                  </div>
                  <div className="info-item">
                    <label>Updated:</label>
                    <span>{formatDate(selectedConversation.updated_at)}</span>
                  </div>
                </div>
              </div>

              <div className="email-thread">
                <h4>Email Thread ({selectedConversation.emails?.length || 0} messages)</h4>
                {selectedConversation.emails?.map((email: any, index: number) => (
                  <div key={index} className="email-message">
                    <div className="email-header">
                      <div className="email-meta">
                        <span className="sender">{email.sender}</span>
                        <span className="timestamp">{formatDate(email.timestamp)}</span>
                      </div>
                      <div className="email-subject">{email.subject}</div>
                    </div>
                    <div className="email-body">
                      <pre>{email.body}</pre>
                    </div>
                    {email.analysis && (
                      <div className="email-analysis">
                        <h5>AI Analysis:</h5>
                        <div className="analysis-content">
                          <div><strong>Summary:</strong> {email.analysis.summary}</div>
                          <div><strong>Next Steps:</strong> {email.analysis.next_steps}</div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Admin Panel */}
              {showAdminPanel && (
                <div className="admin-panel">
                  <h4>Admin Actions</h4>
                  
                  <div className="admin-section">
                    <h5>Update Conversation State</h5>
                    <div className="admin-controls">
                      <select
                        value={newState}
                        onChange={(e) => setNewState(e.target.value)}
                        className="admin-select"
                      >
                        <option value="">Select new state...</option>
                        <option value="initial_request">Initial Request</option>
                        <option value="waiting_docs">Waiting for Docs</option>
                        <option value="underwriting">Underwriting</option>
                        <option value="complete">Complete</option>
                      </select>
                      <textarea
                        placeholder="Admin notes (optional)"
                        value={adminNotes}
                        onChange={(e) => setAdminNotes(e.target.value)}
                        className="admin-textarea"
                        rows={3}
                      />
                      <button
                        onClick={handleStateChange}
                        className="btn btn-primary"
                        disabled={saving || !newState}
                      >
                        {saving ? 'Updating...' : 'Update State'}
                      </button>
                    </div>
                  </div>

                  <div className="admin-section">
                    <h5>Add Admin Response</h5>
                    <div className="admin-controls">
                      <textarea
                        placeholder="Enter your admin response to the borrower..."
                        value={adminResponse}
                        onChange={(e) => setAdminResponse(e.target.value)}
                        className="admin-textarea"
                        rows={4}
                      />
                      <button
                        onClick={handleAdminResponse}
                        className="btn btn-success"
                        disabled={saving || !adminResponse.trim()}
                      >
                        {saving ? 'Adding...' : 'Add Response'}
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="no-selection">
              <p>Select a conversation to view details and take admin actions.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ConversationManager; 