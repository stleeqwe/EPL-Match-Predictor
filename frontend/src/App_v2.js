import React, { useState } from 'react';
import { Moon, Sun } from 'lucide-react';
import OddsDashboard from './components/odds/OddsDashboard';
import './App.css';

/**
 * Main App Component
 * Version 2.0 - Odds-Based Value Betting System
 */
function App() {
  const [darkMode, setDarkMode] = useState(true);

  return (
    <div className={darkMode ? 'dark' : ''}>
      {/* Dark Mode Toggle */}
      <div className="fixed top-4 right-4 z-50">
        <button
          onClick={() => setDarkMode(!darkMode)}
          className="p-3 rounded-full bg-gray-800 dark:bg-gray-700 text-white hover:bg-gray-700 dark:hover:bg-gray-600 transition-all shadow-lg"
          aria-label="Toggle dark mode"
        >
          {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>
      </div>

      {/* Main Dashboard */}
      <OddsDashboard darkMode={darkMode} />

      {/* Footer */}
      <footer className={`${darkMode ? 'bg-gray-900 text-gray-400' : 'bg-gray-100 text-gray-600'} py-6 border-t ${darkMode ? 'border-gray-800' : 'border-gray-200'}`}>
        <div className="max-w-7xl mx-auto px-6 text-center">
          <p className="text-sm">
            ⚽ EPL Odds-Based Value Betting System v2.0
          </p>
          <p className="text-xs mt-2">
            <span className="font-semibold">⚠️ Disclaimer:</span> For educational purposes only. 
            Bet responsibly. Past performance does not guarantee future results.
          </p>
          <p className="text-xs mt-2 text-gray-500">
            Powered by The Odds API • Kelly Criterion • Bayesian Analysis
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
