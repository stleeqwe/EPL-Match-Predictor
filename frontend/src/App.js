import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowUp, ChevronDown, LayoutDashboard, Eye, Zap, Swords } from 'lucide-react';
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
  const [selectedPlayer, setSelectedPlayer] = useState(null); // 선택된 선수
  const [selectedMatch, setSelectedMatch] = useState(null); // 선택된 경기 (홈팀, 원정팀)
  const [selectedPredictionMatch, setSelectedPredictionMatch] = useState(null); // 선택된 경기예측 경기
  const [showScrollTop, setShowScrollTop] = useState(false); // 스크롤 맨 위로 버튼
  const [selectedLeague, setSelectedLeague] = useState('EPL'); // 선택된 리그
  const [leagueDropdownOpen, setLeagueDropdownOpen] = useState(false); // 리그 드롭다운 상태
  const leagueDropdownRef = useRef(null);

  // 🔧 선수 평가 데이터 상태 (모든 팀의 평가를 통합 관리)
  const [playerRatings, setPlayerRatings] = useState({});

  // 백엔드 연결 상태
  const [backendStatus, setBackendStatus] = useState('checking'); // 'checking' | 'connected' | 'error'
  const [retryCount, setRetryCount] = useState(0);
  const MAX_RETRIES = 5;

  // V3 Auth 테스트 상태
  const [v3AuthTesting, setV3AuthTesting] = useState(false);

  // 🔧 localStorage에서 모든 팀의 평가 데이터 로드
  useEffect(() => {
    const loadAllRatings = () => {
      const allRatings = {};

      // localStorage의 모든 키를 순회하며 team_ratings_로 시작하는 것만 로드
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith('team_ratings_')) {
          const teamName = key.replace('team_ratings_', '');
          try {
            const ratings = JSON.parse(localStorage.getItem(key));
            // 팀명을 키로, 해당 팀의 선수 평가들을 값으로 저장
            allRatings[teamName] = ratings;
          } catch (error) {
            console.error(`❌ Failed to parse ratings for ${teamName}:`, error);
          }
        }
      }

      setPlayerRatings(allRatings);
    };

    loadAllRatings();

    // localStorage 변경 감지 (다른 탭에서 변경 시)
    const handleStorageChange = (e) => {
      if (e.key && e.key.startsWith('team_ratings_')) {
        loadAllRatings();
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  // 🔧 선수 평가 업데이트 핸들러
  const handleRatingsUpdate = (teamName, updatedRatings) => {
    setPlayerRatings(prev => ({
      ...prev,
      [teamName]: updatedRatings
    }));
  };

  // 🔧 모든 팀의 평가를 하나의 객체로 병합 (선수 ID를 키로)
  const getMergedRatings = () => {
    const merged = {};
    Object.values(playerRatings).forEach(teamRatings => {
      Object.assign(merged, teamRatings);
    });
    return merged;
  };

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

  // 드롭다운 외부 클릭 감지
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (leagueDropdownRef.current && !leagueDropdownRef.current.contains(event.target)) {
        setLeagueDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // 맨 위로 스크롤
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // 로고 클릭 핸들러 (메인 대시보드로 이동)
  const handleLogoClick = () => {
    setCurrentPage('dashboard');
    setSelectedTeam(null);
    setSelectedMatch(null);
    setSelectedPredictionMatch(null);
    scrollToTop();
  };

  // 팀 선택 핸들러 (대시보드에서 팀 클릭 시)
  const handleTeamClick = (teamName) => {
    setSelectedTeam(teamName);
    setSelectedPlayer(null); // 이전 선수 선택 초기화
    setCurrentPage('ratings'); // 팀 분석 페이지로 이동

    // 페이지 전환 애니메이션 완료 후 스크롤 (300ms transition + 여유)
    setTimeout(() => {
      window.scrollTo({ top: 0, behavior: 'auto' });
    }, 350);
  };

  // 선수 선택 핸들러 (리더보드에서 선수 클릭 시)
  const handlePlayerClick = (player) => {
    setSelectedTeam(player.team); // 선수의 팀 설정
    setSelectedPlayer(player); // 선수 정보 저장
    setCurrentPage('ratings'); // 팀 분석 페이지로 이동
    // 스크롤은 PlayerRatingManager에서 처리
  };

  // 가상대결 버튼 클릭 핸들러
  const handleMatchSimulatorClick = (fixture) => {
    setSelectedMatch({
      homeTeam: fixture.team_h_name,
      awayTeam: fixture.team_a_name
    });
    setCurrentPage('match-simulator'); // 가상대결 페이지로 이동
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        window.scrollTo({ top: 0, behavior: 'auto' });
      });
    });
  };

  // 경기예측 버튼 클릭 핸들러
  const handleMatchPredictionClick = (fixture) => {
    // 경기예측 페이지로 이동하고 해당 경기 정보 전달
    setSelectedPredictionMatch({
      homeTeam: fixture.team_h_name,
      awayTeam: fixture.team_a_name
    });
    setCurrentPage('match-predictions');
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        window.scrollTo({ top: 0, behavior: 'auto' });
      });
    });
  };

  // V3 Auth API 테스트 함수
  const testV3Auth = async () => {
    if (v3AuthTesting) return;

    setV3AuthTesting(true);
    console.log('🚀 V3 Auth API 테스트 시작...');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

    const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';
    const timestamp = Date.now();
    const testEmail = `test_${timestamp}@example.com`;
    const testPassword = 'SecurePass123!';

    try {
      // 1. 회원가입 테스트
      console.log('\n📝 1. 회원가입 테스트 (POST /v1/auth/signup)');
      console.log('요청 데이터:', { email: testEmail, password: '***', display_name: 'Test User' });

      const signupResponse = await fetch(`${API_BASE_URL}/v1/auth/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: testEmail,
          password: testPassword,
          display_name: 'Test User'
        })
      });

      const signupData = await signupResponse.json();

      if (signupResponse.ok) {
        console.log('✅ 회원가입 성공!');
        console.log('응답 데이터:', {
          success: signupData.success,
          user: signupData.user,
          access_token: signupData.access_token ? `${signupData.access_token.substring(0, 20)}...` : null,
          refresh_token: signupData.refresh_token ? `${signupData.refresh_token.substring(0, 20)}...` : null
        });
      } else {
        console.error('❌ 회원가입 실패:', signupData);
      }

      // 2. 로그인 테스트
      console.log('\n🔑 2. 로그인 테스트 (POST /v1/auth/login)');
      console.log('요청 데이터:', { email: testEmail, password: '***' });

      const loginResponse = await fetch(`${API_BASE_URL}/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: testEmail,
          password: testPassword
        })
      });

      const loginData = await loginResponse.json();

      if (loginResponse.ok) {
        console.log('✅ 로그인 성공!');
        console.log('응답 데이터:', {
          success: loginData.success,
          user: loginData.user,
          access_token: loginData.access_token ? `${loginData.access_token.substring(0, 20)}...` : null,
          refresh_token: loginData.refresh_token ? `${loginData.refresh_token.substring(0, 20)}...` : null
        });
      } else {
        console.error('❌ 로그인 실패:', loginData);
      }

      console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
      console.log('🎉 V3 Auth API 테스트 완료!');

    } catch (error) {
      console.error('❌ V3 Auth API 테스트 중 오류 발생:', error);
      console.log('\n⚠️ 백엔드 서버가 실행 중인지 확인해주세요.');
      console.log('   - 서버 URL:', API_BASE_URL);
      console.log('   - 오류:', error.message);
    } finally {
      setV3AuthTesting(false);
    }
  };

  // 리그 목록
  const leagues = [
    { id: 'EPL', name: 'EPL', fullName: 'Premier League', flag: '🏴󠁧󠁢󠁥󠁮󠁧󠁿' },
    { id: 'Serie A', name: '세리에A', fullName: 'Serie A', flag: '🇮🇹' },
    { id: 'Bundesliga', name: '분데스리가', fullName: 'Bundesliga', flag: '🇩🇪' },
    { id: 'La Liga', name: '라리가', fullName: 'La Liga', flag: '🇪🇸' }
  ];

  const currentLeague = leagues.find(l => l.id === selectedLeague) || leagues[0];

  // 탭 정의
  const tabs = [
    { id: 'dashboard', label: '대시보드', icon: LayoutDashboard },
    { id: 'ratings', label: 'MyVision', icon: Eye },
    { id: 'match-simulator', label: '가상대결', icon: Swords },
    { id: 'match-predictions', label: 'Sharp Vision AI', icon: Zap }
  ];

  // 백엔드 연결 확인 중
  if (backendStatus === 'checking') {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: '#1e1b2e' }}>
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
      <div className="min-h-screen flex items-center justify-center p-4" style={{ backgroundColor: '#1e1b2e' }}>
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
          <div className="glass p-4 rounded-sm mb-6">
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
        <div className={`min-h-screen transition-colors duration-300 ${darkMode ? 'dark' : ''}`} style={{ backgroundColor: '#1e1b2e' }}>
          {/* Header */}
          <Header
            darkMode={darkMode}
            setDarkMode={setDarkMode}
            onLogoClick={handleLogoClick}
          />

          {/* League Coming Soon Banner */}
          <AnimatePresence>
            {selectedLeague !== 'EPL' && (
              <motion.div
                className="bg-gradient-to-r from-amber-500/20 via-orange-500/20 to-amber-500/20 border-y border-amber-500/30"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3 }}
              >
                <div className="container-custom py-3">
                  <div className="flex items-center justify-center gap-3">
                    <span className="text-2xl">🚧</span>
                    <div className="text-center">
                      <p className="text-white font-bold text-sm md:text-base">
                        {selectedLeague} 리그 준비중입니다
                      </p>
                      <p className="text-white/60 text-xs md:text-sm">
                        곧 서비스 예정이니 조금만 기다려주세요!
                      </p>
                    </div>
                    <span className="text-2xl">🚧</span>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Navigation Tabs - Professional Redesign */}
          <nav className="relative z-30 mt-4 shadow-2xl border-b border-cyan-500/20" style={{ backgroundColor: '#1e1b2e' }}>
            <div className="container-custom">
              <div className="flex justify-between items-center gap-4 relative">
                {/* Left: Tabs */}
                <div className="flex gap-1">
                  {tabs.map((tab) => {
                    const IconComponent = tab.icon;
                    return (
                      <motion.button
                        key={tab.id}
                        onClick={() => setCurrentPage(tab.id)}
                        className={`
                          relative px-3 md:px-5 py-2.5 md:py-3.5 transition-all duration-300
                          flex items-center gap-2 overflow-hidden group
                          ${currentPage === tab.id
                            ? 'text-white'
                            : 'text-white/50 hover:text-white/80'
                          }
                        `}
                        whileHover={{ y: currentPage === tab.id ? 0 : -1 }}
                        whileTap={{ scale: 0.97 }}
                      >
                        {/* Active tab background */}
                        {currentPage === tab.id && (
                          <>
                            {/* Main gradient background */}
                            <motion.div
                              layoutId="activeTabBg"
                              className="absolute inset-0 bg-gradient-to-b from-white/8 to-white/3"
                              initial={false}
                              transition={{
                                type: 'spring',
                                stiffness: 400,
                                damping: 30
                              }}
                            />
                            {/* Top accent line */}
                            <motion.div
                              layoutId="activeTabAccent"
                              className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-cyan-400 to-transparent"
                              initial={false}
                              transition={{
                                type: 'spring',
                                stiffness: 400,
                                damping: 30
                              }}
                            />
                            {/* Subtle glow */}
                            <motion.div
                              className="absolute inset-0 bg-gradient-to-b from-cyan-400/10 to-transparent"
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              transition={{ duration: 0.2 }}
                            />
                          </>
                        )}

                        {/* Hover effect for inactive tabs */}
                        {currentPage !== tab.id && (
                          <div className="absolute inset-0 bg-white/0 group-hover:bg-white/5 transition-colors duration-300" />
                        )}

                        {/* Icon */}
                        <IconComponent
                          className={`
                            relative z-10 w-4 h-4 md:w-5 md:h-5 transition-all duration-300
                            ${currentPage === tab.id
                              ? 'text-cyan-400'
                              : 'text-white/40 group-hover:text-white/60'
                            }
                          `}
                        />

                        {/* Label */}
                        <span className={`
                          relative z-10 text-xs md:text-sm font-extrabold tracking-wide transition-all duration-300
                          ${currentPage === tab.id ? 'text-white' : 'text-white/70 group-hover:text-white/90'}
                        `}>
                          {tab.label}
                        </span>

                        {/* Active indicator dot - 항상 공간 차지 */}
                        <motion.div
                          className="relative z-10 w-1.5 h-1.5 rounded-full bg-cyan-400"
                          initial={false}
                          animate={{
                            scale: currentPage === tab.id ? 1 : 0,
                            opacity: currentPage === tab.id ? 1 : 0
                          }}
                          transition={{
                            type: 'spring',
                            stiffness: 500,
                            damping: 25
                          }}
                        />
                      </motion.button>
                    );
                  })}
                </div>

                {/* Right: League Selector */}
                <div className="relative" ref={leagueDropdownRef}>
                  <motion.button
                    onClick={() => setLeagueDropdownOpen(!leagueDropdownOpen)}
                    className="flex items-center gap-2 px-4 py-2 rounded-sm bg-transparent hover:bg-white/5 transition-all duration-300"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <span className="text-2xl">{currentLeague.flag}</span>
                    <span className="text-sm font-bold text-white">{currentLeague.name}</span>
                    <motion.div
                      animate={{ rotate: leagueDropdownOpen ? 180 : 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <ChevronDown className="w-4 h-4 text-cyan-400" />
                    </motion.div>
                  </motion.button>

                  {/* Dropdown Menu */}
                  <AnimatePresence>
                    {leagueDropdownOpen && (
                      <motion.div
                        className="absolute right-0 top-full mt-2 w-56 rounded-sm overflow-hidden shadow-2xl z-50"
                        style={{ backgroundColor: '#1e1b2e' }}
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{ duration: 0.2 }}
                      >
                        {leagues.map((league) => (
                          <button
                            key={league.id}
                            onClick={() => {
                              setSelectedLeague(league.id);
                              setLeagueDropdownOpen(false);
                            }}
                            className={`
                              w-full px-4 py-3 transition-all
                              ${selectedLeague === league.id
                                ? 'bg-cyan-400/20 text-white'
                                : 'text-white/70 hover:bg-white/10 hover:text-white'
                              }
                            `}
                          >
                            <motion.div
                              className="flex items-center gap-3"
                              whileHover={{ x: 4 }}
                              transition={{ duration: 0.1 }}
                            >
                              <span className="text-2xl">{league.flag}</span>
                              <div className="flex-1 text-left">
                                <div className="text-sm font-bold">{league.name}</div>
                                <div className="text-xs text-white/50">{league.fullName}</div>
                              </div>
                              {selectedLeague === league.id && (
                                <motion.div
                                  className="w-2 h-2 rounded-full bg-cyan-400"
                                  initial={{ scale: 0 }}
                                  animate={{ scale: 1 }}
                                  transition={{ type: 'spring', stiffness: 500 }}
                                />
                              )}
                            </motion.div>
                          </button>
                        ))}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </div>
            </div>
          </nav>

          {/* Main Content */}
          <main className="relative">
            {/* 조건부 렌더링: 현재 페이지만 마운트하여 성능 최적화 */}
            {currentPage === 'dashboard' && (
              <EPLDashboard
                darkMode={darkMode}
                onTeamClick={handleTeamClick}
                onMatchSimulatorClick={handleMatchSimulatorClick}
                onMatchPredictionClick={handleMatchPredictionClick}
                onPlayerClick={handlePlayerClick}
              />
            )}
            {currentPage === 'ratings' && (
              <PlayerRatingManager
                darkMode={darkMode}
                initialTeam={selectedTeam}
                initialPlayer={selectedPlayer}
                onRatingsUpdate={handleRatingsUpdate}
              />
            )}
            {currentPage === 'match-simulator' && (
              <MatchSimulator
                darkMode={darkMode}
                selectedMatch={selectedMatch}
                onTeamClick={handleTeamClick}
                playerRatings={getMergedRatings()}
                isActive={true}
              />
            )}
            {currentPage === 'match-predictions' && (
              <MatchPredictionsDashboard darkMode={darkMode} selectedMatch={selectedPredictionMatch} />
            )}
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
                  Visionary AI for Soccer v2.0
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
                className="fixed bottom-8 right-8 z-50 p-3 rounded-full bg-slate-800 hover:bg-cyan-600 transition-colors"
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

          {/* V3 Auth Test Button */}
          <motion.button
            onClick={testV3Auth}
            disabled={v3AuthTesting}
            className={`
              fixed bottom-8 left-8 z-50 px-4 py-3 rounded-sm
              flex items-center gap-2 shadow-glow
              ${v3AuthTesting
                ? 'bg-gray-500 cursor-not-allowed'
                : 'bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-600 hover:to-indigo-700'
              }
              transition-all duration-300
            `}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            whileHover={v3AuthTesting ? {} : { scale: 1.05 }}
            whileTap={v3AuthTesting ? {} : { scale: 0.95 }}
            aria-label="V3 Auth 테스트"
          >
            {v3AuthTesting ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span className="text-sm font-bold text-white">테스트 중...</span>
              </>
            ) : (
              <>
                <span className="text-lg">🔐</span>
                <span className="text-sm font-bold text-white">V3 Auth 테스트</span>
              </>
            )}
          </motion.button>
        </div>
      </ToastProvider>
    </ErrorBoundary>
  );
}

export default App;
