import React, { useEffect, useState } from 'react';
import './Dashboard.css';
import { fetchLoanFiles, LoanFile } from '../api/loanFiles';

const uniqueStatuses = (files: LoanFile[]) => Array.from(new Set(files.map(f => f.status)));

const Dashboard: React.FC = () => {
  const [loanFiles, setLoanFiles] = useState<LoanFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selected, setSelected] = useState<LoanFile | null>(null);

  useEffect(() => {
    fetchLoanFiles()
      .then(data => {
        setLoanFiles(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const filtered = loanFiles.filter(file => {
    const matchesSearch =
      file.borrower.toLowerCase().includes(search.toLowerCase()) ||
      file.broker.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter ? file.status === statusFilter : true;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="dashboard-container">
      <h2>Loan Files</h2>
      <div className="dashboard-controls">
        <input
          type="text"
          placeholder="Search by borrower or broker..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="dashboard-search"
        />
        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          className="dashboard-filter"
        >
          <option value="">All Statuses</option>
          {uniqueStatuses(loanFiles).map(status => (
            <option key={status} value={status}>{status}</option>
          ))}
        </select>
      </div>
      {loading && <div>Loading...</div>}
      {error && <div className="error">{error}</div>}
      {!loading && !error && (
        <div className="dashboard-table-wrapper">
          <table className="loan-table">
            <thead>
              <tr>
                <th>Borrower</th>
                <th>Broker</th>
                <th>Status</th>
                <th>Last Activity</th>
                <th>Outstanding Items</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(file => (
                <tr key={file.id}>
                  <td>{file.borrower}</td>
                  <td>{file.broker}</td>
                  <td>{file.status}</td>
                  <td>{new Date(file.last_activity).toLocaleString()}</td>
                  <td>{file.outstanding_items ? file.outstanding_items : 'None'}</td>
                  <td>
                    <button className="action-btn" onClick={() => setSelected(file)}>View</button>
                    <button className="action-btn">Upload</button>
                    <button className="action-btn">Message</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {selected && (
        <div className="modal-overlay" onClick={() => setSelected(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h3>Loan File Details</h3>
            <table className="modal-table">
              <tbody>
                <tr><td><b>Borrower</b></td><td>{selected.borrower}</td></tr>
                <tr><td><b>Broker</b></td><td>{selected.broker}</td></tr>
                <tr><td><b>Status</b></td><td>{selected.status}</td></tr>
                <tr><td><b>Last Activity</b></td><td>{new Date(selected.last_activity).toLocaleString()}</td></tr>
                <tr><td><b>Outstanding Items</b></td><td>{selected.outstanding_items || 'None'}</td></tr>
                <tr><td><b>ID</b></td><td>{selected.id}</td></tr>
              </tbody>
            </table>
            <button className="action-btn" onClick={() => setSelected(null)} style={{marginTop: 16}}>Close</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard; 