import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import PlayerRatingManager from './components/PlayerRatingManager';
import { ToastContainer } from './components/Toast';
import { useToast } from './hooks/useToast';
import { fixturesAPI } from './services/api';
import './App.css';

function App() {
  const [darkMode, setDarkMode] = useState(false);
  const [selectedTeam, setSelectedTeam] = useState('');
  const { toasts, removeToast, success, error: showError, info } = useToast();

  const bgColor = darkMode ? 'bg-gray-900' : 'bg-gray-50';
  const textColor = darkMode ? 'text-gray-100' : 'text-gray-900';

  return (
    <>
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      <div className={`min-h-screen ${bgColor} ${textColor} p-4 md:p-6 transition-colors duration-300 ${darkMode ? 'dark' : ''}`}>
        <Header darkMode={darkMode} setDarkMode={setDarkMode} />

        {/* 메인 컨텐츠 */}
        <div className="max-w-7xl mx-auto mt-8">
          <div className="text-center mb-8">
            <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4">
              ⚽ EPL 선수 능력치 분석
            </h1>
            <p className="text-lg text-gray-600 dark:text-gray-400">
              프리미어리그 팀별 선수 능력을 전문적으로 평가하세요
            </p>
          </div>

          {/* 선수 평가 시스템 */}
          <PlayerRatingManager
            darkMode={darkMode}
            onTeamSelect={setSelectedTeam}
          />
        </div>

        {/* Footer */}
        <div className="max-w-7xl mx-auto mt-12 text-center text-sm text-gray-500 dark:text-gray-400">
          <p>EPL Player Analysis Platform v2.0 | 선수 데이터는 FBref에서 제공됩니다</p>
        </div>
      </div>
    </>
  );
}

export default App;
