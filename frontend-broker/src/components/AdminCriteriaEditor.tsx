import React, { useState, useEffect, useCallback } from 'react';
import { fetchCriteria, fetchCriteriaList } from '../api/criteria';
import { useToast } from './ToastContainer';
import './AdminCriteriaEditor.css';

interface Criteria {
  [key: string]: any;
}



const AdminCriteriaEditor: React.FC = () => {
  const { showSuccess, showError, showInfo } = useToast();
  const [loanTypes, setLoanTypes] = useState<string[]>([]);
  const [selectedLoanType, setSelectedLoanType] = useState<string>('');
  const [criteria, setCriteria] = useState<Criteria>({});
  const [originalCriteria, setOriginalCriteria] = useState<Criteria>({});
  const [aiRequest, setAiRequest] = useState('');
  const [suggested, setSuggested] = useState<Criteria | null>(null);
  const [rawSuggestion, setRawSuggestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  const loadCriteriaList = useCallback(async () => {
    try {
      const types = await fetchCriteriaList();
      setLoanTypes(types);
    } catch (error) {
      showError('Failed to load criteria list', 'Please try refreshing the page.');
    }
  }, [showError]);

  const loadCriteria = useCallback(async (loanType: string) => {
    setLoading(true);
    try {
      const data = await fetchCriteria(loanType.replace('.yaml', ''));
      setCriteria(data);
      setOriginalCriteria(data);
      setSuggested(null);
      setRawSuggestion('');
    } catch (error) {
      showError('Failed to load criteria', 'Please try selecting a different loan type.');
    } finally {
      setLoading(false);
    }
  }, [showError]);

  useEffect(() => {
    loadCriteriaList();
  }, [loadCriteriaList]);

  useEffect(() => {
    if (selectedLoanType) {
      loadCriteria(selectedLoanType);
    }
  }, [selectedLoanType, loadCriteria]);

  useEffect(() => {
    setHasChanges(JSON.stringify(criteria) !== JSON.stringify(originalCriteria));
  }, [criteria, originalCriteria]);

  const handleLoanTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const loanType = e.target.value;
    setSelectedLoanType(loanType);
  };

  const handleFieldChange = (key: string, value: any) => {
    setCriteria((prev) => ({ ...prev, [key]: value }));
  };

  const handleSuggest = async () => {
    if (!aiRequest.trim()) {
      showError('AI Request Required', 'Please enter a description of the changes you want.');
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`/criteria/${selectedLoanType.replace('.yaml', '')}/suggest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_request: aiRequest, current_criteria: criteria }),
      });
      
      if (!res.ok) {
        throw new Error('Failed to get AI suggestions');
      }
      
      const data = await res.json();
      setSuggested(data.suggested_criteria);
      setRawSuggestion(data.raw);
      showSuccess('AI Suggestions Generated', 'Review the suggested changes below.');
    } catch (error) {
      showError('Failed to get AI suggestions', 'Please try again or adjust your request.');
    } finally {
      setLoading(false);
    }
  };

  const applySuggestion = (suggestedCriteria: Criteria) => {
    setCriteria(suggestedCriteria);
    setSuggested(null);
    showSuccess('Suggestion Applied', 'The AI suggestions have been applied to the criteria.');
  };

  const saveCriteria = async () => {
    setSaving(true);
    try {
      // TODO: Implement save functionality when backend endpoint is ready
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API call
      setOriginalCriteria(criteria);
      showSuccess('Criteria Saved', 'The criteria have been successfully updated.');
    } catch (error) {
      showError('Failed to save criteria', 'Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const resetCriteria = () => {
    setCriteria(originalCriteria);
    showInfo('Criteria Reset', 'All changes have been discarded.');
  };

  const renderField = (key: string, value: any): React.ReactElement | null => {
    const fieldType = typeof value;
    
    if (fieldType === 'number') {
      return (
        <input
          type="number"
          value={value}
          onChange={(e) => handleFieldChange(key, parseFloat(e.target.value) || 0)}
          className="criteria-input"
          step="0.01"
        />
      );
    }
    
    if (fieldType === 'boolean') {
      return (
        <select
          value={value.toString()}
          onChange={(e) => handleFieldChange(key, e.target.value === 'true')}
          className="criteria-select"
        >
          <option value="true">Yes</option>
          <option value="false">No</option>
        </select>
      );
    }
    
    return (
      <input
        type="text"
        value={value}
        onChange={(e) => handleFieldChange(key, e.target.value)}
        className="criteria-input"
      />
    );
  };

  return (
    <div className="admin-criteria-editor">
      <div className="criteria-header">
        <h2>Admin Criteria Editor</h2>
        <p>Adjust analysis criteria for different loan types. Changes will affect how Gemini analyzes loan requests.</p>
      </div>

      <div className="criteria-controls">
        <div className="criteria-selector">
          <label htmlFor="loanType">Loan Type:</label>
          <select
            id="loanType"
            value={selectedLoanType}
            onChange={handleLoanTypeChange}
            className="criteria-select"
          >
            <option value="">Select a loan type...</option>
            {loanTypes.map((lt) => (
              <option key={lt} value={lt}>{lt.replace('.yaml', '')}</option>
            ))}
          </select>
        </div>

        {hasChanges && (
          <div className="criteria-actions">
            <button
              onClick={resetCriteria}
              className="btn btn-secondary"
              disabled={saving}
            >
              Reset Changes
            </button>
            <button
              onClick={saveCriteria}
              className="btn btn-primary"
              disabled={saving}
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        )}
      </div>

      {loading && <div className="loading">Loading criteria...</div>}

      {selectedLoanType && !loading && (
        <div className="criteria-content">
          <div className="criteria-section">
            <h3>Current Criteria Parameters</h3>
            <div className="criteria-grid">
              {Object.entries(criteria).map(([key, value]) => (
                <div key={key} className="criteria-field">
                  <label htmlFor={key} className="field-label">
                    {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </label>
                  {renderField(key, value)}
                  <div className="field-description">
                    Current value: {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : value}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="criteria-section">
            <h3>AI Assistant</h3>
            <p>Describe the changes you want to make to the criteria. The AI will suggest specific adjustments.</p>
            
            <div className="ai-input-section">
              <textarea
                placeholder="e.g., 'Make the credit score requirements more lenient for FHA loans' or 'Increase the minimum down payment for conventional loans'"
                value={aiRequest}
                onChange={(e) => setAiRequest(e.target.value)}
                className="ai-textarea"
                rows={4}
              />
              <button
                onClick={handleSuggest}
                className="btn btn-primary"
                disabled={loading || !aiRequest.trim()}
              >
                {loading ? 'Generating Suggestions...' : 'Get AI Suggestions'}
              </button>
            </div>

            {suggested && (
              <div className="suggestions-section">
                <h4>AI Suggestions</h4>
                <div className="suggestions-content">
                  <div className="suggested-changes">
                    <h5>Suggested Changes:</h5>
                    <pre className="suggestions-json">{JSON.stringify(suggested, null, 2)}</pre>
                    <button
                      onClick={() => applySuggestion(suggested)}
                      className="btn btn-success"
                    >
                      Apply Suggestions
                    </button>
                  </div>
                  
                  <div className="raw-ai-output">
                    <h5>Raw AI Output:</h5>
                    <pre className="raw-output">{rawSuggestion}</pre>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {!selectedLoanType && !loading && (
        <div className="no-selection">
          <p>Please select a loan type to edit its criteria.</p>
        </div>
      )}
    </div>
  );
};

export default AdminCriteriaEditor; 