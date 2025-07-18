import React, { useEffect, useState } from 'react';
import './Dashboard.css';
import { fetchLoanFiles, LoanFile, createLoanFile, softDeleteLoanFile } from '../api/loanFiles';
import { FaEye, FaUpload, FaCommentDots, FaTrash, FaPlus } from 'react-icons/fa';
import ConfirmModal from './ConfirmModal';
import Tooltip from './Tooltip';
import { useToast } from './ToastContainer';
import { apiClient } from '../utils/apiClient';
import { AppError, formatError } from '../utils/errorHandler';

const uniqueStatuses = (files: LoanFile[]) => Array.from(new Set(files.map(f => f.status)));

const Dashboard: React.FC = () => {
  const { showSuccess, showError, showWarning, showInfo } = useToast();
  const [loanFiles, setLoanFiles] = useState<LoanFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selected, setSelected] = useState<LoanFile | null>(null);
  const [showNewLoan, setShowNewLoan] = useState(false);
  const [form, setForm] = useState({
    borrower: '',
    broker: '',
    loanType: '',
    amount: '',
    document: null as File | null,
  });
  const [formError, setFormError] = useState<string | null>(null);
  const [formLoading, setFormLoading] = useState(false);
  const [sortBy, setSortBy] = useState<'last_activity' | 'borrower' | 'broker' | 'status'>('last_activity');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    loadLoanFiles();
  }, []);

  const loadLoanFiles = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await apiClient.get<LoanFile[]>('/loan-files', {
        maxRetries: 3,
        onRetry: (error, retryCount) => {
          showWarning('Connection issue', `Retrying... (${retryCount}/3)`);
        }
      });
      setLoanFiles(data);
    } catch (err) {
      const appError = err instanceof AppError ? err : new AppError('Failed to load loan files');
      const { title, message } = formatError(appError);
      setError(title);
      showError(title, message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    setDeleteLoading(true);
    setError(null);
    
    try {
      await apiClient.delete(`/loan-files/${id}`, {
        maxRetries: 2,
        onRetry: (error, retryCount) => {
          showWarning('Delete failed', `Retrying... (${retryCount}/2)`);
        }
      });
      
      showSuccess('Loan file deleted', 'The loan file has been successfully deleted.');
      await loadLoanFiles();
      setConfirmOpen(false);
      setDeleteId(null);
    } catch (err) {
      const appError = err instanceof AppError ? err : new AppError('Failed to delete loan file');
      const { title, message } = formatError(appError);
      setError(title);
      showError(title, message);
    } finally {
      setDeleteLoading(false);
    }
  };

  const isHighPriority = (file: LoanFile) =>
    ['docs needed', 'pending docs', 'incomplete'].includes(file.status.toLowerCase());

  const statusBadgeClass = (status: string) => {
    const s = status.toLowerCase();
    if (s === 'docs needed') return 'status-badge docs-needed';
    if (s === 'pending docs') return 'status-badge pending-docs';
    if (s === 'incomplete') return 'status-badge incomplete';
    if (s === 'complete') return 'status-badge complete';
    if (s === 'under review') return 'status-badge under-review';
    return 'status-badge';
  };

  let filtered = loanFiles.filter(file => {
    const matchesSearch =
      file.borrower.toLowerCase().includes(search.toLowerCase()) ||
      file.broker.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter ? file.status === statusFilter : true;
    const notDeleted = file.status !== 'deleted';
    const priority = showAll ? true : isHighPriority(file);
    return matchesSearch && matchesStatus && notDeleted && priority;
  });
  filtered = filtered.sort((a, b) => {
    let aVal: string | number;
    let bVal: string | number;
    if (sortBy === 'last_activity') {
      aVal = new Date(a.last_activity).getTime();
      bVal = new Date(b.last_activity).getTime();
    } else {
      aVal = (a[sortBy] || '').toString().toLowerCase();
      bVal = (b[sortBy] || '').toString().toLowerCase();
    }
    if (aVal < bVal) return sortDir === 'asc' ? -1 : 1;
    if (aVal > bVal) return sortDir === 'asc' ? 1 : -1;
    return 0;
  });

  const handleCreateLoan = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setFormLoading(true);
    
    try {
      const formData = new FormData();
      formData.append('borrower', form.borrower);
      formData.append('broker', form.broker);
      formData.append('loanType', form.loanType);
      formData.append('amount', form.amount);
      
      if (form.document) {
        await apiClient.uploadFile('/loan-files', form.document, (progress) => {
          // Could show upload progress here
          console.log(`Upload progress: ${progress}%`);
        }, {
          maxRetries: 2,
          onRetry: (error, retryCount) => {
            showWarning('Upload failed', `Retrying upload... (${retryCount}/2)`);
          }
        });
      } else {
        await apiClient.post('/loan-files', {
          borrower: form.borrower,
          broker: form.broker,
          loanType: form.loanType,
          amount: form.amount,
        }, {
          maxRetries: 2,
          onRetry: (error, retryCount) => {
            showWarning('Creation failed', `Retrying... (${retryCount}/2)`);
          }
        });
      }
      
      showSuccess('Loan file created', 'The new loan file has been successfully created.');
      setShowNewLoan(false);
      setForm({borrower:'',broker:'',loanType:'',amount:'',document:null});
      await loadLoanFiles();
    } catch (err) {
      const appError = err instanceof AppError ? err : new AppError('Failed to create loan file');
      const { title, message } = formatError(appError);
      setFormError(title);
      showError(title, message);
    } finally {
      setFormLoading(false);
    }
  };

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h2>Loan Files</h2>
        <div style={{display:'flex',alignItems:'center',gap:16}}>
          <Tooltip content={showAll ? 'Show only urgent/high-priority loan files' : 'Show all loan files (including non-urgent)'}>
            <button
              className="action-btn"
              style={{background: showAll ? '#888' : '#6C2EB7', minWidth: 90, fontWeight: 500, fontSize: '1rem'}}
              onClick={() => setShowAll(v => !v)}
              aria-label={showAll ? 'Show High Priority' : 'Show All'}
            >
              {showAll ? 'Show High Priority' : 'Show All'}
            </button>
          </Tooltip>
          <button className="action-btn" style={{marginBottom: 0, display: 'flex', alignItems: 'center', gap: 8}} onClick={() => setShowNewLoan(true)} aria-label="New Loan">
            <FaPlus /> <span>New Loan</span>
          </button>
        </div>
      </div>
      <div className="dashboard-controls">
        <input
          type="text"
          placeholder="Search"
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="dashboard-search"
        />
        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          className="dashboard-filter"
        >
          <option value="">Status</option>
          {uniqueStatuses(loanFiles).map(status => (
            <option key={status} value={status}>{status}</option>
          ))}
        </select>
        <select
          value={sortBy}
          onChange={e => setSortBy(e.target.value as any)}
          className="dashboard-filter"
        >
          <option value="last_activity">Sort by Last Activity</option>
          <option value="borrower">Sort by Borrower</option>
          <option value="broker">Sort by Broker</option>
          <option value="status">Sort by Status</option>
        </select>
        <Tooltip content={sortDir === 'desc' ? 'Sort by most recent activity' : 'Sort by oldest activity'}>
          <button
            className="action-btn"
            style={{background: sortDir === 'desc' ? '#6C2EB7' : '#B76C2E', minWidth: 40, padding: '7px 10px'}}
            onClick={() => setSortDir(d => d === 'asc' ? 'desc' : 'asc')}
            aria-label={sortDir === 'desc' ? 'Sort Descending' : 'Sort Ascending'}
          >
            {sortDir === 'desc' ? '↓' : '↑'}
          </button>
        </Tooltip>
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
                <tr key={file.id} className={
                  (isHighPriority(file) ? 'priority-row ' : '') + (selected && selected.id === file.id ? 'selected-row' : '')
                }>
                  <td>{file.borrower}</td>
                  <td>{file.broker}</td>
                  <td>
                    <Tooltip content={(() => {
                      const s = file.status.toLowerCase();
                      if (s === 'docs needed') return 'Missing required documents. Needs immediate attention.';
                      if (s === 'pending docs') return 'Waiting for borrower to upload documents.';
                      if (s === 'incomplete') return 'Loan file is incomplete and needs attention.';
                      if (s === 'complete') return 'All documents received. Ready for review.';
                      if (s === 'under review') return 'Loan file is under review.';
                      return `Status: ${file.status}`;
                    })()}>
                      <span className={statusBadgeClass(file.status)}>{file.status}</span>
                    </Tooltip>
                  </td>
                  <td>{new Date(file.last_activity).toLocaleString()}</td>
                  <td>{file.outstanding_items ? file.outstanding_items : 'None'}</td>
                  <td className="actions-cell">
                    <Tooltip content="View loan file details">
                      <button className="action-btn" aria-label="View details" onClick={() => setSelected(file)}><FaEye /> <span style={{marginLeft: 4}}>View</span></button>
                    </Tooltip>
                    <Tooltip content="Upload a new document to this loan file">
                      <button className="action-btn" aria-label="Upload document"><FaUpload /> <span style={{marginLeft: 4}}>Upload</span></button>
                    </Tooltip>
                    <Tooltip content="Send a message to the broker or borrower">
                      <button className="action-btn" aria-label="Send message"><FaCommentDots /> <span style={{marginLeft: 4}}>Message</span></button>
                    </Tooltip>
                    <Tooltip content="Delete this loan file (soft delete, can be restored later)">
                      <button className="action-btn" style={{background:'#b71c1c', display: 'flex', alignItems: 'center', gap: 4}} aria-label="Delete (soft)" onClick={() => {
                        setDeleteId(file.id);
                        setConfirmOpen(true);
                      }}><FaTrash /> <span>Delete</span></button>
                    </Tooltip>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {showNewLoan && (
        <div className="modal-overlay" onClick={() => { setShowNewLoan(false); setFormError(null); setForm({borrower:'',broker:'',loanType:'',amount:'',document:null}); }}>
          <div className="modal" style={{animation:'modalPop 0.22s cubic-bezier(.4,1.4,.6,1)'}} onClick={e => e.stopPropagation()}>
            <h3>New Loan File</h3>
            <form
              onSubmit={handleCreateLoan}
            >
              <div style={{marginBottom: 12}}>
                <label>Borrower Name<br/>
                  <input type="text" value={form.borrower} required onChange={e => setForm(f => ({...f, borrower: e.target.value}))} style={{width: '100%'}} />
                </label>
              </div>
              <div style={{marginBottom: 12}}>
                <label>Broker Name<br/>
                  <input type="text" value={form.broker} required onChange={e => setForm(f => ({...f, broker: e.target.value}))} style={{width: '100%'}} />
                </label>
              </div>
              <div style={{marginBottom: 12}}>
                <label>Loan Type<br/>
                  <input type="text" value={form.loanType} required onChange={e => setForm(f => ({...f, loanType: e.target.value}))} style={{width: '100%'}} placeholder="e.g. Conventional, FHA, VA..." />
                </label>
              </div>
              <div style={{marginBottom: 12}}>
                <label>Loan Amount<br/>
                  <input type="number" value={form.amount} required onChange={e => setForm(f => ({...f, amount: e.target.value}))} style={{width: '100%'}} />
                </label>
              </div>
              <div style={{marginBottom: 12}}>
                <label>Document Upload<br/>
                  <input type="file" accept=".pdf,image/*" onChange={e => setForm(f => ({...f, document: e.target.files ? e.target.files[0] : null}))} />
                </label>
              </div>
              {formError && <div className="error">{formError}</div>}
              <div style={{display: 'flex', justifyContent: 'flex-end', gap: 12}}>
                <button type="button" className="action-btn" style={{background: '#888'}} onClick={() => { setShowNewLoan(false); setFormError(null); setForm({borrower:'',broker:'',loanType:'',amount:'',document:null}); }}>Cancel</button>
                <button type="submit" className="action-btn" disabled={formLoading}>{formLoading ? 'Submitting...' : 'Submit'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
      {selected && (
        <div className="modal-overlay" onClick={() => setSelected(null)}>
          <div className="modal" style={{animation:'modalPop 0.22s cubic-bezier(.4,1.4,.6,1)'}} onClick={e => e.stopPropagation()}>
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
      <ConfirmModal
        open={confirmOpen}
        title="Delete Loan File"
        message="Are you sure you want to delete this loan file? This action cannot be undone."
        onConfirm={() => deleteId && handleDelete(deleteId)}
        onCancel={() => { setConfirmOpen(false); setDeleteId(null); }}
        loading={deleteLoading}
      />
    </div>
  );
};

export default Dashboard; 