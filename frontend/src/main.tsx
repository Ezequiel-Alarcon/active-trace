import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';
import { apiClient } from './shared/services/api';
import { installProfessorDemoMocks, isProfessorDemoMocksEnabled } from './mocks/professorDemo';

const rootElement = document.getElementById('root');
if (!rootElement) throw new Error('Root element not found');

if (isProfessorDemoMocksEnabled()) {
  installProfessorDemoMocks(apiClient);
}

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
