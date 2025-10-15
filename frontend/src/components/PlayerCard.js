import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { User } from 'lucide-react';
import { getPlayerPhotoUrl } from '../utils/playerPhoto';
import InjuryBadge, { InjuryIndicator } from './InjuryBadge';

/**
 * PlayerCard Component
 * 선수 프로필 카드 - Enhanced with Framer Motion
 */
const PlayerCard = ({
  player,
  darkMode = false,
  onClick,
  averageRating = null,
  compact = false,
  injury = null
}) => {
  // Premier League API 포지션 → Squad Builder 역할 변환
  const getPlayerRole = (premierLeaguePosition) => {
    if (!premierLeaguePosition) return 'CM';

    const posLower = premierLeaguePosition.toLowerCase();

    // Goalkeeper
    if (posLower.includes('goalkeeper')) return 'GK';

    // Defenders
    if (posLower.includes('central defender') || posLower.includes('centre back') || posLower.includes('centre central defender')) return 'CB';
    if (posLower.includes('full back') || posLower.includes('wing back') || posLower.includes('wingback')) return 'FB';

    // Midfielders
    if (posLower.includes('defensive midfielder')) return 'DM';
    if (posLower.includes('attacking midfielder')) return 'CAM';
    if (posLower.includes('central midfielder') || posLower.includes('centre midfielder')) return 'CM';

    // Forwards
    if (posLower.includes('winger') || posLower.includes('wide')) return 'WG';
    if (posLower.includes('forward') || posLower.includes('striker')) return 'ST';

    // Fallback
    if (posLower.includes('defender')) return 'CB';
    if (posLower.includes('midfielder')) return 'CM';

    return 'CM';  // 기본값
  };

  // 포지션별 색상 스킴 (배지용)
  const getPositionBadgeColor = (role) => {
    switch (role) {
      case 'GK':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/40';  // 골키퍼: 노란색
      case 'CB':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';  // 센터백: 녹색
      case 'FB':
        return 'bg-teal-500/20 text-teal-300 border-teal-500/40';  // 풀백: 청록색
      case 'DM':
        return 'bg-blue-500/20 text-blue-300 border-blue-500/40';  // 수비형 미드필더: 파란색
      case 'CM':
        return 'bg-purple-500/20 text-purple-300 border-purple-500/40';  // 중앙 미드필더: 보라색
      case 'CAM':
        return 'bg-pink-500/20 text-pink-300 border-pink-500/40';  // 공격형 미드필더: 핑크
      case 'WG':
        return 'bg-orange-500/20 text-orange-300 border-orange-500/40';  // 윙어: 주황색
      case 'ST':
        return 'bg-red-500/20 text-red-300 border-red-500/40';  // 스트라이커: 빨간색
      default:
        return 'bg-gray-500/20 text-gray-300 border-gray-500/40';  // 기본: 회색
    }
  };

  // 대조적인 색상 시스템 (평균 기준 양방향)
  const getColorSystem = (rating) => {
    if (rating >= 4.5) {
      return {
        color: '#00FFFF',      // 형광 사이언 - 월드클래스
        gradient: 'linear-gradient(to right, #00FFFF, rgba(0, 255, 255, 0.7))',
        bgGradient: 'from-[#00FFFF]/20 to-[#00FFFF]/5'
      };
    }
    if (rating >= 4.0) {
      return {
        color: '#60A5FA',      // 밝은 파랑 - 상위
        gradient: 'linear-gradient(to right, #60A5FA, rgba(96, 165, 250, 0.7))',
        bgGradient: 'from-[#60A5FA]/20 to-[#60A5FA]/5'
      };
    }
    if (rating >= 3.0) {
      return {
        color: '#A855F7',      // 보라색 - 중상위
        gradient: 'linear-gradient(to right, #A855F7, rgba(168, 85, 247, 0.7))',
        bgGradient: 'from-[#A855F7]/20 to-[#A855F7]/5'
      };
    }
    if (rating >= 2.0) {
      return {
        color: '#FBBF24',      // 노랑색 - 평균
        gradient: 'linear-gradient(to right, #FBBF24, rgba(251, 191, 36, 0.7))',
        bgGradient: 'from-[#FBBF24]/20 to-[#FBBF24]/5'
      };
    }
    if (rating >= 1.5) {
      return {
        color: '#FB923C',      // 빛바랜 주황색 - 평균 이하
        gradient: 'linear-gradient(to right, #FB923C, rgba(251, 146, 60, 0.7))',
        bgGradient: 'from-[#FB923C]/20 to-[#FB923C]/5'
      };
    }
    return {
      color: '#9CA3AF',        // 무채색 회색 - 하위
      gradient: 'linear-gradient(to right, #9CA3AF, rgba(156, 163, 175, 0.7))',
      bgGradient: 'from-[#9CA3AF]/20 to-[#9CA3AF]/5'
    };
  };

  // 선수 사진 에러 처리
  const [photoError, setPhotoError] = useState(false);
  const photoUrlSmall = player.photo ? getPlayerPhotoUrl(player.photo, '110x140') : null;
  const photoUrlLarge = player.photo ? getPlayerPhotoUrl(player.photo, '250x250') : null;


  // 🔍 DEBUG: 이미지 로드 에러 추적
  const handlePhotoError = (e) => {
    console.error('❌ Photo Load Error:');
    console.error(`  Player: ${player.name}`);
    console.error(`  Photo Code: ${player.photo}`);
    console.error(`  Attempted URL: ${e.target.src}`);
    console.error(`  Natural Size: ${e.target.naturalWidth}x${e.target.naturalHeight}`);
    setPhotoError(true);
  };

  // Compact 모드 (리스트용)
  if (compact) {
    const displayRating = averageRating !== null ? averageRating : 2.5;
    const colorSystem = getColorSystem(displayRating);
    const playerRole = getPlayerRole(player.position);

    return (
      <motion.div
        onClick={onClick}
        className="relative card-hover p-4 cursor-pointer group bg-gradient-to-br from-slate-900/80 via-blue-950/60 to-slate-900/80 backdrop-blur-sm border border-cyan-500/20 rounded overflow-hidden"
        whileHover={{ scale: 1.02, y: -2 }}
        whileTap={{ scale: 0.98 }}
        transition={{ duration: 0.2, ease: "easeOut" }}
      >
        {/* Tech Grid Pattern */}
        <div
          className="absolute inset-0 opacity-[0.03] pointer-events-none"
          style={{
            backgroundImage: `
              linear-gradient(rgba(6, 182, 212, 0.5) 1px, transparent 1px),
              linear-gradient(90deg, rgba(6, 182, 212, 0.5) 1px, transparent 1px)
            `,
            backgroundSize: '20px 20px'
          }}
        />

        <div className="relative">
        <div className="flex items-center justify-between gap-4">
          {/* Left: Player Info */}
          <div className="flex items-center gap-3 flex-1 min-w-0">
            {/* Player Photo */}
            <div className="relative w-12 h-12 flex-shrink-0">
              {photoUrlSmall && !photoError ? (
                <img
                  src={photoUrlSmall}
                  alt={player.name}
                  crossOrigin="anonymous"
                  referrerPolicy="no-referrer"
                  className="w-12 h-12 rounded-sm object-cover border-2 border-white/20 group-hover:border-cyan-400 transition-all duration-300"
                  style={{
                    boxShadow: '0 0 0 rgba(6, 182, 212, 0)'
                  }}
                  onError={handlePhotoError}
                />
              ) : (
                <div className="w-12 h-12 rounded-sm flex items-center justify-center bg-white/5 border border-white/20">
                  <User className="w-6 h-6 text-white/40" />
                </div>
              )}

              {/* Injury Badge Overlay - 프로필 사진 우측 상단 */}
              {injury && (
                <div className="absolute -top-1 -right-1">
                  <InjuryIndicator injury={injury} />
                </div>
              )}
            </div>

            {/* Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="font-grotesk font-semibold text-white truncate group-hover:text-cyan-400 transition-colors">
                  {player.name}
                </h3>
                {player.number > 0 && (
                  <span className="text-sm text-cyan-400/80 font-mono font-bold">
                    #{player.number}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                {/* Position Badge - 축약어 + 포지션별 색상 */}
                <span className={`
                  px-2.5 py-0.5 rounded-sm text-sm font-bold border flex-shrink-0 uppercase tracking-wide font-mono
                  ${getPositionBadgeColor(playerRole)}
                `}>
                  {playerRole}
                </span>
                <p className="text-sm text-white/50 truncate">
                  {player.age}Y • {player.team}
                </p>
              </div>
            </div>
          </div>

          {/* Right: Rating */}
          <motion.div
            className="text-right flex-shrink-0"
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
          >
            <div className="text-2xl font-bold font-numeric" style={{ color: colorSystem.color }}>
              {displayRating.toFixed(2)}
            </div>
            <div className="text-xs text-white/60">평균</div>
          </motion.div>
        </div>
        </div>
      </motion.div>
    );
  }

  // Full 모드 (그리드용)
  const displayRating = averageRating !== null ? averageRating : 2.5;
  const colorSystem = getColorSystem(displayRating);
  const playerRole = getPlayerRole(player.position);

  return (
    <motion.div
      onClick={onClick}
      className="card-hover p-4 cursor-pointer group relative overflow-hidden bg-gradient-to-br from-slate-900/80 via-blue-950/60 to-slate-900/80 backdrop-blur-sm border border-cyan-500/20 rounded"
      whileHover={{ scale: 1.03, y: -4 }}
      whileTap={{ scale: 0.98 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
    >
      {/* Tech Grid Pattern */}
      <div
        className="absolute inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage: `
            linear-gradient(rgba(6, 182, 212, 0.5) 1px, transparent 1px),
            linear-gradient(90deg, rgba(6, 182, 212, 0.5) 1px, transparent 1px)
          `,
          backgroundSize: '20px 20px'
        }}
      />

      {/* Content */}
      <div className="relative z-10">
        {/* Header with Photo */}
        <div className="flex items-center gap-4 mb-3">
          {/* Player Photo */}
          <div className="relative w-28 h-28 flex-shrink-0">
            {photoUrlLarge && !photoError ? (
              <img
                src={photoUrlLarge}
                alt={player.name}
                crossOrigin="anonymous"
                referrerPolicy="no-referrer"
                className="w-28 h-28 rounded-sm object-cover border-2 border-white/30 group-hover:border-cyan-400 shadow-lg transition-all duration-300"
                style={{
                  boxShadow: 'rgba(0, 0, 0, 0.3) 0px 10px 15px -3px, rgba(0, 0, 0, 0.2) 0px 4px 6px -2px'
                }}
                onError={handlePhotoError}
              />
            ) : (
              <div className="w-28 h-28 rounded-sm flex items-center justify-center bg-white/5 border-2 border-white/20">
                <User className="w-14 h-14 text-white/40" />
              </div>
            )}

            {/* Injury Badge Overlay - 프로필 사진 우측 상단 */}
            {injury && (
              <div className="absolute -top-1 -right-1">
                <InjuryBadge injury={injury} compact={true} />
              </div>
            )}
          </div>

          {/* Player Name & Info */}
          <div className="flex-1 min-w-0">
            <h3
              className={`
                font-grotesk font-bold text-white group-hover:text-cyan-400 transition-colors
                leading-tight line-clamp-2 mb-2
                ${
                  player.name.length > 20 ? 'text-lg' :
                  player.name.length > 15 ? 'text-xl' :
                  'text-2xl'
                }
              `}
              title={player.name}
            >
              {player.name}
            </h3>
            <div className="flex items-center gap-2 flex-wrap">
              {/* Position Badge - 축약어 + 포지션별 색상 */}
              <span className={`
                px-3 py-1 rounded-sm text-base font-bold border flex-shrink-0 uppercase tracking-wider font-mono
                ${getPositionBadgeColor(playerRole)}
              `}>
                {playerRole}
              </span>
              {player.number > 0 && (
                <span className="text-base text-cyan-400/80 font-mono font-bold">
                  #{player.number}
                </span>
              )}
              <p className="text-base text-white/50 truncate">
                {player.team}
              </p>
            </div>
          </div>
        </div>

        {/* Stats Grid - Single Color Background */}
        <div className="grid grid-cols-2 gap-2 mb-3">
          <motion.div
            className="bg-slate-900/60 border border-cyan-500/20 p-3 rounded-sm"
            whileHover={{ scale: 1.05, borderColor: 'rgba(6, 182, 212, 0.4)' }}
            transition={{ duration: 0.15, ease: "easeOut" }}
          >
            <div className="flex items-center justify-between gap-2">
              <div className="text-xs text-cyan-400/80 font-mono uppercase tracking-wider">나이</div>
              <div className="font-bold text-white font-mono text-base">{player.age}</div>
            </div>
          </motion.div>

          <motion.div
            className="bg-slate-900/60 border border-cyan-500/20 p-3 rounded-sm"
            whileHover={{ scale: 1.05, borderColor: 'rgba(6, 182, 212, 0.4)' }}
            transition={{ duration: 0.15, ease: "easeOut" }}
          >
            <div className="flex items-center justify-between gap-2">
              <div className="text-xs text-cyan-400/80 font-mono uppercase tracking-wider">출전</div>
              <div className="font-bold text-white font-mono text-base">
                {player.appearances || 0}
              </div>
            </div>
          </motion.div>

          <motion.div
            className="bg-slate-900/60 border border-cyan-500/20 p-3 rounded-sm"
            whileHover={{ scale: 1.05, borderColor: 'rgba(6, 182, 212, 0.4)' }}
            transition={{ duration: 0.15, ease: "easeOut" }}
          >
            <div className="flex items-center justify-between gap-2">
              <div className="text-xs text-cyan-400/80 font-mono uppercase tracking-wider">골</div>
              <div className="font-bold text-white font-mono text-base">
                {player.goals || 0}
              </div>
            </div>
          </motion.div>

          <motion.div
            className="bg-slate-900/60 border border-cyan-500/20 p-3 rounded-sm"
            whileHover={{ scale: 1.05, borderColor: 'rgba(6, 182, 212, 0.4)' }}
            transition={{ duration: 0.15, ease: "easeOut" }}
          >
            <div className="flex items-center justify-between gap-2">
              <div className="text-xs text-cyan-400/80 font-mono uppercase tracking-wider">어시스트</div>
              <div className="font-bold text-white font-mono text-base">
                {player.assists || 0}
              </div>
            </div>
          </motion.div>
        </div>

        {/* Average Rating - Single Color Background */}
        <motion.div
          className="bg-slate-900/60 border border-cyan-500/30 p-4 rounded-sm"
          whileHover={{ scale: 1.02, borderColor: 'rgba(6, 182, 212, 0.5)' }}
          transition={{ duration: 0.15, ease: "easeOut" }}
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
              <span className="text-sm text-cyan-400/80 font-mono uppercase tracking-wider">AVG RATING</span>
            </div>
            <div className="flex items-center gap-2">
              <motion.span
                className="text-2xl font-bold font-mono"
                style={{ color: colorSystem.color }}
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', stiffness: 300, delay: 0.2 }}
              >
                {displayRating.toFixed(2)}
              </motion.span>
              <span className="text-sm text-white/50 font-mono">/5.0</span>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="relative h-2 bg-slate-900/50 rounded-sm overflow-hidden border border-cyan-500/20">
            <motion.div
              className="absolute inset-0"
              style={{
                backgroundImage: colorSystem.gradient,
                boxShadow: `0 0 10px ${colorSystem.color}40`
              }}
              initial={{ width: 0 }}
              animate={{ width: `${(displayRating / 5) * 100}%` }}
              transition={{ duration: 0.8, ease: 'easeOut', delay: 0.3 }}
            />
          </div>
        </motion.div>
      </div>

      {/* Starter Badge */}
      {player.is_starter && (
        <motion.div
          className="absolute top-2 right-2"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', stiffness: 500, delay: 0.1 }}
        >
          <div className="w-2 h-2 rounded-full bg-success group-hover:shadow-glow transition-all" />
        </motion.div>
      )}
    </motion.div>
  );
};

export default PlayerCard;
