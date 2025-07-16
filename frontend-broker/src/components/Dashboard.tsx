import React from 'react';
import './Dashboard.css';

const mockLoanFiles = [
  {
    id: '1',
    borrower: 'Natalie M Tan',
    broker: 'Ian Tan',
    status: 'Incomplete',
    lastActivity: '2024-06-10T14:23:00Z',
    outstandingItems: ['Credit Report', 'Purchase Agreement'],
  },
  {
    id: '2',
    borrower: 'John Smith',
    broker: 'Rett Johnson',
    status: 'Pending Docs',
    lastActivity: '2024-06-09T10:12:00Z',
    outstandingItems: ['Bank Statements'],
  },
  {
    id: '3',
    borrower: 'Alice Lee',
    broker: 'Ian Tan',
    status: 'Under Review',
    lastActivity: '2024-06-08T16:45:00Z',
    outstandingItems: [],
  },
];

const Dashboard: React.FC = () => {
  return (
    <div className="dashboard-container">
      <h2>Loan Files</h2>
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
          {mockLoanFiles.map(file => (
            <tr key={file.id}>
              <td>{file.borrower}</td>
              <td>{file.broker}</td>
              <td>{file.status}</td>
              <td>{new Date(file.lastActivity).toLocaleString()}</td>
              <td>{file.outstandingItems.length > 0 ? file.outstandingItems.join(', ') : 'None'}</td>
              <td>
                <button className="action-btn">View</button>
                <button className="action-btn">Upload</button>
                <button className="action-btn">Message</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Dashboard; 