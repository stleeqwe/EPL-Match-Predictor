/**
 * InlineSimulationProgress - V3 Pipeline용 인라인 시뮬레이션 진행 UI
 *
 * 사용자 친화적 설명 중심, 기술 용어 최소화
 */

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Loader2, CheckCircle2, TrendingUp, Users,
  Zap, Target, Award, AlertCircle, ChevronRight,
  Clock, BarChart3, Brain, Activity, Trophy
} from 'lucide-react';
import useSSESimulation from '../hooks/useSSESimulation';

const InlineSimulationProgress = ({ homeTeam, awayTeam, onComplete, onCancel }) => {
  const {
    status,
    currentEvent,
    result,
    error,
    progress,
    scenarios,
    simulationStats,
    getElapsedTime,
    startSimulation,
    cancelSimulation,
    isCompleted,
    hasError
  } = useSSESimulation();

  const [elapsedTime, setElapsedTime] = useState(0);
  const [currentPhase, setCurrentPhase] = useState('준비');
  const [phaseMessage, setPhaseMessage] = useState('시뮬레이션 준비 중...');
  const [insights, setInsights] = useState([]);
  const [probabilities, setProbabilities] = useState(null);

  // Start simulation on mount
  useEffect(() => {
    startSimulation(homeTeam, awayTeam);
  }, [homeTeam, awayTeam, startSimulation]);

  // Update elapsed time
  useEffect(() => {
    const interval = setInterval(() => {
      setElapsedTime(getElapsedTime());
    }, 100);
    return () => clearInterval(interval);
  }, [getElapsedTime]);

  // Handle completion - Don't auto-navigate, show result inline
  // useEffect(() => {
  //   if (isCompleted && result) {
  //     setTimeout(() => {
  //       onComplete(result);
  //     }, 2000);
  //   }
  // }, [isCompleted, result, onComplete]);

  // Update UI based on current event
  useEffect(() => {
    if (!currentEvent) return;

    const eventType = currentEvent.data.stage || currentEvent.type;
    const eventData = currentEvent.data;

    console.log('Current event:', eventType, eventData);

    switch (eventType) {
      case 'started':
        setCurrentPhase('준비');
        setPhaseMessage('시뮬레이션을 시작합니다...');
        break;

      case 'loading_teams':
        setCurrentPhase('데이터 로딩');
        setPhaseMessage('팀 데이터와 선수 정보를 불러오는 중...');
        break;

      case 'teams_loaded':
        setCurrentPhase('데이터 로딩 완료');
        setPhaseMessage(`${homeTeam}와 ${awayTeam}의 선수 능력치 분석 완료`);
        break;

      case 'phase1_started':
        setCurrentPhase('Phase 1: 기초 전력 분석');
        setPhaseMessage('세 가지 수학 모델로 팀 전력을 계산하고 있습니다...');
        setInsights([
          '선수 평점 기반으로 예상 골 수 계산 중',
          '포메이션 구역별 지배력 분석 중',
          '핵심 선수의 영향력 평가 중'
        ]);
        break;

      case 'phase1_complete':
        setCurrentPhase('Phase 1: 분석 완료');
        const probs = eventData.probabilities || {};
        setProbabilities(probs);

        const winner = probs.home_win > probs.away_win ? homeTeam :
                      probs.away_win > probs.home_win ? awayTeam : '무승부';

        setPhaseMessage(`초기 분석 결과: ${winner}가 유리합니다`);
        setInsights([
          `${homeTeam} 승률: ${(probs.home_win * 100).toFixed(0)}%`,
          `무승부 확률: ${(probs.draw * 100).toFixed(0)}%`,
          `${awayTeam} 승률: ${(probs.away_win * 100).toFixed(0)}%`
        ]);
        break;

      case 'phase2_started':
        setCurrentPhase('Phase 2: AI 시나리오 생성');
        setPhaseMessage('AI가 가능한 경기 전개 시나리오를 분석하고 있습니다...');
        setInsights([
          '양 팀의 전술과 선수 특성 분석',
          '공격-수비 밸런스 계산',
          '핵심 선수의 활약 시나리오 구상'
        ]);
        break;

      case 'phase2_complete':
        setCurrentPhase('Phase 2: 시나리오 생성 완료');
        const scenarioCount = eventData.scenario_count || scenarios.length;
        setPhaseMessage(`${scenarioCount}가지 경기 전개 시나리오가 생성되었습니다`);

        const scenarioInsights = (eventData.scenarios || scenarios).slice(0, 3).map((s, i) =>
          `${i + 1}. ${s.name} (${(s.expected_probability * 100).toFixed(0)}% 가능성)`
        );
        setInsights(scenarioInsights);
        break;

      case 'phase3_started':
        setCurrentPhase('Phase 3: 시뮬레이션 검증');
        const totalRuns = eventData.total_runs || 12000;
        setPhaseMessage(`${totalRuns.toLocaleString()}번의 가상 경기를 진행합니다...`);
        setInsights([
          '각 시나리오를 3,000번씩 시뮬레이션',
          '통계적으로 가장 가능성 높은 결과 도출',
          '예상치 못한 변수 확인'
        ]);
        break;

      case 'phase3_complete':
        setCurrentPhase('Phase 3: 검증 완료');
        setPhaseMessage('모든 시뮬레이션이 완료되었습니다');

        const finalProbs = eventData.convergence || probabilities || {};
        setProbabilities(finalProbs);

        setInsights([
          `총 ${(eventData.total_runs || 0).toLocaleString()}번의 가상 경기 진행`,
          `최종 승률: ${homeTeam} ${(finalProbs.home_win * 100).toFixed(0)}% vs ${awayTeam} ${(finalProbs.away_win * 100).toFixed(0)}%`,
          '결과 분석 중...'
        ]);
        break;

      case 'completed':
        setCurrentPhase('✅ 시뮬레이션 완료');
        setPhaseMessage(`분석이 ${elapsedTime}초 만에 완료되었습니다`);
        setInsights([
          '최종 결과를 확인하세요',
          '상세 분석 리포트가 곧 표시됩니다'
        ]);
        break;

      default:
        break;
    }
  }, [currentEvent, homeTeam, awayTeam, scenarios, probabilities, elapsedTime]);

  // Handle error
  if (hasError) {
    return (
      <div className="p-6 rounded-lg bg-red-500/10 border border-red-500/30">
        <div className="flex items-center gap-3 mb-4">
          <AlertCircle className="w-6 h-6 text-red-400" />
          <h3 className="text-xl font-bold text-red-400">시뮬레이션 오류</h3>
        </div>
        <p className="text-white/80 mb-4">{error}</p>
        <button
          onClick={onCancel}
          className="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-colors"
        >
          돌아가기
        </button>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="text-center">
        <div className="flex items-center justify-center gap-3 mb-2">
          <Zap className="w-8 h-8 text-cyan-400" />
          <h2 className="text-2xl font-bold text-white">
            {homeTeam} vs {awayTeam}
          </h2>
        </div>
        <p className="text-white/60">AI 기반 가상 대결 시뮬레이션</p>
      </div>

      {/* Progress Card */}
      <div className="p-6 rounded-lg bg-slate-800/50 backdrop-blur-sm border border-cyan-500/20">
        {/* Current Phase */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              {!isCompleted ? (
                <Loader2 className="w-5 h-5 text-cyan-400 animate-spin" />
              ) : (
                <CheckCircle2 className="w-5 h-5 text-green-400" />
              )}
              <h3 className="text-lg font-bold text-white">{currentPhase}</h3>
            </div>
            <div className="flex items-center gap-2 text-sm text-white/60">
              <Clock className="w-4 h-4" />
              {elapsedTime.toFixed(1)}초
            </div>
          </div>
          <p className="text-white/80">{phaseMessage}</p>
        </div>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-cyan-500 to-blue-500"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
          <div className="mt-2 text-right text-sm text-white/60">
            {progress}%
          </div>
        </div>

        {/* Insights */}
        {insights.length > 0 && (
          <div className="space-y-2">
            <AnimatePresence mode="popLayout">
              {insights.map((insight, index) => (
                <motion.div
                  key={insight}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex items-start gap-2 text-sm"
                >
                  <ChevronRight className="w-4 h-4 text-cyan-400 mt-0.5 flex-shrink-0" />
                  <span className="text-white/70">{insight}</span>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}

        {/* Live Probabilities */}
        {probabilities && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 p-4 rounded-lg bg-slate-900/50 border border-cyan-500/20"
          >
            <div className="flex items-center gap-2 mb-3">
              <BarChart3 className="w-4 h-4 text-cyan-400" />
              <h4 className="text-sm font-semibold text-white">현재 예측 승률</h4>
            </div>
            <div className="space-y-2">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-white/80">{homeTeam}</span>
                  <span className="text-cyan-400 font-semibold">
                    {(probabilities.home_win * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-cyan-500"
                    style={{ width: `${probabilities.home_win * 100}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-white/80">무승부</span>
                  <span className="text-gray-400 font-semibold">
                    {(probabilities.draw * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gray-500"
                    style={{ width: `${probabilities.draw * 100}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-white/80">{awayTeam}</span>
                  <span className="text-blue-400 font-semibold">
                    {(probabilities.away_win * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500"
                    style={{ width: `${probabilities.away_win * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Scenarios Display */}
        {scenarios.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 space-y-2"
          >
            <div className="flex items-center gap-2 mb-2">
              <Brain className="w-4 h-4 text-cyan-400" />
              <h4 className="text-sm font-semibold text-white">생성된 시나리오</h4>
            </div>
            {scenarios.slice(0, 4).map((scenario, index) => (
              <div
                key={scenario.id}
                className="p-3 rounded-lg bg-slate-900/30 border border-slate-700/50"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <div className="text-sm font-medium text-white/90">
                      {index + 1}. {scenario.name}
                    </div>
                  </div>
                  <div className="text-xs text-cyan-400 font-semibold whitespace-nowrap">
                    {((scenario.probability || scenario.expected_probability) * 100).toFixed(0)}%
                  </div>
                </div>
              </div>
            ))}
          </motion.div>
        )}
      </div>

      {/* Stats */}
      {simulationStats.totalSimulations > 0 && (
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
            <div className="flex items-center gap-2 mb-1">
              <Activity className="w-4 h-4 text-cyan-400" />
              <span className="text-xs text-white/60">시뮬레이션 횟수</span>
            </div>
            <div className="text-xl font-bold text-white">
              {simulationStats.totalSimulations.toLocaleString()}
            </div>
          </div>
          <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
            <div className="flex items-center gap-2 mb-1">
              <Target className="w-4 h-4 text-cyan-400" />
              <span className="text-xs text-white/60">분석 시나리오</span>
            </div>
            <div className="text-xl font-bold text-white">
              {simulationStats.scenariosCount || scenarios.length}개
            </div>
          </div>
        </div>
      )}

      {/* Final Results - Show when completed */}
      {isCompleted && result && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6 mt-8 pt-8 border-t border-cyan-500/20"
        >
          {/* Winner Section */}
          <div className="text-center">
            <div className="inline-flex items-center gap-3 px-6 py-3 rounded-full bg-gradient-to-r from-green-500/20 to-cyan-500/20 border border-green-500/40">
              <Trophy className="w-6 h-6 text-yellow-400" />
              <div className="text-xl font-bold text-white">
                {result.probabilities.home_win > result.probabilities.away_win && result.probabilities.home_win > result.probabilities.draw
                  ? `${homeTeam} 승리 예상!`
                  : result.probabilities.away_win > result.probabilities.home_win && result.probabilities.away_win > result.probabilities.draw
                  ? `${awayTeam} 승리 예상!`
                  : '무승부 예상!'}
              </div>
            </div>
          </div>

          {/* Final Probabilities */}
          <div className="p-6 rounded-lg bg-slate-900/50 border border-cyan-500/30">
            <div className="flex items-center gap-2 mb-4">
              <Award className="w-5 h-5 text-cyan-400" />
              <h3 className="text-lg font-bold text-white">최종 승률 분석</h3>
            </div>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-white font-semibold">{homeTeam} 승리</span>
                  <span className="text-cyan-400 font-bold text-lg">
                    {(result.probabilities.home_win * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-cyan-500 to-cyan-400"
                    initial={{ width: 0 }}
                    animate={{ width: `${result.probabilities.home_win * 100}%` }}
                    transition={{ duration: 1, delay: 0.3 }}
                  />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-white font-semibold">무승부</span>
                  <span className="text-gray-400 font-bold text-lg">
                    {(result.probabilities.draw * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-gray-500 to-gray-400"
                    initial={{ width: 0 }}
                    animate={{ width: `${result.probabilities.draw * 100}%` }}
                    transition={{ duration: 1, delay: 0.4 }}
                  />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-white font-semibold">{awayTeam} 승리</span>
                  <span className="text-blue-400 font-bold text-lg">
                    {(result.probabilities.away_win * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-blue-500 to-blue-400"
                    initial={{ width: 0 }}
                    animate={{ width: `${result.probabilities.away_win * 100}%` }}
                    transition={{ duration: 1, delay: 0.5 }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Scenarios Summary */}
          {result.scenarios && result.scenarios.length > 0 && (
            <div className="p-6 rounded-lg bg-slate-900/50 border border-cyan-500/30">
              <div className="flex items-center gap-2 mb-4">
                <Brain className="w-5 h-5 text-cyan-400" />
                <h3 className="text-lg font-bold text-white">시나리오 분석 결과</h3>
              </div>
              <div className="space-y-3">
                {result.scenarios.map((scenario, index) => (
                  <div
                    key={scenario.id}
                    className="p-4 rounded-lg bg-slate-800/50 border border-slate-700/50"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1">
                        <div className="text-sm font-semibold text-white mb-1">
                          {index + 1}. {scenario.name}
                        </div>
                        <div className="text-xs text-white/60">
                          {scenario.events_count}개 이벤트
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-cyan-400">
                          {(scenario.expected_probability * 100).toFixed(1)}%
                        </div>
                        <div className="text-xs text-white/60">발생 확률</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Execution Stats */}
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700/50">
              <div className="flex items-center gap-2 mb-2">
                <Activity className="w-4 h-4 text-cyan-400" />
                <span className="text-xs text-white/60">총 시뮬레이션</span>
              </div>
              <div className="text-2xl font-bold text-white">
                {result.validation?.total_runs?.toLocaleString() || '12,000'}회
              </div>
            </div>
            <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700/50">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="w-4 h-4 text-cyan-400" />
                <span className="text-xs text-white/60">소요 시간</span>
              </div>
              <div className="text-2xl font-bold text-white">
                {result.execution_time?.toFixed(1) || elapsedTime.toFixed(1)}초
              </div>
            </div>
          </div>

          {/* New Match Button */}
          <div className="text-center">
            <button
              onClick={onCancel}
              className="px-8 py-3 bg-gradient-to-r from-cyan-500/20 to-blue-500/20 hover:from-cyan-500/30 hover:to-blue-500/30 border border-cyan-500/40 text-white rounded-lg transition-all font-semibold"
            >
              새로운 대결
            </button>
          </div>
        </motion.div>
      )}

      {/* Cancel Button */}
      {!isCompleted && (
        <div className="text-center">
          <button
            onClick={() => {
              cancelSimulation();
              onCancel();
            }}
            className="px-6 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
          >
            취소
          </button>
        </div>
      )}
    </motion.div>
  );
};

export default InlineSimulationProgress;
