import React from 'react';
import Dashboard from './components/Dashboard';
import { ToastProvider } from './components/ToastContainer';
import ErrorBoundary from './components/ErrorBoundary';
import './components/ErrorBoundary.css';

function App() {
  return (
    <ErrorBoundary>
      <ToastProvider>
        <div className="App">
          <Dashboard />
        </div>
      </ToastProvider>
    </ErrorBoundary>
  );
}

export default App;