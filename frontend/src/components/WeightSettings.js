import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Info, RotateCcw, Save, X, Lightbulb, TrendingUp, BarChart3,
  User, Scale, Database, Target, Gem, LineChart, Users
} from 'lucide-react';

/**
 * Enhanced Tooltip Component
 */
const EnhancedTooltip = ({ source, onClose }) => {
  const tooltipRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (tooltipRef.current && !tooltipRef.current.contains(event.target)) {
        onClose();
      }
    };

    const handleEscapeKey = (event) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscapeKey);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscapeKey);
    };
  }, [onClose]);

  return (
    <motion.div
      ref={tooltipRef}
      initial={{ opacity: 0, scale: 0.95, x: -10 }}
      animate={{ opacity: 1, scale: 1, x: 0 }}
      exit={{ opacity: 0, scale: 0.95, x: -10 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className={`absolute left-full -top-32 ml-2 z-50 w-[95vw] sm:w-96 max-w-md bg-gradient-to-br ${source.bgGradient} backdrop-blur-xl border-2 ${source.borderColor} rounded-lg shadow-2xl ${source.glowColor} shadow-lg overflow-hidden`}
    >
      {/* Scan Line Effect */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <motion.div
          className="absolute inset-x-0 h-px"
          style={{
            background: `linear-gradient(to right, transparent, ${source.color}80, transparent)`
          }}
          animate={{ y: [0, 400] }}
          transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
        />
      </div>

      {/* Grid Pattern */}
      <div
        className="absolute inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage: `
            linear-gradient(${source.color} 1px, transparent 1px),
            linear-gradient(90deg, ${source.color} 1px, transparent 1px)
          `,
          backgroundSize: '20px 20px'
        }}
      />

      {/* Content */}
      <div className="relative bg-slate-950/90 p-5">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className={`p-2 rounded bg-gradient-to-br ${source.bgGradient} border ${source.borderColor}`}>
              <source.icon className={`w-5 h-5 ${source.lightColor}`} />
            </div>
            <div>
              <h4 className={`text-base font-bold ${source.lightColor} flex items-center gap-2`}>
                {source.title}
              </h4>
              <span className="text-xs text-white/40">{source.label}</span>
            </div>
          </div>
          <button
            onClick={onClose}
            className={`p-1 rounded hover:bg-white/10 transition-colors ${source.lightColor}`}
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Description */}
        <div className="mb-4 space-y-2">
          <p className="text-sm text-white/90 leading-relaxed">
            {source.description}
          </p>
          <p className="text-xs text-white/60 leading-relaxed italic border-l-2 border-white/20 pl-3">
            {source.subDescription}
          </p>
        </div>

        {/* Usage Guide */}
        <div className="mb-4">
          <h5 className="text-xs font-semibold text-white/70 mb-3 uppercase tracking-wider">
            사용 가이드
          </h5>
          <div className="space-y-2">
            {source.usageGuides.map((guide, i) => {
              const IconComponent = guide.icon;
              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="flex items-start gap-3 p-2 rounded bg-white/5 border border-white/10"
                >
                  <div className={`flex-shrink-0 p-1 rounded ${source.lightColor}`}>
                    <IconComponent className="w-4 h-4" strokeWidth={2.5} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <span className={`text-xs font-bold ${source.lightColor} block mb-1`}>
                      {guide.range}
                    </span>
                    <span className="text-xs text-white/70 leading-relaxed">
                      {guide.desc}
                    </span>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* Pro Tip */}
        <div className={`p-3 rounded-lg bg-gradient-to-br ${source.bgGradient} border ${source.borderColor}`}>
          <p className="text-xs text-white/80 leading-relaxed">
            {source.proTip}
          </p>
        </div>
      </div>
    </motion.div>
  );
};

/**
 * WeightSettings Component
 * AI 분석 가중치 설정
 */
export default function WeightSettings({ weights, onChange, presets, darkMode }) {
  const [localWeights, setLocalWeights] = useState(weights || {
    user_value: 0.65,
    odds: 0.20,
    stats: 0.15
  });
  const [showTooltip, setShowTooltip] = useState(null);

  useEffect(() => {
    if (weights) {
      setLocalWeights(weights);
    }
  }, [weights]);

  const handleSliderChange = (key, value) => {
    const newValue = parseFloat(value);
    const oldValue = localWeights[key];
    const diff = newValue - oldValue;

    const otherKeys = Object.keys(localWeights).filter(k => k !== key);
    const otherTotal = otherKeys.reduce((sum, k) => sum + localWeights[k], 0);

    let newWeights = { ...localWeights, [key]: newValue };

    if (otherTotal > 0) {
      otherKeys.forEach(k => {
        const proportion = localWeights[k] / otherTotal;
        newWeights[k] = Math.max(0, Math.min(1, localWeights[k] - diff * proportion));
      });
    }

    const sum = Object.values(newWeights).reduce((a, b) => a + b, 0);
    if (sum > 0) {
      Object.keys(newWeights).forEach(k => {
        newWeights[k] = newWeights[k] / sum;
      });
    }

    setLocalWeights(newWeights);
    onChange(newWeights);
  };

  const applyPreset = (preset) => {
    setLocalWeights(preset.weights);
    onChange(preset.weights);
  };

  const resetToDefault = () => {
    const defaultWeights = {
      user_value: 0.65,
      odds: 0.20,
      stats: 0.15
    };
    setLocalWeights(defaultWeights);
    onChange(defaultWeights);
  };

  const saveToLocal = () => {
    localStorage.setItem('ai_simulator_weights', JSON.stringify(localWeights));
    alert('가중치가 저장되었습니다!');
  };

  const userPct = Math.round(localWeights.user_value * 100);
  const oddsPct = Math.round(localWeights.odds * 100);
  const statsPct = Math.round(localWeights.stats * 100);
  const total = userPct + oddsPct + statsPct;

  const dataSources = [
    {
      key: 'user_value',
      label: 'User Value',
      icon: Lightbulb,
      emoji: '💡',
      title: '당신의 전문가 인사이트',
      description: '선수 능력, 전술 적합성, 팀 케미스트리에 대한 당신의 독자적 분석을 AI 예측에 반영합니다.',
      subDescription: '프로 분석가들은 자신의 심층 연구를 신뢰할 때 이 가중치를 높게 설정합니다.',
      usageGuides: [
        { icon: User, range: '80%+', desc: '당신의 전술 분석이 시장보다 정확하다고 확신할 때' },
        { icon: Scale, range: '50-80%', desc: '데이터와 인사이트의 균형을 원할 때' },
        { icon: Database, range: '50% 미만', desc: '객관적 데이터를 더 신뢰할 때' }
      ],
      proTip: '💡 Pro Tip: EPL 시청 시간이 많고 팀/선수에 대한 깊은 이해가 있다면 높게 설정하세요.',
      color: '#06b6d4',
      lightColor: 'text-cyan-400',
      bgGradient: 'from-cyan-500/10 via-blue-500/5 to-transparent',
      borderColor: 'border-cyan-500/30',
      glowColor: 'shadow-cyan-500/20',
      percentage: userPct
    },
    {
      key: 'odds',
      label: 'Sharp Odds',
      icon: TrendingUp,
      emoji: '📈',
      title: 'Sharp 북메이커 확률',
      description: 'Pinnacle 등 수수료가 낮은 Sharp 북메이커의 배당률입니다. 시장에서 가장 정확한 확률을 제공하는 것으로 알려져 있습니다.',
      subDescription: '프로 베터들이 기준으로 삼는 "시장의 지혜"를 대표하며, 효율적 시장 가설에 가장 근접합니다.',
      usageGuides: [
        { icon: Target, range: '80%+', desc: '시장 컨센서스를 최우선할 때 (안정적 예측)' },
        { icon: Scale, range: '50-80%', desc: '시장과 개인 분석의 균형' },
        { icon: Gem, range: '50% 미만', desc: '시장이 놓친 가치를 찾을 때' }
      ],
      proTip: '🎯 Pro Tip: 정보가 부족한 경기나 객관적 예측을 원할 때 높게 설정하세요.',
      color: '#f59e0b',
      lightColor: 'text-amber-400',
      bgGradient: 'from-amber-500/10 via-orange-500/5 to-transparent',
      borderColor: 'border-amber-500/30',
      glowColor: 'shadow-amber-500/20',
      percentage: oddsPct
    },
    {
      key: 'stats',
      label: 'Stats',
      icon: BarChart3,
      emoji: '📊',
      title: '검증된 통계 데이터',
      description: '최근 5경기 폼, 득실점, xG, FPL 포인트, 홈/원정 성적 등 공식 출처에서 수집한 객관적 통계입니다.',
      subDescription: '감정을 배제하고 순수 데이터만으로 판단합니다. 통계는 거짓말을 하지 않습니다.',
      usageGuides: [
        { icon: LineChart, range: '80%+', desc: '데이터 기반 의사결정을 선호할 때' },
        { icon: Scale, range: '50-80%', desc: '통계와 맥락의 균형' },
        { icon: Users, range: '50% 미만', desc: '최근 폼보다 장기 트렌드/인사이트 중시' }
      ],
      proTip: '📈 Pro Tip: 통계가 명확한 스토리를 말해주는 경기에 높게 설정하세요.',
      color: '#10b981',
      lightColor: 'text-emerald-400',
      bgGradient: 'from-emerald-500/10 via-green-500/5 to-transparent',
      borderColor: 'border-emerald-500/30',
      glowColor: 'shadow-emerald-500/20',
      percentage: statsPct
    }
  ];

  return (
    <div className="relative bg-gradient-to-br from-slate-900/80 via-blue-950/60 to-slate-900/80 backdrop-blur-sm rounded border border-cyan-500/20 shadow-lg p-6">
      {/* Tech Grid Background */}
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

      {/* Header */}
      <div className="relative flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-cyan-400">
          분석 가중치 설정
        </h3>
        <div className="flex gap-2">
          <button
            onClick={resetToDefault}
            className="p-2 rounded-sm bg-slate-800 hover:bg-slate-700 text-cyan-400 border border-cyan-500/30 transition-all"
            title="기본값으로 초기화"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
          <button
            onClick={saveToLocal}
            className="p-2 rounded-sm bg-cyan-600 hover:bg-cyan-700 text-white transition-all"
            title="현재 설정 저장"
          >
            <Save className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Data Source Sliders */}
      <div className="relative space-y-4 mb-6">
        {dataSources.map((source) => (
          <div
            key={source.key}
            className={`bg-slate-900/50 rounded border ${source.borderColor} p-4`}
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className={`text-sm font-semibold ${source.lightColor}`}>
                  {source.label}
                </span>
                <div className="relative">
                  <button
                    onClick={() => setShowTooltip(showTooltip === source.key ? null : source.key)}
                    onMouseEnter={() => setShowTooltip(source.key)}
                    className={`p-1 rounded transition-all focus:outline-none focus:ring-2 focus:ring-offset-1 ${
                      showTooltip === source.key
                        ? `${source.lightColor} bg-white/10 focus:ring-${source.lightColor.replace('text-', '')}`
                        : `text-gray-400 hover:${source.lightColor} focus:ring-gray-400`
                    }`}
                    style={
                      showTooltip === source.key
                        ? { '--tw-ring-color': source.color }
                        : undefined
                    }
                    aria-label={`${source.label} 정보 보기`}
                    aria-expanded={showTooltip === source.key}
                  >
                    <Info className="w-4 h-4" />
                  </button>
                  <AnimatePresence>
                    {showTooltip === source.key && (
                      <EnhancedTooltip
                        source={source}
                        onClose={() => setShowTooltip(null)}
                      />
                    )}
                  </AnimatePresence>
                </div>
              </div>
              <span className={`text-xl font-bold ${source.lightColor}`}>
                {source.percentage}%
              </span>
            </div>

            {/* Slider */}
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={localWeights[source.key]}
              onChange={(e) => handleSliderChange(source.key, e.target.value)}
              className="w-full h-2 rounded-sm appearance-none cursor-pointer"
              style={{
                background: `linear-gradient(to right, ${source.color} 0%, ${source.color} ${source.percentage}%, #1e293b ${source.percentage}%, #1e293b 100%)`
              }}
            />
          </div>
        ))}
      </div>

      {/* Total Display */}
      <div className={`relative p-4 rounded border ${
        total === 100
          ? 'bg-cyan-900/20 border-cyan-500/30'
          : 'bg-red-900/20 border-red-500/30'
      }`}>
        <div className="flex items-center justify-between">
          <span className={`text-sm font-semibold ${total === 100 ? 'text-cyan-400' : 'text-red-400'}`}>
            합계
          </span>
          <span className={`text-2xl font-bold ${total === 100 ? 'text-cyan-400' : 'text-red-400'}`}>
            {total}%
          </span>
        </div>
      </div>

      {/* Presets */}
      {presets && presets.length > 0 && (
        <div className="relative mt-6">
          <h4 className="text-sm font-semibold text-white mb-3">
            빠른 프리셋
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {presets.map((preset) => (
              <button
                key={preset.id}
                onClick={() => applyPreset(preset)}
                className="p-3 rounded-sm text-left transition-all bg-slate-800 hover:bg-slate-700 border border-cyan-500/20 hover:border-cyan-500/50"
                title={preset.description}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xl">{preset.icon}</span>
                  <span className="text-xs font-bold text-cyan-400">
                    {preset.name}
                  </span>
                </div>
                <div className="text-xs text-white/60">
                  {Math.round(preset.weights.user_value * 100)}/{Math.round(preset.weights.odds * 100)}/{Math.round(preset.weights.stats * 100)}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
