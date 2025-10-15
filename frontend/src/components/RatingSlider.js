import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Info } from 'lucide-react';

/**
 * RatingSlider Component - Premium Enhanced
 * 선수 능력치 평가를 위한 프리미엄 슬라이더
 * 범위: 0.0 ~ 5.0 (0.25 단위)
 *
 * 주요 개선사항:
 * - 빠른 설정 버튼 (Quick Set)
 * - 키보드 접근성 향상
 * - 시각적 구간 가이드
 * - 더블클릭 기본값 복귀
 * - 향상된 터치 제스처
 */
const RatingSlider = ({
  label,
  value,
  onChange,
  darkMode = false,
  disabled = false,
  showValue = true,
  helperText = null,
  weight = null,
  description = null
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);
  const [thumbPosition, setThumbPosition] = useState(0);
  const [isInitialLoad, setIsInitialLoad] = useState(true);

  const trackRef = useRef(null);
  const thumbRef = useRef(null);
  const sliderRef = useRef(null);
  const lastTapTime = useRef(0);

  // Ensure value is a valid number
  const numericValue = typeof value === 'number' && !isNaN(value) ? value : 0;

  // 0.0 ~ 5.0을 0 ~ 20으로 변환 (0.25 단위 = 20 steps)
  const sliderValue = Math.round(numericValue * 4);
  const maxSteps = 20; // 5.0 * 4

  // 값 변경 핸들러
  const handleSliderChange = (e) => {
    const steps = parseInt(e.target.value);
    const rating = steps / 4; // 0 ~ 20 -> 0.0 ~ 5.0
    onChange(rating);
  };

  // 더블 클릭으로 2.5(리그 평균)로 리셋
  const handleDoubleClick = () => {
    const now = Date.now();
    const timeSinceLastTap = now - lastTapTime.current;

    if (timeSinceLastTap < 300 && timeSinceLastTap > 0) {
      onChange(2.5);
    }

    lastTapTime.current = now;
  };

  // 키보드 핸들러 (향상된 접근성)
  const handleKeyDown = (e) => {
    if (disabled) return;

    let newValue = numericValue;

    switch(e.key) {
      case 'ArrowRight':
      case 'ArrowUp':
        e.preventDefault();
        newValue = Math.min(5.0, numericValue + 0.25);
        break;
      case 'ArrowLeft':
      case 'ArrowDown':
        e.preventDefault();
        newValue = Math.max(0.0, numericValue - 0.25);
        break;
      case 'Home':
        e.preventDefault();
        newValue = 0.0;
        break;
      case 'End':
        e.preventDefault();
        newValue = 5.0;
        break;
      case 'PageUp':
        e.preventDefault();
        newValue = Math.min(5.0, numericValue + 1.0);
        break;
      case 'PageDown':
        e.preventDefault();
        newValue = Math.max(0.0, numericValue - 1.0);
        break;
      default:
        return;
    }

    if (newValue !== numericValue) {
      onChange(newValue);
    }
  };

  // TPGi Method: thumb 너비를 고려한 정확한 percentage 계산
  useEffect(() => {
    if (!sliderRef.current || !thumbRef.current || !trackRef.current) return;

    const calculateThumbPosition = () => {
      const track = trackRef.current;
      const thumb = thumbRef.current;

      // DOM 요소가 없거나 마운트되지 않은 경우 early return
      if (!track || !thumb) return;

      const min = 0;
      const max = 5;

      // 정규화된 값 (0 ~ 1)
      const distance = (numericValue - min) / (max - min);

      // Track 너비에 대한 thumb 너비 비율로 offset 계산
      const offset = (thumb.offsetWidth / track.offsetWidth) * distance;

      // 최종 percentage (0~100% 사이로 제한)
      const position = Math.floor((distance - offset) * 100);
      const finalThumbPosition = Math.min(Math.max(position, 0), 100);

      setThumbPosition(finalThumbPosition);
    };

    calculateThumbPosition();

    // ResizeObserver로 반응형 처리
    const resizeObserver = new ResizeObserver(calculateThumbPosition);
    if (trackRef.current) {
      resizeObserver.observe(trackRef.current);
    }

    return () => resizeObserver.disconnect();
  }, [numericValue]);

  // Initial load animation
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsInitialLoad(false);
    }, 100);
    return () => clearTimeout(timer);
  }, []);

  // Marker 위치 계산 (TPGi Method 적용 - thumb와 동일한 방식)
  const getMarkerPosition = (markerValue) => {
    const track = trackRef.current;
    const thumb = thumbRef.current;

    // DOM 요소가 없거나 마운트되지 않은 경우 단순 계산
    if (!track || !thumb) {
      return (markerValue / 5) * 100;
    }

    const min = 0;
    const max = 5;

    const distance = (markerValue - min) / (max - min);
    const offset = (thumb.offsetWidth / track.offsetWidth) * distance;
    const position = Math.floor((distance - offset) * 100);
    const finalPosition = Math.min(Math.max(position, 0), 100);

    return finalPosition;
  };

  // 평가 등급 표시
  const getRatingLabel = (rating) => {
    if (rating >= 4.75) return { label: '월드클래스', emoji: '🌟' };
    if (rating >= 4.0) return { label: '최상위', emoji: '⭐' };
    if (rating >= 3.5) return { label: '상위권', emoji: '✨' };
    if (rating >= 3.0) return { label: '평균 이상', emoji: '💫' };
    if (rating >= 2.0) return { label: '평균', emoji: '⚡' };
    return { label: '평균 이하', emoji: '💭' };
  };

  // 대조적인 색상 시스템 (평균 기준 양방향)
  const getColorSystem = (rating) => {
    if (rating >= 4.5) {
      return {
        text: '#00FFFF',      // 형광 사이언 - 월드클래스
        fill: 'rgba(0, 255, 255, 0.8)',
        thumb: '#00FFFF',
        glow: 'rgba(0, 255, 255, 0.5)'
      };
    }
    if (rating >= 4.0) {
      return {
        text: '#60A5FA',      // 밝은 파랑 - 상위
        fill: 'rgba(96, 165, 250, 0.8)',
        thumb: '#60A5FA',
        glow: 'rgba(96, 165, 250, 0.5)'
      };
    }
    if (rating >= 3.0) {
      return {
        text: '#A855F7',      // 보라색 - 중상위
        fill: 'rgba(168, 85, 247, 0.8)',
        thumb: '#A855F7',
        glow: 'rgba(168, 85, 247, 0.5)'
      };
    }
    if (rating >= 2.0) {
      return {
        text: '#FBBF24',      // 노랑색 - 평균
        fill: 'rgba(251, 191, 36, 0.8)',
        thumb: '#FBBF24',
        glow: 'rgba(251, 191, 36, 0.5)'
      };
    }
    if (rating >= 1.5) {
      return {
        text: '#FB923C',      // 빛바랜 주황색 - 평균 이하
        fill: 'rgba(251, 146, 60, 0.8)',
        thumb: '#FB923C',
        glow: 'rgba(251, 146, 60, 0.5)'
      };
    }
    return {
      text: '#9CA3AF',        // 무채색 회색 - 하위
      fill: 'rgba(156, 163, 175, 0.8)',
      thumb: '#9CA3AF',
      glow: 'rgba(156, 163, 175, 0.5)'
    };
  };

  const ratingInfo = getRatingLabel(numericValue);
  const colorSystem = getColorSystem(numericValue);

  // 마커 위치
  const markers = [
    { value: 0, label: '0' },
    { value: 1.25, label: '1.25' },
    { value: 2.5, label: '2.5', highlight: true },
    { value: 3.75, label: '3.75' },
    { value: 5, label: '5' }
  ];

  return (
    <div className="mb-6">
      {/* Label & Value */}
      <div className="mb-3">
        <div className="flex justify-between items-start mb-1">
          <div className="flex items-start gap-2">
            <div className="flex flex-col gap-1 flex-1">
              <div className="flex items-center gap-2">
                <label className="text-lg font-medium text-white">
                  {label}
                </label>
                {weight && (
                  <span className="text-xs px-2 py-0.5 rounded-none bg-slate-900 text-white border border-cyan-500/40 font-mono">
                    {Math.round(weight * 100)}%
                  </span>
                )}
                {helperText && (
                  <div className="relative flex items-center">
                    <button
                      className="text-cyan-400/60 hover:text-cyan-300 transition-colors"
                      onMouseEnter={() => setShowTooltip(true)}
                      onMouseLeave={() => setShowTooltip(false)}
                    >
                      <Info className="w-4 h-4" />
                    </button>
                    <AnimatePresence>
                      {showTooltip && (
                        <motion.div
                          className="absolute left-6 -top-2 z-50 bg-slate-900/95 border border-cyan-500/40 p-2 rounded-none text-xs text-cyan-100 whitespace-nowrap backdrop-blur-sm"
                          initial={{ opacity: 0, x: -5 }}
                          animate={{ opacity: 1, x: 0 }}
                          exit={{ opacity: 0, x: -5 }}
                        >
                          {helperText}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                )}
              </div>
              {description && (
                <p className="text-xs text-white/50">
                  {description}
                </p>
              )}
            </div>
          </div>

          {showValue && (
            <motion.div
              className="flex items-center gap-2"
              initial={{ opacity: 0, filter: 'blur(10px)' }}
              animate={{
                opacity: 1,
                filter: 'blur(0px)',
                scale: isDragging ? 1.1 : 1
              }}
              transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1], delay: 0.3 }}
            >
              <motion.span
                className="text-2xl font-bold font-numeric"
                style={{ color: colorSystem.text }}
                key={numericValue}
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ type: 'spring', stiffness: 500 }}
              >
                {numericValue.toFixed(2)}
              </motion.span>
              <span className="text-xs text-white/40">/ 5.0</span>
            </motion.div>
          )}
        </div>

        {/* Rating Label */}
        {showValue && (
          <motion.div
            className="text-center"
            style={{ transform: 'translateX(-8px)' }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <span className="text-sm font-semibold" style={{ color: colorSystem.text }}>
              {ratingInfo.label}
            </span>
          </motion.div>
        )}
      </div>

      {/* Slider Container - Tech Style */}
      <div
        ref={trackRef}
        className="relative group px-4"
        onDoubleClick={handleDoubleClick}
        onClick={handleDoubleClick}
      >
        {/* Background Track - Tech Enhanced */}
        <div className="relative h-5 bg-slate-900/50 rounded-none overflow-hidden border border-cyan-500/20">
          {/* Grid Pattern */}
          <div
            className="absolute inset-0 opacity-10"
            style={{
              backgroundImage: `
                linear-gradient(rgba(6, 182, 212, 0.3) 1px, transparent 1px),
                linear-gradient(90deg, rgba(6, 182, 212, 0.3) 1px, transparent 1px)
              `,
              backgroundSize: '4px 4px'
            }}
          />

          {/* Progress Fill with Glow */}
          <motion.div
            className="h-full relative z-0"
            style={{
              backgroundColor: colorSystem.fill,
              boxShadow: `0 0 10px ${colorSystem.glow}, inset 0 1px 0 rgba(255,255,255,0.1)`
            }}
            initial={{ width: 0 }}
            animate={{ width: `${(numericValue / 5) * 100}%` }}
            transition={{
              duration: isInitialLoad ? 0.8 : 0.15,
              ease: isInitialLoad ? [0.22, 1, 0.36, 1] : "easeOut",
              delay: isInitialLoad ? 0.1 : 0
            }}
          >
            {/* Animated Scan Line */}
            <motion.div
              className="absolute top-0 bottom-0 w-[2px]"
              style={{
                background: 'linear-gradient(to bottom, transparent, rgba(255,255,255,0.5), transparent)',
                right: 0
              }}
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
        </div>

        {/* Actual Range Input - 키보드 접근성 향상 */}
        <input
          ref={sliderRef}
          type="range"
          min="0"
          max={maxSteps}
          step="1"
          value={sliderValue}
          onChange={handleSliderChange}
          onKeyDown={handleKeyDown}
          onMouseDown={() => setIsDragging(true)}
          onMouseUp={() => setIsDragging(false)}
          onTouchStart={() => setIsDragging(true)}
          onTouchEnd={() => setIsDragging(false)}
          disabled={disabled}
          className="absolute top-0 left-0 w-full h-5 opacity-0 cursor-pointer z-20"
          style={{
            cursor: disabled ? 'not-allowed' : 'pointer',
            padding: 0,
            margin: 0
          }}
          aria-label={`${label} (현재 값: ${numericValue.toFixed(2)})`}
          aria-valuemin={0}
          aria-valuemax={5}
          aria-valuenow={numericValue}
          aria-valuetext={`${ratingInfo.label} - ${numericValue.toFixed(2)}`}
        />

        {/* Custom Thumb - Tech Square Style */}
        {/* 🔧 저장 중 깜빡임 방지: disabled 상태에서도 opacity 유지 (2025-10-08) */}
        <motion.div
          ref={thumbRef}
          className="absolute pointer-events-none z-30"
          style={{
            left: `${thumbPosition}%`,
            top: '-2px',
            transform: 'translateX(-50%)',
            width: '24px',
            height: '24px'
          }}
          animate={{
            scale: isDragging ? 1.3 : 1
          }}
          transition={{ duration: 0.1 }}
        >
          {/* Outer Glow */}
          <motion.div
            className="absolute inset-0 rounded-sm blur-md"
            style={{ backgroundColor: colorSystem.glow }}
            animate={{
              opacity: isDragging ? [0.5, 0.8, 0.5] : 0.3
            }}
            transition={{
              duration: 1,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />

          {/* Square Body */}
          <div className="relative w-full h-full flex items-center justify-center rounded-sm">
            {/* Background */}
            <div
              className="absolute inset-0 rounded-sm"
              style={{
                background: `linear-gradient(135deg, ${colorSystem.thumb}, ${colorSystem.fill})`,
                boxShadow: `0 0 15px ${colorSystem.glow}`
              }}
            />

            {/* Inner Border */}
            <div
              className="absolute inset-[2px] rounded-sm"
              style={{
                background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.9))'
              }}
            />

            {/* Center Dot */}
            <div
              className="relative w-1.5 h-1.5 rounded-sm"
              style={{
                backgroundColor: colorSystem.thumb,
                boxShadow: `0 0 6px ${colorSystem.glow}`
              }}
            />
          </div>
        </motion.div>
      </div>

      {/* Markers */}
      <div className="relative h-6 mt-3">
        {markers.map(({ value, label, highlight }) => {
          const markerPosition = getMarkerPosition(value);
          const transformValue = value === 0 ? 'translateX(0)' :
                                value === 5 ? 'translateX(-100%)' :
                                'translateX(-50%)';

          return (
            <div
              key={value}
              className={`
                absolute text-xs
                ${numericValue === value
                  ? 'font-bold'
                  : 'text-white/50'
                }
              `}
              style={{
                color: numericValue === value ? colorSystem.text : undefined,
                left: `calc(${markerPosition}% + 12px)`,
                transform: transformValue
              }}
            >
              {label}
            </div>
          );
        })}
      </div>


      {/* Custom Styling for Range Input Thumb (fallback) */}
      <style jsx>{`
        input[type="range"]::-webkit-slider-thumb {
          -webkit-appearance: none;
          appearance: none;
          width: 0;
          height: 0;
          opacity: 0;
        }

        input[type="range"]::-moz-range-thumb {
          width: 0;
          height: 0;
          opacity: 0;
          border: none;
          background: transparent;
        }
      `}</style>
    </div>
  );
};

export default RatingSlider;
