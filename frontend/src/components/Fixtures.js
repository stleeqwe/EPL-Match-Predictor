import React, { useState, useEffect, useMemo } from 'react';
import PropTypes from 'prop-types';
import { motion, AnimatePresence } from 'framer-motion';
import { Calendar, Clock, Trophy, Loader, Swords, Sparkles } from 'lucide-react';
import { eplAPI } from '../services/api';
import LoadingSkeleton from './LoadingSkeleton';
import ErrorState from './ErrorState';
import { getTeamLogo } from '../utils/teamLogos';

/**
 * Fixtures Component - Clean & Minimal Design
 * EPL 경기 일정 및 결과
 * 🔧 preloadedData 지원 (깜빡임 방지)
 * 🎬 탭 전환 시마다 애니메이션 실행
 */
const Fixtures = ({ darkMode = false, limit = 10, onMatchSimulatorClick, onMatchPredictionClick, preloadedData = null }) => {
  const [fixtures, setFixtures] = useState(preloadedData || []);
  const [loading, setLoading] = useState(!preloadedData);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('upcoming'); // 'upcoming' | 'results'

  // 🎬 애니메이션 설정 (항상 실행)
  const shouldAnimate = true;

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.08
      }
    }
  };

  const cardVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.3, ease: 'easeOut' }
    }
  };

  useEffect(() => {
    // preloadedData가 있으면 fetch 스킵
    if (!preloadedData) {
      fetchFixtures();
    }
  }, [preloadedData]);

  const fetchFixtures = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await eplAPI.getFixtures();
      setFixtures(data.fixtures || []);
    } catch (err) {
      console.error('Error:', err);
      setError('경기 일정을 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  // 🚀 useMemo로 계산 최적화 (깜빡임 방지)
  const recentFixtures = useMemo(() =>
    fixtures.filter(f => f.finished).slice(-limit),
    [fixtures, limit]
  );

  const upcomingFixtures = useMemo(() =>
    fixtures.filter(f => !f.finished).slice(0, limit),
    [fixtures, limit]
  );

  // 경기 결과 색상
  const getResultColor = (homeScore, awayScore) => {
    if (homeScore > awayScore) return 'text-success';
    if (homeScore < awayScore) return 'text-error';
    return 'text-warning';
  };

  // 날짜 포맷팅
  const formatDate = (dateString) => {
    if (!dateString) return null;
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.floor((date - now) / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return '오늘';
    if (diffDays === 1) return '내일';
    if (diffDays === -1) return '어제';

    return date.toLocaleDateString('ko-KR', {
      month: 'short',
      day: 'numeric',
      weekday: 'short'
    });
  };

  const formatTime = (dateString) => {
    if (!dateString) return null;
    const date = new Date(dateString);
    return date.toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  };

  // 탭 데이터
  const tabs = [
    { id: 'upcoming', label: '예정된 경기', icon: Calendar, count: upcomingFixtures.length },
    { id: 'results', label: '최근 결과', icon: Trophy, count: recentFixtures.length }
  ];

  if (loading) {
    return (
      <div className="bg-slate-900/60 backdrop-blur-sm border border-cyan-500/20 rounded-sm shadow-lg p-6">
        <div className="flex items-center gap-2 mb-4">
          <Loader className="w-5 h-5 text-brand-accent animate-spin" />
          <h2 className="text-xl font-bold text-white">경기 일정 로딩 중...</h2>
        </div>
        <LoadingSkeleton type="list" count={5} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-slate-900/60 backdrop-blur-sm border border-cyan-500/20 rounded-sm shadow-lg">
        <ErrorState
          type="network"
          title="경기 일정 로드 실패"
          message={error}
          onRetry={fetchFixtures}
        />
      </div>
    );
  }


  return (
    <div className="relative bg-gradient-to-br from-slate-900/80 via-blue-950/60 to-slate-900/80 backdrop-blur-sm border border-cyan-500/20 rounded-sm shadow-lg p-6">
      {/* Tech Grid Pattern */}
      <div
        className="absolute inset-0 opacity-[0.02] pointer-events-none rounded-sm"
        style={{
          backgroundImage: `
            linear-gradient(rgba(6, 182, 212, 0.5) 1px, transparent 1px),
            linear-gradient(90deg, rgba(6, 182, 212, 0.5) 1px, transparent 1px)
          `,
          backgroundSize: '20px 20px'
        }}
      />
      {/* Header */}
      <div className="relative flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-white">경기 일정</h2>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-sm bg-white/5 border border-white/10">
          <div className="w-2 h-2 rounded-full bg-brand-accent animate-pulse"></div>
          <span className="text-xs font-semibold text-white/70">LIVE</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="relative flex gap-2 mb-4">
        {tabs.map(tab => {
          const IconComponent = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                flex-1 px-4 py-2 rounded-sm font-semibold text-sm transition-all
                flex items-center justify-center gap-2
                ${activeTab === tab.id
                  ? 'bg-slate-800 text-cyan-400 border-2 border-cyan-500/60'
                  : 'bg-slate-900/80 text-white/60 hover:bg-slate-800/80 border-2 border-slate-700/40'}
              `}
            >
              <IconComponent className="w-4 h-4" />
              {tab.label}
              <span className="text-xs opacity-70">({tab.count})</span>
            </button>
          );
        })}
      </div>

      {/* Content - 🎬 조건부 애니메이션 적용 */}
      <div>
        {activeTab === 'upcoming' ? (
          <motion.div
            className="relative space-y-3"
            variants={shouldAnimate ? containerVariants : {}}
            initial={shouldAnimate ? "hidden" : false}
            animate={shouldAnimate ? "visible" : false}
          >
            {upcomingFixtures.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-5xl mb-4">📅</div>
                <p className="text-white/60 font-medium">예정된 경기가 없습니다</p>
              </div>
            ) : (
              upcomingFixtures.map((fixture, idx) => (
                <motion.div
                  key={fixture.id}
                  variants={shouldAnimate ? cardVariants : {}}
                >
                  {/* Card */}
                  <div className="bg-white/5 hover:bg-white/10 rounded-sm p-4 border border-white/10 transition-all">
                    {/* Date & Time */}
                    {fixture.kickoff_time && (
                      <div className="flex items-center gap-3 mb-3 pb-3 border-b border-white/10">
                        <div className="flex items-center gap-1.5">
                          <Calendar className="w-4 h-4 text-brand-accent" />
                          <span className="text-sm text-white/70">{formatDate(fixture.kickoff_time)}</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <Clock className="w-4 h-4 text-brand-accent" />
                          <span className="text-sm text-white/70">{formatTime(fixture.kickoff_time)}</span>
                        </div>
                        {fixture.event && (
                          <span className="text-xs text-white/50">GW {fixture.event}</span>
                        )}
                      </div>
                    )}

                    {/* Teams */}
                    <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-4">
                      {/* Home Team */}
                      <div className="flex flex-col items-center gap-2">
                        <div className="w-10 h-10 flex items-center justify-center">
                          <img
                            src={getTeamLogo(fixture.team_h_name)}
                            alt={fixture.team_h_name}
                            className="w-full h-full object-contain"
                            onError={(e) => {
                              e.target.style.display = 'none';
                              e.target.nextSibling.style.display = 'flex';
                            }}
                          />
                          <div className="hidden w-full h-full items-center justify-center text-base font-bold text-white/40">
                            {fixture.team_h_short || '?'}
                          </div>
                        </div>
                        <div className="text-center">
                          <div className="font-semibold text-white text-sm">
                            {fixture.team_h_name}
                          </div>
                        </div>
                      </div>

                      {/* VS */}
                      <div className="px-6">
                        <div className="text-lg font-bold text-white/60">VS</div>
                      </div>

                      {/* Away Team */}
                      <div className="flex flex-col items-center gap-2">
                        <div className="w-10 h-10 flex items-center justify-center">
                          <img
                            src={getTeamLogo(fixture.team_a_name)}
                            alt={fixture.team_a_name}
                            className="w-full h-full object-contain"
                            onError={(e) => {
                              e.target.style.display = 'none';
                              e.target.nextSibling.style.display = 'flex';
                            }}
                          />
                          <div className="hidden w-full h-full items-center justify-center text-base font-bold text-white/40">
                            {fixture.team_a_short || '?'}
                          </div>
                        </div>
                        <div className="text-center">
                          <div className="font-semibold text-white text-sm">
                            {fixture.team_a_name}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="mt-3 pt-3 border-t border-white/10">
                      <div className="grid grid-cols-2 gap-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onMatchSimulatorClick && onMatchSimulatorClick(fixture);
                          }}
                          className="px-3 py-2.5 rounded-sm bg-gradient-to-br from-orange-700 via-orange-800 to-red-900 text-white text-sm font-semibold border-2 border-amber-500/60 hover:border-amber-400 transition-all flex items-center justify-center gap-1.5 hover:scale-[1.02] hover:-translate-y-px active:scale-[0.98]"
                          style={{
                            boxShadow: 'none',
                            transition: 'all 0.3s ease'
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.boxShadow = '0 0 15px rgba(251, 191, 36, 0.4)';
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.boxShadow = 'none';
                          }}
                        >
                          <Swords className="w-4 h-4" />
                          가상대결
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onMatchPredictionClick && onMatchPredictionClick(fixture);
                          }}
                          className="px-3 py-2.5 rounded-sm bg-gradient-to-br from-emerald-700 via-emerald-800 to-teal-900 text-white text-sm font-semibold border-2 border-cyan-500/60 hover:border-cyan-400 transition-all flex items-center justify-center gap-1.5 hover:scale-[1.02] hover:-translate-y-px active:scale-[0.98]"
                          style={{
                            boxShadow: 'none',
                            transition: 'all 0.3s ease'
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.boxShadow = '0 0 15px rgba(34, 211, 238, 0.4)';
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.boxShadow = 'none';
                          }}
                        >
                          <Sparkles className="w-4 h-4" />
                          경기예측
                        </button>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))
            )}
          </motion.div>
        ) : (
          <motion.div
            className="relative space-y-3"
            variants={shouldAnimate ? containerVariants : {}}
            initial={shouldAnimate ? "hidden" : false}
            animate={shouldAnimate ? "visible" : false}
          >
            {recentFixtures.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-5xl mb-4">🏆</div>
                <p className="text-white/60 font-medium">최근 경기 결과가 없습니다</p>
              </div>
            ) : (
              recentFixtures.reverse().map((fixture, idx) => (
                <motion.div
                  key={fixture.id}
                  variants={shouldAnimate ? cardVariants : {}}
                >
                  {/* Card */}
                  <div className="bg-white/5 hover:bg-white/10 rounded-sm p-4 border border-white/10 transition-all">
                    {/* Result Badge - 상단에 배치 */}
                    <div className="flex items-center justify-center gap-3 mb-4 pb-3 border-b border-white/10">
                      <div className="flex items-center gap-1.5">
                        <Trophy className="w-4 h-4 text-success" />
                        <span className="text-sm font-semibold text-success">경기종료</span>
                      </div>
                      {fixture.event && (
                        <>
                          <div className="w-px h-4 bg-white/20"></div>
                          <span className="text-xs text-white/50 font-semibold">GW {fixture.event}</span>
                        </>
                      )}
                    </div>

                    {/* Teams & Score */}
                    <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-4">
                      {/* Home Team */}
                      <div className="flex flex-col items-center gap-2">
                        <div className="w-10 h-10 flex items-center justify-center">
                          <img
                            src={getTeamLogo(fixture.team_h_name)}
                            alt={fixture.team_h_name}
                            className="w-full h-full object-contain"
                            onError={(e) => {
                              e.target.style.display = 'none';
                              e.target.nextSibling.style.display = 'flex';
                            }}
                          />
                          <div className="hidden w-full h-full items-center justify-center text-base font-bold text-white/40">
                            {fixture.team_h_short || '?'}
                          </div>
                        </div>
                        <div className="text-center">
                          <div className={`
                            font-semibold text-sm
                            ${fixture.team_h_score > fixture.team_a_score
                              ? 'text-success'
                              : fixture.team_h_score < fixture.team_a_score
                              ? 'text-white/60'
                              : 'text-white'}
                          `}>
                            {fixture.team_h_name}
                          </div>
                        </div>
                      </div>

                      {/* Score */}
                      <div className="px-6">
                        <div className={`
                          text-3xl font-black
                          ${getResultColor(fixture.team_h_score, fixture.team_a_score)}
                        `}>
                          {fixture.team_h_score} - {fixture.team_a_score}
                        </div>
                      </div>

                      {/* Away Team */}
                      <div className="flex flex-col items-center gap-2">
                        <div className="w-10 h-10 flex items-center justify-center">
                          <img
                            src={getTeamLogo(fixture.team_a_name)}
                            alt={fixture.team_a_name}
                            className="w-full h-full object-contain"
                            onError={(e) => {
                              e.target.style.display = 'none';
                              e.target.nextSibling.style.display = 'flex';
                            }}
                          />
                          <div className="hidden w-full h-full items-center justify-center text-base font-bold text-white/40">
                            {fixture.team_a_short || '?'}
                          </div>
                        </div>
                        <div className="text-center">
                          <div className={`
                            font-semibold text-sm
                            ${fixture.team_a_score > fixture.team_h_score
                              ? 'text-success'
                              : fixture.team_a_score < fixture.team_h_score
                              ? 'text-white/60'
                              : 'text-white'}
                          `}>
                            {fixture.team_a_name}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))
            )}
          </motion.div>
        )}
      </div>
    </div>
  );
};

Fixtures.propTypes = {
  darkMode: PropTypes.bool,
  limit: PropTypes.number,
  onMatchSimulatorClick: PropTypes.func,
  onMatchPredictionClick: PropTypes.func
};

Fixtures.defaultProps = {
  darkMode: false,
  limit: 10,
  onMatchSimulatorClick: null,
  onMatchPredictionClick: null
};

// 🚀 React.memo로 불필요한 리렌더링 방지
export default React.memo(Fixtures);
