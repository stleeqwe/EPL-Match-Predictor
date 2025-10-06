/**
 * Match Predictions Dashboard v3.0
 * 배당률 기반 경기 결과 예측 대시보드
 * UI/UX 통일: 그리드 레이아웃 (1:4 비율)
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import PropTypes from 'prop-types';
import { motion } from 'framer-motion';
import matchPredictionsAPI from '../services/matchPredictionsAPI';

const MatchPredictionsDashboard = ({ darkMode = false, selectedMatch = null }) => {
  const [predictions, setPredictions] = useState([]);
  const [methodology, setMethodology] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [showAlgorithm, setShowAlgorithm] = useState(false); // 알고리즘 펼침/닫힘 상태
  const [currentRound, setCurrentRound] = useState(null); // 현재 라운드 정보
  const refreshTimerRef = useRef(null);
  const matchRefsMap = useRef({}); // 각 경기 카드의 ref를 저장할 Map

  // 구독 관리
  const [isPremium, setIsPremium] = useState(false); // 실제 구독 상태 (추후 구현)
  const [isDeveloperMode, setIsDeveloperMode] = useState(() => {
    // localStorage에서 개발자 모드 상태 로드
    return localStorage.getItem('sharpVisionDevMode') === 'true';
  });

  // 개발자 모드 토글
  const toggleDeveloperMode = useCallback(() => {
    const newMode = !isDeveloperMode;
    setIsDeveloperMode(newMode);
    localStorage.setItem('sharpVisionDevMode', newMode.toString());
  }, [isDeveloperMode]);

  // 접근 권한 확인
  const hasAccess = isPremium || isDeveloperMode;

  // 경기 예측 데이터 가져오기
  const fetchPredictions = useCallback(async () => {
    // 접근 권한이 없으면 methodology만 가져오기
    if (!hasAccess) {
      setLoading(true);
      try {
        // Methodology만 가져오기 위해 빈 응답 처리
        const data = await matchPredictionsAPI.getMatchPredictions(false);
        setMethodology(data.methodology);
      } catch (err) {
        console.error('Methodology fetch error:', err);
      } finally {
        setLoading(false);
      }
      return;
    }

    // Premium/Developer 모드: 실제 데이터 가져오기
    setLoading(true);
    setError(null);

    try {
      // Real API 사용
      const data = await matchPredictionsAPI.getMatchPredictions(false);

      setPredictions(data.predictions || []);
      setMethodology(data.methodology);
      setCurrentRound(data.current_round); // 라운드 정보 저장
      setLastUpdated(new Date());

      if (!data.predictions || data.predictions.length === 0) {
        setError('다가오는 EPL 경기의 배당률이 아직 오픈되지 않았습니다.');
      }
    } catch (err) {
      console.error('Predictions fetch error:', err);
      setError('데이터를 불러오는 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  }, [hasAccess]);

  // 초기 데이터 로드 (Auto-refresh 제거 - API 호출 절약)
  useEffect(() => {
    fetchPredictions();
  }, [fetchPredictions]);

  // 팀 이름 정규화 함수 (다양한 형식을 통일)
  const normalizeTeamName = useCallback((teamName) => {
    const nameMap = {
      'Man City': 'Manchester City',
      'Man Utd': 'Manchester United',
      'Spurs': 'Tottenham Hotspur',
      'Tottenham': 'Tottenham Hotspur',
      'Wolves': 'Wolverhampton Wanderers',
      'Nott\'m Forest': 'Nottingham Forest',
      'AFC Bournemouth': 'Bournemouth',
      'Brighton': 'Brighton and Hove Albion',
      'Leicester': 'Leicester City',
      'Ipswich': 'Ipswich Town',
      'West Ham': 'West Ham United',
      'Newcastle': 'Newcastle United',
      'Sheffield Utd': 'Sheffield United',
      'West Brom': 'West Bromwich Albion',
      'Norwich': 'Norwich City',
      'Hull': 'Hull City',
      'Stoke': 'Stoke City',
      'Swansea': 'Swansea City',
      'Cardiff': 'Cardiff City',
      'Luton': 'Luton Town',
      'Leeds': 'Leeds United',
      'Burnley FC': 'Burnley',
      'Sunderland AFC': 'Sunderland'
    };

    return nameMap[teamName] || teamName;
  }, []);

  // 선택된 경기로 스크롤
  useEffect(() => {
    if (selectedMatch && predictions.length > 0) {
      console.log('🎯 Auto-scroll triggered:', selectedMatch);
      console.log('📋 Available matches:', Object.keys(matchRefsMap.current));

      // 탭 전환 애니메이션 후 스크롤하기 위해 딜레이 추가
      setTimeout(() => {
        // 팀 이름 정규화
        const normalizedHome = normalizeTeamName(selectedMatch.homeTeam);
        const normalizedAway = normalizeTeamName(selectedMatch.awayTeam);
        const matchKey = `${normalizedHome}_${normalizedAway}`;

        console.log('🔍 Original:', `${selectedMatch.homeTeam}_${selectedMatch.awayTeam}`);
        console.log('🔍 Normalized match key:', matchKey);

        const matchElement = matchRefsMap.current[matchKey];
        console.log('📍 Found element:', matchElement);

        if (matchElement) {
          console.log('✅ Scrolling to match...');
          matchElement.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
          });
        } else {
          console.warn('❌ Match element not found for key:', matchKey);
        }
      }, 400); // 탭 전환 애니메이션 시간 고려
    }
  }, [selectedMatch, predictions, normalizeTeamName]);

  // 신뢰도에 따른 색상 (Dark Mode)
  const getConfidenceColor = (confidence) => {
    if (confidence >= 70) return 'text-success bg-success/20 border border-success/30';
    if (confidence >= 50) return 'text-warning bg-warning/20 border border-warning/30';
    return 'text-error bg-error/20 border border-error/30';
  };

  // 결과 아이콘
  const getOutcomeIcon = (outcome) => {
    const icons = {
      home: '🏠',
      draw: '🤝',
      away: '✈️'
    };
    return icons[outcome] || '⚽';
  };

  // 결과 텍스트
  const getOutcomeText = (outcome) => {
    const text = {
      home: '홈 승리',
      draw: '무승부',
      away: '원정 승리'
    };
    return text[outcome] || outcome;
  };

  // 팀 엠블럼 URL 가져오기 (FPL API 기반)
  const getTeamBadgeUrl = (teamName) => {
    // 팀 이름 정규화 및 FPL API 팀 ID 매핑 (현재 및 과거 시즌 포함)
    const teamMapping = {
      // 현재 시즌 팀들
      'Arsenal': 3,
      'Aston Villa': 7,
      'Bournemouth': 91,
      'AFC Bournemouth': 91,
      'Brentford': 94,
      'Brighton': 36,
      'Brighton and Hove Albion': 36,
      'Chelsea': 8,
      'Crystal Palace': 31,
      'Everton': 11,
      'Fulham': 54,
      'Ipswich': 40,
      'Ipswich Town': 40,
      'Leicester': 13,
      'Leicester City': 13,
      'Liverpool': 14,
      'Manchester City': 43,
      'Man City': 43,
      'Manchester United': 1,
      'Man Utd': 1,
      'Newcastle': 4,
      'Newcastle United': 4,
      'Nottingham Forest': 17,
      'Nott\'m Forest': 17,
      'Southampton': 20,
      'Tottenham': 6,
      'Tottenham Hotspur': 6,
      'Spurs': 6,
      'West Ham': 21,
      'West Ham United': 21,
      'Wolverhampton Wanderers': 39,
      'Wolves': 39,
      // 과거/승격 팀들
      'Burnley': 90,
      'Leeds': 2,
      'Leeds United': 2,
      'Sunderland': 56,
      'Sunderland AFC': 56,
      'Watford': 57,
      'Norwich': 45,
      'Norwich City': 45,
      'Sheffield United': 49,
      'Sheffield Utd': 49,
      'West Brom': 35,
      'West Bromwich Albion': 35,
      'Luton': 163,
      'Luton Town': 163,
      'Middlesbrough': 25,
      'Stoke': 110,
      'Stoke City': 110,
      'Swansea': 80,
      'Swansea City': 80,
      'Hull': 88,
      'Hull City': 88,
      'Cardiff': 97,
      'Cardiff City': 97,
      'Huddersfield': 38,
      'Huddersfield Town': 38
    };

    const teamId = teamMapping[teamName];
    if (teamId) {
      return `https://resources.premierleague.com/premierleague/badges/70/t${teamId}.png`;
    }
    return null;
  };

  if (loading && predictions.length === 0 && !methodology) {
    return (
      <div className="section">
        <div className="container-custom">
          <div className="card p-12 text-center">
            <div className="spinner mx-auto mb-4"></div>
            <p className="text-white/60">경기 예측 데이터 로딩 중...</p>
          </div>
        </div>
      </div>
    );
  }

  // 무료 사용자 프리뷰 화면 (구독 안내)
  if (!hasAccess) {
    return (
      <div className="section min-h-screen">
        <div className="container-custom">
          <div className="max-w-4xl mx-auto">
            <motion.div
              className="card p-8"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              {/* 헤더 */}
              <div className="text-center mb-8">
                <div className="inline-block mb-4">
                  <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-brand-accent to-purple-400 mb-2">
                    ✨ Sharp Vision AI
                  </h1>
                  <div className="h-1 bg-gradient-to-r from-brand-accent to-purple-400 rounded-full"></div>
                </div>
                <p className="text-white/80 text-lg mb-2">
                  프리미엄 AI 경기 예측 시스템
                </p>
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-brand-accent/20 border border-brand-accent/40 rounded-lg">
                  <span className="text-brand-accent font-bold">🎯 60% 예측 정확도</span>
                  <span className="text-white/60">|</span>
                  <span className="text-purple-300 font-bold">Sharp 북메이커 분석</span>
                </div>
              </div>

              {/* 시스템 소개 */}
              {methodology && (
                <div className="space-y-6 mb-8">
                  {/* 설명 */}
                  <div className="glass-strong rounded-xl p-6 border border-brand-accent/30">
                    <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                      <span>🚀</span> 시스템 소개
                    </h3>
                    <p className="text-white/90 leading-relaxed mb-4">
                      {methodology.description}
                    </p>
                    <div className="flex flex-wrap gap-2">
                      <span className="px-3 py-1 bg-brand-accent/20 border border-brand-accent/40 rounded-lg text-sm font-semibold text-brand-accent">
                        Pinnacle
                      </span>
                      <span className="px-3 py-1 bg-purple-500/20 border border-purple-400/40 rounded-lg text-sm font-semibold text-purple-300">
                        Betfair Exchange
                      </span>
                      <span className="px-3 py-1 bg-success/20 border border-success/40 rounded-lg text-sm font-semibold text-success">
                        Smarkets
                      </span>
                    </div>
                  </div>

                  {/* 분석 알고리즘 */}
                  <div className="glass-strong rounded-xl p-6 border border-white/10">
                    <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                      <span>🔄</span> 분석 알고리즘
                    </h3>
                    <div className="space-y-3">
                      {methodology.steps.map((step) => (
                        <div
                          key={step.step}
                          className="glass rounded-lg p-4 border border-white/10"
                        >
                          <div className="flex items-start gap-3">
                            <div className="w-8 h-8 rounded-full bg-brand-accent text-black flex items-center justify-center font-bold text-sm flex-shrink-0">
                              {step.step}
                            </div>
                            <div className="flex-1">
                              <h6 className="font-bold text-white mb-1">
                                {step.name}
                              </h6>
                              <p className="text-sm text-brand-accent font-mono bg-black/20 rounded px-3 py-1 mb-2">
                                {step.formula}
                              </p>
                              <p className="text-sm text-white/80 leading-relaxed">
                                {step.description}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* 데이터 출처 */}
                  <div className="glass-strong rounded-xl p-6 border border-white/10">
                    <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                      <span>📡</span> 데이터 출처
                    </h3>
                    <ul className="space-y-2">
                      {methodology.data_sources.map((source, idx) => (
                        <li key={idx} className="flex items-start gap-3 text-white/80">
                          <span className="text-brand-accent mt-1">•</span>
                          <span>{source}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {/* 구독 안내 */}
              <div className="glass-strong rounded-xl p-8 border-2 border-brand-accent/50 bg-gradient-to-br from-brand-accent/10 to-purple-500/10 text-center">
                <div className="text-5xl mb-4">🔒</div>
                <h3 className="text-2xl font-bold text-white mb-3">
                  프리미엄 구독으로 Sharp Vision AI를 경험하세요
                </h3>
                <p className="text-white/80 mb-6 leading-relaxed">
                  세계 최고 Sharp 북메이커의 배당률을 실시간으로 분석하여<br />
                  가장 정확한 경기 예측을 제공합니다.
                </p>
                <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                  <motion.button
                    className="btn btn-primary text-lg px-8 py-3"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => alert('구독 기능은 곧 출시됩니다!')}
                  >
                    ⭐ 프리미엄 구독하기
                  </motion.button>
                  <motion.button
                    className="btn bg-white/10 hover:bg-white/20 text-white text-sm px-6 py-2"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={toggleDeveloperMode}
                  >
                    🔧 개발자 모드 {isDeveloperMode ? 'OFF' : 'ON'}
                  </motion.button>
                </div>
              </div>

              {/* 기능 미리보기 */}
              <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="glass rounded-lg p-4 text-center border border-white/10">
                  <div className="text-3xl mb-2">🎯</div>
                  <h4 className="font-bold text-white mb-1">승/무/패 확률</h4>
                  <p className="text-sm text-white/60">Sharp 북메이커 합의 확률</p>
                </div>
                <div className="glass rounded-lg p-4 text-center border border-white/10">
                  <div className="text-3xl mb-2">⚽</div>
                  <h4 className="font-bold text-white mb-1">예상 스코어</h4>
                  <p className="text-sm text-white/60">Poisson 분포 기반 예측</p>
                </div>
                <div className="glass rounded-lg p-4 text-center border border-white/10">
                  <div className="text-3xl mb-2">📊</div>
                  <h4 className="font-bold text-white mb-1">상세 분석</h4>
                  <p className="text-sm text-white/60">득점 확률 및 통계</p>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    );
  }

  // Premium/Developer 모드: 실제 경기 예측 화면
  return (
    <div className="section min-h-screen">
      <div className="container-custom">
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
          {/* Left Sidebar - 시스템 가이드 */}
          <div className="lg:col-span-1 space-y-4">
            <motion.div
              className="card p-4"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
            >
              <div>
                {methodology && (
                  <>
                    {/* 메인 타이틀 & 설명 - 강조 */}
                    <div className="mb-6">
                      {/* 타이틀 */}
                      <div className="mb-4">
                        <div className="inline-block">
                          <h3 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-brand-accent to-purple-400 mb-1 leading-tight">
                            {methodology.title}
                          </h3>
                          <div className="h-1 bg-gradient-to-r from-brand-accent to-purple-400 rounded-full"></div>
                        </div>
                      </div>

                      {/* 강조된 설명 박스 */}
                      <div className="glass-strong rounded-xl p-4 border border-brand-accent/30 bg-gradient-to-br from-brand-accent/10 to-purple-500/10">
                        {/* 핵심 포인트 배지들 */}
                        <div className="flex flex-wrap gap-2 mb-3">
                          <span className="inline-flex items-center gap-1 px-2 py-1 bg-brand-accent/20 border border-brand-accent/40 rounded-lg text-xs font-semibold text-brand-accent">
                            <span>🌍</span> 20+ 북메이커
                          </span>
                          <span className="inline-flex items-center gap-1 px-2 py-1 bg-success/20 border border-success/40 rounded-lg text-xs font-semibold text-success">
                            <span>⚡</span> 실시간 분석
                          </span>
                          <span className="inline-flex items-center gap-1 px-2 py-1 bg-purple-500/20 border border-purple-400/40 rounded-lg text-xs font-semibold text-purple-300">
                            <span>🤖</span> AI 역추산
                          </span>
                        </div>

                        {/* 설명 텍스트 */}
                        <p className="text-sm text-white/90 leading-relaxed">
                          {methodology.description}
                        </p>

                        {/* 강조 아이콘 */}
                        <div className="mt-3 pt-3 border-t border-white/10 flex items-center gap-2">
                          <div className="flex-shrink-0 w-6 h-6 rounded-full bg-brand-accent/30 flex items-center justify-center">
                            <span className="text-brand-accent text-xs">✓</span>
                          </div>
                          <p className="text-xs text-brand-accent font-semibold">
                            과학적 통계 기반 최상의 예측 시스템
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* 분석 알고리즘 - 토글 */}
                    <div className="mb-4">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-xs font-semibold text-brand-accent">🔄 분석 알고리즘</p>
                        <button
                          onClick={() => setShowAlgorithm(!showAlgorithm)}
                          className="text-xs px-3 py-1 rounded-lg bg-brand-accent/20 text-brand-accent hover:bg-brand-accent/30 transition-colors"
                        >
                          {showAlgorithm ? '닫기' : '자세히'}
                        </button>
                      </div>

                      {showAlgorithm && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          className="space-y-2 mt-3"
                        >
                          {methodology.steps.map((step) => (
                            <div
                              key={step.step}
                              className="glass-strong rounded-lg p-2 border border-white/10"
                            >
                              <div className="flex items-start gap-2">
                                <div className="w-5 h-5 rounded-full bg-brand-accent text-black flex items-center justify-center font-bold text-xs flex-shrink-0 mt-0.5">
                                  {step.step}
                                </div>
                                <div className="flex-1">
                                  <h6 className="font-bold text-white text-xs mb-1">
                                    {step.name}
                                  </h6>
                                  <p className="text-xs text-brand-accent font-mono font-semibold bg-black/20 rounded px-2 py-1 mb-1 break-all">
                                    {step.formula}
                                  </p>
                                  <p className="text-xs text-white leading-relaxed">
                                    {step.description}
                                  </p>
                                </div>
                              </div>
                            </div>
                          ))}
                        </motion.div>
                      )}
                    </div>

                    {/* 데이터 출처 */}
                    <div className="mb-4">
                      <p className="text-xs font-semibold text-brand-accent mb-2">📡 데이터 출처</p>
                      <div className="glass-strong rounded-lg p-3 border border-white/10">
                        <ul className="text-xs text-white space-y-1">
                          {methodology.data_sources.map((source, idx) => (
                            <li key={idx} className="flex items-start gap-2">
                              <span className="text-brand-accent mt-0.5">•</span>
                              <span className="flex-1">{source}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    {/* 신뢰도 주의사항 */}
                    <div>
                      <p className="text-xs font-semibold text-brand-accent mb-2">⚠️ 신뢰도 주의사항</p>
                      <div className="glass-strong rounded-lg p-3 border border-white/10">
                        <div className="space-y-3">
                          {/* 역사적 정확도 */}
                          <div>
                            <p className="text-xs font-bold text-white mb-1">📊 역사적 정확도</p>
                            <p className="text-xs text-white/80 leading-relaxed">
                              북메이커 배당률 기반 예측의 역사적 적중률은 <span className="text-brand-accent font-bold">약 57%</span> 수준입니다.
                            </p>
                          </div>

                          {/* 본 시스템 */}
                          <div className="pt-2 border-t border-white/10">
                            <p className="text-xs font-bold text-white mb-1">🎯 본 시스템 적중률</p>
                            <p className="text-xs text-white/80 leading-relaxed">
                              본 시스템은 가장 정확한 Sharp 북메이커(Pinnacle, Betfair Exchange 등)의 배당률을 종합하여 <span className="text-brand-accent font-bold">약 60%</span>의 예측 정확도를 목표로 합니다.
                            </p>
                          </div>

                          {/* 주의사항 */}
                          <div className="pt-2 border-t border-white/10">
                            <p className="text-xs font-bold text-warning mb-1">⚠️ 유의사항</p>
                            <ul className="text-xs text-white/70 space-y-1">
                              <li className="flex gap-1">
                                <span>•</span>
                                <span>축구는 변수가 많아 100% 정확한 예측은 불가능</span>
                              </li>
                              <li className="flex gap-1">
                                <span>•</span>
                                <span>참고용으로만 활용하시기 바랍니다</span>
                              </li>
                            </ul>
                          </div>
                        </div>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </motion.div>
          </div>

          {/* Main Content - 경기 예측 */}
          <div className="lg:col-span-4">
            <motion.div
              className="card p-6"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              {/* 헤더 */}
              <div className="mb-6">
                <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
                  <div className="flex items-center gap-4">
                    {/* EPL 로고 */}
                    <div className="bg-white rounded-lg p-2 flex items-center justify-center">
                      <img
                        src="/premier-league-logo-white.png"
                        alt="Premier League"
                        className="w-10 h-10 lg:w-14 lg:h-14 object-contain"
                      />
                    </div>
                    <div>
                      <h1 className="text-2xl lg:text-3xl font-bold text-white mb-1">
                        {currentRound
                          ? `Gameweek ${currentRound} 경기 예측`
                          : 'EPL 경기 예측'
                        }
                      </h1>
                      <p className="text-white/60 text-xs lg:text-sm">
                        배당률 기반 AI 예측 시스템
                      </p>
                    </div>
                  </div>
                  <div className="flex flex-col items-start lg:items-end gap-2 w-full lg:w-auto">
                    {isDeveloperMode && (
                      <div className="px-3 py-1 bg-warning/20 border border-warning/40 rounded-lg text-xs font-semibold text-warning mb-2">
                        🔧 개발자 모드 활성화
                      </div>
                    )}
                    <div className="flex gap-2 w-full lg:w-auto">
                      <button
                        onClick={fetchPredictions}
                        disabled={loading}
                        className="btn btn-primary flex-1 lg:flex-none"
                      >
                        {loading ? '새로고침 중...' : '🔄 수동 새로고침'}
                      </button>
                      {isDeveloperMode && (
                        <button
                          onClick={toggleDeveloperMode}
                          className="btn bg-white/10 hover:bg-white/20 text-white text-xs px-4"
                        >
                          🔧 OFF
                        </button>
                      )}
                    </div>
                    {lastUpdated && (
                      <p className="text-xs text-white/40">
                        마지막 업데이트: {lastUpdated.toLocaleTimeString('ko-KR')}
                      </p>
                    )}
                  </div>
                </div>
              </div>

              {/* 에러 메시지 */}
              {error && (
                <div className="glass-strong border border-error/30 rounded-lg p-4 mb-6 bg-error/10">
                  <p className="text-error text-sm">{error}</p>
                </div>
              )}

              {/* 경기 예측 카드 */}
              <div className="space-y-4">
                {predictions.map((match, idx) => {
                  const pred = match.prediction;
                  const expectedScore = `${pred.expected_goals.home} - ${pred.expected_goals.away}`;
                  const matchKey = `${match.home_team}_${match.away_team}`;

                  return (
                    <motion.div
                      key={match.match_id || idx}
                      ref={(el) => {
                        if (el) matchRefsMap.current[matchKey] = el;
                      }}
                      className="glass-strong rounded-xl overflow-hidden border border-white/10 hover:border-brand-accent/50 transition-all"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: idx * 0.1 }}
                    >
                      {/* 경기 헤더 */}
                      <div className="bg-gradient-to-r from-brand-accent/20 to-purple-500/20 p-3 border-b border-white/10">
                        {/* 팀 정보 */}
                        <div className="flex justify-between items-center gap-3">
                          {/* 홈 팀 */}
                          <div className="flex-1 flex flex-col items-center">
                            {/* 엠블럼 */}
                            <div className="w-12 h-12 lg:w-14 lg:h-14 mb-1.5 flex items-center justify-center relative">
                              {getTeamBadgeUrl(match.home_team) ? (
                                <>
                                  <img
                                    src={getTeamBadgeUrl(match.home_team)}
                                    alt={match.home_team}
                                    className="w-full h-full object-contain"
                                    onError={(e) => {
                                      e.target.style.display = 'none';
                                      e.target.parentElement.querySelector('.fallback-icon').style.display = 'block';
                                    }}
                                  />
                                  <span className="fallback-icon text-2xl lg:text-3xl absolute" style={{ display: 'none' }}>⚽</span>
                                </>
                              ) : (
                                <span className="text-2xl lg:text-3xl">⚽</span>
                              )}
                            </div>
                            {/* 팀명 */}
                            <h3 className="text-sm lg:text-base font-bold text-white text-center">{match.home_team}</h3>
                            <p className="text-xs text-white/60">홈</p>
                          </div>

                          {/* VS + 경기 일시 */}
                          <div className="px-2 flex flex-col items-center">
                            <div className="text-lg lg:text-xl font-bold text-brand-accent mb-1">VS</div>
                            {match.commence_time && (
                              <p className="text-xs text-white/50 text-center whitespace-nowrap">
                                {new Date(match.commence_time).toLocaleString('ko-KR')}
                              </p>
                            )}
                          </div>

                          {/* 원정 팀 */}
                          <div className="flex-1 flex flex-col items-center">
                            {/* 엠블럼 */}
                            <div className="w-12 h-12 lg:w-14 lg:h-14 mb-1.5 flex items-center justify-center relative">
                              {getTeamBadgeUrl(match.away_team) ? (
                                <>
                                  <img
                                    src={getTeamBadgeUrl(match.away_team)}
                                    alt={match.away_team}
                                    className="w-full h-full object-contain"
                                    onError={(e) => {
                                      e.target.style.display = 'none';
                                      e.target.parentElement.querySelector('.fallback-icon').style.display = 'block';
                                    }}
                                  />
                                  <span className="fallback-icon text-2xl lg:text-3xl absolute" style={{ display: 'none' }}>⚽</span>
                                </>
                              ) : (
                                <span className="text-2xl lg:text-3xl">⚽</span>
                              )}
                            </div>
                            {/* 팀명 */}
                            <h3 className="text-sm lg:text-base font-bold text-white text-center">{match.away_team}</h3>
                            <p className="text-xs text-white/60">원정</p>
                          </div>
                        </div>
                      </div>

                      {/* 예측 결과 */}
                      <div className="p-4 lg:p-6">
                        {/* 승/무/패 확률 */}
                        <div className="mb-6">
                          <h4 className="font-semibold text-white mb-3 text-sm lg:text-base">승/무/패 확률 (Consensus)</h4>
                          <div className="grid grid-cols-3 gap-2 lg:gap-4">
                            <div className="glass rounded-lg p-3 lg:p-4 text-center border border-blue-500/30">
                              <p className="text-xs lg:text-sm text-white/60 mb-1">홈 승리</p>
                              <p className="text-xl lg:text-2xl font-bold text-blue-400">{pred.probabilities.home}%</p>
                            </div>
                            <div className="glass rounded-lg p-3 lg:p-4 text-center border border-yellow-500/30">
                              <p className="text-xs lg:text-sm text-white/60 mb-1">무승부</p>
                              <p className="text-xl lg:text-2xl font-bold text-yellow-400">{pred.probabilities.draw}%</p>
                            </div>
                            <div className="glass rounded-lg p-3 lg:p-4 text-center border border-red-500/30">
                              <p className="text-xs lg:text-sm text-white/60 mb-1">원정 승리</p>
                              <p className="text-xl lg:text-2xl font-bold text-red-400">{pred.probabilities.away}%</p>
                            </div>
                          </div>
                        </div>

                        {/* 예상 스코어 */}
                        <div className="mb-6">
                          <h4 className="font-semibold text-white mb-3 text-sm lg:text-base">예상 스코어</h4>
                          <div className="glass rounded-lg p-4 border border-white/10">
                            <div className="text-center mb-4">
                              <p className="text-3xl lg:text-4xl font-bold text-brand-accent">{expectedScore}</p>
                              <p className="text-xs lg:text-sm text-white/60 mt-1">
                                (평균 예상 득점)
                              </p>
                            </div>

                            {/* 가장 가능성 높은 스코어들 */}
                            <div>
                              <p className="text-xs lg:text-sm text-white/60 mb-2 text-center">가능성 높은 스코어 (Poisson 분포)</p>
                              <div className="grid grid-cols-5 gap-2">
                                {pred.most_likely_scores.map((score, idx) => (
                                  <div key={idx} className="glass-strong rounded-lg p-2 text-center border border-white/10">
                                    <p className="text-xs lg:text-sm font-bold text-white">{score.score}</p>
                                    <p className="text-xs text-white/50">{score.probability}%</p>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Poisson 확률 */}
                        <div className="mb-4">
                          <h4 className="font-semibold text-white mb-3 text-sm lg:text-base">Poisson Distribution 예측</h4>
                          <div className="grid grid-cols-3 gap-2 lg:gap-4">
                            <div className="glass rounded-lg p-3 text-center border border-green-500/30">
                              <p className="text-xs text-white/60 mb-1">홈 승리</p>
                              <p className="text-lg lg:text-xl font-bold text-green-400">{pred.poisson_probabilities.home_win}%</p>
                            </div>
                            <div className="glass rounded-lg p-3 text-center border border-white/10">
                              <p className="text-xs text-white/60 mb-1">무승부</p>
                              <p className="text-lg lg:text-xl font-bold text-white/80">{pred.poisson_probabilities.draw}%</p>
                            </div>
                            <div className="glass rounded-lg p-3 text-center border border-orange-500/30">
                              <p className="text-xs text-white/60 mb-1">원정 승리</p>
                              <p className="text-lg lg:text-xl font-bold text-orange-400">{pred.poisson_probabilities.away_win}%</p>
                            </div>
                          </div>
                        </div>

                        {/* 데이터 출처 */}
                        <div className="text-center text-xs text-white/40 pt-4 border-t border-white/10">
                          <p>데이터: {match.methodology?.data_source} ({match.methodology?.num_bookmakers} bookmakers)</p>
                          <p>분석 방법: {match.methodology?.approach}</p>
                          {match.methodology?.uses_totals_odds && (
                            <p className="text-success font-semibold mt-1">
                              ✓ 언더/오버 배당률 기반 득점 예측 (향상된 정확도)
                            </p>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </div>

              {/* 경기가 없을 때 */}
              {predictions.length === 0 && !loading && (
                <div className="glass-strong rounded-xl p-8 lg:p-12 text-center border border-white/10">
                  <div className="text-5xl lg:text-6xl mb-4">🏴</div>
                  <h3 className="text-xl lg:text-2xl font-bold text-white mb-2">
                    예측 가능한 경기가 없습니다
                  </h3>
                  <p className="text-sm lg:text-base text-white/60">
                    다가오는 EPL 경기의 배당률이 아직 오픈되지 않았습니다.
                  </p>
                </div>
              )}
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
};

MatchPredictionsDashboard.propTypes = {
  darkMode: PropTypes.bool,
  selectedMatch: PropTypes.shape({
    homeTeam: PropTypes.string,
    awayTeam: PropTypes.string
  })
};

export default MatchPredictionsDashboard;
