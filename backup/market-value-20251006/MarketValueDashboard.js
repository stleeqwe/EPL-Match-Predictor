import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TrendingUp,
  DollarSign,
  AlertCircle,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Clock,
  Shield,
  Target,
  X
} from 'lucide-react';
import marketValueAPI from '../services/marketValueAPI';
import ValueBetCard from './ValueBetCard';
import OddsComparisonTable from './OddsComparisonTable';

/**
 * MarketValueDashboard - Value Betting 기반 경기 예측 대시보드
 */
const MarketValueDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [selectedMatch, setSelectedMatch] = useState(null);
  const [kellyModalData, setKellyModalData] = useState(null);
  const [kellyResult, setKellyResult] = useState(null);
  const [bankroll, setBankroll] = useState(10000);
  const [expandedSections, setExpandedSections] = useState({
    valueBets: true,
    matches: false,
    settings: false
  });

  // 초기 데이터 로드
  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);

    try {
      // 데모 모드로 데이터 가져오기
      const data = await marketValueAPI.getDashboardData(true);
      setDashboardData(data);

      // 배당률이 없는 경우 체크
      if (!data.matches || data.matches.length === 0) {
        setError('다가오는 EPL 경기의 배당률이 아직 오픈되지 않았습니다.');
      }
    } catch (err) {
      console.error('Dashboard data fetch error:', err);
      setError('데이터를 불러오는 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  // Kelly Criterion 계산
  const handleCalculateKelly = async (valueBet) => {
    setKellyModalData(valueBet);

    try {
      const result = await marketValueAPI.calculateKelly({
        win_probability: valueBet.estimated_probability,
        decimal_odds: valueBet.odds,
        bankroll: bankroll
      });
      setKellyResult(result);
    } catch (err) {
      console.error('Kelly calculation error:', err);
    }
  };

  // 섹션 토글
  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  // 로딩 상태
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <motion.div
          className="text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <motion.div
            className="w-16 h-16 border-4 border-violet-500 border-t-transparent rounded-full mx-auto mb-4"
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          />
          <p className="text-white/60 font-medium">배당률 데이터 로딩 중...</p>
        </motion.div>
      </div>
    );
  }

  // 에러 또는 배당률 미오픈 안내
  if (error || !dashboardData || !dashboardData.matches || dashboardData.matches.length === 0) {
    return (
      <div className="container-custom py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-2xl mx-auto"
        >
          <div className="rounded-2xl bg-gradient-to-br from-amber-500/20 to-orange-600/20 border border-amber-400/40 p-8 text-center">
            <motion.div
              animate={{ scale: [1, 1.1, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              <AlertCircle className="w-16 h-16 text-amber-300 mx-auto mb-4" />
            </motion.div>
            <h2 className="text-2xl font-bold text-white mb-3">
              배당률 미오픈
            </h2>
            <p className="text-white/80 mb-6">
              {error || '다가오는 EPL 경기의 배당률이 아직 오픈되지 않았습니다.'}
            </p>
            <div className="bg-white/10 rounded-xl p-4 mb-6">
              <p className="text-sm text-white/60 mb-2">
                배당률은 일반적으로 경기 시작 1-2일 전에 오픈됩니다.
              </p>
              <p className="text-xs text-white/40">
                다음 게임위크가 가까워지면 다시 확인해주세요.
              </p>
            </div>
            <motion.button
              onClick={fetchDashboardData}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 text-white font-semibold shadow-lg shadow-violet-600/25 transition-all duration-300 flex items-center gap-2 mx-auto"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <RefreshCw className="w-4 h-4" />
              새로고침
            </motion.button>
          </div>

          {/* 데모 데이터 안내 */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="mt-6 rounded-xl bg-white/5 border border-white/10 p-6"
          >
            <div className="flex items-start gap-3">
              <Sparkles className="w-5 h-5 text-violet-400 mt-0.5 flex-shrink-0" />
              <div>
                <h3 className="text-white font-semibold mb-2">데모 모드 안내</h3>
                <p className="text-sm text-white/60 mb-3">
                  현재 데모 모드로 실행 중입니다. 실제 배당률을 받아오려면 The Odds API 키가 필요합니다.
                </p>
                <a
                  href="https://the-odds-api.com/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-violet-300 hover:text-violet-200 underline"
                >
                  The Odds API 키 발급받기 →
                </a>
              </div>
            </div>
          </motion.div>
        </motion.div>
      </div>
    );
  }

  const { matches, value_bets, arbitrage } = dashboardData;
  const valueBetsData = value_bets?.opportunities || [];
  const summary = value_bets?.summary || {};

  return (
    <div className="container-custom py-8">
      {/* 헤더 */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-600 to-purple-700 flex items-center justify-center shadow-lg shadow-violet-600/30">
              <TrendingUp className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-black text-white">Market Value</h1>
              <p className="text-white/60 text-sm">배당률 기반 가치 베팅 분석</p>
            </div>
          </div>
          <motion.button
            onClick={fetchDashboardData}
            className="p-3 rounded-xl bg-white/10 hover:bg-white/20 border border-white/10 transition-colors"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <RefreshCw className="w-5 h-5 text-white" />
          </motion.button>
        </div>
      </motion.div>

      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <StatCard
          icon={Target}
          label="분석된 경기"
          value={matches?.length || 0}
          color="from-blue-500 to-cyan-500"
        />
        <StatCard
          icon={Sparkles}
          label="Value Bets"
          value={summary.total_count || 0}
          color="from-violet-500 to-purple-500"
        />
        <StatCard
          icon={TrendingUp}
          label="평균 Edge"
          value={summary.avg_edge ? `${(summary.avg_edge * 100).toFixed(1)}%` : '-'}
          color="from-emerald-500 to-green-500"
        />
        <StatCard
          icon={Shield}
          label="평균 신뢰도"
          value={summary.avg_confidence ? `${(summary.avg_confidence * 100).toFixed(0)}%` : '-'}
          color="from-amber-500 to-orange-500"
        />
      </div>

      {/* Value Bets 섹션 */}
      <CollapsibleSection
        title="Value Betting 기회"
        icon={Sparkles}
        count={valueBetsData.length}
        isExpanded={expandedSections.valueBets}
        onToggle={() => toggleSection('valueBets')}
      >
        {valueBetsData.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {valueBetsData.map((valueBet, index) => (
              <ValueBetCard
                key={index}
                valueBet={valueBet}
                index={index}
                onCalculateKelly={handleCalculateKelly}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-12 text-white/60">
            <Target className="w-12 h-12 mx-auto mb-3 opacity-40" />
            <p>현재 발견된 Value Bet이 없습니다</p>
            <p className="text-sm mt-2">경기가 가까워지면 더 많은 기회가 생길 수 있습니다</p>
          </div>
        )}
      </CollapsibleSection>

      {/* 경기별 배당률 비교 */}
      <CollapsibleSection
        title="경기별 배당률 비교"
        icon={DollarSign}
        count={matches?.length || 0}
        isExpanded={expandedSections.matches}
        onToggle={() => toggleSection('matches')}
      >
        <div className="space-y-4">
          {matches?.map((match, index) => (
            <OddsComparisonTable key={index} match={match} />
          ))}
        </div>
      </CollapsibleSection>

      {/* Kelly Calculator 모달 */}
      <AnimatePresence>
        {kellyModalData && (
          <KellyModal
            valueBet={kellyModalData}
            kellyResult={kellyResult}
            bankroll={bankroll}
            onBankrollChange={setBankroll}
            onClose={() => {
              setKellyModalData(null);
              setKellyResult(null);
            }}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

// 통계 카드 컴포넌트
const StatCard = ({ icon: Icon, label, value, color }) => (
  <motion.div
    initial={{ opacity: 0, scale: 0.9 }}
    animate={{ opacity: 1, scale: 1 }}
    className={`rounded-xl bg-gradient-to-br ${color} bg-opacity-20 border border-white/10 p-4`}
  >
    <div className="flex items-center justify-between mb-2">
      <Icon className="w-5 h-5 text-white/60" />
    </div>
    <div className="text-2xl font-black text-white mb-1">{value}</div>
    <div className="text-xs text-white/60">{label}</div>
  </motion.div>
);

// 접을 수 있는 섹션 컴포넌트
const CollapsibleSection = ({ title, icon: Icon, count, isExpanded, onToggle, children }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    className="mb-6"
  >
    <button
      onClick={onToggle}
      className="w-full flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors mb-4"
    >
      <div className="flex items-center gap-3">
        <Icon className="w-5 h-5 text-violet-400" />
        <h2 className="text-xl font-bold text-white">{title}</h2>
        <span className="px-2 py-1 rounded-lg bg-violet-500/20 text-violet-300 text-sm font-semibold">
          {count}
        </span>
      </div>
      {isExpanded ? (
        <ChevronUp className="w-5 h-5 text-white/60" />
      ) : (
        <ChevronDown className="w-5 h-5 text-white/60" />
      )}
    </button>

    <AnimatePresence>
      {isExpanded && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.3 }}
          style={{ overflow: 'hidden' }}
        >
          {children}
        </motion.div>
      )}
    </AnimatePresence>
  </motion.div>
);

// Kelly Calculator 모달
const KellyModal = ({ valueBet, kellyResult, bankroll, onBankrollChange, onClose }) => (
  <motion.div
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    exit={{ opacity: 0 }}
    className="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center z-50 p-6"
    onClick={onClose}
  >
    <motion.div
      initial={{ opacity: 0, scale: 0.9, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.9, y: 20 }}
      className="bg-gradient-to-br from-slate-900/95 to-slate-950/95 backdrop-blur-xl rounded-3xl border border-white/10 shadow-2xl p-8 max-w-2xl w-full"
      onClick={(e) => e.stopPropagation()}
    >
      {/* 헤더 */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Kelly Criterion 계산</h2>
          <p className="text-white/60 text-sm">
            {valueBet.home_team} vs {valueBet.away_team}
          </p>
        </div>
        <button
          onClick={onClose}
          className="p-2 rounded-xl bg-white/10 hover:bg-white/20 transition-colors"
        >
          <X className="w-5 h-5 text-white" />
        </button>
      </div>

      {/* 자금 입력 */}
      <div className="mb-6">
        <label className="block text-sm font-semibold text-white/80 mb-2">
          총 자금 (Bankroll)
        </label>
        <input
          type="number"
          value={bankroll}
          onChange={(e) => onBankrollChange(Number(e.target.value))}
          className="w-full px-4 py-3 rounded-xl bg-white/10 border border-white/20 text-white font-semibold text-lg focus:outline-none focus:ring-2 focus:ring-violet-500"
          min="100"
          step="100"
        />
      </div>

      {/* Kelly 결과 */}
      {kellyResult && (
        <div className="space-y-4">
          {/* 추천 베팅 금액 */}
          <div className="rounded-2xl bg-gradient-to-br from-violet-500/20 to-purple-600/20 border border-violet-400/40 p-6">
            <div className="text-sm text-white/60 mb-2">추천 베팅 금액</div>
            <div className="text-4xl font-black text-white mb-2">
              ${kellyResult.bet_amount.toLocaleString()}
            </div>
            <div className="text-sm text-white/60">
              (자금의 {(kellyResult.kelly_percent * 100).toFixed(2)}% - Quarter Kelly)
            </div>
          </div>

          {/* 상세 정보 */}
          <div className="grid grid-cols-2 gap-4">
            <InfoCard
              label="예상 수익"
              value={`$${kellyResult.potential_profit.toLocaleString()}`}
              color="text-emerald-300"
            />
            <InfoCard
              label="예상 손실"
              value={`$${kellyResult.potential_loss.toLocaleString()}`}
              color="text-rose-300"
            />
            <InfoCard
              label="기댓값 (EV)"
              value={`$${kellyResult.expected_value.toLocaleString()}`}
              color="text-blue-300"
            />
            <InfoCard
              label="Edge"
              value={`${kellyResult.edge.toFixed(1)}%`}
              color="text-violet-300"
            />
          </div>

          {/* 시뮬레이션 */}
          <div className="rounded-xl bg-white/5 border border-white/10 p-4">
            <div className="text-xs text-white/60 mb-3">시뮬레이션</div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <div className="text-xs text-white/40 mb-1">승리 시</div>
                <div className="text-lg font-bold text-emerald-300">
                  ${kellyResult.bankroll_after_win.toLocaleString()}
                </div>
              </div>
              <div>
                <div className="text-xs text-white/40 mb-1">패배 시</div>
                <div className="text-lg font-bold text-rose-300">
                  ${kellyResult.bankroll_after_loss.toLocaleString()}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </motion.div>
  </motion.div>
);

const InfoCard = ({ label, value, color }) => (
  <div className="rounded-xl bg-white/5 border border-white/10 p-4">
    <div className="text-xs text-white/60 mb-1">{label}</div>
    <div className={`text-xl font-bold ${color}`}>{value}</div>
  </div>
);

export default MarketValueDashboard;
