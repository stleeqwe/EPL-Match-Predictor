import React from 'react';
import { motion } from 'framer-motion';
import { Activity, AlertCircle } from 'lucide-react';

/**
 * InjuryBadge Component
 * 선수 부상 상태 배지
 */
const InjuryBadge = ({
  injury,
  compact = false,
  className = ''
}) => {
  if (!injury) return null;

  // 부상 상태별 스타일
  const getInjuryStyle = (status) => {
    switch (status) {
      case 'injured':
        return {
          bgColor: 'bg-red-500/20',
          borderColor: 'border-red-500/60',
          textColor: 'text-red-300',
          iconColor: 'text-red-400',
          label: '부상',
          icon: AlertCircle
        };
      case 'recovering':
        return {
          bgColor: 'bg-yellow-500/20',
          borderColor: 'border-yellow-500/60',
          textColor: 'text-yellow-300',
          iconColor: 'text-yellow-400',
          label: '회복중',
          icon: Activity
        };
      case 'doubtful':
        return {
          bgColor: 'bg-orange-500/20',
          borderColor: 'border-orange-500/60',
          textColor: 'text-orange-300',
          iconColor: 'text-orange-400',
          label: '불확실',
          icon: AlertCircle
        };
      default:
        return {
          bgColor: 'bg-gray-500/20',
          borderColor: 'border-gray-500/60',
          textColor: 'text-gray-300',
          iconColor: 'text-gray-400',
          label: '부상',
          icon: AlertCircle
        };
    }
  };

  const style = getInjuryStyle(injury.status);
  const Icon = style.icon;

  // Compact 모드 (작은 배지 - 프로필 사진 위 오버레이용)
  if (compact) {
    return (
      <motion.div
        className={`
          flex items-center justify-center px-1.5 py-0.5 rounded-sm border shadow-lg
          ${style.bgColor} ${style.borderColor} ${className}
        `}
        initial={{ opacity: 0, scale: 0.5 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.2, type: 'spring', stiffness: 400 }}
        title={`${injury.injury_type || '부상'} - ${injury.player_name || ''}`}
      >
        <Icon className={`w-3 h-3 ${style.iconColor}`} />
      </motion.div>
    );
  }

  // Full 모드 (상세 배지)
  return (
    <motion.div
      className={`
        flex items-center gap-2 px-3 py-2 rounded-sm border
        ${style.bgColor} ${style.borderColor} ${className}
      `}
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Icon className={`w-4 h-4 ${style.iconColor}`} />
      <div className="flex-1 min-w-0">
        <div className={`text-sm font-bold ${style.textColor} uppercase tracking-wide font-mono`}>
          {style.label}
        </div>
        {injury.injury_type && (
          <div className="text-xs text-white/70 truncate">
            {injury.injury_type}
          </div>
        )}
        {injury.days_out && (
          <div className="text-xs text-white/50">
            {injury.days_out}
          </div>
        )}
      </div>
    </motion.div>
  );
};

/**
 * InjuryIndicator Component
 * 선수 카드 우측 상단에 표시되는 간단한 인디케이터 (작은 아이콘 배지)
 */
export const InjuryIndicator = ({ injury, className = '' }) => {
  if (!injury) return null;

  const getIndicatorStyle = (status) => {
    switch (status) {
      case 'injured':
        return {
          bgColor: 'bg-red-500/90',
          borderColor: 'border-red-400/80',
          iconColor: 'text-red-100',
          icon: AlertCircle
        };
      case 'recovering':
        return {
          bgColor: 'bg-yellow-500/90',
          borderColor: 'border-yellow-400/80',
          iconColor: 'text-yellow-100',
          icon: Activity
        };
      case 'doubtful':
        return {
          bgColor: 'bg-orange-500/90',
          borderColor: 'border-orange-400/80',
          iconColor: 'text-orange-100',
          icon: AlertCircle
        };
      default:
        return {
          bgColor: 'bg-gray-500/90',
          borderColor: 'border-gray-400/80',
          iconColor: 'text-gray-100',
          icon: AlertCircle
        };
    }
  };

  const style = getIndicatorStyle(injury.status);
  const Icon = style.icon;

  return (
    <motion.div
      className={`
        flex items-center justify-center p-0.5 rounded-full border
        ${style.bgColor} ${style.borderColor} ${className}
        shadow-lg
      `}
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      transition={{ type: 'spring', stiffness: 500, delay: 0.05 }}
      style={{
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.3)'
      }}
      title={`부상: ${injury.injury_type || '상태 확인 필요'}`}
    >
      <Icon className={`w-3 h-3 ${style.iconColor}`} strokeWidth={2.5} />
    </motion.div>
  );
};

export default InjuryBadge;
