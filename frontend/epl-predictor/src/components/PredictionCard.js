import React from 'react';
import { motion } from 'framer-motion';
import { Target, TrendingUp, Clock, BarChart3, Activity } from 'lucide-react';

/**
 * PredictionCard - 개별 경기 예측 카드
 */
const PredictionCard = ({ prediction, index }) => {
  const {
    home_team,
    away_team,
    outcome,
    bookmaker,
    odds,
    confidence,
    estimated_probability,
    recommendation,
    commence_time
  } = prediction;

  // 신뢰도 등급별 스타일 (베팅 용어 제거)
  const confidenceStyles = {
    'STRONG_BET': {
      bg: 'from-emerald-500/20 to-green-600/20',
      border: 'border-emerald-400/40',
      text: 'text-emerald-300',
      icon: '🎯',
      label: '높은 신뢰도'
    },
    'MODERATE_BET': {
      bg: 'from-blue-500/20 to-cyan-600/20',
      border: 'border-blue-400/40',
      text: 'text-blue-300',
      icon: '📊',
      label: '중간 신뢰도'
    },
    'SMALL_BET': {
      bg: 'from-amber-500/20 to-yellow-600/20',
      border: 'border-amber-400/40',
      text: 'text-amber-300',
      icon: '💡',
      label: '낮은 신뢰도'
    }
  };

  const style = confidenceStyles[recommendation] || confidenceStyles['SMALL_BET'];

  // 결과 한글 변환
  const outcomeKR = {
    'home': '홈 승',
    'draw': '무승부',
    'away': '원정 승'
  };

  // 시간 포맷
  const formatTime = (timeString) => {
    if (!timeString) return '-';
    try {
      const date = new Date(timeString);
      return date.toLocaleString('ko-KR', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return '-';
    }
  };

  // 배당률 → 암시 확률 변환 (Implied Probability)
  const impliedProbability = (1 / odds) * 100;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className={`relative rounded-2xl bg-gradient-to-br ${style.bg} border ${style.border} backdrop-blur-sm overflow-hidden group hover:scale-[1.02] transition-transform duration-300`}
    >
      {/* 배경 그라데이션 효과 */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

      <div className="relative p-6">
        {/* 헤더 - 경기 정보 */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-2xl">{style.icon}</span>
              <span className={`text-xs font-bold px-2 py-1 rounded-sm bg-white/10 ${style.text}`}>
                {style.label}
              </span>
            </div>
            <h3 className="text-lg font-bold text-white mb-1">
              {home_team} vs {away_team}
            </h3>
            <div className="flex items-center gap-2 text-sm text-white/60">
              <Clock className="w-3.5 h-3.5" />
              <span>{formatTime(commence_time)}</span>
            </div>
          </div>

          {/* 신뢰도 배지 */}
          <div className="flex flex-col items-end gap-1">
            <div className="px-3 py-1.5 rounded-sm bg-gradient-to-r from-violet-500/30 to-purple-600/30 border border-violet-400/30">
              <div className="text-xs text-white/60 mb-0.5">신뢰도</div>
              <div className="text-xl font-black text-white">
                {(confidence * 100).toFixed(0)}%
              </div>
            </div>
          </div>
        </div>

        {/* 예측 정보 */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          {/* 예측 결과 */}
          <div className="rounded-sm bg-white/5 p-3 border border-white/10">
            <div className="flex items-center gap-2 mb-1">
              <Target className="w-3.5 h-3.5 text-white/60" />
              <span className="text-xs text-white/60">예측 결과</span>
            </div>
            <div className="text-base font-bold text-white">
              {outcomeKR[outcome] || outcome}
            </div>
          </div>

          {/* 배당률 */}
          <div className="rounded-sm bg-white/5 p-3 border border-white/10">
            <div className="flex items-center gap-2 mb-1">
              <TrendingUp className="w-3.5 h-3.5 text-white/60" />
              <span className="text-xs text-white/60">배당률</span>
            </div>
            <div className="text-base font-bold text-white">
              {odds.toFixed(2)}
            </div>
          </div>
        </div>

        {/* 확률 분석 섹션 */}
        <div className="rounded-sm bg-gradient-to-br from-blue-500/10 to-cyan-500/10 border border-blue-400/20 p-4 mb-4">
          <div className="text-xs text-white/60 mb-3 font-semibold">📊 확률 분석</div>

          <div className="grid grid-cols-2 gap-3 mb-3">
            {/* Pinnacle 암시 확률 */}
            <div>
              <div className="text-xs text-white/60 mb-1">배당률 암시 확률</div>
              <div className="text-lg font-bold text-blue-300">
                {impliedProbability.toFixed(1)}%
              </div>
              <div className="text-xs text-white/40 mt-0.5">
                ({bookmaker})
              </div>
            </div>

            {/* 예측 모델 확률 */}
            <div>
              <div className="text-xs text-white/60 mb-1">예측 모델 확률</div>
              <div className="text-lg font-bold text-emerald-300">
                {(estimated_probability * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-white/40 mt-0.5">
                (Sharp Odds 기준)
              </div>
            </div>
          </div>

          {/* 확률 차이 시각화 */}
          <div className="mt-3">
            <div className="text-xs text-white/60 mb-2">
              확률 비교
            </div>
            <div className="grid grid-cols-2 gap-2">
              {/* 암시 확률 바 */}
              <div>
                <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min(impliedProbability, 100)}%` }}
                    transition={{ duration: 0.8, delay: index * 0.05 + 0.2 }}
                    className="h-full bg-gradient-to-r from-blue-400 to-cyan-400"
                  />
                </div>
              </div>
              {/* 예측 모델 확률 바 */}
              <div>
                <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${(estimated_probability * 100)}%` }}
                    transition={{ duration: 0.8, delay: index * 0.05 + 0.3 }}
                    className="h-full bg-gradient-to-r from-emerald-400 to-green-400"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 부가 정보 */}
        <div className="rounded-sm bg-white/5 border border-white/10 p-3">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2 text-white/60">
              <BarChart3 className="w-3.5 h-3.5" />
              <span>데이터 출처</span>
            </div>
            <div className="text-white/80 font-semibold">
              {bookmaker} (Sharp Odds)
            </div>
          </div>
        </div>

        {/* 참조용 안내 */}
        <div className="mt-3 pt-3 border-t border-white/10">
          <div className="flex items-center gap-2 text-xs text-amber-300/80">
            <Activity className="w-3.5 h-3.5" />
            <span>본 예측은 참조용 정보입니다</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default PredictionCard;
