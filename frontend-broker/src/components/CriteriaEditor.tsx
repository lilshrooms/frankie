import React, { useState } from 'react';
import { fetchCriteria, fetchCriteriaList } from '../api/criteria';

interface Criteria {
  [key: string]: any;
}

const CriteriaEditor: React.FC = () => {
  const [loanTypes, setLoanTypes] = useState<string[]>([]);
  const [selectedLoanType, setSelectedLoanType] = useState<string>('');
  const [criteria, setCriteria] = useState<Criteria>({});
  const [aiRequest, setAiRequest] = useState('');
  const [suggested, setSuggested] = useState<Criteria | null>(null);
  const [rawSuggestion, setRawSuggestion] = useState('');

  React.useEffect(() => {
    fetchCriteriaList().then(setLoanTypes);
  }, []);

  const handleLoanTypeChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const loanType = e.target.value;
    setSelectedLoanType(loanType);
    const data = await fetchCriteria(loanType.replace('.yaml', ''));
    setCriteria(data);
    setSuggested(null);
    setRawSuggestion('');
  };

  const handleFieldChange = (key: string, value: any) => {
    setCriteria((prev) => ({ ...prev, [key]: value }));
  };

  const handleSuggest = async () => {
    const res = await fetch(`/criteria/${selectedLoanType.replace('.yaml', '')}/suggest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_request: aiRequest, current_criteria: criteria }),
    });
    const data = await res.json();
    setSuggested(data.suggested_criteria);
    setRawSuggestion(data.raw);
  };

  return (
    <div>
      <h2>Criteria Editor</h2>
      <label>Loan Type: </label>
      <select value={selectedLoanType} onChange={handleLoanTypeChange}>
        <option value="">Select...</option>
        {loanTypes.map((lt) => (
          <option key={lt} value={lt}>{lt.replace('.yaml', '')}</option>
        ))}
      </select>
      {selectedLoanType && (
        <div>
          <h3>Parameters</h3>
          {Object.entries(criteria).map(([key, value]) => (
            <div key={key}>
              <label>{key}: </label>
              <input
                type="text"
                value={value}
                onChange={(e) => handleFieldChange(key, e.target.value)}
              />
            </div>
          ))}
          <h3>AI Assistant</h3>
          <textarea
            placeholder="Describe how you want to adjust the standards..."
            value={aiRequest}
            onChange={(e) => setAiRequest(e.target.value)}
            rows={3}
            style={{ width: '100%' }}
          />
          <button onClick={handleSuggest}>Suggest Changes</button>
          {suggested && (
            <div style={{ marginTop: 20 }}>
              <h4>Suggested Changes</h4>
              <pre>{JSON.stringify(suggested, null, 2)}</pre>
              <h5>Raw AI Output</h5>
              <pre>{rawSuggestion}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default CriteriaEditor;
