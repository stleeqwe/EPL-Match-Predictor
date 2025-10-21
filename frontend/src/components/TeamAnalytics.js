import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BarChart3,
  TrendingUp,
  Award,
  Target,
  AlertCircle,
  Shield,
  Activity,
  Crosshair,
  Brain,
  Heart,
  Gauge,
  Swords,
  Save,
  Check,
  X
} from 'lucide-react';
import { calculateWeightedAverage, DEFAULT_SUB_POSITION } from '../config/positionAttributes';

// 팀 전력 프레임워크
const TEAM_STRENGTH_FRAMEWORK = {
  tactical_organization: {
    name: '전술적 조직력',
    weight: 0.38,
    icon: Brain,
    attributes: ['tactical_understanding', 'positioning_balance', 'attack_to_defense_transition', 'defense_to_attack_transition', 'pressing_organization']
  },
  attacking_efficiency: {
    name: '공격 효율성',
    weight: 0.25,
    icon: Swords,
    attributes: ['buildup_quality', 'pass_network', 'final_third_penetration', 'goal_conversion']
  },
  defensive_stability: {
    name: '수비 안정성',
    weight: 0.22,
    icon: Shield,
    attributes: ['backline_organization', 'central_control', 'flank_defense', 'counter_prevention']
  },
  physicality: {
    name: '피지컬 & 체력',
    weight: 0.08,
    icon: Gauge,
    attributes: ['team_stamina', 'speed_balance']
  },
  psychological: {
    name: '심리적 요소',
    weight: 0.07,
    icon: Heart,
    attributes: ['game_control', 'mental_strength', 'team_chemistry']
  }
};

// 포지션 설정
const POSITION_CONFIG = {
  GK: { name: '골키퍼', icon: Target, color: 'rgb(168, 85, 247)' },
  DF: { name: '수비수', icon: Shield, color: 'rgb(59, 130, 246)' },
  MF: { name: '미드필더', icon: Activity, color: 'rgb(34, 197, 94)' },
  FW: { name: '공격수', icon: Crosshair, color: 'rgb(239, 68, 68)' }
};

/**
 * TeamAnalytics Component - Clean & Unified Design
 */
const TeamAnalytics = ({
  team,
  players = [],
  playerRatings = {},
  darkMode = false
}) => {
  const [analytics, setAnalytics] = useState({
    teamAverage: 0,
    positionAverages: {},
    topPlayers: [],
    weakestAreas: []
  });
  const [teamStrength, setTeamStrength] = useState({
    overall: 0,
    categories: {}
  });
  const [playerWeight, setPlayerWeight] = useState(50);
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState(null); // 'success', 'error', null

  useEffect(() => {
    if (players.length > 0) {
      calculateAnalytics();
    }
  }, [players, playerRatings]);

  useEffect(() => {
    if (team) {
      loadTeamStrength();
      loadSavedWeightFromBackend();
    }
  }, [team]);

  // 🔧 자동 저장: playerRatings나 teamStrength가 변경될 때마다 overall score 자동 저장
  useEffect(() => {
    const autoSaveOverallScore = async () => {
      // 팀이 있고, 선수 평가 데이터가 있을 때만 저장
      if (!team || analytics.teamAverage === 0) return;

      // 너무 자주 저장되지 않도록 debounce 효과 (500ms 대기)
      const timeoutId = setTimeout(async () => {
        try {
          const scores = calculateOverallScore();
          const dataToSave = {
            overallScore: scores.overall,
            playerScore: scores.playerScore,
            strengthScore: scores.strengthScore,
            playerWeight: playerWeight,
            strengthWeight: 100 - playerWeight
          };

          const response = await fetch(`http://localhost:5001/api/teams/${encodeURIComponent(team)}/overall_score`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(dataToSave)
          });

          if (response.ok) {
            console.log(`✅ Auto-saved overall score for ${team}:`, scores.overall.toFixed(1));
          }
        } catch (error) {
          console.warn('Failed to auto-save overall score:', error);
        }
      }, 500);

      return () => clearTimeout(timeoutId);
    };

    autoSaveOverallScore();
  }, [team, analytics.teamAverage, teamStrength.overall, playerWeight]);

  const loadTeamStrength = async () => {
    try {
      // 🔧 Backend API에서 먼저 로드 시도
      const response = await fetch(`http://localhost:5001/api/teams/${encodeURIComponent(team)}/strength`);
      if (response.ok) {
        const result = await response.json();
        if (result.success && result.data && result.data.ratings) {
          const ratings = result.data.ratings;
          const categories = {};
          let overallWeightedSum = 0;
          let overallTotalWeight = 0;

          Object.entries(TEAM_STRENGTH_FRAMEWORK).forEach(([key, category]) => {
            const categoryRatings = category.attributes
              .map(attrKey => ratings[attrKey])
              .filter(val => typeof val === 'number' && val >= 0);

            if (categoryRatings.length > 0) {
              const avg = categoryRatings.reduce((sum, val) => sum + val, 0) / categoryRatings.length;
              categories[key] = avg;
              overallWeightedSum += avg * category.weight;
              overallTotalWeight += category.weight;
            } else {
              categories[key] = 0;
            }
          });

          const overall = overallTotalWeight > 0 ? overallWeightedSum / overallTotalWeight : 0;
          setTeamStrength({ overall, categories });
          console.log(`✅ Loaded team strength from backend for ${team}`);
          return;
        }
      }
    } catch (error) {
      console.warn('Failed to load team strength from backend, trying localStorage:', error);
    }

    // Fallback to localStorage
    const saved = localStorage.getItem(`team_strength_${team}`);
    if (saved) {
      const ratings = JSON.parse(saved);
      const categories = {};
      let overallWeightedSum = 0;
      let overallTotalWeight = 0;

      Object.entries(TEAM_STRENGTH_FRAMEWORK).forEach(([key, category]) => {
        const categoryRatings = category.attributes
          .map(attrKey => ratings[attrKey])
          .filter(val => typeof val === 'number' && val >= 0);

        if (categoryRatings.length > 0) {
          const avg = categoryRatings.reduce((sum, val) => sum + val, 0) / categoryRatings.length;
          categories[key] = avg;
          overallWeightedSum += avg * category.weight;
          overallTotalWeight += category.weight;
        } else {
          categories[key] = 0;
        }
      });

      const overall = overallTotalWeight > 0 ? overallWeightedSum / overallTotalWeight : 0;
      setTeamStrength({ overall, categories });
      console.log(`⚠️ Loaded team strength from localStorage for ${team}`);
    } else {
      const categories = {};
      Object.keys(TEAM_STRENGTH_FRAMEWORK).forEach(key => {
        categories[key] = 0;
      });
      setTeamStrength({ overall: 0, categories });
    }
  };

  const loadSavedWeightFromBackend = async () => {
    try {
      const response = await fetch(`http://localhost:5001/api/teams/${encodeURIComponent(team)}/overall_score`);
      if (response.ok) {
        const result = await response.json();
        if (result.success && result.data) {
          setPlayerWeight(result.data.playerWeight || 50);
        }
      }
    } catch (e) {
      console.error('Failed to load saved weight from backend:', e);
    }
  };

  const saveOverallScore = async () => {
    if (!team) return;

    setSaving(true);
    setSaveStatus(null);

    try {
      const scores = calculateOverallScore();
      const dataToSave = {
        overallScore: scores.overall,
        playerScore: scores.playerScore,
        strengthScore: scores.strengthScore,
        playerWeight: playerWeight,
        strengthWeight: 100 - playerWeight
      };

      const response = await fetch(`http://localhost:5001/api/teams/${encodeURIComponent(team)}/overall_score`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(dataToSave)
      });

      if (!response.ok) {
        throw new Error('Failed to save overall score');
      }

      const result = await response.json();
      if (result.success) {
        setSaveStatus('success');
        console.log('✅ Successfully saved overall score to backend:', result);

        // 성공 메시지 3초 후 자동 제거
        setTimeout(() => setSaveStatus(null), 3000);
      } else {
        throw new Error('Server returned unsuccessful response');
      }
    } catch (error) {
      console.error('Error saving overall score:', error);
      setSaveStatus('error');

      // 에러 메시지 5초 후 자동 제거
      setTimeout(() => setSaveStatus(null), 5000);
    } finally {
      setSaving(false);
    }
  };

  const normalizePosition = (position) => {
    if (!position) return null;
    const pos = position.toUpperCase();
    if (pos.includes('GOALKEEPER') || pos.includes('GK')) return 'GK';
    if (pos.includes('DEFENDER') || pos.includes('BACK') || pos === 'DF') return 'DF';
    if (pos.includes('FORWARD') || pos.includes('STRIKER') || pos.includes('ATTACKER') || pos === 'FW') return 'FW';
    if (pos.includes('MIDFIELD') || pos === 'MF') return 'MF';
    if (['GK', 'DF', 'MF', 'FW'].includes(pos)) return pos;
    return null;
  };

  const getPlayerAverage = (playerId, playerPosition) => {
    const ratings = playerRatings[playerId];
    if (!ratings || Object.keys(ratings).length === 0) return 0;
    const normalizedPos = normalizePosition(playerPosition) || playerPosition;
    let subPosition = ratings._subPosition || DEFAULT_SUB_POSITION[normalizedPos];

    // 🔧 Fix: Remove numeric suffixes from subPosition (CB1 → CB, CM2 → CM, etc.)
    if (subPosition && typeof subPosition === 'string') {
      subPosition = subPosition.replace(/\d+$/, '');
    }

    return calculateWeightedAverage(ratings, subPosition) || 0;
  };

  const calculateAnalytics = () => {
    const positionGroups = { GK: [], DF: [], MF: [], FW: [] };
    const playerAverages = [];

    players.forEach(player => {
      const avg = getPlayerAverage(player.id, player.position);
      const normalizedPos = normalizePosition(player.position);

      if (avg > 0 && normalizedPos) {
        playerAverages.push({ ...player, average: avg, normalizedPosition: normalizedPos });
        positionGroups[normalizedPos].push(avg);
      }
    });

    const teamAvg = playerAverages.length > 0
      ? playerAverages.reduce((sum, p) => sum + p.average, 0) / playerAverages.length
      : 0;

    const posAvgs = {};
    Object.keys(positionGroups).forEach(pos => {
      const values = positionGroups[pos];
      posAvgs[pos] = values.length > 0
        ? values.reduce((sum, val) => sum + val, 0) / values.length
        : 0;
    });

    const topPlayers = playerAverages
      .sort((a, b) => b.average - a.average)
      .slice(0, 5);

    const weakestAreas = Object.entries(posAvgs)
      .sort((a, b) => a[1] - b[1])
      .filter(([_, avg]) => avg > 0)
      .slice(0, 2);

    setAnalytics({
      teamAverage: teamAvg,
      positionAverages: posAvgs,
      topPlayers,
      weakestAreas
    });
  };

  const calculateOverallScore = () => {
    const playerScore = (analytics.teamAverage / 5) * 100;
    const strengthScore = (teamStrength.overall / 5) * 100;
    const teamStrengthWeight = 100 - playerWeight;
    const overallScore = (playerScore * playerWeight / 100) + (strengthScore * teamStrengthWeight / 100);

    return { overall: overallScore, playerScore, strengthScore };
  };

  const scores = calculateOverallScore();

  if (!team || players.length === 0) {
    return (
      <div className="bg-slate-900/80 border border-slate-700 rounded p-12 text-center">
        <BarChart3 className="w-16 h-16 text-slate-500 mx-auto mb-4" />
        <p className="text-slate-400">팀 데이터를 불러오는 중...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 종합 측정 */}
      <section className="bg-slate-900/80 border border-slate-700 rounded p-6">
        <h2 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
          <Gauge className="w-5 h-5 text-cyan-400" />
          종합 측정
        </h2>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 종합 점수 */}
          <div className="text-center">
            <div className="text-sm text-slate-400 mb-2">종합 점수</div>
            <div className="text-6xl font-bold text-cyan-400 mb-3">
              {scores.overall.toFixed(1)}
            </div>
            <div className="text-sm text-slate-500">/ 100점</div>
          </div>

          {/* 가중치 조정 */}
          <div className="lg:col-span-2">
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="bg-slate-800/50 rounded p-4 text-center">
                <div className="text-xs text-slate-400 mb-1">선수 평가</div>
                <div className="text-2xl font-bold text-cyan-400">{playerWeight}%</div>
              </div>
              <div className="bg-slate-800/50 rounded p-4 text-center">
                <div className="text-xs text-slate-400 mb-1">팀 전력</div>
                <div className="text-2xl font-bold text-violet-400">{100 - playerWeight}%</div>
              </div>
            </div>

            <input
              type="range"
              min="0"
              max="100"
              value={playerWeight}
              onChange={(e) => setPlayerWeight(parseInt(e.target.value))}
              className="w-full h-2 bg-slate-700 rounded-full appearance-none cursor-pointer"
              style={{
                background: `linear-gradient(to right, rgb(6, 182, 212) 0%, rgb(6, 182, 212) ${playerWeight}%, rgb(51, 65, 85) ${playerWeight}%, rgb(51, 65, 85) 100%)`
              }}
            />

            <div className="grid grid-cols-2 gap-4 mt-4">
              <div className="text-center">
                <div className="text-xs text-slate-400 mb-1">선수 평가 점수</div>
                <div className="text-xl font-bold text-cyan-400">{scores.playerScore.toFixed(1)}</div>
              </div>
              <div className="text-center">
                <div className="text-xs text-slate-400 mb-1">팀 전력 점수</div>
                <div className="text-xl font-bold text-violet-400">{scores.strengthScore.toFixed(1)}</div>
              </div>
            </div>
          </div>
        </div>

        {/* 저장 버튼 */}
        <div className="mt-6 flex items-center justify-center gap-4">
          <motion.button
            onClick={saveOverallScore}
            disabled={saving || !team || analytics.teamAverage === 0}
            className={`
              px-6 py-3 rounded-lg font-bold text-white flex items-center gap-2 transition-all
              ${saving || !team || analytics.teamAverage === 0
                ? 'bg-slate-600 cursor-not-allowed opacity-50'
                : 'bg-cyan-500 hover:bg-cyan-600 active:scale-95'
              }
            `}
            whileHover={!saving && team && analytics.teamAverage > 0 ? { scale: 1.05 } : {}}
            whileTap={!saving && team && analytics.teamAverage > 0 ? { scale: 0.95 } : {}}
          >
            {saving ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>저장 중...</span>
              </>
            ) : (
              <>
                <Save className="w-5 h-5" />
                <span>종합점수 저장</span>
              </>
            )}
          </motion.button>

          {/* 상태 메시지 */}
          <AnimatePresence>
            {saveStatus === 'success' && (
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 10 }}
                className="flex items-center gap-2 text-green-400 font-semibold"
              >
                <Check className="w-5 h-5" />
                <span>저장 완료!</span>
              </motion.div>
            )}
            {saveStatus === 'error' && (
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 10 }}
                className="flex items-center gap-2 text-red-400 font-semibold"
              >
                <X className="w-5 h-5" />
                <span>저장 실패</span>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </section>

      {/* 선수 능력치 분석 */}
      <section>
        <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <Award className="w-5 h-5 text-cyan-400" />
          선수 능력치 분석
        </h2>

        <div className="grid grid-cols-5 gap-4">
          {/* 팀 평균 */}
          <div className="col-span-5 md:col-span-1 bg-slate-900/80 border border-slate-700 rounded p-6">
            <div className="text-sm text-slate-400 mb-2">팀 평균</div>
            <div className="text-5xl font-bold text-cyan-400 mb-3">
              {analytics.teamAverage.toFixed(2)}
            </div>
            <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-cyan-500"
                style={{ width: `${(analytics.teamAverage / 5) * 100}%` }}
              />
            </div>
          </div>

          {/* 포지션별 */}
          {['GK', 'DF', 'MF', 'FW'].map(pos => {
            const config = POSITION_CONFIG[pos];
            const Icon = config.icon;
            const avg = analytics.positionAverages[pos] || 0;

            return (
              <div key={pos} className="bg-slate-900/80 border border-slate-700 rounded p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Icon className="w-4 h-4" style={{ color: config.color }} />
                  <div className="text-xs text-slate-400">{config.name}</div>
                </div>
                <div className="text-3xl font-bold mb-2" style={{ color: config.color }}>
                  {avg.toFixed(2)}
                </div>
                <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full"
                    style={{
                      width: `${(avg / 5) * 100}%`,
                      backgroundColor: config.color
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* 상세 분석 */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 최고 능력치 선수 */}
        <div className="bg-slate-900/80 border border-slate-700 rounded p-6">
          <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-cyan-400" />
            최고 능력치 선수
          </h3>
          <div className="space-y-2">
            {analytics.topPlayers.map((player, index) => {
              const pos = player.normalizedPosition || player.position;
              const config = POSITION_CONFIG[pos] || POSITION_CONFIG.MF;
              const Icon = config.icon;

              return (
                <div key={player.id} className="flex items-center justify-between p-3 bg-slate-800/50 rounded">
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                      index === 0 ? 'bg-yellow-500 text-slate-900' :
                      index === 1 ? 'bg-slate-400 text-slate-900' :
                      index === 2 ? 'bg-orange-500 text-slate-900' :
                      'bg-slate-700 text-slate-300'
                    }`}>
                      #{index + 1}
                    </div>
                    <div>
                      <div className="text-sm font-medium text-white">{player.name}</div>
                      <div className="text-xs text-slate-400 flex items-center gap-1">
                        <Icon className="w-3 h-3" style={{ color: config.color }} />
                        {config.name}
                      </div>
                    </div>
                  </div>
                  <div className="text-xl font-bold" style={{ color: config.color }}>
                    {player.average.toFixed(2)}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* 포지션별 능력치 차트 */}
        <div className="bg-slate-900/80 border border-slate-700 rounded p-6">
          <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-cyan-400" />
            포지션별 능력치
          </h3>
          <div className="space-y-4">
            {Object.entries(analytics.positionAverages)
              .filter(([_, avg]) => avg > 0)
              .sort((a, b) => b[1] - a[1])
              .map(([pos, avg]) => {
                const config = POSITION_CONFIG[pos];
                const Icon = config.icon;

                return (
                  <div key={pos}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2 text-sm">
                        <Icon className="w-4 h-4" style={{ color: config.color }} />
                        <span className="text-white">{config.name}</span>
                      </div>
                      <span className="text-sm font-bold" style={{ color: config.color }}>
                        {avg.toFixed(2)}
                      </span>
                    </div>
                    <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full"
                        style={{
                          width: `${(avg / 5) * 100}%`,
                          backgroundColor: config.color
                        }}
                      />
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      </section>

      {/* 팀 전력 분석 */}
      <section>
        <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5 text-violet-400" />
          팀 전력 분석
        </h2>

        {/* 종합 팀 전력 */}
        <div className="bg-slate-900/80 border border-slate-700 rounded p-6 mb-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-slate-400 mb-1">종합 팀 전력</div>
              <div className="text-xs text-slate-500">5개 영역 가중 평균</div>
            </div>
            <div className="text-5xl font-bold text-violet-400">
              {teamStrength.overall.toFixed(2)}
            </div>
          </div>
          <div className="mt-4 h-3 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-violet-500"
              style={{ width: `${(teamStrength.overall / 5) * 100}%` }}
            />
          </div>
        </div>

        {/* 카테고리 */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {Object.entries(TEAM_STRENGTH_FRAMEWORK).map(([key, category]) => {
            const score = teamStrength.categories[key] || 0;
            const Icon = category.icon;

            return (
              <div key={key} className="bg-slate-900/80 border border-slate-700 rounded p-4">
                <div className="flex items-center justify-between mb-2">
                  <Icon className="w-4 h-4 text-slate-400" />
                  <span className="text-xs text-slate-500">{Math.round(category.weight * 100)}%</span>
                </div>
                <div className="text-xs text-slate-400 mb-2 h-8">
                  {category.name}
                </div>
                <div className="text-2xl font-bold text-white mb-2">
                  {score.toFixed(2)}
                </div>
                <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-violet-500"
                    style={{ width: `${(score / 5) * 100}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* 개선 제안 */}
      {analytics.weakestAreas.length > 0 && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
            <div>
              <div className="text-sm font-bold text-amber-400 mb-1">개선 제안</div>
              <div className="text-sm text-slate-300">
                <span className="font-medium text-amber-300">
                  {analytics.weakestAreas.map(([pos]) => POSITION_CONFIG[pos]?.name || pos).join(', ')}
                </span>
                {' '}포지션의 능력치가 상대적으로 낮습니다. 해당 포지션 선수들의 평가를 검토해보세요.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TeamAnalytics;
