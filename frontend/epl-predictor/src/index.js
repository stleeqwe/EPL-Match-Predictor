import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import ErrorBoundary from './components/ErrorBoundary';
import reportWebVitals from './reportWebVitals';

// ============================================================
// Environment Validation
// ============================================================

const validateEnvironment = () => {
  const requiredEnvVars = {
    REACT_APP_API_URL: process.env.REACT_APP_API_URL
  };

  const missingVars = Object.entries(requiredEnvVars)
    .filter(([_, value]) => !value)
    .map(([key]) => key);

  if (missingVars.length > 0) {
    const errorMsg = `
      ❌ Missing required environment variables:
      ${missingVars.join(', ')}

      Please create a .env file in the frontend/epl-predictor directory with:
      REACT_APP_API_URL=http://localhost:5001/api
    `;

    console.error(errorMsg);

    // Show error in UI
    document.body.innerHTML = `
      <div style="display: flex; justify-content: center; align-items: center; height: 100vh; font-family: Arial;">
        <div style="max-width: 600px; padding: 2rem; background: #fee; border: 2px solid #c00; border-radius: 8px;">
          <h1 style="color: #c00;">⚠️ Configuration Error</h1>
          <pre style="white-space: pre-wrap; background: #fff; padding: 1rem; border-radius: 4px;">${errorMsg}</pre>
        </div>
      </div>
    `;

    throw new Error('Missing required environment variables');
  }

  // Log config in development
  if (process.env.NODE_ENV === 'development') {
    console.log('✅ Environment validated successfully');
    console.log('📡 API URL:', process.env.REACT_APP_API_URL);
  }
};

validateEnvironment();

// ============================================================
// Render App
// ============================================================

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
