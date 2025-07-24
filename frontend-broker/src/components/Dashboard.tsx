import React, { useState } from 'react';
import './Dashboard.css';
import { FaPlus, FaUpload, FaChartLine, FaCog, FaEnvelope } from 'react-icons/fa';
import Tooltip from './Tooltip';
import { useToast } from './ToastContainer';

const Dashboard: React.FC = () => {
  const { showSuccess, showError, showWarning, showInfo } = useToast();
  const [activeSection, setActiveSection] = useState<string>('overview');

  const handleQuickAction = (action: string) => {
    showInfo('Action', `${action} functionality coming soon!`);
  };

  return (
    <div className="dashboard-container">
      {/* Modern Header */}
      <div className="dashboard-header">
        <div className="header-content">
          <h2>Frankie Dashboard</h2>
          <p>AI-powered loan assistant - streamline your mortgage workflow</p>
        </div>
        <div className="header-actions">
          <Tooltip content="View system notifications and alerts">
            <button
              className="action-btn notification-btn"
              onClick={() => handleQuickAction('Notifications')}
              aria-label="Notifications"
            >
              <FaEnvelope />
              <span>Notifications</span>
            </button>
          </Tooltip>
          <Tooltip content="Configure system settings and preferences">
            <button
              className="action-btn settings-btn"
              onClick={() => handleQuickAction('Settings')}
              aria-label="Settings"
            >
              <FaCog />
              <span>Settings</span>
            </button>
          </Tooltip>
        </div>
      </div>

      {/* Quick Actions Grid */}
      <div className="quick-actions-grid">
        <div className="action-card primary-action">
          <div className="action-icon">
            <FaUpload />
          </div>
          <div className="action-content">
            <h3>Upload Documents</h3>
            <p>Process loan documents with AI analysis</p>
            <button 
              className="action-card-btn primary"
              onClick={() => handleQuickAction('Upload Documents')}
            >
              Upload Now
            </button>
          </div>
        </div>

        <div className="action-card">
          <div className="action-icon">
            <FaChartLine />
          </div>
          <div className="action-content">
            <h3>Rate Analysis</h3>
            <p>Generate and compare mortgage rates</p>
            <button 
              className="action-card-btn"
              onClick={() => handleQuickAction('Rate Analysis')}
            >
              Analyze Rates
            </button>
          </div>
        </div>

        <div className="action-card">
          <div className="action-icon">
            <FaPlus />
          </div>
          <div className="action-content">
            <h3>New Application</h3>
            <p>Start a new loan application</p>
            <button 
              className="action-card-btn"
              onClick={() => handleQuickAction('New Application')}
            >
              Create New
            </button>
          </div>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="stats-overview">
        <div className="stat-card">
          <div className="stat-number">12</div>
          <div className="stat-label">Active Applications</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">8</div>
          <div className="stat-label">Pending Reviews</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">95%</div>
          <div className="stat-label">Completion Rate</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">2.3</div>
          <div className="stat-label">Avg. Processing Days</div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="recent-activity">
        <h3>Recent Activity</h3>
        <div className="activity-list">
          <div className="activity-item">
            <div className="activity-icon">📄</div>
            <div className="activity-content">
              <div className="activity-title">Document uploaded</div>
              <div className="activity-desc">Pay stub for John Smith's application</div>
              <div className="activity-time">2 hours ago</div>
            </div>
          </div>
          <div className="activity-item">
            <div className="activity-icon">💰</div>
            <div className="activity-content">
              <div className="activity-title">Rate quote generated</div>
              <div className="activity-desc">3.75% for $450k conventional loan</div>
              <div className="activity-time">4 hours ago</div>
            </div>
          </div>
          <div className="activity-item">
            <div className="activity-icon">🤖</div>
            <div className="activity-content">
              <div className="activity-title">AI analysis completed</div>
              <div className="activity-desc">Tax returns analyzed for Sarah Johnson</div>
              <div className="activity-time">1 day ago</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 