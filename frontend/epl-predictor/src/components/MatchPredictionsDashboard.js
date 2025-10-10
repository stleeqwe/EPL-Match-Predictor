/**
 * Match Predictions Dashboard v3.0
 * 배당률 기반 경기 결과 예측 대시보드
 * UI/UX 통일: 그리드 레이아웃 (1:4 비율)
 * v3.1: 승/무/패 확률 툴팁 시스템 추가
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import ReactDOM from 'react-dom';
import PropTypes from 'prop-types';
import { motion, AnimatePresence } from 'framer-motion';
import matchPredictionsAPI from '../services/matchPredictionsAPI';

const MatchPredictionsDashboard = ({ darkMode = false, selectedMatch = null }) => {
  const [predictions, setPredictions] = useState([]);
  const [methodology, setMethodology] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [showAlgorithm, setShowAlgorithm] = useState(false); // 알고리즘 펼침/닫힘 상태
  const [showDataSources, setShowDataSources] = useState(false); // 데이터 출처 펼침/닫힘
  const [showWarnings, setShowWarnings] = useState(false); // 주의사항 펼침/닫힘
  const [showFullDescription, setShowFullDescription] = useState(false); // 설명 전체 보기
  const [currentRound, setCurrentRound] = useState(null); // 현재 라운드 정보
  const [selectedMatchId, setSelectedMatchId] = useState(null); // 선택된 경기 ID
  const refreshTimerRef = useRef(null);
  const matchRefsMap = useRef({}); // 각 경기 카드의 ref를 저장할 Map

  // 팝업 상태 관리
  const [activePopup, setActivePopup] = useState(null); // { type, outcome, matchId, match }

  // 구독 관리
  const [isPremium, setIsPremium] = useState(false); // 실제 구독 상태 (추후 구현)
  const [isDeveloperMode, setIsDeveloperMode] = useState(() => {
    // localStorage에서 개발자 모드 상태 로드
    return localStorage.getItem('sharpVisionDevMode') === 'true';
  });
  const [hasUsedFreeTrial, setHasUsedFreeTrial] = useState(() => {
    // localStorage에서 무료 체험 사용 여부 로드
    return localStorage.getItem('sharpVisionFreeTrial') === 'used';
  });
  const [isUsingFreeTrial, setIsUsingFreeTrial] = useState(false);
  const [dataSource, setDataSource] = useState('demo'); // 'demo' or 'live'

  // 개발자 모드 토글
  const toggleDeveloperMode = useCallback(() => {
    const newMode = !isDeveloperMode;
    setIsDeveloperMode(newMode);
    localStorage.setItem('sharpVisionDevMode', newMode.toString());
  }, [isDeveloperMode]);

  // 무료 체험 시작
  const startFreeTrial = useCallback(() => {
    setIsUsingFreeTrial(true);
    setHasUsedFreeTrial(true);
    localStorage.setItem('sharpVisionFreeTrial', 'used');
  }, []);

  // 접근 권한 확인
  const hasAccess = isPremium || isDeveloperMode || isUsingFreeTrial;

  // 경기 예측 데이터 가져오기
  const fetchPredictions = useCallback(async (useDemo = true) => {
    // 접근 권한이 없으면 methodology만 가져오기
    if (!hasAccess) {
      setLoading(true);
      try {
        // Methodology만 가져오기 위해 데모 데이터 사용
        const data = await matchPredictionsAPI.getMatchPredictions(true);
        setMethodology(data.methodology);
      } catch (err) {
        console.error('Methodology fetch error:', err);
      } finally {
        setLoading(false);
      }
      return;
    }

    // Premium/Developer 모드: useDemo 파라미터에 따라 호출
    setLoading(true);
    setError(null);

    try {
      const data = await matchPredictionsAPI.getMatchPredictions(useDemo);

      setPredictions(data.predictions || []);
      setMethodology(data.methodology);
      setCurrentRound(data.current_round);
      setLastUpdated(new Date());
      setDataSource(useDemo ? 'demo' : 'live');

      if (!data.predictions || data.predictions.length === 0) {
        if (useDemo) {
          setError('데모 데이터를 불러올 수 없습니다.');
        } else {
          setError('다가오는 EPL 경기의 배당률이 아직 오픈되지 않았거나 API 할당량이 소진되었습니다.');
        }
      }
    } catch (err) {
      console.error('Predictions fetch error:', err);
      if (!useDemo) {
        setError('실제 API 호출 실패. API 키 확인 또는 할당량 확인이 필요합니다.');
      } else {
        setError('데이터를 불러오는 중 오류가 발생했습니다.');
      }
    } finally {
      setLoading(false);
    }
  }, [hasAccess]);

  // 실제 API 호출 (개발자 모드 전용)
  const fetchLiveData = useCallback(() => {
    if (isDeveloperMode) {
      fetchPredictions(false); // use_demo=false
    }
  }, [isDeveloperMode, fetchPredictions]);

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

  // 팝업 핸들러
  const handlePopupClick = useCallback((type, outcome, matchId, match) => {
    setActivePopup({ type, outcome, matchId, match });
  }, []);

  const handleClosePopup = useCallback(() => {
    setActivePopup(null);
  }, []);

  // ESC 키로 팝업 닫기
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && activePopup) {
        handleClosePopup();
      }
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [activePopup, handleClosePopup]);

  // selectedMatchId 상태 변경 감지
  useEffect(() => {
    // selectedMatchId tracking
  }, [selectedMatchId]);

  // 선택된 경기로 스크롤
  useEffect(() => {
    if (selectedMatch && predictions.length > 0) {
      // 탭 전환 애니메이션 후 스크롤하기 위해 딜레이 추가
      setTimeout(() => {
        // 팀 이름 정규화
        const normalizedHome = normalizeTeamName(selectedMatch.homeTeam);
        const normalizedAway = normalizeTeamName(selectedMatch.awayTeam);
        const matchKey = `${normalizedHome}_${normalizedAway}`;

        const matchElement = matchRefsMap.current[matchKey];

        if (matchElement) {
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

  /**
   * ProbabilityPopup Component
   * 승/무/패 확률에 대한 상세 설명 팝업 - REAL CALCULATION DATA
   */
  const ProbabilityPopup = ({ type, probability, match, methodology, visible, onClose }) => {
    if (!visible || !methodology) return null;

    // 툴팁 제목 및 아이콘
    const tooltipConfig = {
      home: {
        title: '홈 승리 예측',
        icon: '🏠',
        color: 'blue',
        field: 'home'
      },
      draw: {
        title: '무승부 예측',
        icon: '🤝',
        color: 'yellow',
        field: 'draw'
      },
      away: {
        title: '원정 승리 예측',
        icon: '✈️',
        color: 'red',
        field: 'away'
      }
    };

    const config = tooltipConfig[type];

    // Extract real calculation data from backend
    const calcDetails = match?.prediction?.calculation_details?.consensus;
    const bookmakers = calcDetails?.bookmakers || [];
    const rawAverage = calcDetails?.raw_average;
    const marginRemoved = calcDetails?.margin_removed;
    const numBookmakers = calcDetails?.num_bookmakers || bookmakers.length;

    // 색상 클래스 동적 생성
    const colorClasses = {
      blue: {
        border: 'border-blue-500/50',
        borderLight: 'border-blue-500/40',
        borderDivider: 'divide-blue-500/20',
        text: 'text-blue-400',
        textBright: 'text-blue-400'
      },
      yellow: {
        border: 'border-amber-500/50',
        borderLight: 'border-amber-500/40',
        borderDivider: 'divide-amber-500/20',
        text: 'text-amber-400',
        textBright: 'text-amber-400'
      },
      red: {
        border: 'border-red-500/50',
        borderLight: 'border-red-500/40',
        borderDivider: 'divide-red-500/20',
        text: 'text-red-400',
        textBright: 'text-red-400'
      }
    };

    const colors = colorClasses[config.color];

    return ReactDOM.createPortal(
      <AnimatePresence>
        {/* 오버레이 */}
        <motion.div
          className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[9998] flex items-center justify-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          {/* 팝업 */}
          <motion.div
            className="relative w-full max-w-lg max-h-[90vh] overflow-y-auto"
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            onClick={(e) => e.stopPropagation()}
          >
          <div className={`bg-slate-900 backdrop-blur-md border-2 ${colors.border} rounded-lg p-4 shadow-2xl`}>
            {/* 헤더 with 닫기 버튼 */}
            <div className={`flex items-center justify-between mb-3 pb-2 border-b ${colors.borderLight}`}>
              <div className="flex items-center gap-2">
                <span className="text-2xl">{config.icon}</span>
                <div>
                  <h4 className="font-bold text-white text-xl leading-tight">{config.title}</h4>
                  <p className={`text-2xl ${colors.text} font-mono font-bold`}>{probability}%</p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="text-white/60 hover:text-white transition-colors p-1 hover:bg-white/10 rounded flex-shrink-0"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Sharp Vision AI 분석 과정 - 간결한 버전 */}
            <div className={`space-y-0 divide-y ${colors.borderDivider}`}>
              {/* Step 1: Sharp 북메이커별 배당률 및 확률 */}
              <div className="py-2">
                <div className="flex items-baseline gap-1.5 mb-1.5">
                  <span className={`${colors.text} font-bold text-sm`}>1.</span>
                  <h5 className="font-bold text-white text-base">Sharp 북메이커 데이터</h5>
                </div>
                {bookmakers.length > 0 ? (
                  <div className="space-y-0.5 ml-4">
                    {bookmakers.map((bookie, idx) => {
                      const odds = bookie[`${config.field}_odds`];
                      const prob = bookie[`${config.field}_prob`];
                      return (
                        <div key={idx} className="flex justify-between items-center text-sm">
                          <span className="text-white/80 capitalize">{bookie.name}</span>
                          <span className={`${colors.text} font-mono font-bold`}>
                            {odds ? `${odds.toFixed(2)}` : 'N/A'} → {prob ? `${prob.toFixed(1)}%` : 'N/A'}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-sm text-white/70 ml-4">
                    Pinnacle, Betfair Exchange, Smarkets 등 Sharp 북메이커만 선별
                  </p>
                )}
              </div>

              {/* Step 2: 역확률 계산 공식 */}
              <div className="py-2">
                <div className="flex items-baseline gap-1.5 mb-1.5">
                  <span className={`${colors.text} font-bold text-sm`}>2.</span>
                  <h5 className="font-bold text-white text-base">역확률 계산</h5>
                </div>
                <div className="ml-4">
                  <p className={`text-base ${colors.text} font-mono font-bold mb-0.5`}>
                    P = 1 / odds × 100
                  </p>
                  <p className="text-sm text-white/70">
                    각 북메이커의 배당률을 확률로 변환
                  </p>
                </div>
              </div>

              {/* Step 3: 평균 확률 계산 */}
              <div className="py-2">
                <div className="flex items-baseline gap-1.5 mb-1.5">
                  <span className={`${colors.text} font-bold text-sm`}>3.</span>
                  <h5 className="font-bold text-white text-base">평균 확률 산출</h5>
                </div>
                <div className="ml-4">
                  {rawAverage && rawAverage[config.field] !== undefined ? (
                    <>
                      <p className={`text-base ${colors.text} font-mono font-bold mb-0.5`}>
                        ({bookmakers.map(b => {
                          const prob = b[`${config.field}_prob`];
                          return prob ? prob.toFixed(1) : '0';
                        }).join(' + ')}) / {numBookmakers}
                      </p>
                      <p className="text-sm text-white/70">
                        평균: <span className={`${colors.text} font-bold`}>{rawAverage[config.field].toFixed(1)}%</span>
                      </p>
                    </>
                  ) : (
                    <>
                      <p className={`text-base ${colors.text} font-mono font-bold mb-0.5`}>
                        P_avg = Σ(P_i) / N
                      </p>
                      <p className="text-sm text-white/70">
                        {numBookmakers}개 북메이커의 평균 확률 계산
                      </p>
                    </>
                  )}
                </div>
              </div>

              {/* Step 4: 마진 제거 */}
              <div className="py-2">
                <div className="flex items-baseline gap-1.5 mb-1.5">
                  <span className={`${colors.text} font-bold text-sm`}>4.</span>
                  <h5 className="font-bold text-white text-base">마진 제거</h5>
                </div>
                <div className="ml-4">
                  {marginRemoved && marginRemoved[config.field] !== undefined ? (
                    <>
                      <p className={`text-lg ${colors.text} font-mono font-bold mb-0.5`}>
                        최종: {marginRemoved[config.field].toFixed(1)}%
                      </p>
                      <p className="text-sm text-white/70">
                        북메이커 마진 제거 후 실제 확률
                      </p>
                    </>
                  ) : (
                    <p className="text-sm text-white/70">
                      북메이커 마진을 제거하여 실제 확률 산출
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* 데이터 출처 - 간결하게 */}
            <div className={`mt-2.5 pt-2 border-t ${colors.borderLight} text-xs text-white/60 space-y-0`}>
              <p><span className={colors.text}>데이터:</span> {match?.methodology?.data_source || 'The Odds API'}</p>
              <p><span className={colors.text}>분석:</span> {match?.methodology?.approach || 'Sharp Consensus'} ({numBookmakers}개 북메이커)</p>
            </div>
          </div>
          </motion.div>
        </motion.div>
      </AnimatePresence>,
      document.body
    );
  };

  /**
   * PoissonPopup Component
   * 예상 스코어 계산 방법 설명 팝업
   */
  const PoissonPopup = ({ type, probability, match, methodology, visible, onClose }) => {
    if (!visible || !methodology) return null;

    // 예상 스코어 계산용 설정
    const config = {
      title: '예상 스코어 계산 방법',
      icon: '⚽',
      subtitle: match?.prediction?.expected_goals
        ? `${match.home_team} ${match.prediction.expected_goals.home} : ${match.prediction.expected_goals.away} ${match.away_team}`
        : '평균 예상 득점'
    };

    // 색상 클래스 (cyan으로 통일)
    const colors = {
      border: 'border-cyan-500/50',
      borderLight: 'border-cyan-500/40',
      borderDivider: 'divide-cyan-500/20',
      text: 'text-cyan-400',
      textBright: 'text-cyan-400'
    };

    return ReactDOM.createPortal(
      <AnimatePresence>
        {/* 오버레이 */}
        <motion.div
          className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[9998] flex items-center justify-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          {/* 팝업 */}
          <motion.div
            className="relative w-full max-w-lg max-h-[90vh] overflow-y-auto"
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            onClick={(e) => e.stopPropagation()}
          >
          <div className={`relative bg-slate-900 backdrop-blur-md border-2 ${colors.border} rounded-lg p-4 shadow-2xl`}>
            {/* 닫기 버튼 */}
            <button
              onClick={onClose}
              className="absolute top-3 right-3 text-white/60 hover:text-white transition-colors p-1 hover:bg-white/10 rounded flex-shrink-0 z-10"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            {/* 헤더 */}
            <div className={`text-center mb-3 pb-2 border-b ${colors.borderLight}`}>
              <p className={`text-lg ${colors.text} font-mono font-bold`}>{config.subtitle}</p>
            </div>

            {/* 스코어 계산 과정 */}
            <div className={`space-y-0 divide-y ${colors.borderDivider}`}>
              {/* Step 1: 예상 득점 계산 */}
              <div className="py-2">
                <div className="flex items-baseline gap-1.5 mb-1.5">
                  <span className={`${colors.text} font-bold text-sm`}>1.</span>
                  <h5 className="font-bold text-white text-base">예상 득점 (Expected Goals) 계산</h5>
                </div>
                <div className="ml-4">
                  <p className={`text-base ${colors.text} font-mono font-bold mb-0.5`}>
                    λ = Expected Goals
                  </p>
                  <p className="text-sm text-white/70 mb-1">
                    언더/오버 배당률로부터 각 팀의 예상 득점(λ) 역추산
                  </p>
                  {match?.prediction?.expected_goals && (
                    <div className="bg-slate-800/60 rounded px-3 py-2 mt-2">
                      <p className="text-sm font-semibold text-white">
                        {match.home_team}: <span className={`${colors.text} font-mono`}>{match.prediction.expected_goals.home}</span>
                      </p>
                      <p className="text-sm font-semibold text-white">
                        {match.away_team}: <span className={`${colors.text} font-mono`}>{match.prediction.expected_goals.away}</span>
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Step 2: Poisson 분포로 스코어 확률 계산 */}
              <div className="py-2">
                <div className="flex items-baseline gap-1.5 mb-1.5">
                  <span className={`${colors.text} font-bold text-sm`}>2.</span>
                  <h5 className="font-bold text-white text-base">Poisson 분포로 스코어 확률 계산</h5>
                </div>
                <div className="ml-4">
                  <p className={`text-base ${colors.text} font-mono font-bold mb-0.5`}>
                    P(X=k) = (λ^k × e^(-λ)) / k!
                  </p>
                  <p className="text-sm text-white/70 mb-1">
                    각 팀의 예상 득점(λ)을 기반으로 모든 가능한 스코어의 확률을 계산
                  </p>
                  {match?.prediction?.most_likely_scores && match.prediction.most_likely_scores.length > 0 && (
                    <div className="mt-2">
                      <p className="text-xs text-white/60 mb-1">가능성 높은 스코어:</p>
                      <div className="flex flex-wrap gap-1">
                        {match.prediction.most_likely_scores.slice(0, 5).map((score, idx) => (
                          <div key={idx} className="bg-slate-800/60 rounded px-2 py-1">
                            <span className="text-sm font-bold text-white">{score.score}</span>
                            <span className="text-xs text-white/50 ml-1">({score.probability}%)</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Step 3: 평균 스코어 도출 */}
              <div className="py-2">
                <div className="flex items-baseline gap-1.5 mb-1.5">
                  <span className={`${colors.text} font-bold text-sm`}>3.</span>
                  <h5 className="font-bold text-white text-base">평균 예상 스코어</h5>
                </div>
                <div className="ml-4">
                  <p className="text-sm text-white/70 mb-1">
                    가능성 높은 스코어들의 가중 평균으로 최종 예상 스코어 산출
                  </p>
                  {match?.prediction?.expected_goals && (
                    <div className="bg-slate-800/80 rounded px-3 py-2 mt-2">
                      <p className={`text-lg font-bold ${colors.text} text-center`}>
                        {match.prediction.expected_goals.home} : {match.prediction.expected_goals.away}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* 특징 - 간결하게 */}
            <div className={`mt-2.5 pt-2 border-t ${colors.borderLight} text-xs text-white/60 space-y-0`}>
              <p><span className={colors.text}>💡 Poisson 분포:</span> 축구 득점 패턴을 통계적으로 모델링하여 정확한 스코어 예측</p>
              {match?.methodology?.uses_totals_odds && (
                <p className="text-success font-semibold">✓ 언더/오버 배당률 기반 (향상된 정확도)</p>
              )}
            </div>
          </div>
          </motion.div>
        </motion.div>
      </AnimatePresence>,
      document.body
    );
  };

  if (loading && predictions.length === 0 && !methodology) {
    return (
      <div className="section">
        <div className="container-custom">
          <div className="bg-slate-900/60 backdrop-blur-sm border border-cyan-500/20 rounded-sm p-12 text-center">
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
              className="bg-slate-900/60 backdrop-blur-sm border border-cyan-500/20 rounded-sm p-8"
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
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-brand-accent/20 border border-brand-accent/40 rounded-sm">
                  <span className="text-brand-accent font-bold">🎯 60% 예측 정확도</span>
                  <span className="text-white/60">|</span>
                  <span className="text-purple-300 font-bold">Sharp 북메이커 분석</span>
                </div>
              </div>

              {/* 시스템 소개 */}
              {methodology && (
                <div className="space-y-6 mb-8">
                  {/* 설명 */}
                  <div className="bg-slate-900/60 backdrop-blur-sm border border-brand-accent/30 rounded-sm p-6">
                    <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                      <span>🚀</span> 시스템 소개
                    </h3>
                    <p className="text-white/90 leading-relaxed mb-4">
                      {methodology.description}
                    </p>
                    <div className="flex flex-wrap gap-2">
                      <span className="px-3 py-1 bg-brand-accent/20 border border-brand-accent/40 rounded-sm text-sm font-semibold text-brand-accent">
                        Pinnacle
                      </span>
                      <span className="px-3 py-1 bg-purple-500/20 border border-purple-400/40 rounded-sm text-sm font-semibold text-purple-300">
                        Betfair Exchange
                      </span>
                      <span className="px-3 py-1 bg-success/20 border border-success/40 rounded-sm text-sm font-semibold text-success">
                        Smarkets
                      </span>
                    </div>
                  </div>

                  {/* 분석 알고리즘 */}
                  <div className="bg-slate-900/60 backdrop-blur-sm border border-cyan-500/20 rounded-sm p-6">
                    <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                      <span>🔄</span> 분석 알고리즘
                    </h3>
                    <div className="space-y-3">
                      {methodology.steps.map((step) => (
                        <div
                          key={step.step}
                          className="bg-slate-900/80 backdrop-blur-sm border border-cyan-500/30 rounded-sm p-4"
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
                  <div className="bg-slate-900/60 backdrop-blur-sm border border-cyan-500/20 rounded-sm p-6">
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
              <div className="bg-gradient-to-br from-slate-900/80 via-blue-950/60 to-slate-900/80 backdrop-blur-sm border-2 border-brand-accent/50 rounded-sm p-8 text-center">
                <div className="text-5xl mb-4">🔒</div>
                <h3 className="text-2xl font-bold text-white mb-3">
                  프리미엄 구독으로 Sharp Vision AI를 경험하세요
                </h3>
                <p className="text-white/80 mb-6 leading-relaxed">
                  세계 최고 Sharp 북메이커의 배당률을 실시간으로 분석하여<br />
                  가장 정확한 경기 예측을 제공합니다.
                </p>

                {/* 무료 체험 안내 */}
                {!hasUsedFreeTrial && (
                  <div className="mb-6 p-4 bg-success/10 border border-success/30 rounded-sm">
                    <p className="text-success font-bold mb-2">🎁 무료 체험 1회 제공!</p>
                    <p className="text-white/70 text-sm">
                      지금 바로 Sharp Vision AI의 놀라운 예측 정확도를 체험해보세요
                    </p>
                  </div>
                )}

                {hasUsedFreeTrial && (
                  <div className="mb-6 p-4 bg-white/5 border border-white/10 rounded-sm">
                    <p className="text-white/60 text-sm">
                      ✅ 무료 체험을 이미 사용하셨습니다
                    </p>
                  </div>
                )}

                <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                  {!hasUsedFreeTrial && (
                    <motion.button
                      className="btn bg-success hover:bg-success/80 text-white text-lg px-8 py-3 font-bold"
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={startFreeTrial}
                    >
                      🎁 무료 1회 체험하기
                    </motion.button>
                  )}
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
                <div className="bg-slate-900/80 backdrop-blur-sm border border-cyan-500/30 rounded-sm p-4 text-center">
                  <div className="text-3xl mb-2">🎯</div>
                  <h4 className="font-bold text-white mb-1">승/무/패 확률</h4>
                  <p className="text-sm text-white/60">Sharp 북메이커 합의 확률</p>
                </div>
                <div className="bg-slate-900/80 backdrop-blur-sm border border-cyan-500/30 rounded-sm p-4 text-center">
                  <div className="text-3xl mb-2">⚽</div>
                  <h4 className="font-bold text-white mb-1">예상 스코어</h4>
                  <p className="text-sm text-white/60">Poisson 분포 기반 예측</p>
                </div>
                <div className="bg-slate-900/80 backdrop-blur-sm border border-cyan-500/30 rounded-sm p-4 text-center">
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
    <div className="py-4 min-h-screen">
      <div className="container-custom">
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
          {/* Left Sidebar - 시스템 가이드 */}
          <div className="lg:col-span-1 space-y-4">
            <motion.div
              className="bg-slate-900/60 backdrop-blur-sm border border-cyan-500/20 rounded-sm p-4"
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
                      <div className="bg-gradient-to-br from-slate-900/80 via-blue-950/60 to-slate-900/80 backdrop-blur-sm border border-brand-accent/30 rounded-sm p-4">
                        {/* 핵심 포인트 배지들 */}
                        <div className="flex flex-wrap gap-2 mb-3">
                          <span className="inline-flex items-center gap-1 px-2 py-1 bg-brand-accent/20 border border-brand-accent/40 rounded-sm text-xs font-semibold text-brand-accent">
                            <span>🌍</span> 20+ 북메이커
                          </span>
                          <span className="inline-flex items-center gap-1 px-2 py-1 bg-success/20 border border-success/40 rounded-sm text-xs font-semibold text-success">
                            <span>⚡</span> 실시간 분석
                          </span>
                          <span className="inline-flex items-center gap-1 px-2 py-1 bg-purple-500/20 border border-purple-400/40 rounded-sm text-xs font-semibold text-purple-300">
                            <span>🤖</span> AI 역추산
                          </span>
                        </div>

                        {/* 설명 텍스트 */}
                        <div>
                          <p className="text-sm text-white/90 leading-relaxed">
                            {showFullDescription
                              ? methodology.description
                              : `${methodology.description.substring(0, 91)}...`
                            }
                          </p>
                          {methodology.description.length > 91 && (
                            <button
                              onClick={() => setShowFullDescription(!showFullDescription)}
                              className="text-xs text-brand-accent hover:text-brand-accent/80 mt-2 font-semibold"
                            >
                              {showFullDescription ? '접기' : '자세히'}
                            </button>
                          )}
                        </div>

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
                          className="text-xs px-3 py-1 rounded-sm bg-brand-accent/20 text-brand-accent hover:bg-brand-accent/30 transition-colors"
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
                              className="bg-slate-900/60 backdrop-blur-sm border border-cyan-500/20 rounded-sm p-2"
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

                    {/* 데이터 출처 - 토글 */}
                    <div className="mb-4">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-xs font-semibold text-brand-accent">📡 데이터 출처</p>
                        <button
                          onClick={() => setShowDataSources(!showDataSources)}
                          className="text-xs px-3 py-1 rounded-sm bg-brand-accent/20 text-brand-accent hover:bg-brand-accent/30 transition-colors"
                        >
                          {showDataSources ? '닫기' : '자세히'}
                        </button>
                      </div>

                      {showDataSources && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          className="mt-3"
                        >
                          <div className="bg-slate-900/60 backdrop-blur-sm border border-cyan-500/20 rounded-sm p-3">
                            <ul className="text-xs text-white space-y-1">
                              {methodology.data_sources.map((source, idx) => (
                                <li key={idx} className="flex items-start gap-2">
                                  <span className="text-brand-accent mt-0.5">•</span>
                                  <span className="flex-1">{source}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        </motion.div>
                      )}
                    </div>

                    {/* 주의사항 - 토글 */}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-xs font-semibold text-brand-accent">⚠️ 주의사항</p>
                        <button
                          onClick={() => setShowWarnings(!showWarnings)}
                          className="text-xs px-3 py-1 rounded-sm bg-brand-accent/20 text-brand-accent hover:bg-brand-accent/30 transition-colors"
                        >
                          {showWarnings ? '닫기' : '자세히'}
                        </button>
                      </div>

                      {showWarnings && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          className="mt-3"
                        >
                          <div className="bg-slate-900/60 backdrop-blur-sm border border-cyan-500/20 rounded-sm p-3">
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

                              {/* 유의사항 */}
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
                        </motion.div>
                      )}
                    </div>
                  </>
                )}
              </div>
            </motion.div>
          </div>

          {/* Main Content - 경기 예측 */}
          <div className="lg:col-span-4">
            <motion.div
              className="bg-slate-900/60 backdrop-blur-sm border border-cyan-500/20 rounded-sm p-6"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              {/* 헤더 */}
              <div className="mb-6">
                <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
                  <div className="flex items-center gap-4">
                    {/* EPL 로고 */}
                    <div className="flex items-center justify-center">
                      <img
                        src="/premier-league-logo-white.svg"
                        alt="Premier League"
                        className="w-20 h-20 lg:w-24 lg:h-24 object-contain"
                      />
                    </div>
                    <div>
                      <h1 className="text-xl lg:text-2xl font-bold text-white mb-1">
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
                    {/* 상태 배지들 */}
                    <div className="flex flex-wrap gap-2">
                      {isDeveloperMode && (
                        <div className="px-3 py-1 bg-warning/20 border border-warning/40 rounded-sm text-xs font-semibold text-warning">
                          🔧 개발자 모드 활성화
                        </div>
                      )}
                      {isUsingFreeTrial && (
                        <div className="px-3 py-1 bg-success/20 border border-success/40 rounded-sm text-xs font-semibold text-success">
                          🎁 무료 체험 중 (1회 한정)
                        </div>
                      )}
                      {/* 데이터 소스 표시 */}
                      {predictions.length > 0 && (
                        <div className={`px-3 py-1 rounded-sm text-xs font-semibold ${
                          dataSource === 'live'
                            ? 'bg-error/20 border border-error/40 text-error'
                            : 'bg-success/20 border border-success/40 text-success'
                        }`}>
                          {dataSource === 'live' ? '🔴 LIVE API' : '🟢 DEMO DATA'}
                        </div>
                      )}
                    </div>

                    {/* 버튼들 */}
                    <div className="flex gap-2 w-full lg:w-auto">
                      <button
                        onClick={() => fetchPredictions(true)}
                        disabled={loading}
                        className="btn btn-primary flex-1 lg:flex-none text-sm"
                      >
                        {loading ? '새로고침 중...' : '🔄 데모 데이터'}
                      </button>
                      {isDeveloperMode && (
                        <button
                          onClick={fetchLiveData}
                          disabled={loading}
                          className="btn bg-error hover:bg-error/80 text-white text-sm px-4"
                          title="실제 API 호출 - 할당량 소진 주의!"
                        >
                          {loading ? '⏳ 호출 중...' : '🔴 실제 API'}
                        </button>
                      )}
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
                <div className="bg-slate-900/60 backdrop-blur-sm border border-error/30 rounded-sm p-4 mb-6">
                  <p className="text-error text-sm">{error}</p>
                </div>
              )}

              {/* 경기 예측 섹션 */}
              {selectedMatchId === null ? (
                /* 경기 목록 - 간단한 카드 */
                <div>
                  <h3 className="text-lg font-bold text-white mb-4">
                    📋 이번 라운드 경기 목록 ({predictions.length}경기)
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {predictions.map((match, idx) => {
                      const pred = match.prediction;
                      const matchKey = `${match.home_team}_${match.away_team}`;

                      return (
                        <motion.div
                          key={match.match_id || idx}
                          className="bg-slate-900/60 backdrop-blur-sm border border-cyan-500/20 rounded-sm overflow-hidden hover:border-brand-accent/50 transition-all cursor-pointer"
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: idx * 0.05 }}
                          onClick={() => {
                            setSelectedMatchId(match.match_id || idx);
                          }}
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                        >
                          {/* 간단한 경기 정보 */}
                          <div className="p-4">
                            <div className="flex justify-between items-center mb-3">
                              {/* 홈 팀 */}
                              <div className="flex-1 flex flex-col items-center">
                                <div className="w-10 h-10 mb-1.5 flex items-center justify-center">
                                  {getTeamBadgeUrl(match.home_team) ? (
                                    <img
                                      src={getTeamBadgeUrl(match.home_team)}
                                      alt={match.home_team}
                                      className="w-full h-full object-contain"
                                      onError={(e) => { e.target.src = ''; e.target.style.display = 'none'; }}
                                    />
                                  ) : (
                                    <span className="text-2xl">⚽</span>
                                  )}
                                </div>
                                <p className="text-sm font-bold text-white text-center">{match.home_team}</p>
                              </div>

                              {/* VS */}
                              <div className="px-3 flex flex-col items-center">
                                <div className="text-base font-bold text-brand-accent">VS</div>
                              </div>

                              {/* 원정 팀 */}
                              <div className="flex-1 flex flex-col items-center">
                                <div className="w-10 h-10 mb-1.5 flex items-center justify-center">
                                  {getTeamBadgeUrl(match.away_team) ? (
                                    <img
                                      src={getTeamBadgeUrl(match.away_team)}
                                      alt={match.away_team}
                                      className="w-full h-full object-contain"
                                      onError={(e) => { e.target.src = ''; e.target.style.display = 'none'; }}
                                    />
                                  ) : (
                                    <span className="text-2xl">⚽</span>
                                  )}
                                </div>
                                <p className="text-sm font-bold text-white text-center">{match.away_team}</p>
                              </div>
                            </div>

                            {/* 간단한 예측 정보 */}
                            <div className="bg-white/5 rounded-sm p-2 mb-2">
                              <div className="grid grid-cols-3 gap-2 text-center">
                                <div>
                                  <p className="text-xs text-white/60">홈승</p>
                                  <p className="text-sm font-bold text-blue-400">{pred.probabilities.home}%</p>
                                </div>
                                <div>
                                  <p className="text-xs text-white/60">무승부</p>
                                  <p className="text-sm font-bold text-yellow-400">{pred.probabilities.draw}%</p>
                                </div>
                                <div>
                                  <p className="text-xs text-white/60">원정승</p>
                                  <p className="text-sm font-bold text-red-400">{pred.probabilities.away}%</p>
                                </div>
                              </div>
                            </div>

                            {/* 경기 일시 + 상세보기 안내 */}
                            <div className="flex justify-between items-center">
                              {match.commence_time && (
                                <p className="text-xs text-white/50">
                                  {new Date(match.commence_time).toLocaleString('ko-KR', {
                                    month: 'short',
                                    day: 'numeric',
                                    hour: '2-digit',
                                    minute: '2-digit'
                                  })}
                                </p>
                              )}
                              <p className="text-xs text-brand-accent font-semibold">상세보기 →</p>
                            </div>
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                </div>
              ) : (
                /* 선택된 경기 상세 정보 */
                <div>
                  {/* 뒤로가기 버튼 */}
                  <button
                    onClick={() => setSelectedMatchId(null)}
                    className="mb-4 flex items-center gap-2 px-4 py-2 bg-slate-900/60 backdrop-blur-sm rounded-sm border border-cyan-500/20 hover:border-brand-accent/50 text-white transition-all"
                  >
                    <span>←</span>
                    <span>경기 목록으로 돌아가기</span>
                  </button>

                  {/* 상세 경기 카드 */}
                  <div className="space-y-4">
                    {predictions.filter((match, idx) => (match.match_id || idx) === selectedMatchId).map((match, idx) => {
                      const pred = match.prediction;
                      const expectedScore = `${pred.expected_goals.home} : ${pred.expected_goals.away}`;
                      const matchKey = `${match.home_team}_${match.away_team}`;

                      return (
                        <motion.div
                      key={match.match_id || idx}
                      ref={(el) => {
                        if (el) matchRefsMap.current[matchKey] = el;
                      }}
                      className="bg-slate-900/60 backdrop-blur-sm border border-cyan-500/20 rounded-sm overflow-hidden hover:border-brand-accent/50 transition-all"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: idx * 0.1 }}
                    >
                      {/* 경기 헤더 */}
                      <div className="bg-gradient-to-r from-pink-600/20 to-pink-700/20 p-3 border-b border-white/10">
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
                          <h4 className="font-semibold text-white mb-3 text-sm lg:text-base">
                            승/무/패 확률 (Consensus)
                            <span className="ml-2 text-xs text-cyan-400/60">클릭하여 상세 분석 보기</span>
                          </h4>
                          <div className="grid grid-cols-3 gap-2 lg:gap-4">
                            {/* 홈 승리 */}
                            <div
                              className="relative bg-slate-900/80 backdrop-blur-sm border border-blue-500/30 rounded-sm p-3 lg:p-4 text-center cursor-pointer hover:border-blue-400/60 hover:bg-blue-500/10 transition-all"
                              onClick={() => handlePopupClick('consensus', 'home', match.match_id || idx, match)}
                            >
                              <p className="text-xs lg:text-sm text-white/60 mb-1">홈 승리</p>
                              <p className="text-xl lg:text-2xl font-bold text-blue-400">{pred.probabilities.home}%</p>
                            </div>

                            {/* 무승부 */}
                            <div
                              className="relative bg-slate-900/80 backdrop-blur-sm border border-amber-500/30 rounded-sm p-3 lg:p-4 text-center cursor-pointer hover:border-amber-400/60 hover:bg-amber-500/10 transition-all"
                              onClick={() => handlePopupClick('consensus', 'draw', match.match_id || idx, match)}
                            >
                              <p className="text-xs lg:text-sm text-white/60 mb-1">무승부</p>
                              <p className="text-xl lg:text-2xl font-bold text-amber-400">{pred.probabilities.draw}%</p>
                            </div>

                            {/* 원정 승리 */}
                            <div
                              className="relative bg-slate-900/80 backdrop-blur-sm border border-red-500/30 rounded-sm p-3 lg:p-4 text-center cursor-pointer hover:border-red-400/60 hover:bg-red-500/10 transition-all"
                              onClick={() => handlePopupClick('consensus', 'away', match.match_id || idx, match)}
                            >
                              <p className="text-xs lg:text-sm text-white/60 mb-1">원정 승리</p>
                              <p className="text-xl lg:text-2xl font-bold text-red-400">{pred.probabilities.away}%</p>
                            </div>
                          </div>
                        </div>

                        {/* 예상 스코어 */}
                        <div className="mb-4">
                          <h4 className="font-semibold text-white mb-3 text-sm lg:text-base">
                            예상 스코어
                            <span className="ml-2 text-xs text-purple-400/60">클릭하여 계산식 보기</span>
                          </h4>
                          <div className="bg-slate-900/80 backdrop-blur-sm border border-cyan-500/30 rounded-sm p-4">
                            <div
                              className="text-center mb-4 cursor-pointer hover:bg-cyan-500/5 transition-all rounded-sm py-2"
                              onClick={() => handlePopupClick('poisson', 'home_win', match.match_id || idx, match)}
                            >
                              <p className="text-3xl lg:text-4xl font-bold text-brand-accent">{expectedScore}</p>
                              <p className="text-xs lg:text-sm text-white/60 mt-1">
                                (평균 예상 득점 - Poisson 분포)
                              </p>
                            </div>

                            {/* 가장 가능성 높은 스코어들 */}
                            <div>
                              <p className="text-xs lg:text-sm text-white/60 mb-2 text-center">가능성 높은 스코어</p>
                              <div className="grid grid-cols-5 gap-2">
                                {pred.most_likely_scores.map((score, idx) => (
                                  <div key={idx} className="bg-slate-900/60 backdrop-blur-sm border border-cyan-500/20 rounded-sm p-2 text-center">
                                    <p className="text-xs lg:text-sm font-bold text-white">{score.score}</p>
                                    <p className="text-xs text-white/50">{score.probability}%</p>
                                  </div>
                                ))}
                              </div>
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
                </div>
              )}

              {/* 경기가 없을 때 */}
              {predictions.length === 0 && !loading && (
                <div className="bg-slate-900/60 backdrop-blur-sm border border-cyan-500/20 rounded-sm p-8 lg:p-12 text-center">
                  <div className="text-5xl lg:text-6xl mb-4">🏴</div>
                  <h3 className="text-xl lg:text-2xl font-bold text-white mb-2">
                    예측 가능한 경기가 없습니다
                  </h3>
                  <p className="text-sm lg:text-base text-white/60">
                    다가오는 EPL 경기의 배당률이 아직 오픈되지 않았습니다.
                  </p>
                </div>
              )}

              {/* 무료 체험 안내 */}
              {isUsingFreeTrial && predictions.length > 0 && (
                <motion.div
                  className="mt-6 bg-gradient-to-br from-slate-900/80 via-blue-950/60 to-slate-900/80 backdrop-blur-sm rounded-sm p-6 border-2 border-brand-accent/50 text-center"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <div className="text-4xl mb-3">🎁</div>
                  <h4 className="text-xl font-bold text-white mb-2">
                    무료 체험을 즐기고 계신가요?
                  </h4>
                  <p className="text-white/80 mb-4">
                    프리미엄 구독으로 언제든지 Sharp Vision AI의 정확한 예측을 이용하세요!
                  </p>
                  <motion.button
                    className="btn btn-primary text-lg px-8 py-3"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => alert('구독 기능은 곧 출시됩니다!')}
                  >
                    ⭐ 프리미엄 구독하기
                  </motion.button>
                  <p className="text-xs text-white/50 mt-3">
                    * 무료 체험은 1회 한정으로 제공됩니다
                  </p>
                </motion.div>
              )}
            </motion.div>
          </div>
        </div>
      </div>

      {/* 팝업 렌더링 */}
      {activePopup && (
        <>
          {activePopup.type === 'consensus' && (
            <ProbabilityPopup
              type={activePopup.outcome}
              probability={
                activePopup.match?.prediction?.probabilities?.[activePopup.outcome] || 0
              }
              match={activePopup.match}
              methodology={methodology}
              visible={true}
              onClose={handleClosePopup}
            />
          )}
          {activePopup.type === 'poisson' && (
            <PoissonPopup
              type={activePopup.outcome}
              probability={
                activePopup.match?.prediction?.poisson_probabilities?.[activePopup.outcome] || 0
              }
              match={activePopup.match}
              methodology={methodology}
              visible={true}
              onClose={handleClosePopup}
            />
          )}
        </>
      )}
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
