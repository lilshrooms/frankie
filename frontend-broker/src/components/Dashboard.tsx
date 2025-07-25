import React, { useState, useEffect } from 'react';
import './Dashboard.css';
import { FaPlus, FaEye, FaEdit, FaTrash, FaDownload, FaUpload } from 'react-icons/fa';
import Tooltip from './Tooltip';
import { useToast } from './ToastContainer';
import ConfirmModal from './ConfirmModal';

interface LoanFile {
  id: number;
  borrower: string;
  status: string;
  lastActivity: string;
  documents: string[];
  priority: 'high' | 'medium' | 'low';
}

const Dashboard: React.FC = () => {
  const { showSuccess, showError, showWarning, showInfo } = useToast();
  const [loanFiles, setLoanFiles] = useState<LoanFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [showNewLoan, setShowNewLoan] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState<LoanFile | null>(null);
  const [form, setForm] = useState({
    borrower: '',
    status: 'Incomplete',
    priority: 'medium' as const
  });

  useEffect(() => {
    loadLoanFiles();
  }, []);

  const loadLoanFiles = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/loan-files');
      if (response.ok) {
        const data = await response.json();
        setLoanFiles(data);
      } else {
        // Mock data for demonstration
        setLoanFiles([
          {
            id: 1,
            borrower: 'John Smith',
            status: 'Incomplete',
            lastActivity: '2024-01-15',
            documents: ['Tax Return', 'Pay Stub'],
            priority: 'high'
          },
          {
            id: 2,
            borrower: 'Sarah Johnson',
            status: 'Under Review',
            lastActivity: '2024-01-14',
            documents: ['W2', 'Bank Statement'],
            priority: 'medium'
          },
          {
            id: 3,
            borrower: 'Mike Wilson',
            status: 'Complete',
            lastActivity: '2024-01-13',
            documents: ['All Documents'],
            priority: 'low'
          }
        ]);
      }
    } catch (error) {
      showError('Error', 'Failed to load loan files');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (file: LoanFile) => {
    setSelectedFile(file);
    setShowDeleteModal(true);
  };

  const confirmDelete = async () => {
    if (!selectedFile) return;
    
    try {
      const response = await fetch(`/api/loan-files/${selectedFile.id}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        setLoanFiles(loanFiles.filter(f => f.id !== selectedFile.id));
        showSuccess('Success', 'Loan file deleted successfully');
      } else {
        showError('Error', 'Failed to delete loan file');
      }
    } catch (error) {
      showError('Error', 'Failed to delete loan file');
    } finally {
      setShowDeleteModal(false);
      setSelectedFile(null);
    }
  };

  const handleAnalyze = async (file: LoanFile) => {
    try {
      showInfo('Analysis', `Starting AI analysis for ${file.borrower}...`);
      // Mock analysis process
      setTimeout(() => {
        showSuccess('Analysis Complete', `AI analysis completed for ${file.borrower}`);
      }, 2000);
    } catch (error) {
      showError('Error', 'Failed to start analysis');
    }
  };

  const filteredFiles = loanFiles.filter(file => {
    const matchesSearch = file.borrower.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || file.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusBadgeClass = (status: string) => {
    switch (status.toLowerCase()) {
      case 'complete': return 'status-badge complete';
      case 'under review': return 'status-badge under-review';
      case 'incomplete': return 'status-badge incomplete';
      case 'pending docs': return 'status-badge pending-docs';
      case 'docs needed': return 'status-badge docs-needed';
      default: return 'status-badge';
    }
  };

  const getPriorityClass = (priority: string) => {
    switch (priority) {
      case 'high': return 'priority-high';
      case 'medium': return 'priority-medium';
      case 'low': return 'priority-low';
      default: return '';
    }
  };

  if (loading) {
    return (
      <div className="dashboard-container">
        <div className="loading">Loading loan files...</div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      {/* Header */}
      <div className="dashboard-header">
        <div className="header-content">
          <h2>Loan Files Dashboard</h2>
          <p>Manage and track all loan applications</p>
        </div>
        <div className="header-actions">
          <Tooltip content="Upload new documents">
            <button className="action-btn" onClick={() => setShowNewLoan(true)}>
              <FaUpload />
              <span>Upload</span>
            </button>
          </Tooltip>
          <Tooltip content="Create new loan file">
            <button className="action-btn" onClick={() => setShowNewLoan(true)}>
              <FaPlus />
              <span>New Loan</span>
            </button>
          </Tooltip>
        </div>
      </div>

      {/* Controls */}
      <div className="dashboard-controls">
        <div className="search-filter-group">
          <div className="search-container">
            <span className="search-icon">🔍</span>
            <input
              type="text"
              placeholder="Search by borrower name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="dashboard-search"
            />
          </div>
          <div className="filter-container">
            <span className="filter-icon">⚙️</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="dashboard-filter"
            >
              <option value="all">All Status</option>
              <option value="Incomplete">Incomplete</option>
              <option value="Under Review">Under Review</option>
              <option value="Complete">Complete</option>
              <option value="Pending Docs">Pending Docs</option>
            </select>
          </div>
        </div>
      </div>

      {/* Loan Files Table */}
      <div className="dashboard-table-wrapper">
        <table className="loan-table">
          <thead>
            <tr>
              <th>Borrower</th>
              <th>Status</th>
              <th>Priority</th>
              <th>Last Activity</th>
              <th>Documents</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredFiles.map((file) => (
              <tr key={file.id} className={`priority-row ${getPriorityClass(file.priority)}`}>
                <td>{file.borrower}</td>
                <td>
                  <span className={getStatusBadgeClass(file.status)}>
                    {file.status}
                  </span>
                </td>
                <td>
                  <span className={`priority-badge ${getPriorityClass(file.priority)}`}>
                    {file.priority}
                  </span>
                </td>
                <td>{file.lastActivity}</td>
                <td>{file.documents.join(', ')}</td>
                <td className="actions-cell">
                  <Tooltip content="View details">
                    <button className="action-btn" onClick={() => handleAnalyze(file)}>
                      <FaEye />
                    </button>
                  </Tooltip>
                  <Tooltip content="Edit loan file">
                    <button className="action-btn" onClick={() => handleAnalyze(file)}>
                      <FaEdit />
                    </button>
                  </Tooltip>
                  <Tooltip content="Download documents">
                    <button className="action-btn" onClick={() => handleAnalyze(file)}>
                      <FaDownload />
                    </button>
                  </Tooltip>
                  <Tooltip content="Delete loan file">
                    <button className="action-btn" onClick={() => handleDelete(file)}>
                      <FaTrash />
                    </button>
                  </Tooltip>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Delete Confirmation Modal */}
      <ConfirmModal
        open={showDeleteModal}
        onCancel={() => setShowDeleteModal(false)}
        onConfirm={confirmDelete}
        title="Delete Loan File"
        message={`Are you sure you want to delete the loan file for ${selectedFile?.borrower}? This action cannot be undone.`}
      />
    </div>
  );
};

export default Dashboard; 