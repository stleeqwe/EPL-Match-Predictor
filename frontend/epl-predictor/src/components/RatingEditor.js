import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence, useMotionValue, useTransform, animate } from 'framer-motion';
import { Save, RotateCcw, X, MessageSquare, ArrowLeft, User, Check, Sparkles, Zap } from 'lucide-react';
import RatingSlider from './RatingSlider';
import {
  POSITION_ATTRIBUTES,
  getSubPositions,
  DEFAULT_SUB_POSITION,
  calculateWeightedAverage
} from '../config/positionAttributes';
import { getPlayerPhotoUrl } from '../utils/playerPhoto';

/**
 * RatingEditor Component - Enhanced with Framer Motion
 * 포지션별 선수 능력치 편집기 (세부 포지션 지원)
 */
const RatingEditor = ({
  player,
  darkMode = false,
  onSave,
  onCancel,
  initialRatings = {}
}) => {
  const [ratings, setRatings] = useState({});
  const [isSaving, setIsSaving] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [subPosition, setSubPosition] = useState('');
  const [comment, setComment] = useState('');
  const [photoError, setPhotoError] = useState(false);

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

  // Animated counter for avg.value
  const avgValueMotion = useMotionValue(0);
  const avgValueDisplay = useTransform(avgValueMotion, (latest) => latest.toFixed(2));

  // initialRatings의 최신 값을 항상 참조
  const initialRatingsRef = useRef(initialRatings);
  useEffect(() => {
    initialRatingsRef.current = initialRatings;
  }, [initialRatings]);

  // 초기화
  useEffect(() => {
    const position = player.position || 'MF';
    
    let savedSubPosition;
    if (POSITION_ATTRIBUTES[position]) {
      savedSubPosition = initialRatings._subPosition || position;
    } else {
      savedSubPosition = initialRatings._subPosition || DEFAULT_SUB_POSITION[position] || 'CM';
    }

    setSubPosition(savedSubPosition);

    const attributes = POSITION_ATTRIBUTES[savedSubPosition]?.attributes || [];
    const initialState = {};
    attributes.forEach(attr => {
      initialState[attr.key] = initialRatings[attr.key] || 2.5;
    });

    setRatings(initialState);
    setComment(initialRatings._comment || '');
    setHasChanges(false);
  }, [player.id]);

  // 세부 포지션 변경
  const handleSubPositionChange = (newSubPosition) => {
    const attributes = POSITION_ATTRIBUTES[newSubPosition]?.attributes || [];
    const newRatings = {};
    const latestInitialRatings = initialRatingsRef.current;

    attributes.forEach(attr => {
      newRatings[attr.key] = latestInitialRatings[attr.key] || ratings[attr.key] || 2.5;
    });

    setSubPosition(newSubPosition);
    setRatings(newRatings);
    setHasChanges(false);
  };

  // 능력치 변경
  const handleRatingChange = (attributeKey, value) => {
    setRatings(prev => ({
      ...prev,
      [attributeKey]: value
    }));
    setHasChanges(true);
  };

  // 코멘트 변경
  const handleCommentChange = (e) => {
    const value = e.target.value;
    if (value.length <= 500) {
      setComment(value);
      setHasChanges(true);
    }
  };

  // 저장
  const handleSave = async () => {
    setIsSaving(true);
    setIsSaved(false);
    try {
      const dataToSave = {
        ...ratings,
        _subPosition: subPosition,
        _comment: comment
      };
      await onSave(player.id, dataToSave);
      setHasChanges(false);
      setIsSaved(true);

      // 2초 후 저장 완료 상태 초기화
      setTimeout(() => {
        setIsSaved(false);
      }, 2000);
    } catch (error) {
      console.error('Failed to save ratings:', error);
    } finally {
      setIsSaving(false);
    }
  };

  // 초기화
  const handleReset = () => {
    const attributes = POSITION_ATTRIBUTES[subPosition]?.attributes || [];
    const resetState = {};
    attributes.forEach(attr => {
      resetState[attr.key] = 2.5;
    });

    setRatings(resetState);
    setComment('');
    setHasChanges(true);
  };

  const position = player.position || 'MF';
  const playerRole = getPlayerRole(player.position);
  const availableSubPositions = getSubPositions(position);
  const attributes = POSITION_ATTRIBUTES[subPosition]?.attributes || [];
  const positionInfo = POSITION_ATTRIBUTES[subPosition];
  const weightedAverage = calculateWeightedAverage(ratings, subPosition) || 0;
  const photoUrl = player.photo ? getPlayerPhotoUrl(player.photo, '250x250') : null;

  // Animate counter when weightedAverage changes
  useEffect(() => {
    const controls = animate(avgValueMotion, weightedAverage, {
      duration: 1.2,
      ease: "easeOut",
      delay: 0.3
    });
    return controls.stop;
  }, [weightedAverage, avgValueMotion]);

  // 포지션 색상 클래스
  const getPositionClass = (pos) => {
    if (pos === 'GK') return 'bg-position-gk/20 text-position-gk';
    if (pos === 'CB' || pos === 'FB') return 'bg-position-df/20 text-position-df';
    if (pos === 'DM' || pos === 'CM' || pos === 'CAM') return 'bg-position-mf/20 text-position-mf';
    return 'bg-position-fw/20 text-position-fw';
  };

  // 대조적인 색상 시스템 (평균 기준 양방향)
  const getColorSystem = (avg) => {
    if (avg >= 4.5) {
      return {
        label: '월드클래스',
        color: '#00FFFF',      // 형광 사이언 - 월드클래스
        gradient: 'linear-gradient(to right, rgba(0, 255, 255, 0.5), rgba(0, 255, 255, 0.2))',
        emoji: '🌟'
      };
    }
    if (avg >= 4.0) {
      return {
        label: '최상위',
        color: '#60A5FA',      // 밝은 파랑 - 상위
        gradient: 'linear-gradient(to right, rgba(96, 165, 250, 0.5), rgba(96, 165, 250, 0.2))',
        emoji: '⭐'
      };
    }
    if (avg >= 3.0) {
      return {
        label: '상위권',
        color: '#A855F7',      // 보라색 - 중상위
        gradient: 'linear-gradient(to right, rgba(168, 85, 247, 0.45), rgba(168, 85, 247, 0.18))',
        emoji: '✨'
      };
    }
    if (avg >= 2.0) {
      return {
        label: '평균',
        color: '#FBBF24',      // 노랑색 - 평균
        gradient: 'linear-gradient(to right, rgba(251, 191, 36, 0.45), rgba(251, 191, 36, 0.18))',
        emoji: '⚡'
      };
    }
    if (avg >= 1.5) {
      return {
        label: '평균 이하',
        color: '#FB923C',      // 빛바랜 주황색 - 평균 이하
        gradient: 'linear-gradient(to right, rgba(251, 146, 60, 0.45), rgba(251, 146, 60, 0.18))',
        emoji: '💭'
      };
    }
    return {
      label: '하위',
      color: '#9CA3AF',        // 무채색 회색 - 하위
      gradient: 'linear-gradient(to right, rgba(156, 163, 175, 0.45), rgba(156, 163, 175, 0.18))',
      emoji: '📉'
    };
  };

  const colorSystem = getColorSystem(weightedAverage);

  return (
    <motion.div
      className="relative overflow-hidden bg-gradient-to-br from-slate-900/60 via-blue-950/40 to-slate-900/60 backdrop-blur-sm rounded border border-cyan-500/20 shadow-2xl p-4 md:p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
    >
      {/* Tech Grid Background */}
      <div
        className="absolute inset-0 opacity-[0.02] pointer-events-none"
        style={{
          backgroundImage: `
            linear-gradient(rgba(6, 182, 212, 0.5) 1px, transparent 1px),
            linear-gradient(90deg, rgba(6, 182, 212, 0.5) 1px, transparent 1px)
          `,
          backgroundSize: '30px 30px'
        }}
      />

      {/* Back Button */}
      {onCancel && (
        <motion.button
          onClick={onCancel}
          disabled={isSaving}
          className="relative mb-4 px-4 py-2 rounded-sm font-medium flex items-center gap-2 text-sm bg-slate-900/50 text-white border border-cyan-500/30 hover:bg-cyan-500/10 hover:border-cyan-500/50 transition-all duration-200"
          whileHover={!isSaving ? { scale: 1.02, x: -2 } : {}}
          whileTap={!isSaving ? { scale: 0.98 } : {}}
        >
          <ArrowLeft className="w-4 h-4" />
          <span className="font-mono uppercase text-xs tracking-wider">이전</span>
        </motion.button>
      )}

      {/* Main Layout: Sidebar + Content */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Left Sidebar: Tech-Enhanced Player Profile */}
        <div className="lg:col-span-1 lg:border-r lg:border-cyan-500/20 lg:pr-6">
          <motion.div
            className="relative overflow-hidden rounded bg-gradient-to-br from-slate-900/80 via-blue-950/60 to-slate-900/80 backdrop-blur-sm border border-cyan-500/20 shadow-lg p-6"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
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

            <div className="relative space-y-6">
              {/* Player Photo with Tech Frame */}
              <div className="flex justify-center">
                <div className="relative">
                  {/* Corner Brackets */}
                  <div className="absolute -top-2 -left-2 w-4 h-4 border-l-2 border-t-2 border-cyan-400 z-20" />
                  <div className="absolute -top-2 -right-2 w-4 h-4 border-r-2 border-t-2 border-cyan-400 z-20" />
                  <div className="absolute -bottom-2 -left-2 w-4 h-4 border-l-2 border-b-2 border-cyan-400 z-20" />
                  <div className="absolute -bottom-2 -right-2 w-4 h-4 border-r-2 border-b-2 border-cyan-400 z-20" />

                  {/* Data Grid Overlay - Behind Photo */}
                  <motion.div
                    className="absolute inset-0 pointer-events-none z-0 overflow-hidden rounded-sm"
                    style={{
                      backgroundImage: `
                        linear-gradient(rgba(6, 182, 212, 0.3) 1px, transparent 1px),
                        linear-gradient(90deg, rgba(6, 182, 212, 0.3) 1px, transparent 1px)
                      `,
                      backgroundSize: '8px 8px'
                    }}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: [0, 0.6, 0] }}
                    transition={{
                      duration: 4.5,
                      repeat: Infinity,
                      ease: "linear"
                    }}
                  />

                  {/* Enhanced Scan Line Effect */}
                  <div className="absolute inset-0 pointer-events-none z-10 overflow-hidden rounded-sm">
                    {/* Main Scan Line */}
                    <motion.div
                      className="absolute left-0 right-0"
                      animate={{
                        top: ['0%', '100%']
                      }}
                      transition={{
                        duration: 4.5,
                        repeat: Infinity,
                        ease: "linear"
                      }}
                    >
                      {/* Glow Above */}
                      <div className="absolute left-0 right-0 h-8 -top-8 bg-gradient-to-b from-transparent to-cyan-400/20" style={{ filter: 'blur(8px)' }} />

                      {/* Main Bright Line */}
                      <div className="absolute left-0 right-0 h-[1.5px] bg-gradient-to-r from-transparent via-cyan-400/80 to-transparent" style={{ boxShadow: '0 0 6px rgba(6, 182, 212, 0.6)' }} />

                      {/* Glow Below */}
                      <div className="absolute left-0 right-0 h-8 top-0 bg-gradient-to-t from-transparent to-cyan-400/20" style={{ filter: 'blur(8px)' }} />
                    </motion.div>
                  </div>

                  {photoUrl && !photoError ? (
                    <motion.img
                      src={photoUrl}
                      alt={player.name}
                      className="w-48 h-48 rounded-sm object-cover border-2 border-cyan-500/30 relative z-5"
                      style={{
                        boxShadow: '0 0 20px rgba(6, 182, 212, 0.3)'
                      }}
                      onError={() => setPhotoError(true)}
                      whileHover={{ scale: 1.02 }}
                      transition={{ duration: 0.2 }}
                    />
                  ) : (
                    <motion.div
                      className="w-48 h-48 rounded-sm flex items-center justify-center bg-slate-900/50 border-2 border-cyan-500/30 relative z-5 overflow-hidden"
                      style={{
                        boxShadow: '0 0 20px rgba(6, 182, 212, 0.3)'
                      }}
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ type: 'spring', stiffness: 500 }}
                    >
                      <User className="w-24 h-24 text-cyan-400/40" />
                    </motion.div>
                  )}
                </div>
              </div>

              {/* Player Info */}
              <div className="space-y-3">
                <motion.h2
                  className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-400 text-center"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                >
                  {player.name}
                </motion.h2>

                <div className="text-center space-y-2">
                  <p className="text-sm text-white/90 font-mono uppercase tracking-wider">
                    {player.team}
                  </p>
                  {/* Single line: Position, Number, Age */}
                  <div className="flex items-center justify-center gap-2 text-sm">
                    <span className={`px-2 py-1 rounded-sm text-xs font-bold border font-mono uppercase ${getPositionBadgeColor(playerRole)}`}>
                      {playerRole}
                    </span>
                    <span className="text-cyan-300/60">•</span>
                    <span className="text-white/80 font-mono">#{player.number || '?'}</span>
                    <span className="text-cyan-300/60">•</span>
                    <span className="text-white/80 font-mono">{player.age}세</span>
                  </div>
                </div>
              </div>

              {/* Tech Divider */}
              <div className="relative h-[1px] bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent" />

              {/* AVG.RATING Section - Tech Style */}
              <div className="relative text-center space-y-4">
                <div className="flex items-center justify-center gap-2">
                  <div className="w-1 h-1 rounded-full bg-cyan-400 animate-pulse" />
                  <span className="text-xs font-bold text-cyan-400 tracking-widest font-mono uppercase">AVG.RATING</span>
                  <div className="w-1 h-1 rounded-full bg-cyan-400 animate-pulse" />
                </div>

                <div className="relative inline-block">
                  {/* Glow Effect */}
                  <motion.div
                    className="absolute inset-0 blur-xl"
                    style={{ backgroundColor: colorSystem.color, opacity: 0.15 }}
                    animate={{
                      scale: [1, 1.05, 1],
                      opacity: [0.15, 0.25, 0.15]
                    }}
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                      ease: "easeInOut"
                    }}
                  />

                  <motion.span
                    className="relative text-7xl font-bold font-numeric"
                    style={{
                      color: colorSystem.color,
                      textShadow: `0 0 10px ${colorSystem.color}`
                    }}
                    initial={{ scale: 0.5, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ type: 'spring', stiffness: 300, delay: 0.2 }}
                  >
                    {avgValueDisplay}
                  </motion.span>
                </div>

                {/* Grade Badge */}
                <div className="flex items-center justify-center gap-2">
                  <div
                    className="text-sm font-semibold font-mono uppercase tracking-wider"
                    style={{ color: colorSystem.color }}
                  >
                    {colorSystem.label}
                  </div>
                </div>

                {/* Tech Progress Bar */}
                <div className="relative h-3 bg-slate-900/50 rounded-none overflow-hidden border border-cyan-500/20">
                  <motion.div
                    className="h-full relative"
                    style={{
                      background: `linear-gradient(90deg, ${colorSystem.color}, ${colorSystem.fill})`,
                      boxShadow: `0 0 10px ${colorSystem.color}`
                    }}
                    initial={{ width: 0 }}
                    animate={{ width: `${(weightedAverage / 5) * 100}%` }}
                    transition={{ duration: 0.8, ease: 'easeOut' }}
                  >
                    {/* Animated Scan Line */}
                    <motion.div
                      className="absolute top-0 bottom-0 w-[2px] bg-white/50 right-0"
                      animate={{
                        opacity: [0.3, 1, 0.3]
                      }}
                      transition={{
                        duration: 1.5,
                        repeat: Infinity,
                        ease: "easeInOut"
                      }}
                    />
                  </motion.div>

                  {/* Grid Pattern */}
                  <div
                    className="absolute inset-0 opacity-10 pointer-events-none"
                    style={{
                      backgroundImage: `
                        linear-gradient(rgba(6, 182, 212, 0.5) 1px, transparent 1px),
                        linear-gradient(90deg, rgba(6, 182, 212, 0.5) 1px, transparent 1px)
                      `,
                      backgroundSize: '3px 3px'
                    }}
                  />
                </div>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Right Content: Rating Sliders - Tech Enhanced */}
        <div className="lg:col-span-3 space-y-3">
          {/* Rating Sliders Container */}
          <motion.div
            className="relative bg-gradient-to-br from-slate-900/80 via-blue-950/60 to-slate-900/80 backdrop-blur-sm rounded border border-cyan-500/20 shadow-lg overflow-hidden"
            initial={{ opacity: 0, scale: 0.95, rotateX: -5 }}
            animate={{ opacity: 1, scale: 1, rotateX: 0 }}
            transition={{ duration: 0.5, ease: "easeOut", delay: 0.1 }}
          >
            {/* Tech Grid Pattern Overlay */}
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

            {/* Header with Tech Style */}
            <div className="relative p-6 pb-4">
              <motion.div
                className="flex items-center justify-between gap-4 mb-4"
                initial={{ opacity: 0, y: -20, filter: 'blur(5px)' }}
                animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
                transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1], delay: 0.15 }}
              >
                <motion.div
                  className="flex items-center gap-3"
                  initial={{ x: -30 }}
                  animate={{ x: 0 }}
                  transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1], delay: 0.25 }}
                >
                  <motion.h3
                    className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-400"
                    style={{ fontFamily: 'SF Mono, Roboto Mono, monospace', letterSpacing: '0.1em' }}
                    initial={{ opacity: 0, letterSpacing: '0.5em' }}
                    animate={{ opacity: 1, letterSpacing: '0.1em' }}
                    transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1], delay: 0.35 }}
                  >
                    PLAYER VALUATION
                  </motion.h3>
                </motion.div>

                {/* Sub Position Selection - Tech Style */}
                <AnimatePresence mode="wait">
                  {availableSubPositions.length > 1 && (
                    <motion.div
                      initial={{ opacity: 0, x: 10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 10 }}
                      className="flex items-center gap-2"
                    >
                      {availableSubPositions.map(pos => (
                        <motion.button
                          key={pos}
                          onClick={() => handleSubPositionChange(pos)}
                          disabled={isSaving}
                          className={`
                            relative px-4 py-2 rounded-sm font-semibold text-xs transition-all overflow-hidden
                            ${subPosition === pos
                              ? 'bg-cyan-500/20 text-white border border-cyan-500/50'
                              : 'bg-white/5 text-white/60 border border-white/10 hover:border-cyan-500/30 hover:text-white'}
                          `}
                          whileHover={{ scale: isSaving ? 1 : 1.05 }}
                          whileTap={{ scale: isSaving ? 1 : 0.95 }}
                        >
                          {subPosition === pos && (
                            <motion.div
                              className="absolute inset-0 bg-cyan-400/10"
                              layoutId="activePosition"
                              transition={{ type: "spring", stiffness: 300, damping: 30 }}
                            />
                          )}
                          <span className="relative">{POSITION_ATTRIBUTES[pos]?.name}</span>
                        </motion.button>
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>

              {/* Tech Divider */}
              <div className="relative h-[1px] bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent" />
            </div>

            {/* Sliders Section with Enhanced Scroll */}
            <div className="relative px-6 pb-6 max-h-[calc(100vh-20rem)] overflow-y-auto scrollbar-thin scrollbar-thumb-cyan-500/30 scrollbar-track-transparent">
              <div className="space-y-1">
                {attributes.map((attr, index) => (
                  <React.Fragment key={attr.key}>
                    <motion.div
                      className="relative group py-4 px-4 -mx-4 rounded-sm transition-all duration-300 hover:bg-cyan-500/5 hover:shadow-lg hover:shadow-cyan-500/10"
                      initial={{
                        opacity: 0,
                        filter: 'blur(5px)'
                      }}
                      animate={{
                        opacity: 1,
                        filter: 'blur(0px)'
                      }}
                      transition={{
                        delay: 0.2 + index * 0.05,
                        duration: 0.4,
                        ease: "easeOut"
                      }}
                    >
                      <RatingSlider
                        label={attr.label}
                        value={ratings[attr.key] || 2.5}
                        onChange={(value) => handleRatingChange(attr.key, value)}
                        darkMode={darkMode}
                        disabled={isSaving}
                        weight={attr.weight}
                        helperText={`전체 평가의 ${Math.round(attr.weight * 100)}%`}
                        description={attr.description}
                      />
                    </motion.div>

                    {/* Tech Divider */}
                    {index < attributes.length - 1 && (
                      <div className="relative h-[1px] my-2">
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-500/30 to-transparent" />
                      </div>
                    )}
                  </React.Fragment>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Comment Input - Tech Style */}
          <motion.div
            className="relative bg-gradient-to-br from-slate-900/80 via-blue-950/60 to-slate-900/80 backdrop-blur-sm rounded p-6 border border-cyan-500/20 shadow-lg overflow-hidden"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            {/* Grid Pattern */}
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

            <div className="relative mb-4">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="relative">
                    <div className="absolute inset-0 bg-cyan-500/20 blur-lg" />
                    <MessageSquare className="relative w-5 h-5 text-cyan-400" />
                  </div>
                  <label className="text-lg font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-400">
                    COMMENT
                  </label>
                </div>

                {/* AI Notice */}
                <div className="flex items-center gap-2">
                  <motion.div
                    animate={{
                      rotate: [0, 10, -10, 10, 0],
                      scale: [1, 1.1, 1, 1.1, 1]
                    }}
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                      repeatDelay: 1
                    }}
                  >
                    <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                  </motion.div>
                  <span className="text-xs font-medium text-white/90 font-mono">입력하신 코멘트는 AI가상대결에 참조됩니다.</span>
                </div>
              </div>

              {/* Tech Divider */}
              <div className="relative h-[1px] bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent mb-4" />
            </div>

            <div className="relative">
              <textarea
                value={comment}
                onChange={handleCommentChange}
                disabled={isSaving}
                placeholder="선수에 대한 평가나 특징을 입력하세요..."
                rows={3}
                className="w-full px-4 py-3 bg-slate-900/50 border border-cyan-500/30 rounded-sm text-white placeholder-cyan-400/40 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all resize-none text-base font-mono"
                style={{
                  boxShadow: 'inset 0 0 10px rgba(6, 182, 212, 0.1)'
                }}
              />
              <div className="flex justify-between items-center mt-3">
                <p className="text-xs text-white/70 font-mono">
                  선수의 강점, 약점, 플레이 스타일 등을 자유롭게 기록하세요
                </p>
                <div className="flex items-center gap-2">
                  <div className="w-1 h-1 rounded-full bg-cyan-400 animate-pulse" />
                  <p className="text-xs text-white/90 font-mono font-semibold">
                    {comment.length}/500
                  </p>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Actions - Tech Style */}
          <motion.div
            className="flex flex-col sm:flex-row gap-3"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <motion.button
              onClick={handleSave}
              disabled={!hasChanges || isSaving || isSaved}
              className={`
            relative overflow-hidden flex-1 px-6 py-3 rounded-sm font-bold flex items-center justify-center gap-2 text-base
            transition-all duration-300 focus:outline-none border font-mono uppercase tracking-wider text-sm
            ${isSaved
              ? 'bg-green-500/20 text-green-100 border-green-500/50'
              : (hasChanges && !isSaving)
              ? 'bg-cyan-500/20 text-cyan-50 border-cyan-500/50 hover:bg-cyan-500/30'
              : 'bg-slate-900/30 text-cyan-400/30 cursor-not-allowed border-cyan-500/10'}
              `}
              style={{
                boxShadow: (hasChanges && !isSaving) ? '0 0 20px rgba(6, 182, 212, 0.2)' : 'none'
              }}
              whileHover={hasChanges && !isSaving && !isSaved ? { scale: 1.02, y: -2 } : {}}
              whileTap={hasChanges && !isSaving && !isSaved ? { scale: 0.98 } : {}}
              animate={isSaved ? { scale: [1, 1.05, 1] } : {}}
              transition={{ duration: 0.3 }}
            >
              {isSaved ? (
                <>
                  <Check className="w-4 h-4" />
                  저장 완료
                </>
              ) : isSaving ? (
                <>
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  >
                    <Save className="w-4 h-4" />
                  </motion.div>
                  저장 중...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  저장
                </>
              )}
            </motion.button>

            <motion.button
              onClick={handleReset}
              disabled={isSaving}
              className={`
                relative px-6 py-3 rounded-sm font-bold flex items-center justify-center gap-2 text-base
                bg-purple-500/20 text-purple-100 border border-purple-500/50
                hover:bg-purple-500/30
                disabled:bg-slate-900/30 disabled:text-purple-400/30 disabled:border-purple-500/10 disabled:cursor-not-allowed
                transition-all duration-300 font-mono uppercase tracking-wider text-sm
              `}
              style={{
                boxShadow: !isSaving ? '0 0 20px rgba(168, 85, 247, 0.2)' : 'none'
              }}
              whileHover={!isSaving ? { scale: 1.02, y: -2 } : {}}
              whileTap={!isSaving ? { scale: 0.98 } : {}}
            >
              <RotateCcw className="w-4 h-4" />
              초기화
            </motion.button>

            {onCancel && (
              <motion.button
                onClick={onCancel}
                disabled={isSaving}
                className={`
                  relative px-6 py-3 rounded-sm font-bold flex items-center justify-center gap-2 text-base
                  bg-red-500/20 text-red-100 border border-red-500/50
                  hover:bg-red-500/30
                  disabled:opacity-50 disabled:cursor-not-allowed
                  transition-all duration-300 font-mono uppercase tracking-wider text-sm
                `}
                style={{
                  boxShadow: !isSaving ? '0 0 20px rgba(239, 68, 68, 0.2)' : 'none'
                }}
                whileHover={!isSaving ? { scale: 1.02, y: -2 } : {}}
                whileTap={!isSaving ? { scale: 0.98 } : {}}
              >
                <X className="w-4 h-4" />
                <span className="hidden sm:inline">취소</span>
              </motion.button>
            )}
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
};

export default RatingEditor;
