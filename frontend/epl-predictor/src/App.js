import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowUp } from 'lucide-react';
import Header from './components/Header';
import PlayerRatingManager from './components/PlayerRatingManager';
import EPLDashboard from './components/EPLDashboard';
import MatchSimulator from './components/MatchSimulator';
import MatchPredictionsDashboard from './components/MatchPredictionsDashboard';
import ErrorBoundary from './components/ErrorBoundary';
import { ToastProvider } from './contexts/ToastContext';
import api from './services/api';
import './App.css';

/**
 * App Component
 * Visionary AI Analytics - Main Entry Point
 * Version 1.0 (Personal Analysis & AI Simulation)
 */
function App() {
  const [darkMode, setDarkMode] = useState(false);
  const [currentPage, setCurrentPage] = useState('dashboard'); // 'dashboard' or 'ratings'
  const [selectedTeam, setSelectedTeam] = useState(null); // 선택된 팀
  const [selectedMatch, setSelectedMatch] = useState(null); // 선택된 경기 (홈팀, 원정팀)
  const [selectedPredictionMatch, setSelectedPredictionMatch] = useState(null); // 선택된 경기예측 경기
  const [showScrollTop, setShowScrollTop] = useState(false); // 스크롤 맨 위로 버튼

  // 백엔드 연결 상태
  const [backendStatus, setBackendStatus] = useState('checking'); // 'checking' | 'connected' | 'error'
  const [retryCount, setRetryCount] = useState(0);
  const MAX_RETRIES = 5;

  // 백엔드 헬스 체크
  useEffect(() => {
    const checkBackend = async () => {
      try {
        await api.health.check();
        setBackendStatus('connected');
        console.log('✅ Backend connected successfully');
      } catch (error) {
        console.error('❌ Backend connection failed:', error);

        if (retryCount < MAX_RETRIES) {
          console.log(`⏳ Retrying... (${retryCount + 1}/${MAX_RETRIES})`);
          setRetryCount(prev => prev + 1);
          setTimeout(checkBackend, 3000); // 3초 후 재시도
        } else {
          setBackendStatus('error');
        }
      }
    };

    checkBackend();
  }, [retryCount]);

  const handleManualRetry = () => {
    setRetryCount(0);
    setBackendStatus('checking');
  };

  // 스크롤 위치 감지
  useEffect(() => {
    const handleScroll = () => {
      setShowScrollTop(window.scrollY > 300);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // 맨 위로 스크롤
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // 팀 선택 핸들러 (대시보드에서 팀 클릭 시)
  const handleTeamClick = (teamName) => {
    setSelectedTeam(teamName);
    setCurrentPage('ratings'); // 팀 분석 페이지로 이동
  };

  // 가상대결 버튼 클릭 핸들러
  const handleMatchSimulatorClick = (fixture) => {
    setSelectedMatch({
      homeTeam: fixture.team_h_name,
      awayTeam: fixture.team_a_name
    });
    setCurrentPage('match-simulator'); // 가상대결 페이지로 이동
  };

  // 경기예측 버튼 클릭 핸들러
  const handleMatchPredictionClick = (fixture) => {
    // 경기예측 페이지로 이동하고 해당 경기 정보 전달
    setSelectedPredictionMatch({
      homeTeam: fixture.team_h_name,
      awayTeam: fixture.team_a_name
    });
    setCurrentPage('match-predictions');
  };

  // 탭 정의
  const tabs = [
    { id: 'dashboard', label: '대시보드' },
    { id: 'ratings', label: '팀 분석' },
    { id: 'match-predictions', label: 'Sharp Vision AI' },
    { id: 'match-simulator', label: '가상대결' }
  ];

  // 백엔드 연결 확인 중
  if (backendStatus === 'checking') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-brand-darker">
        <motion.div 
          className="text-center"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3 }}
        >
          <div className="relative w-16 h-16 mx-auto mb-6">
            <div className="spinner"></div>
          </div>
          <motion.h2 
            className="text-2xl font-bold mb-2 text-white"
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            백엔드 서버 연결 중...
          </motion.h2>
          <p className="text-white/60">
            {retryCount > 0 && `재시도 중... (${retryCount}/${MAX_RETRIES})`}
          </p>
        </motion.div>
      </div>
    );
  }

  // 백엔드 연결 실패
  if (backendStatus === 'error') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-brand-darker p-4">
        <motion.div 
          className="card max-w-md p-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ type: 'spring', stiffness: 300 }}
        >
          <motion.div 
            className="text-6xl text-center mb-4"
            animate={{ rotate: [0, -10, 10, -10, 0] }}
            transition={{ duration: 0.5 }}
          >
            ⚠️
          </motion.div>
          <h2 className="text-2xl font-bold text-center mb-4 text-white">
            백엔드 서버 연결 실패
          </h2>
          <p className="text-center mb-6 text-white/60">
            백엔드 API 서버에 연결할 수 없습니다.
            <br />
            서버가 실행 중인지 확인해주세요.
          </p>
          <div className="glass p-4 rounded-lg mb-6">
            <p className="text-sm text-white/80 font-mono break-all">
              API URL: {process.env.REACT_APP_API_URL}
            </p>
            <p className="text-xs mt-2 text-white/50">
              백엔드 서버 시작: <code className="text-brand-accent">./start_backend.sh</code>
            </p>
          </div>
          <motion.button
            onClick={handleManualRetry}
            className="btn btn-primary w-full"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            🔄 다시 시도
          </motion.button>
        </motion.div>
      </div>
    );
  }

  // 정상 연결 - 앱 렌더링
  return (
    <ErrorBoundary darkMode={darkMode}>
      <ToastProvider darkMode={darkMode}>
        <div className={`min-h-screen transition-colors duration-300 bg-brand-darker ${darkMode ? 'dark' : ''}`}>
          {/* Header */}
          <Header darkMode={darkMode} setDarkMode={setDarkMode} />

          {/* Navigation Tabs */}
          <nav className="relative z-30 mt-4 backdrop-blur-lg bg-brand-darker/95 shadow-lg">
            <div className="container-custom">
              <div className="flex gap-2 relative">
                {tabs.map((tab) => (
                  <motion.button
                    key={tab.id}
                    onClick={() => setCurrentPage(tab.id)}
                    className={`
                      relative px-4 md:px-6 py-2 md:py-3 font-bold transition-all duration-300
                      flex items-center gap-2 rounded-t-xl overflow-hidden
                      ${currentPage === tab.id
                        ? 'text-white scale-105'
                        : 'text-white/60 hover:text-white/90'
                      }
                    `}
                    whileHover={{ y: currentPage === tab.id ? 0 : -2 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    {/* Background Image Layer */}
                    <div
                      className="absolute inset-0 rounded-t-xl opacity-50"
                      style={{
                        backgroundImage: 'url(/tab.png)',
                        backgroundSize: 'cover',
                        backgroundPosition: 'center',
                        backgroundRepeat: 'no-repeat'
                      }}
                    />

                    {/* Overlay for inactive tabs */}
                    {currentPage !== tab.id && (
                      <div className="absolute inset-0 bg-black/40 rounded-t-xl" />
                    )}

                    {/* Active tab overlay */}
                    {currentPage === tab.id && (
                      <>
                        <motion.div
                          layoutId="activeTab"
                          className="absolute inset-0 bg-black/20 rounded-t-xl"
                          initial={false}
                          transition={{
                            type: 'spring',
                            stiffness: 500,
                            damping: 30
                          }}
                        />
                        {/* Glow Effect */}
                        <motion.div
                          className="absolute inset-0 bg-brand-accent/20 rounded-t-xl blur-lg"
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 0.5 }}
                          transition={{ duration: 0.3 }}
                        />
                        {/* Bottom Border Accent */}
                        <div className="absolute bottom-0 left-0 right-0 h-1 bg-brand-accent/80" />
                      </>
                    )}

                    {/* Tab Content */}
                    <span className="relative z-10 text-sm md:text-base font-extrabold">
                      {tab.label}
                    </span>
                  </motion.button>
                ))}
              </div>
            </div>
          </nav>

          {/* Main Content */}
          <main className="relative">
            {/* 각 페이지를 동시에 마운트하고 CSS로 표시/숨김 제어 */}
            <div
              className={`w-full transition-opacity duration-300 ${
                currentPage === 'dashboard'
                  ? 'opacity-100 relative'
                  : 'opacity-0 absolute inset-0 pointer-events-none'
              }`}
            >
              <EPLDashboard
                darkMode={darkMode}
                onTeamClick={handleTeamClick}
                onMatchSimulatorClick={handleMatchSimulatorClick}
                onMatchPredictionClick={handleMatchPredictionClick}
              />
            </div>
            <div
              className={`w-full transition-opacity duration-300 ${
                currentPage === 'ratings'
                  ? 'opacity-100 relative'
                  : 'opacity-0 absolute inset-0 pointer-events-none'
              }`}
            >
              <PlayerRatingManager darkMode={darkMode} initialTeam={selectedTeam} />
            </div>
            <div
              className={`w-full transition-opacity duration-300 ${
                currentPage === 'match-predictions'
                  ? 'opacity-100 relative'
                  : 'opacity-0 absolute inset-0 pointer-events-none'
              }`}
            >
              <MatchPredictionsDashboard darkMode={darkMode} selectedMatch={selectedPredictionMatch} />
            </div>
            <div
              className={`w-full transition-opacity duration-300 ${
                currentPage === 'match-simulator'
                  ? 'opacity-100 relative'
                  : 'opacity-0 absolute inset-0 pointer-events-none'
              }`}
            >
              <MatchSimulator darkMode={darkMode} selectedMatch={selectedMatch} />
            </div>
          </main>

          {/* Footer */}
          <footer className="section border-t border-white/10 mt-16">
            <div className="container-custom text-center">
              <motion.div
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5 }}
              >
                <p className="text-sm text-white/60 mb-2">
                  Visionary AI Analytics v2.0
                </p>
                <div className="flex items-center justify-center gap-2 mb-2">
                  <span className="text-xs text-white/50">Powered by</span>
                  <span className="text-xs font-bold text-emerald-300">ChatGPT</span>
                  <span className="text-white/50">&</span>
                  <span className="text-xs font-bold text-orange-300">Claude</span>
                </div>
                <p className="text-xs text-white/40">
                  © 2025 pukaworks. All rights reserved.
                </p>
              </motion.div>
            </div>
          </footer>

          {/* Scroll to Top Button */}
          <AnimatePresence>
            {showScrollTop && (
              <motion.button
                onClick={scrollToTop}
                className="fixed bottom-8 right-8 z-50 p-3 rounded-full bg-brand-primary hover:bg-brand-accent shadow-glow transition-colors"
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0 }}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                aria-label="맨 위로"
              >
                <ArrowUp className="w-6 h-6 text-white" />
              </motion.button>
            )}
          </AnimatePresence>
        </div>
      </ToastProvider>
    </ErrorBoundary>
  );
}

export default App;
