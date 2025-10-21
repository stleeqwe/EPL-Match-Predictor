import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { motion } from 'framer-motion';
import { Loader } from 'lucide-react';
import Standings from './Standings';
import Fixtures from './Fixtures';
import Leaderboard from './Leaderboard';
import LoadingSkeleton from './LoadingSkeleton';
import ErrorState from './ErrorState';
import { eplAPI } from '../services/api';

/**
 * EPLDashboard Component
 * 통합 로딩 관리로 깜빡임 최소화
 */
const EPLDashboard = ({ darkMode = false, onTeamClick, onMatchSimulatorClick, onMatchPredictionClick, onPlayerClick }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [hasLoadedOnce, setHasLoadedOnce] = useState(false); // 🔧 최초 로딩 완료 추적
  const [data, setData] = useState({
    fixtures: [],
    standings: [],
    leaderboard: null
  });

  useEffect(() => {
    // 최초 1회만 데이터 로드
    if (!hasLoadedOnce) {
      fetchAllData();
    }
  }, [hasLoadedOnce]);

  const fetchAllData = async () => {
    try {
      setLoading(true);
      setError(null);

      // 🚀 3개 API 병렬 호출 (Promise.all)
      const [fixturesRes, standingsRes, leaderboardRes] = await Promise.all([
        eplAPI.getFixtures(),
        eplAPI.getStandings(),
        eplAPI.getLeaderboard()
      ]);

      setData({
        fixtures: fixturesRes.fixtures || [],
        standings: standingsRes.standings || [],
        leaderboard: leaderboardRes
      });
      setHasLoadedOnce(true); // 🔧 최초 로딩 완료 표시
    } catch (err) {
      console.error('❌ Dashboard data fetch failed:', err);
      setError('대시보드 데이터를 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  // 로딩 중
  if (loading) {
    return (
      <div className="py-4 min-h-screen">
        <div className="container-custom">
          <div className="bg-slate-900/60 backdrop-blur-sm border border-cyan-500/20 rounded-sm shadow-lg p-8">
            <div className="flex items-center gap-3 mb-6">
              <Loader className="w-6 h-6 text-brand-accent animate-spin" />
              <h2 className="text-2xl font-bold text-white">대시보드 로딩 중...</h2>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <div>
                <LoadingSkeleton type="list" count={5} />
              </div>
              <div className="lg:col-span-2 space-y-4">
                <LoadingSkeleton type="table" count={10} />
                <LoadingSkeleton type="list" count={5} />
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 에러 발생
  if (error) {
    return (
      <div className="py-4 min-h-screen">
        <div className="container-custom">
          <div className="bg-slate-900/60 backdrop-blur-sm border border-cyan-500/20 rounded-sm shadow-lg">
            <ErrorState
              type="network"
              title="대시보드 로드 실패"
              message={error}
              onRetry={fetchAllData}
            />
          </div>
        </div>
      </div>
    );
  }

  // 정상 렌더링 (데이터를 props로 전달)
  // 🎬 탭 전환 시마다 애니메이션 실행
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.4, ease: 'easeOut' }
    }
  };

  return (
    <div className="py-4 min-h-screen">
      <div className="container-custom">
        {/* Main Grid */}
        <motion.div
          className="grid grid-cols-1 lg:grid-cols-3 gap-4"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {/* Left: Fixtures */}
          <motion.div variants={itemVariants}>
            <Fixtures
              darkMode={darkMode}
              limit={10}
              onMatchSimulatorClick={onMatchSimulatorClick}
              onMatchPredictionClick={onMatchPredictionClick}
              preloadedData={data.fixtures}
            />
          </motion.div>

          {/* Right: Standings + Leaderboard (2 columns on large screens) */}
          <div className="lg:col-span-2 space-y-4">
            <motion.div variants={itemVariants}>
              <Standings
                darkMode={darkMode}
                onTeamClick={onTeamClick}
                preloadedData={data.standings}
              />
            </motion.div>
            <motion.div variants={itemVariants}>
              <Leaderboard
                darkMode={darkMode}
                onPlayerClick={onPlayerClick}
                preloadedData={data.leaderboard}
              />
            </motion.div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

EPLDashboard.propTypes = {
  darkMode: PropTypes.bool,
  onTeamClick: PropTypes.func,
  onMatchSimulatorClick: PropTypes.func,
  onMatchPredictionClick: PropTypes.func,
  onPlayerClick: PropTypes.func
};

EPLDashboard.defaultProps = {
  darkMode: false,
  onTeamClick: () => {},
  onMatchSimulatorClick: () => {},
  onMatchPredictionClick: () => {},
  onPlayerClick: () => {}
};

// 🚀 React.memo로 불필요한 리렌더링 방지
export default React.memo(EPLDashboard);
