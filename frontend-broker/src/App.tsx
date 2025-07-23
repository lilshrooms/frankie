import React, { useState } from 'react';
import Dashboard from './components/Dashboard';
import AdminCriteriaEditor from './components/AdminCriteriaEditor';
import ConversationManager from './components/ConversationManager';
import RateOptimizationDashboard from './components/RateOptimizationDashboard';
import { ToastProvider } from './components/ToastContainer';
import ErrorBoundary from './components/ErrorBoundary';
import { FaHome, FaCog, FaEnvelope, FaChartLine } from 'react-icons/fa';
import './components/ErrorBoundary.css';
import './App.css';

type ViewType = 'dashboard' | 'conversations' | 'criteria' | 'rates';

function App() {
  const [currentView, setCurrentView] = useState<ViewType>('dashboard');

  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard />;
      case 'conversations':
        return <ConversationManager />;
      case 'criteria':
        return <AdminCriteriaEditor />;
      case 'rates':
        return <RateOptimizationDashboard />;
      default:
        return <Dashboard />;
    }
  };

  const getViewTitle = () => {
    switch (currentView) {
      case 'dashboard':
        return 'Loan Files Dashboard';
      case 'conversations':
        return 'Email Conversations';
      case 'criteria':
        return 'Admin Criteria Editor';
      case 'rates':
        return 'Rate Optimization';
      default:
        return 'Frankie Admin';
    }
  };

  return (
    <ErrorBoundary>
      <ToastProvider>
        <div className="App">
          <nav className="admin-nav">
            <div className="nav-brand">
              <h1>Frankie Admin</h1>
            </div>
            <div className="nav-links">
              <button
                className={`nav-link ${currentView === 'dashboard' ? 'active' : ''}`}
                onClick={() => setCurrentView('dashboard')}
              >
                <FaHome /> Dashboard
              </button>
              <button
                className={`nav-link ${currentView === 'conversations' ? 'active' : ''}`}
                onClick={() => setCurrentView('conversations')}
              >
                <FaEnvelope /> Conversations
              </button>
              <button
                className={`nav-link ${currentView === 'criteria' ? 'active' : ''}`}
                onClick={() => setCurrentView('criteria')}
              >
                <FaCog /> Criteria
              </button>
              <button
                className={`nav-link ${currentView === 'rates' ? 'active' : ''}`}
                onClick={() => setCurrentView('rates')}
              >
                <FaChartLine /> Rates
              </button>
            </div>
          </nav>
          
          <main className="admin-main">
            <div className="view-header">
              <h2>{getViewTitle()}</h2>
            </div>
            {renderView()}
          </main>
        </div>
      </ToastProvider>
    </ErrorBoundary>
  );
}

export default App;