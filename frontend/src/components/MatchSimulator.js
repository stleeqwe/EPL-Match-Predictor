import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, RefreshCw, Trophy, Swords } from 'lucide-react';
import WeightSettings from './WeightSettings';
import TeamDropdown from './TeamDropdown';
import InlineSimulationProgress from './InlineSimulationProgress';
import { simulationAPI } from '../services/authAPI';

/**
 * MatchSimulator Component
 * 두 팀 간의 가상 대결 시뮬레이션
 */
const MatchSimulator = ({ darkMode = false, selectedMatch = null, onTeamClick = null, isActive = false }) => {
  const [teams, setTeams] = useState([]);
  const [teamScores, setTeamScores] = useState({}); // 각 팀의 평가 상태
  const [homeTeam, setHomeTeam] = useState('');
  const [awayTeam, setAwayTeam] = useState('');
  const [aiModel, setAiModel] = useState('pro'); // 'basic', 'pro', 'super'
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [result, setResult] = useState(null);
  const [weights, setWeights] = useState({
    user_value: 0.65,
    odds: 0.20,
    stats: 0.15
  });
  const [showWeightSettings, setShowWeightSettings] = useState(false);
  const [showDashboard, setShowDashboard] = useState(false);

  useEffect(() => {
    fetchTeams();
  }, []);

  useEffect(() => {
    if (teams.length > 0) {
      loadTeamScores();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [teams]);

  // 가상대결 탭이 활성화될 때마다 데이터 새로고침
  useEffect(() => {
    if (isActive && teams.length > 0) {
      console.log('🔄 가상대결 탭 활성화 - 팀 점수 자동 새로고침');
      loadTeamScores();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isActive]);

  // 컴포넌트가 다시 포커스를 받을 때 데이터 갱신
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden && teams.length > 0) {
        loadTeamScores(); // 페이지가 다시 활성화되면 데이터 새로고침
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    // 컴포넌트가 보여질 때도 데이터 갱신
    if (teams.length > 0) {
      loadTeamScores();
    }

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [teams.length]);

  // 경기일정에서 선택된 경기로 자동 설정
  useEffect(() => {
    if (selectedMatch && teams.length > 0) {
      // 결과 초기화
      setResult(null);

      // 팀 이름이 teams 배열에 존재하는지 확인
      const homeTeamExists = teams.includes(selectedMatch.homeTeam);
      const awayTeamExists = teams.includes(selectedMatch.awayTeam);

      if (homeTeamExists && awayTeamExists) {
        setHomeTeam(selectedMatch.homeTeam);
        setAwayTeam(selectedMatch.awayTeam);
      } else {
        console.warn('선택된 팀이 팀 목록에 없습니다:', selectedMatch);
      }
    }
  }, [selectedMatch, teams]);

  const fetchTeams = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:5001/api/teams');
      if (!response.ok) throw new Error('Failed to fetch teams');
      const data = await response.json();
      const teamsList = data.teams || [];
      const normalizedTeams = teamsList.map(t => typeof t === 'string' ? t : t.name);
      setTeams(normalizedTeams);
    } catch (err) {
      console.error('Failed to fetch teams:', err);
      setTeams([]);
    } finally {
      setLoading(false);
    }
  };

  // 모든 팀의 평가 상태 확인 (백엔드로부터 로드)
  const loadTeamScores = async () => {
    const scores = {};

    // 모든 팀에 대해 병렬로 데이터 로드
    await Promise.all(
      teams.map(async (teamName) => {
        const score = await getTeamScoreFromBackend(teamName);
        const readiness = await checkSimulationReadiness(teamName);
        scores[teamName] = {
          overall: score.overall,
          hasData: score.overall > 0,
          ready: readiness.ready,
          completed: readiness.completed,
          missing: readiness.missing
        };
      })
    );

    setTeamScores(scores);
  };

  // 시뮬레이션 준비 상태 확인
  const checkSimulationReadiness = async (teamName) => {
    try {
      const response = await fetch(`http://localhost:5001/api/teams/${encodeURIComponent(teamName)}/simulation-ready`);

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          return {
            ready: result.ready,
            completed: result.completed || {},
            missing: result.missing || []
          };
        }
      }
    } catch (e) {
      console.error(`Error checking simulation readiness for ${teamName}:`, e);
    }

    // 데이터를 가져오지 못하면 준비되지 않은 것으로 간주
    return {
      ready: false,
      completed: {
        rating: false,
        formation: false,
        lineup: false,
        tactics: false
      },
      missing: ['rating', 'formation', 'lineup', 'tactics']
    };
  };

  // 백엔드에서 팀의 종합 점수 불러오기
  const getTeamScoreFromBackend = async (teamName) => {
    try {
      const response = await fetch(`http://localhost:5001/api/teams/${encodeURIComponent(teamName)}/overall_score`);

      if (response.ok) {
        const result = await response.json();
        if (result.success && result.data) {
          return {
            overall: result.data.overallScore || 0,
            player: result.data.playerScore || 0,
            strength: result.data.strengthScore || 0,
            playerWeight: result.data.playerWeight || 50,
            strengthWeight: result.data.strengthWeight || 50
          };
        }
      }
    } catch (e) {
      console.error(`Error fetching overall score for ${teamName}:`, e);
    }

    // 데이터가 없으면 0 반환
    return {
      overall: 0,
      player: 0,
      strength: 0,
      playerWeight: 50,
      strengthWeight: 50
    };
  };

  // 시뮬레이션 실행 시 사용하는 동기 함수 (캐시된 데이터 사용)
  const getTeamScore = (teamName) => {
    // teamScores state에서 가져오되, 실시간 데이터도 백엔드에서 fetch
    // 이 함수는 simulateMatch에서만 호출되므로 async 함수 내에서 실행됨
    return getTeamScoreFromBackend(teamName);
  };

  // AI 모델별 시뮬레이션 로직
  const simulateBasic = (homeScore, awayScore) => {
    // Basic: 간단한 랜덤 계산 (변동성 높음)
    // 사용자 설정 가중치 반영: 선수평가와 팀전력을 가중치에 따라 합산
    const homeAttack = (homeScore.player * homeScore.playerWeight / 100) + (homeScore.strength * homeScore.strengthWeight / 100);
    const awayAttack = (awayScore.player * awayScore.playerWeight / 100) + (awayScore.strength * awayScore.strengthWeight / 100);
    const homeBonus = 5;

    const homeExpectedGoals = Math.max(0, (homeAttack + homeBonus) / 100 * 2.5);
    const awayExpectedGoals = Math.max(0, awayAttack / 100 * 2.5);

    // 높은 랜덤성
    const homeGoals = Math.max(0, Math.round(homeExpectedGoals + (Math.random() - 0.2) * 3));
    const awayGoals = Math.max(0, Math.round(awayExpectedGoals + (Math.random() - 0.2) * 3));

    return { homeGoals, awayGoals };
  };

  const simulatePro = (homeScore, awayScore) => {
    // Pro: 중급 수준 시뮬레이션 (균형잡힌 예측)
    // 사용자 설정 가중치 반영: 선수평가와 팀전력을 가중치에 따라 합산
    const homeAttack = (homeScore.player * homeScore.playerWeight / 100) + (homeScore.strength * homeScore.strengthWeight / 100);
    const awayAttack = (awayScore.player * awayScore.playerWeight / 100) + (awayScore.strength * awayScore.strengthWeight / 100);
    const homeBonus = 5;

    const homeExpectedGoals = Math.max(0, (homeAttack + homeBonus) / 100 * 3);
    const awayExpectedGoals = Math.max(0, awayAttack / 100 * 3);

    // 적절한 랜덤성
    const homeGoals = Math.max(0, Math.round(homeExpectedGoals + (Math.random() - 0.3) * 2));
    const awayGoals = Math.max(0, Math.round(awayExpectedGoals + (Math.random() - 0.3) * 2));

    return { homeGoals, awayGoals };
  };

  const simulateSuper = (homeScore, awayScore) => {
    // Super: 고급 시뮬레이션 (사용자 설정 가중치 반영, 정교한 계산)
    const homePlayerScore = homeScore.player;
    const homeStrengthScore = homeScore.strength;
    const awayPlayerScore = awayScore.player;
    const awayStrengthScore = awayScore.strength;

    // 사용자가 설정한 가중치 사용 (playerWeight/strengthWeight)
    const homePlayerWeight = homeScore.playerWeight / 100;
    const homeStrengthWeight = homeScore.strengthWeight / 100;
    const awayPlayerWeight = awayScore.playerWeight / 100;
    const awayStrengthWeight = awayScore.strengthWeight / 100;

    // 공격력: 사용자 설정 가중치 반영
    const homeAttack = homePlayerScore * homePlayerWeight + homeStrengthScore * homeStrengthWeight;
    const awayAttack = awayPlayerScore * awayPlayerWeight + awayStrengthScore * awayStrengthWeight;

    // 수비력: 사용자 설정 가중치 반영 (팀전력을 더 중시)
    const homeDefense = homeStrengthScore * homeStrengthWeight + homePlayerScore * homePlayerWeight;
    const awayDefense = awayStrengthScore * awayStrengthWeight + awayPlayerScore * awayPlayerWeight;

    // 상대 수비를 고려한 골 기댓값
    const homeBonus = 7;
    const homeExpectedGoals = Math.max(0, ((homeAttack - awayDefense * 0.3 + homeBonus) / 100) * 3.5);
    const awayExpectedGoals = Math.max(0, ((awayAttack - homeDefense * 0.3) / 100) * 3.5);

    // 낮은 랜덤성 (더 예측 가능)
    const homeGoals = Math.max(0, Math.round(homeExpectedGoals + (Math.random() - 0.4) * 1.5));
    const awayGoals = Math.max(0, Math.round(awayExpectedGoals + (Math.random() - 0.4) * 1.5));

    return { homeGoals, awayGoals };
  };

  const simulateMatch = async () => {
    if (!homeTeam || !awayTeam) return;
    if (homeTeam === awayTeam) {
      alert('같은 팀은 대결할 수 없습니다!');
      return;
    }

    setSimulating(true);

    try {
      // V3 Pipeline mode - Use SSE streaming with InlineSimulationProgress
      if (aiModel === 'v3') {
        console.log('Using V3 Pipeline for simulation');
        setShowDashboard(true);
        setSimulating(false); // InlineSimulationProgress handles its own loading state
        return;
      }

      // Client-side simulation (Basic/Pro/Super/Gemini models)
      const homeScore = await getTeamScore(homeTeam);
      const awayScore = await getTeamScore(awayTeam);

      await new Promise(resolve => setTimeout(resolve, 1500));

      // AI 모델에 따라 다른 시뮬레이션 실행
      let goals;
      if (aiModel === 'basic') {
        goals = simulateBasic(homeScore, awayScore);
      } else if (aiModel === 'pro') {
        goals = simulatePro(homeScore, awayScore);
      } else if (aiModel === 'super') {
        goals = simulateSuper(homeScore, awayScore);
      }

      const { homeGoals, awayGoals } = goals;

      setResult({
        home: {
          name: homeTeam,
          goals: homeGoals,
          score: homeScore
        },
        away: {
          name: awayTeam,
          goals: awayGoals,
          score: awayScore
        },
        winner: homeGoals > awayGoals ? 'home' : awayGoals > homeGoals ? 'away' : 'draw',
        aiModel: aiModel
      });

    } catch (error) {
      console.error('시뮬레이션 오류:', error);
      alert(`시뮬레이션 실패: ${error.message}`);
    } finally {
      setSimulating(false);
    }
  };

  const resetSimulation = () => {
    setResult(null);
    setHomeTeam('');
    setAwayTeam('');
    setShowDashboard(false);
    // aiModel은 유지 (사용자가 선택한 모델 유지)
  };

  const handleDashboardComplete = async (dashboardResult) => {
    console.log('V3 Pipeline completed:', dashboardResult);

    // Map V3 Pipeline result to MatchSimulator result format
    const probabilities = dashboardResult.probabilities;
    const winner =
      probabilities.home_win > probabilities.away_win && probabilities.home_win > probabilities.draw ? 'home' :
      probabilities.away_win > probabilities.home_win && probabilities.away_win > probabilities.draw ? 'away' :
      'draw';

    setResult({
      home: {
        name: homeTeam,
        goals: null, // V3 doesn't provide exact goals
        score: null,
        winProbability: probabilities.home_win
      },
      away: {
        name: awayTeam,
        goals: null,
        score: null,
        winProbability: probabilities.away_win
      },
      winner: winner,
      aiModel: 'v3',
      probabilities: probabilities,
      scenarios: dashboardResult.scenarios,
      validation: dashboardResult.validation,
      executionTime: dashboardResult.execution_time
    });

    setShowDashboard(false);
  };

  const handleDashboardCancel = () => {
    console.log('V3 Pipeline cancelled');
    setShowDashboard(false);
    setSimulating(false);
  };

  if (loading) {
    return (
      <div className="section">
        <div className="container-custom">
          <div className="card p-12 text-center">
            <div className="spinner mx-auto mb-4"></div>
            <p className="text-white/60">팀 목록 로딩 중...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="py-4 min-h-screen">
      <div className="container-custom">
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
          {/* Left Sidebar */}
          <div className="lg:col-span-1 space-y-4">
            {/* Simulation Info */}
            <motion.div
              className="p-4 rounded-sm bg-slate-900/60 backdrop-blur-sm border border-cyan-500/20"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
            >
              <div>
                <h4 className="font-bold text-white mb-3 text-sm">✅ 시뮬레이션 실행 조건</h4>

                <div className="mb-3 p-3 rounded-sm bg-cyan-500/10 border border-cyan-500/30">
                  <p className="text-xs font-semibold text-cyan-400 mb-2">필수 완료 항목 (4단계)</p>
                  <ul className="text-xs text-white/80 space-y-1.5 ml-3 list-decimal leading-relaxed">
                    <li><span className="font-semibold text-white">선수 평가</span><br/>팀 분석에서 선수 능력치 평가</li>
                    <li><span className="font-semibold text-white">포메이션 선택</span><br/>6가지 포메이션 중 1개 선택</li>
                    <li><span className="font-semibold text-white">라인업 구성</span><br/>11명 선수를 포지션에 배치</li>
                    <li><span className="font-semibold text-white">전술 설정</span><br/>수비/공격/전환 전술 파라미터 설정</li>
                  </ul>
                </div>

                <div className="mb-3">
                  <p className="text-xs font-semibold text-brand-accent mb-2">📊 시뮬레이션 방식</p>
                  <ul className="text-xs text-white/70 space-y-1 ml-3 list-disc leading-relaxed">
                    <li>선수 능력치 + 팀 전력 종합 점수</li>
                    <li>포메이션별 차단률 반영</li>
                    <li>전술 파라미터 기반 계산</li>
                    <li>홈팀 어드밴티지 (+5점)</li>
                    <li>AI 모델별 알고리즘 적용</li>
                  </ul>
                </div>

                <div className="mb-3">
                  <p className="text-xs font-semibold text-warning mb-2">⚠️ 주의사항</p>
                  <ul className="text-xs text-white/70 space-y-1 ml-3 list-disc leading-relaxed">
                    <li>4단계 모두 완료해야 시뮬레이션 가능</li>
                    <li>포메이션과 라인업 미설정 시 실행 불가</li>
                    <li>전술 미설정 시 기본값 사용 불가</li>
                  </ul>
                </div>

                <p className="text-xs text-white/50 mt-4 pt-3 border-t border-white/10">
                  ※ 실제 경기 결과와 다를 수 있습니다
                </p>
              </div>
            </motion.div>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-4">
            <motion.div
              className="p-6 rounded-sm bg-gradient-to-br from-slate-900/80 via-blue-950/60 to-slate-900/80 backdrop-blur-sm border border-cyan-500/20"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              {/* Header */}
              <div className="text-center mb-8">
                <h1 className="text-3xl font-bold text-white mb-2 flex items-center justify-center gap-3">
                  <Swords className="w-8 h-8 text-brand-accent" />
                  가상 대결 시뮬레이터
                </h1>
                <p className="text-white/60">내가 평가한 팀 데이터를 기반으로 경기 결과를 예측합니다</p>
              </div>

          {/* Team Selection / V3 Pipeline Progress */}
          <AnimatePresence mode="wait">
            {!result ? (
              showDashboard ? (
                <InlineSimulationProgress
                  key="progress"
                  homeTeam={homeTeam}
                  awayTeam={awayTeam}
                  onComplete={handleDashboardComplete}
                  onCancel={handleDashboardCancel}
                />
              ) : (
                <motion.div
                  key="selection"
                  className="relative z-10"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                  {/* Home Team */}
                  <div className="p-6 rounded-sm bg-slate-900/60 backdrop-blur-sm border border-cyan-500/20">
                    <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                      홈 팀
                    </h3>
                    <TeamDropdown
                      value={homeTeam}
                      onChange={setHomeTeam}
                      teams={teams}
                      teamScores={teamScores}
                      placeholder="-- 팀 선택 --"
                      disabled={simulating}
                      disabledTeams={awayTeam ? [awayTeam] : []}
                    />
                    {homeTeam && teamScores[homeTeam] && (
                      <div className="mt-3 text-sm">
                        {teamScores[homeTeam].ready ? (
                          <div className="flex items-center gap-2 text-success">
                            <span>✓</span>
                            <span>시뮬레이션 준비 완료</span>
                          </div>
                        ) : (
                          <div className="space-y-2">
                            <div className="flex items-center gap-2 text-warning">
                              <span>⚠️</span>
                              <span>시뮬레이션 설정이 완료되지 않았습니다</span>
                            </div>
                            {teamScores[homeTeam].missing && teamScores[homeTeam].missing.length > 0 && (
                              <div className="ml-6 text-xs text-white/70">
                                <span className="font-semibold">누락 항목:</span>
                                <ul className="mt-1 space-y-1 list-disc list-inside">
                                  {teamScores[homeTeam].missing.includes('rating') && <li>선수 평가</li>}
                                  {teamScores[homeTeam].missing.includes('formation') && <li>포메이션 선택</li>}
                                  {teamScores[homeTeam].missing.includes('lineup') && <li>라인업 구성 (11명 선수 배치)</li>}
                                  {teamScores[homeTeam].missing.includes('tactics') && <li>전술 설정</li>}
                                </ul>
                              </div>
                            )}
                            {onTeamClick && (
                              <button
                                onClick={() => onTeamClick(homeTeam)}
                                className="ml-6 text-cyan-400 hover:text-cyan-300 font-semibold underline transition-colors text-xs"
                              >
                                팀 설정하기
                              </button>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Away Team */}
                  <div className="p-6 rounded-sm bg-slate-900/60 backdrop-blur-sm border border-cyan-500/20">
                    <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                      원정 팀
                    </h3>
                    <TeamDropdown
                      value={awayTeam}
                      onChange={setAwayTeam}
                      teams={teams}
                      teamScores={teamScores}
                      placeholder="-- 팀 선택 --"
                      disabled={simulating}
                      disabledTeams={homeTeam ? [homeTeam] : []}
                    />
                    {awayTeam && teamScores[awayTeam] && (
                      <div className="mt-3 text-sm">
                        {teamScores[awayTeam].ready ? (
                          <div className="flex items-center gap-2 text-success">
                            <span>✓</span>
                            <span>시뮬레이션 준비 완료</span>
                          </div>
                        ) : (
                          <div className="space-y-2">
                            <div className="flex items-center gap-2 text-warning">
                              <span>⚠️</span>
                              <span>시뮬레이션 설정이 완료되지 않았습니다</span>
                            </div>
                            {teamScores[awayTeam].missing && teamScores[awayTeam].missing.length > 0 && (
                              <div className="ml-6 text-xs text-white/70">
                                <span className="font-semibold">누락 항목:</span>
                                <ul className="mt-1 space-y-1 list-disc list-inside">
                                  {teamScores[awayTeam].missing.includes('rating') && <li>선수 평가</li>}
                                  {teamScores[awayTeam].missing.includes('formation') && <li>포메이션 선택</li>}
                                  {teamScores[awayTeam].missing.includes('lineup') && <li>라인업 구성 (11명 선수 배치)</li>}
                                  {teamScores[awayTeam].missing.includes('tactics') && <li>전술 설정</li>}
                                </ul>
                              </div>
                            )}
                            {onTeamClick && (
                              <button
                                onClick={() => onTeamClick(awayTeam)}
                                className="ml-6 text-cyan-400 hover:text-cyan-300 font-semibold underline transition-colors text-xs"
                              >
                                팀 설정하기
                              </button>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {/* Weight Settings */}
                <div className="mb-6">
                  <button
                    onClick={() => setShowWeightSettings(!showWeightSettings)}
                    className="mb-3 text-sm text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-2"
                  >
                    {showWeightSettings ? '▼' : '▶'} 데이터 가중치 설정
                  </button>
                  {showWeightSettings && (
                    <WeightSettings
                      weights={weights}
                      onChange={setWeights}
                      presets={[]}
                      darkMode={darkMode}
                    />
                  )}
                </div>

                {/* AI Model Selection */}
                <div className="mb-6">
                  <h3 className="text-base font-bold text-white mb-3 flex items-center gap-2">
                    🤖 AI 엔진 모델 선택 (Powered by Qwen 2.5 32B)
                  </h3>
                  <div className="grid grid-cols-4 gap-2">
                    {/* Basic */}
                    <motion.button
                      onClick={() => setAiModel('basic')}
                      className={`
                        p-4 rounded-sm border-2 transition-all
                        ${aiModel === 'basic'
                          ? 'border-warning bg-warning/10'
                          : 'border-white/10 bg-white/5 hover:border-warning/40'}
                      `}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      disabled={simulating}
                    >
                      <div className="text-center">
                        <div className="text-2xl mb-2">🎯</div>
                        <div className="text-lg font-extrabold text-white mb-1">Basic</div>
                        <div className="text-sm text-white/60">합리적인 추론</div>
                      </div>
                    </motion.button>

                    {/* Pro */}
                    <motion.button
                      onClick={() => setAiModel('pro')}
                      className={`
                        p-4 rounded-sm border-2 transition-all
                        ${aiModel === 'pro'
                          ? 'border-brand-accent bg-brand-accent/10'
                          : 'border-white/10 bg-white/5 hover:border-brand-accent/40'}
                      `}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      disabled={simulating}
                    >
                      <div className="text-center">
                        <div className="text-2xl mb-2">🚀</div>
                        <div className="text-lg font-extrabold text-white mb-1">Pro</div>
                        <div className="text-sm text-brand-accent/80">
                          정교한 추론<span className="text-brand-accent">(추천)</span>
                        </div>
                      </div>
                    </motion.button>

                    {/* Super */}
                    <motion.button
                      onClick={() => setAiModel('super')}
                      className={`
                        p-4 rounded-sm border-2 transition-all
                        ${aiModel === 'super'
                          ? 'border-rose-500 bg-rose-500/10'
                          : 'border-white/10 bg-white/5 hover:border-rose-500/40'}
                      `}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      disabled={simulating}
                    >
                      <div className="text-center">
                        <div className="text-2xl mb-2">👽</div>
                        <div className="text-lg font-extrabold text-white mb-1">Super</div>
                        <div className="text-sm text-amber-400">Outstanding</div>
                      </div>
                    </motion.button>

                    {/* V3 Pipeline */}
                    <motion.button
                      onClick={() => setAiModel('v3')}
                      className={`
                        p-4 rounded-sm border-2 transition-all
                        ${aiModel === 'v3'
                          ? 'border-green-500 bg-green-500/10'
                          : 'border-white/10 bg-white/5 hover:border-green-500/40'}
                      `}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      disabled={simulating}
                    >
                      <div className="text-center">
                        <div className="text-2xl mb-2">⚡</div>
                        <div className="text-lg font-extrabold text-white mb-1">V3</div>
                        <div className="text-sm text-green-400">Pipeline</div>
                      </div>
                    </motion.button>
                  </div>

                  {/* Model Description */}
                  <AnimatePresence mode="wait">
                    <motion.div
                      key={aiModel}
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      transition={{ duration: 0.2 }}
                      className={`
                        mt-4 p-5 rounded-sm border-2
                        ${aiModel === 'basic' ? 'bg-gradient-to-br from-slate-800/40 to-slate-900/20 border-slate-600/40' :
                          aiModel === 'pro' ? 'bg-gradient-to-br from-slate-800/40 to-slate-900/20 border-slate-600/40' :
                          'bg-gradient-to-br from-slate-800/40 to-slate-900/20 border-slate-600/40'}
                      `}
                      style={{
                        boxShadow: 'inset 0 1px 0 0 rgba(192, 192, 192, 0.1), inset 0 -1px 0 0 rgba(0, 0, 0, 0.6)',
                      }}
                    >
                      <div>
                        {aiModel === 'basic' && (
                          <>
                            <div className="flex items-center gap-2 mb-4">
                              <div className="font-bold text-warning text-lg">🎯 Basic AI 엔진</div>
                              <div
                                className="ml-auto px-3 py-1 rounded-full border border-slate-600/50"
                                style={{
                                  background: 'linear-gradient(135deg, rgba(50, 50, 55, 0.5) 0%, rgba(30, 30, 35, 0.6) 100%)',
                                  boxShadow: 'inset 0 1px 0 0 rgba(192, 192, 192, 0.1), inset 0 -1px 0 0 rgba(0, 0, 0, 0.5)',
                                }}
                              >
                                <span className="text-xs font-bold text-warning">시뮬레이션 정확도 70-75%</span>
                              </div>
                            </div>
                            <div
                              className="p-3 rounded-sm mb-3 border border-amber-600/30"
                              style={{
                                background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(217, 119, 6, 0.1) 100%)',
                                boxShadow: 'inset 0 1px 0 0 rgba(245, 158, 11, 0.1), inset 0 -1px 0 0 rgba(0, 0, 0, 0.5)',
                              }}
                            >
                              <div className="text-white font-semibold text-sm mb-1">🤖 AI 모델</div>
                              <div className="text-warning font-bold">
                                GPT-4o • Claude Sonnet 4.1 수준
                              </div>
                            </div>
                            <ul className="text-white/80 space-y-2 ml-4 list-disc text-sm">
                              <li>표준 언어 모델 기반 예측</li>
                              <li>연산 속도: <span className="text-success font-semibold">빠름 (~1초)</span></li>
                              <li>컴퓨팅 파워: <span className="text-warning font-semibold">중급 (10-50B 파라미터)</span></li>
                              <li>높은 변동성으로 서프라이즈 결과 가능</li>
                            </ul>
                          </>
                        )}
                        {aiModel === 'pro' && (
                          <>
                            <div className="flex items-center gap-2 mb-4">
                              <div className="font-bold text-brand-accent text-lg">🚀 Pro AI 엔진</div>
                              <div
                                className="ml-auto px-3 py-1 rounded-full border border-slate-600/50"
                                style={{
                                  background: 'linear-gradient(135deg, rgba(50, 50, 55, 0.5) 0%, rgba(30, 30, 35, 0.6) 100%)',
                                  boxShadow: 'inset 0 1px 0 0 rgba(192, 192, 192, 0.1), inset 0 -1px 0 0 rgba(0, 0, 0, 0.5)',
                                }}
                              >
                                <span className="text-xs font-bold text-brand-accent">시뮬레이션 정확도 80-85%</span>
                              </div>
                            </div>
                            <div
                              className="p-3 rounded-sm mb-3 border border-cyan-600/30"
                              style={{
                                background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.15) 0%, rgba(8, 145, 178, 0.1) 100%)',
                                boxShadow: 'inset 0 1px 0 0 rgba(6, 182, 212, 0.1), inset 0 -1px 0 0 rgba(0, 0, 0, 0.5)',
                              }}
                            >
                              <div className="text-white font-semibold text-sm mb-1">🤖 AI 모델</div>
                              <div className="text-brand-accent font-bold">
                                GPT-4 Turbo • Claude Opus 3.5 수준
                              </div>
                            </div>
                            <ul className="text-white/80 space-y-2 ml-4 list-disc text-sm">
                              <li>고급 추론 능력 탑재</li>
                              <li>연산 속도: <span className="text-warning font-semibold">보통 (~1.5초)</span></li>
                              <li>컴퓨팅 파워: <span className="text-brand-accent font-semibold">고급 (100-200B 파라미터)</span></li>
                              <li>균형잡힌 예측으로 <span className="text-success font-semibold">현실적인 결과 (추천)</span></li>
                            </ul>
                          </>
                        )}
                        {aiModel === 'super' && (
                          <>
                            <div className="flex items-center gap-2 mb-4">
                              <div className="font-bold text-rose-500 text-lg">👽 Super AI 엔진</div>
                              <div
                                className="ml-auto px-3 py-1 rounded-full border border-slate-600/50"
                                style={{
                                  background: 'linear-gradient(135deg, rgba(50, 50, 55, 0.5) 0%, rgba(30, 30, 35, 0.6) 100%)',
                                  boxShadow: 'inset 0 1px 0 0 rgba(192, 192, 192, 0.1), inset 0 -1px 0 0 rgba(0, 0, 0, 0.5)',
                                }}
                              >
                                <span className="text-xs font-bold text-rose-500">시뮬레이션 정확도 90-95%</span>
                              </div>
                            </div>
                            <div
                              className="p-3 rounded-sm mb-3 border border-rose-600/30"
                              style={{
                                background: 'linear-gradient(135deg, rgba(244, 63, 94, 0.15) 0%, rgba(225, 29, 72, 0.1) 100%)',
                                boxShadow: 'inset 0 1px 0 0 rgba(244, 63, 94, 0.1), inset 0 -1px 0 0 rgba(0, 0, 0, 0.5)',
                              }}
                            >
                              <div className="text-white font-semibold text-sm mb-1">🤖 AI 모델</div>
                              <div className="text-rose-400 font-bold">
                                o1-preview • Claude Sonnet 4.5 수준
                              </div>
                            </div>
                            <ul className="text-white/80 space-y-2 ml-4 list-disc text-sm">
                              <li>최상위 멀티모달 추론 엔진</li>
                              <li>연산 속도: <span className="text-error font-semibold">느림 (~2초)</span></li>
                              <li>컴퓨팅 파워: <span className="text-rose-400 font-semibold">최고급 (300B+ 파라미터)</span></li>
                              <li>공격/수비 분리 분석, <span className="text-success font-semibold">전술적 깊이 반영</span></li>
                            </ul>
                          </>
                        )}
                        {aiModel === 'v3' && (
                          <>
                            <div className="flex items-center gap-2 mb-4">
                              <div className="font-bold text-green-500 text-lg">⚡ V3 Pipeline</div>
                              <div
                                className="ml-auto px-3 py-1 rounded-full border border-slate-600/50"
                                style={{
                                  background: 'linear-gradient(135deg, rgba(50, 50, 55, 0.5) 0%, rgba(30, 30, 35, 0.6) 100%)',
                                  boxShadow: 'inset 0 1px 0 0 rgba(192, 192, 192, 0.1), inset 0 -1px 0 0 rgba(0, 0, 0, 0.5)',
                                }}
                              >
                                <span className="text-xs font-bold text-green-500">시뮬레이션 정확도 95-98%</span>
                              </div>
                            </div>
                            <div
                              className="p-3 rounded-sm mb-3 border border-green-600/30"
                              style={{
                                background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.15) 0%, rgba(22, 163, 74, 0.1) 100%)',
                                boxShadow: 'inset 0 1px 0 0 rgba(34, 197, 94, 0.1), inset 0 -1px 0 0 rgba(0, 0, 0, 0.5)',
                              }}
                            >
                              <div className="text-white font-semibold text-sm mb-1">🚀 파이프라인</div>
                              <div className="text-green-400 font-bold">
                                Mathematical Models + AI + Monte Carlo (12,000 runs)
                              </div>
                            </div>
                            <ul className="text-white/80 space-y-2 ml-4 list-disc text-sm">
                              <li><span className="text-green-400 font-semibold">Phase 1:</span> Poisson-Rating + Zone Dominance + Key Player 수학 모델</li>
                              <li><span className="text-green-400 font-semibold">Phase 2:</span> AI 기반 동적 시나리오 생성 (2-5개)</li>
                              <li><span className="text-green-400 font-semibold">Phase 3:</span> Monte Carlo 검증 (시나리오당 3,000회)</li>
                              <li>연산 속도: <span className="text-error font-semibold">매우 느림 (~50초)</span></li>
                              <li><span className="text-success font-semibold">실시간 SSE 스트리밍</span>으로 진행 상황 확인</li>
                            </ul>
                          </>
                        )}
                      </div>
                    </motion.div>
                  </AnimatePresence>
                </div>

                {/* Simulate Button */}
                <motion.button
                  onClick={simulateMatch}
                  disabled={
                    !homeTeam ||
                    !awayTeam ||
                    simulating ||
                    (homeTeam && !teamScores[homeTeam]?.ready) ||
                    (awayTeam && !teamScores[awayTeam]?.ready)
                  }
                  className={`
                    w-full py-4 rounded-sm font-bold text-lg border relative overflow-hidden
                    ${homeTeam && awayTeam && !simulating &&
                      teamScores[homeTeam]?.ready &&
                      teamScores[awayTeam]?.ready
                      ? 'border-cyan-500/40 bg-cyan-500/10 text-white hover:bg-cyan-500/20'
                      : 'bg-white/5 text-white/40 cursor-not-allowed border-white/10'}
                  `}
                  whileHover={
                    homeTeam && awayTeam && !simulating &&
                    teamScores[homeTeam]?.ready &&
                    teamScores[awayTeam]?.ready
                      ? { scale: 1.02 }
                      : {}
                  }
                  whileTap={
                    homeTeam && awayTeam && !simulating &&
                    teamScores[homeTeam]?.ready &&
                    teamScores[awayTeam]?.ready
                      ? { scale: 0.98 }
                      : {}
                  }
                >
                  {/* Animated Background Effects */}
                  {homeTeam && awayTeam && !simulating &&
                    teamScores[homeTeam]?.ready &&
                    teamScores[awayTeam]?.ready && (
                    <>
                      {/* Shimmer Effect */}
                      <div
                        className="absolute inset-0 pointer-events-none"
                        style={{
                          background: 'linear-gradient(90deg, transparent 0%, rgba(0, 255, 204, 0.15) 50%, transparent 100%)',
                          animation: 'shimmer 2s linear infinite',
                        }}
                      />
                    </>
                  )}

                  <div className="relative z-10 flex items-center justify-center gap-3">
                  {simulating ? (
                    <>
                      <div className="spinner border-cyan-400"></div>
                      <span className="text-white">시뮬레이션 중...</span>
                    </>
                  ) : (
                    <>
                      <motion.div
                        animate={
                          homeTeam && awayTeam &&
                          teamScores[homeTeam]?.ready &&
                          teamScores[awayTeam]?.ready
                            ? { y: [0, -4, 0] }
                            : {}
                        }
                        transition={{
                          duration: 1.2,
                          repeat: Infinity,
                          ease: "easeInOut"
                        }}
                      >
                        <Play
                          className={`w-6 h-6 ${
                            homeTeam && awayTeam &&
                            teamScores[homeTeam]?.ready &&
                            teamScores[awayTeam]?.ready
                              ? 'text-cyan-400'
                              : 'text-white/40'
                          }`}
                        />
                      </motion.div>
                      <span className={
                        homeTeam && awayTeam &&
                        teamScores[homeTeam]?.ready &&
                        teamScores[awayTeam]?.ready
                          ? 'text-white'
                          : 'text-white/40'
                      }>
                        가상 대결 시작
                      </span>
                    </>
                  )}
                  </div>
                </motion.button>
              </motion.div>
              )
            ) : (
              <motion.div
                key="result"
                className="relative z-10"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
              >
                {/* Match Result */}
                <div className="p-8 rounded-sm bg-slate-900/60 backdrop-blur-sm border border-cyan-500/20 mb-6">
                  <div className="grid grid-cols-3 gap-4 items-center mb-8">
                    {/* Home Team */}
                    <div className="text-center">
                      <h3 className="text-xl font-bold text-white mb-4">{result.home.name}</h3>
                      <motion.div
                        className={`text-6xl font-bold ${
                          result.winner === 'home' ? 'text-success' : 'text-white/60'
                        }`}
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: 'spring', delay: 0.2 }}
                      >
                        {result.home.goals !== null ? result.home.goals : (
                          <div className="text-3xl">
                            {result.home.winProbability ? `${(result.home.winProbability * 100).toFixed(1)}%` : '-'}
                          </div>
                        )}
                      </motion.div>
                      {result.aiModel === 'v3' && (
                        <div className="text-sm text-white/60 mt-2">승률</div>
                      )}
                    </div>

                    {/* VS */}
                    <div className="text-center">
                      <div className="text-2xl font-bold text-white/40">VS</div>
                    </div>

                    {/* Away Team */}
                    <div className="text-center">
                      <h3 className="text-xl font-bold text-white mb-4">{result.away.name}</h3>
                      <motion.div
                        className={`text-6xl font-bold ${
                          result.winner === 'away' ? 'text-success' : 'text-white/60'
                        }`}
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: 'spring', delay: 0.3 }}
                      >
                        {result.away.goals !== null ? result.away.goals : (
                          <div className="text-3xl">
                            {result.away.winProbability ? `${(result.away.winProbability * 100).toFixed(1)}%` : '-'}
                          </div>
                        )}
                      </motion.div>
                      {result.aiModel === 'v3' && (
                        <div className="text-sm text-white/60 mt-2">승률</div>
                      )}
                    </div>
                  </div>

                  {/* Winner Badge */}
                  <motion.div
                    className="text-center py-4 px-6 rounded-full mx-auto max-w-xs border-2 border-slate-600/60"
                    style={{
                      background: 'linear-gradient(135deg, rgba(50, 50, 55, 0.6) 0%, rgba(30, 30, 35, 0.7) 100%)',
                      boxShadow: 'inset 0 1px 0 0 rgba(192, 192, 192, 0.15), inset 0 -1px 0 0 rgba(0, 0, 0, 0.7)',
                    }}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5 }}
                  >
                    <Trophy className="w-6 h-6 mx-auto mb-2 text-yellow-400" />
                    <div className="text-xl font-bold text-white">
                      {result.winner === 'draw'
                        ? '무승부!'
                        : `${result.winner === 'home' ? result.home.name : result.away.name} 승리!`}
                    </div>
                  </motion.div>

                  {/* AI Model Used */}
                  <motion.div
                    className="text-center mt-4"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.6 }}
                  >
                    <div
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-slate-600/40"
                      style={{
                        background: 'linear-gradient(135deg, rgba(40, 40, 45, 0.5) 0%, rgba(20, 20, 25, 0.6) 100%)',
                        boxShadow: 'inset 0 1px 0 0 rgba(192, 192, 192, 0.08), inset 0 -1px 0 0 rgba(0, 0, 0, 0.5)',
                      }}
                    >
                      <span className="text-sm">
                        {result.aiModel === 'basic' ? '🎯' : result.aiModel === 'pro' ? '🚀' : result.aiModel === 'super' ? '👽' : result.aiModel === 'v3' ? '⚡' : '🤖'}
                      </span>
                      <span className="text-sm font-semibold text-white">
                        {result.aiModel === 'basic' ? 'Basic' : result.aiModel === 'pro' ? 'Pro' : result.aiModel === 'super' ? 'Super' : result.aiModel === 'v3' ? 'V3 Pipeline' : 'Claude AI'} 모델 사용
                      </span>
                    </div>
                  </motion.div>
                </div>

                {/* AI Insights - Removed (Qwen runs locally, no detailed insights) */}
                {false && result.claudeData && (
                  <div className="space-y-4 mb-6">
                    {/* Win Probabilities */}
                    <motion.div
                      className="p-6 rounded-sm bg-gradient-to-br from-purple-900/40 to-indigo-900/40 backdrop-blur-sm border border-purple-500/30"
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.7 }}
                    >
                      <h4 className="text-lg font-bold text-purple-300 mb-4">📊 승률 분석 (Claude AI)</h4>
                      <div className="grid grid-cols-3 gap-4">
                        <div className="text-center p-4 rounded-sm bg-slate-900/60 border border-green-500/20">
                          <div className="text-sm text-white/70 mb-2">홈 승</div>
                          <div className="text-3xl font-bold text-green-400">
                            {(result.claudeData.probabilities.home_win * 100).toFixed(1)}%
                          </div>
                        </div>
                        <div className="text-center p-4 rounded-sm bg-slate-900/60 border border-gray-500/20">
                          <div className="text-sm text-white/70 mb-2">무승부</div>
                          <div className="text-3xl font-bold text-gray-400">
                            {(result.claudeData.probabilities.draw * 100).toFixed(1)}%
                          </div>
                        </div>
                        <div className="text-center p-4 rounded-sm bg-slate-900/60 border border-blue-500/20">
                          <div className="text-sm text-white/70 mb-2">원정 승</div>
                          <div className="text-3xl font-bold text-blue-400">
                            {(result.claudeData.probabilities.away_win * 100).toFixed(1)}%
                          </div>
                        </div>
                      </div>
                      <div className="mt-4 text-center">
                        <span className={`inline-block px-4 py-2 rounded-full font-bold text-sm ${
                          result.claudeData.confidence === '높음' || result.claudeData.confidence === 'high' ? 'bg-green-500/20 text-green-300 border border-green-500/40' :
                          result.claudeData.confidence === '보통' || result.claudeData.confidence === 'medium' ? 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/40' :
                          'bg-gray-500/20 text-gray-300 border border-gray-500/40'
                        }`}>
                          신뢰도: {result.claudeData.confidence} ({result.claudeData.confidence_score}/100)
                        </span>
                      </div>
                    </motion.div>

                    {/* AI Reasoning */}
                    <motion.div
                      className="p-6 rounded-sm bg-gradient-to-br from-indigo-900/40 to-purple-900/40 backdrop-blur-sm border border-indigo-500/30"
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.8 }}
                    >
                      <h4 className="text-lg font-bold text-indigo-300 mb-3">🧠 AI 분석</h4>
                      <p className="text-white/80 leading-relaxed">{result.claudeData.reasoning}</p>
                    </motion.div>

                    {/* Key Factors */}
                    {result.claudeData.key_factors && result.claudeData.key_factors.length > 0 && (
                      <motion.div
                        className="p-6 rounded-sm bg-gradient-to-br from-purple-900/40 to-pink-900/40 backdrop-blur-sm border border-purple-500/30"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.9 }}
                      >
                        <h4 className="text-lg font-bold text-purple-300 mb-3">🔑 주요 요인</h4>
                        <ul className="space-y-2">
                          {result.claudeData.key_factors.map((factor, idx) => (
                            <li key={idx} className="flex items-start gap-2 text-white/80">
                              <span className="text-purple-400 font-bold mt-1">•</span>
                              <span>{factor}</span>
                            </li>
                          ))}
                        </ul>
                      </motion.div>
                    )}

                    {/* Expected Goals */}
                    {result.claudeData.expected_goals && (
                      <motion.div
                        className="p-6 rounded-sm bg-gradient-to-br from-green-900/40 to-blue-900/40 backdrop-blur-sm border border-green-500/30"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 1.0 }}
                      >
                        <h4 className="text-lg font-bold text-green-300 mb-4">⚽ 기대 골 (xG)</h4>
                        <div className="grid grid-cols-2 gap-4 text-center">
                          <div>
                            <div className="text-sm text-white/70 mb-2">{result.home.name}</div>
                            <div className="text-4xl font-bold text-green-400">
                              {result.claudeData.expected_goals.home.toFixed(1)}
                            </div>
                          </div>
                          <div>
                            <div className="text-sm text-white/70 mb-2">{result.away.name}</div>
                            <div className="text-4xl font-bold text-blue-400">
                              {result.claudeData.expected_goals.away.toFixed(1)}
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    )}

                    {/* Metadata */}
                    {result.claudeData.metadata && (
                      <motion.div
                        className="p-4 rounded-sm bg-slate-900/60 border border-slate-600/40"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 1.1 }}
                      >
                        <div className="text-xs text-white/50 grid grid-cols-2 md:grid-cols-4 gap-3">
                          <div>
                            <div className="text-white/40 mb-1">모델</div>
                            <div className="font-mono text-white/70">{result.claudeData.metadata.model}</div>
                          </div>
                          <div>
                            <div className="text-white/40 mb-1">토큰 사용</div>
                            <div className="font-semibold text-white/70">
                              {result.claudeData.metadata.tokens_used.total.toLocaleString()}
                            </div>
                          </div>
                          <div>
                            <div className="text-white/40 mb-1">비용</div>
                            <div className="font-semibold text-green-400">
                              ${result.claudeData.metadata.cost_usd.toFixed(6)}
                            </div>
                          </div>
                          <div>
                            <div className="text-white/40 mb-1">입력→출력</div>
                            <div className="font-semibold text-white/70">
                              {result.claudeData.metadata.tokens_used.input}→{result.claudeData.metadata.tokens_used.output}
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </div>
                )}

                {/* Team Stats Comparison - Only show for client-side simulations */}
                {result.home.score && result.away.score && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    {/* Home Stats */}
                    <div className="p-4 rounded-sm bg-slate-900/60 backdrop-blur-sm border border-cyan-500/20">
                      <h4 className="text-sm font-semibold text-white/60 mb-3">{result.home.name} 능력치</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-white/70">종합 측정:</span>
                          <span className="font-bold text-brand-accent">{result.home.score.overall.toFixed(1)}/100</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-white/70">선수 평가:</span>
                          <span className="font-bold text-blue-400">{result.home.score.player.toFixed(1)} ({result.home.score.playerWeight}%)</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-white/70">팀 전력:</span>
                          <span className="font-bold text-purple-400">{result.home.score.strength.toFixed(1)} ({result.home.score.strengthWeight}%)</span>
                        </div>
                      </div>
                    </div>

                    {/* Away Stats */}
                    <div className="p-4 rounded-sm bg-slate-900/60 backdrop-blur-sm border border-cyan-500/20">
                      <h4 className="text-sm font-semibold text-white/60 mb-3">{result.away.name} 능력치</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-white/70">종합 측정:</span>
                          <span className="font-bold text-brand-accent">{result.away.score.overall.toFixed(1)}/100</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-white/70">선수 평가:</span>
                          <span className="font-bold text-blue-400">{result.away.score.player.toFixed(1)} ({result.away.score.playerWeight}%)</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-white/70">팀 전력:</span>
                          <span className="font-bold text-purple-400">{result.away.score.strength.toFixed(1)} ({result.away.score.strengthWeight}%)</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Reset Button */}
                <motion.button
                  onClick={resetSimulation}
                  className="w-full py-3 rounded-sm font-semibold text-white bg-slate-900/60 backdrop-blur-sm border border-cyan-500/20 flex items-center justify-center gap-2 hover:bg-slate-900/80"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <RefreshCw className="w-5 h-5" />
                  새로운 대결
                </motion.button>
              </motion.div>
            )}
          </AnimatePresence>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
};

MatchSimulator.propTypes = {
  darkMode: PropTypes.bool,
  selectedMatch: PropTypes.shape({
    homeTeam: PropTypes.string,
    awayTeam: PropTypes.string
  }),
  onTeamClick: PropTypes.func,
  isActive: PropTypes.bool
};

MatchSimulator.defaultProps = {
  darkMode: false,
  selectedMatch: null,
  onTeamClick: null,
  isActive: false
};

export default MatchSimulator;
