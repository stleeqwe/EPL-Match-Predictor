import React, { useState, useEffect, useMemo } from 'react';
import PropTypes from 'prop-types';
import { motion } from 'framer-motion';
import { Trophy, Star, Circle, GitBranch, Shield } from 'lucide-react';
import { eplAPI } from '../services/api';
import { getPlayerPhoto } from '../utils/teamLogos';

/**
 * Leaderboard Component
 * 🔧 preloadedData 지원 (깜빡임 방지)
 * 🎬 탭 전환 시마다 애니메이션 실행
 */
const Leaderboard = ({ darkMode = false, onPlayerClick, preloadedData = null }) => {
  const [leaderboard, setLeaderboard] = useState(preloadedData);
  const [loading, setLoading] = useState(!preloadedData);
  const [activeTab, setActiveTab] = useState('points'); // goals, assists, clean_sheets, points

  // 🎬 애니메이션 설정 (항상 실행)
  const shouldAnimate = true;

  const cardVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: (i) => ({
      opacity: 1,
      y: 0,
      transition: {
        delay: i * 0.05,
        duration: 0.3,
        ease: 'easeOut'
      }
    })
  };

  useEffect(() => {
    // preloadedData가 있으면 fetch 스킵
    if (!preloadedData) {
      fetchLeaderboard();
    }
  }, [preloadedData]);

  const fetchLeaderboard = async () => {
    try {
      setLoading(true);
      const data = await eplAPI.getLeaderboard();
      setLeaderboard(data);
    } catch (err) {
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  // 🔧 tabs를 useMemo 밖으로 이동 (상수이므로)
  const tabs = useMemo(() => [
    { id: 'points', label: 'FPL 포인트', icon: Trophy, key: 'top_points', stat: 'total_points' },
    { id: 'goals', label: '득점', icon: Circle, key: 'top_scorers', stat: 'goals' },
    { id: 'assists', label: '도움', icon: GitBranch, key: 'top_assists', stat: 'assists' },
    { id: 'clean_sheets', label: '클린시트', icon: Shield, key: 'top_clean_sheets', stat: 'clean_sheets' }
  ], []);

  // 🚀 useMemo로 계산 최적화
  const currentTab = useMemo(() =>
    tabs.find(t => t.id === activeTab),
    [activeTab, tabs]
  );

  const players = useMemo(() =>
    leaderboard?.[currentTab.key] || [],
    [leaderboard, currentTab]
  );

  if (loading) {
    return (
      <div className="rounded-sm shadow-lg p-6 bg-slate-900/60 backdrop-blur-sm border border-cyan-500/20">
        <div className="animate-pulse">
          <div className="h-6 bg-white/10 rounded-sm w-1/4 mb-4"></div>
          <div className="space-y-2">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-16 bg-white/5 rounded-sm"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="relative rounded-sm shadow-lg overflow-hidden bg-gradient-to-br from-slate-900/80 via-blue-950/60 to-slate-900/80 backdrop-blur-sm border border-cyan-500/20">
      {/* Tech Grid Pattern */}
      <div
        className="absolute inset-0 opacity-[0.02] pointer-events-none"
        style={{
          backgroundImage: `
            linear-gradient(rgba(6, 182, 212, 0.5) 1px, transparent 1px),
            linear-gradient(90deg, rgba(6, 182, 212, 0.5) 1px, transparent 1px)
          `,
          backgroundSize: '20px 20px'
        }}
      />
      {/* Unified Container */}
      <div className="relative p-6">
        {/* Header */}
        <div className="mb-4">
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <div className="relative">
              <div className="absolute inset-0 bg-brand-accent/30 blur-lg"></div>
              <Star className="relative w-6 h-6 text-brand-accent fill-brand-accent" />
            </div>
            Top Player
          </h2>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6 overflow-x-auto">
          {tabs.map(tab => {
            const IconComponent = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  px-4 py-2 rounded-sm font-semibold whitespace-nowrap transition-all
                  flex items-center gap-2
                  ${activeTab === tab.id
                    ? 'bg-slate-800 text-cyan-400 border-2 border-cyan-500/60'
                    : 'bg-slate-900/80 text-white/60 hover:bg-slate-800/80 border-2 border-slate-700/40'}
                `}
              >
                <IconComponent className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Players List */}
        <div className="relative">
        <div className="space-y-3">
          {players.slice(0, 10).map((player, idx) => {
            const Component = shouldAnimate ? motion.div : 'div';
            return (
              <Component
                key={player.id}
                onClick={() => onPlayerClick && onPlayerClick(player)}
                className="bg-white/5 hover:bg-white/10 rounded-sm p-4 border border-white/10 transition-all flex items-center justify-between group cursor-pointer"
                {...(shouldAnimate ? {
                  custom: idx,
                  variants: cardVariants,
                  initial: "hidden",
                  animate: "visible"
                } : {})}
              >
              {/* Left: Rank + Player Photo + Player Info */}
              <div className="flex items-center gap-4 flex-1 min-w-0">
                {/* Rank */}
                <div className="flex-shrink-0 w-10 text-center">
                  <span className={`
                    text-xl font-bold font-numeric
                    ${idx === 0 ? 'text-lime-400' :
                      idx === 1 ? 'text-orange-400' :
                      idx === 2 ? 'text-yellow-200' :
                      'text-white/60'}
                  `}>
                    {idx + 1}
                  </span>
                </div>

                {/* Player Photo */}
                <div className="flex-shrink-0 w-14 h-14 rounded-full bg-white overflow-hidden border-2 border-white/20">
                  <img
                    src={getPlayerPhoto(player.code, 'small')}
                    alt={player.name}
                    className="w-full h-full object-cover scale-125"
                    style={{ objectPosition: 'center top' }}
                    onError={(e) => {
                      e.target.style.display = 'none';
                      e.target.nextSibling.style.display = 'flex';
                    }}
                  />
                  <div className="hidden w-full h-full items-center justify-center bg-gradient-to-br from-brand-accent/20 to-brand-primary/20 text-white font-bold text-lg">
                    {player.name.charAt(0)}
                  </div>
                </div>

                {/* Player Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 truncate">
                    <span className="font-bold text-xl text-white group-hover:text-brand-accent transition-colors">
                      {player.name}
                    </span>
                    <span className="text-sm text-white/60">
                      {player.team} • {player.position}
                    </span>
                  </div>
                </div>
              </div>

              {/* Right: Stat */}
              <div className={`
                text-3xl font-bold font-numeric flex-shrink-0 ml-4
                ${idx === 0 ? 'text-lime-400' :
                  idx === 1 ? 'text-orange-400' :
                  idx === 2 ? 'text-yellow-200' :
                  'text-white/60'}
              `}>
                {player[currentTab.stat]}
              </div>
            </Component>
          );
          })}
        </div>
      </div>
    </div>
    </div>
  );
};

Leaderboard.propTypes = {
  darkMode: PropTypes.bool,
  onPlayerClick: PropTypes.func
};

Leaderboard.defaultProps = {
  darkMode: false,
  onPlayerClick: null
};

// 🚀 React.memo로 불필요한 리렌더링 방지
export default React.memo(Leaderboard);
