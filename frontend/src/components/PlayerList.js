import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Filter, SortAsc, Users, Check, ChevronDown } from 'lucide-react';
import PlayerCard from './PlayerCard';
import { calculateWeightedAverage, DEFAULT_SUB_POSITION } from '../config/positionAttributes';
import { injuriesAPI } from '../services/api';

/**
 * PlayerList Component - Enhanced with Framer Motion
 * 팀별 선수 목록
 */
const PlayerList = ({
  team,
  players: playersProp, // 🔧 부모에서 전달된 선수 목록 (optional)
  darkMode = false,
  onPlayerSelect,
  playerRatings = {}
}) => {
  const [playersState, setPlayersState] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dataTransitioning, setDataTransitioning] = useState(false); // 🔧 데이터 전환 중
  const [error, setError] = useState(null);
  const [positionFilter, setPositionFilter] = useState('ALL');
  const [sortBy, setSortBy] = useState('rating'); // rating, name, number
  const [showFilters, setShowFilters] = useState(false);
  const [isSortOpen, setIsSortOpen] = useState(false);
  const [isPositionOpen, setIsPositionOpen] = useState(false);
  const [injuryFilter, setInjuryFilter] = useState('ALL'); // ALL, AVAILABLE, INJURED
  const [injuries, setInjuries] = useState([]); // 부상자 목록
  const [injuriesLoading, setInjuriesLoading] = useState(false);
  const sortDropdownRef = useRef(null);
  const positionDropdownRef = useRef(null);

  // 🔧 props로 전달받은 players가 있으면 사용, 없으면 state 사용
  const players = playersProp || playersState;

  /**
   * 📝 포지션 텍스트를 파싱하여 약어로 변환
   * @param {string} positionText - 전체 포지션 텍스트 (예: "Central Defender #12")
   * @returns {string|null} - 포지션 약어 ('GK', 'DF', 'MF', 'FW') 또는 null
   */
  const parsePosition = (positionText) => {
    if (!positionText) return null;

    const text = positionText.toLowerCase();

    // Goalkeeper
    if (text.includes('goalkeeper') || text.includes('keeper')) {
      return 'GK';
    }

    // Defender (Defender, Back)
    if (text.includes('defender') || text.includes('back')) {
      return 'DF';
    }

    // Midfielder
    if (text.includes('midfielder') || text.includes('midfield')) {
      return 'MF';
    }

    // Forward/Striker/Winger
    if (text.includes('striker') || text.includes('forward') || text.includes('winger') || text.includes('wing')) {
      return 'FW';
    }

    return null;
  };

  // 드롭다운 외부 클릭 감지
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (sortDropdownRef.current && !sortDropdownRef.current.contains(event.target)) {
        setIsSortOpen(false);
      }
      if (positionDropdownRef.current && !positionDropdownRef.current.contains(event.target)) {
        setIsPositionOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // 팀 변경 시 포지션 필터 초기화 및 부상자 데이터 페칭
  useEffect(() => {
    if (team) {
      setPositionFilter('ALL');
      setInjuryFilter('ALL');
      fetchInjuries();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [team]);

  // 선수 목록 로드 (props로 전달받지 않은 경우에만)
  useEffect(() => {
    // 🔧 props로 players가 제공되면 자체 fetch 스킵
    if (playersProp) {
      setLoading(false);
      setDataTransitioning(false);
      return;
    }

    if (team) {
      // 첫 로딩이 아니면 데이터 전환 모드
      if (playersState.length > 0) {
        setDataTransitioning(true);
      }
      fetchPlayers();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [team, playersProp]);

  const fetchPlayers = async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:5001/api/squad/${encodeURIComponent(team)}`);

      if (!response.ok) throw new Error('Failed to fetch players');

      const data = await response.json();
      const playersList = data.squad || [];

      setPlayersState(playersList);
      setError(null);
    } catch (err) {
      console.error('❌ Error fetching players:', err);
      setError('선수 목록을 불러오지 못했습니다');
    } finally {
      setLoading(false);
      setDataTransitioning(false); // 🔧 데이터 전환 완료
    }
  };

  // 부상자 데이터 페칭
  const fetchInjuries = async () => {
    if (!team) return;

    try {
      setInjuriesLoading(true);
      const response = await injuriesAPI.getTeamInjuries(team);

      if (response.success) {
        setInjuries(response.injuries || []);
      } else {
        setInjuries([]);
      }
    } catch (err) {
      console.error('❌ Error fetching injuries:', err);
      setInjuries([]);
    } finally {
      setInjuriesLoading(false);
    }
  };

  // 선수가 부상 중인지 확인
  const getPlayerInjury = (playerName) => {
    return injuries.find(injury =>
      injury.player_name && playerName &&
      injury.player_name.toLowerCase() === playerName.toLowerCase()
    );
  };

  // 평균 능력치 계산
  const getAverageRating = (playerId, playerPosition) => {
    const ratings = playerRatings[playerId];
    if (!ratings || Object.keys(ratings).length === 0) return null;

    const subPosition = ratings._subPosition || DEFAULT_SUB_POSITION[playerPosition];
    return calculateWeightedAverage(ratings, subPosition);
  };

  // 필터링 및 정렬
  const getFilteredAndSortedPlayers = () => {
    let filtered = players;

    // 부상자 필터
    if (injuryFilter === 'AVAILABLE') {
      // 출전 가능 선수만
      filtered = filtered.filter(p => !getPlayerInjury(p.name));
    } else if (injuryFilter === 'INJURED') {
      // 부상자만
      filtered = filtered.filter(p => getPlayerInjury(p.name));
    }

    // 포지션 필터
    if (positionFilter !== 'ALL') {
      if (positionFilter === 'GK') {
        // GK는 일반 포지션으로 필터
        filtered = filtered.filter(p => {
          const parsedPos = parsePosition(p.position);
          return parsedPos === 'GK';
        });
      } else if (['CB', 'FB'].includes(positionFilter)) {
        // DF 세부 포지션 필터
        filtered = filtered.filter(p => {
          const parsedPos = parsePosition(p.position);
          if (parsedPos !== 'DF') return false;
          const subPosition = playerRatings[p.id]?._subPosition || 'CB';
          return subPosition === positionFilter;
        });
      } else if (['DM', 'CM', 'CAM'].includes(positionFilter)) {
        // MF 세부 포지션 필터
        filtered = filtered.filter(p => {
          const parsedPos = parsePosition(p.position);
          if (parsedPos !== 'MF') return false;
          const subPosition = playerRatings[p.id]?._subPosition || 'CM';
          return subPosition === positionFilter;
        });
      } else if (['WG', 'ST'].includes(positionFilter)) {
        // FW 세부 포지션 필터
        filtered = filtered.filter(p => {
          const parsedPos = parsePosition(p.position);
          if (parsedPos !== 'FW') return false;
          const subPosition = playerRatings[p.id]?._subPosition || 'ST';
          return subPosition === positionFilter;
        });
      }
    }

    // 정렬
    filtered = [...filtered].sort((a, b) => {
      if (sortBy === 'number') {
        return (a.number || 999) - (b.number || 999);
      } else if (sortBy === 'name') {
        return a.name.localeCompare(b.name);
      } else if (sortBy === 'rating') {
        const ratingA = getAverageRating(a.id, a.position) || 0;
        const ratingB = getAverageRating(b.id, b.position) || 0;
        return ratingB - ratingA;
      }
      return 0;
    });

    return filtered;
  };

  const filteredPlayers = getFilteredAndSortedPlayers();

  // 주전/후보/전력 외 구분 (ICT Index 기반)
  const starters = filteredPlayers.filter(p => p.role === 'starter');  // 상위 15명
  const substitutes = filteredPlayers.filter(p => p.role === 'substitute');  // 16-25위
  const others = filteredPlayers.filter(p => p.role === 'other');  // 26위 이하

  // 포지션별 통계
  const getPositionStats = () => {
    const stats = {
      ALL: players.length,
      GK: 0,
      CB: 0,
      FB: 0,
      DM: 0,
      CM: 0,
      CAM: 0,
      WG: 0,
      ST: 0
    };

    players.forEach(p => {
      // 포지션 텍스트를 파싱하여 약어로 변환
      const parsedPos = parsePosition(p.position);

      // 세부 포지션이 있으면 사용, 없으면 일반 포지션의 기본 세부 포지션
      const subPosition = playerRatings[p.id]?._subPosition;

      if (parsedPos === 'GK') {
        stats.GK++;
      } else if (parsedPos === 'DF') {
        // DF는 CB와 FB로 나눔
        if (subPosition === 'FB') {
          stats.FB++;
        } else {
          // 기본값은 CB (subPosition이 없거나 CB인 경우)
          stats.CB++;
        }
      } else if (parsedPos === 'MF') {
        // MF는 DM, CM, CAM으로 나눔
        if (subPosition === 'DM') {
          stats.DM++;
        } else if (subPosition === 'CAM') {
          stats.CAM++;
        } else {
          // 기본값은 CM (subPosition이 없거나 CM인 경우)
          stats.CM++;
        }
      } else if (parsedPos === 'FW') {
        // FW는 WG와 ST로 나눔
        if (subPosition === 'WG') {
          stats.WG++;
        } else {
          // 기본값은 ST (subPosition이 없거나 ST인 경우)
          stats.ST++;
        }
      }
    });

    return stats;
  };

  const positionStats = getPositionStats();

  // 포지션 필터 옵션 데이터
  const positionFilters = [
    { id: 'ALL', label: '전체', generalPos: null },
    { id: 'GK', label: 'GK', generalPos: 'GK' },
    { id: 'CB', label: 'CB', generalPos: 'DF' },
    { id: 'FB', label: 'FB', generalPos: 'DF' },
    { id: 'DM', label: 'DM', generalPos: 'MF' },
    { id: 'CM', label: 'CM', generalPos: 'MF' },
    { id: 'CAM', label: 'CAM', generalPos: 'MF' },
    { id: 'WG', label: 'WG', generalPos: 'FW' },
    { id: 'ST', label: 'ST', generalPos: 'FW' }
  ];

  if (!team) {
    return (
      <div className="relative bg-gradient-to-br from-slate-900/80 via-blue-950/60 to-slate-900/80 backdrop-blur-sm border border-cyan-500/20 rounded p-12 text-center overflow-hidden">
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
          <div className="text-6xl mb-4">⚽</div>
          <p className="text-lg text-white/70">
            팀을 선택해주세요
          </p>
        </div>
      </div>
    );
  }

  // 첫 로딩만 스켈레톤 표시 (데이터 전환 중에는 레이아웃 유지)
  if (loading && !dataTransitioning) {
    return (
      <div className="relative bg-gradient-to-br from-slate-900/80 via-blue-950/60 to-slate-900/80 backdrop-blur-sm border border-cyan-500/20 rounded p-6 overflow-hidden">
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
        <div className="relative animate-pulse space-y-4">
          <div className="h-6 bg-cyan-500/10 rounded-sm w-1/3 mb-6 border border-cyan-500/20"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map(i => (
              <div key={i} className="h-48 bg-slate-900/60 rounded-sm border border-cyan-500/20"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="relative bg-gradient-to-br from-slate-900/80 via-blue-950/60 to-slate-900/80 backdrop-blur-sm border border-cyan-500/20 rounded p-6 overflow-hidden">
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
        <div className="relative text-center">
          <p className="text-error mb-4">{error}</p>
          <button
            onClick={fetchPlayers}
            className="px-4 py-2 bg-cyan-500/20 hover:bg-cyan-500/30 text-white border border-cyan-500/40 rounded-sm transition-all font-medium"
          >
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  };

  return (
    <div className="relative bg-gradient-to-br from-slate-900/80 via-blue-950/60 to-slate-900/80 backdrop-blur-sm border border-cyan-500/20 rounded p-4 md:p-6 overflow-hidden">
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
      {/* Player Grid - 데이터 전환 중일 때 페이드 효과 */}
      <AnimatePresence mode="wait">
        <motion.div
          key={team} // 팀이 바뀌면 새로운 인스턴스로 인식
          initial={{ opacity: 0 }}
          animate={{ opacity: dataTransitioning ? 0.4 : 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3, ease: 'easeInOut' }}
        >
          {/* 필터 헤더 - 항상 표시 */}
          <motion.div
            className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6"
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
          >
            {/* Left: 주전 라인업 Title */}
            <div className="flex items-center gap-3">
              <div className="w-1.5 h-1.5 rounded-full bg-success animate-pulse shadow-glow"></div>
              <h3 className="text-lg font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-400 flex items-center gap-2 tracking-wide uppercase">
                주전 라인업
                <span className="text-sm text-cyan-400/70 font-mono ml-1">({starters.length})</span>
              </h3>
            </div>

            {/* Right: Injury Filter, Position Filter & Sort */}
            <div className="flex flex-col md:flex-row gap-4 items-start md:items-center">
                      {/* Injury Filter Buttons */}
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => setInjuryFilter('ALL')}
                          className={`
                            px-3 py-2 rounded-sm text-sm font-medium transition-all font-mono uppercase tracking-wider
                            ${injuryFilter === 'ALL'
                              ? 'bg-cyan-500/30 border-2 border-cyan-400 text-white'
                              : 'bg-slate-900/60 border-2 border-cyan-500/20 text-white/70 hover:border-cyan-500/40 hover:text-white'}
                          `}
                        >
                          전체
                        </button>
                        <button
                          type="button"
                          onClick={() => setInjuryFilter('AVAILABLE')}
                          className={`
                            px-3 py-2 rounded-sm text-sm font-medium transition-all font-mono uppercase tracking-wider
                            ${injuryFilter === 'AVAILABLE'
                              ? 'bg-green-500/30 border-2 border-green-400 text-white'
                              : 'bg-slate-900/60 border-2 border-green-500/20 text-white/70 hover:border-green-500/40 hover:text-white'}
                          `}
                        >
                          출전가능
                        </button>
                        <button
                          type="button"
                          onClick={() => setInjuryFilter('INJURED')}
                          className={`
                            px-3 py-2 rounded-sm text-sm font-medium transition-all font-mono uppercase tracking-wider
                            ${injuryFilter === 'INJURED'
                              ? 'bg-red-500/30 border-2 border-red-400 text-white'
                              : 'bg-slate-900/60 border-2 border-red-500/20 text-white/70 hover:border-red-500/40 hover:text-white'}
                          `}
                        >
                          부상자 ({injuries.length})
                        </button>
                      </div>

                      {/* Position Filter Dropdown */}
                      <div className="relative" ref={positionDropdownRef}>
                        <button
                          type="button"
                          onClick={() => setIsPositionOpen(!isPositionOpen)}
                          className="px-4 py-2 rounded-sm bg-slate-900/60 border-2 border-cyan-500/30 text-white text-sm w-full md:w-auto hover:border-cyan-500/50 transition-all font-medium font-mono uppercase tracking-wider cursor-pointer flex items-center justify-between gap-3 min-w-[180px]"
                          style={{
                            backgroundImage: `
                              linear-gradient(rgba(6, 182, 212, 0.05) 0%, rgba(6, 182, 212, 0.02) 100%)
                            `
                          }}
                        >
                          <span>
                            {positionFilters.find(p => p.id === positionFilter)?.label || '전체'}
                          </span>
                          <ChevronDown
                            className={`w-4 h-4 transition-transform duration-200 ${isPositionOpen ? 'rotate-180' : ''}`}
                          />
                        </button>

                        {/* Dropdown Menu */}
                        {isPositionOpen && (
                          <div className="absolute z-[9999] w-full mt-2 bg-slate-900 border border-cyan-500/40 rounded-sm overflow-hidden backdrop-blur-md" style={{ boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)' }}>
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
                            {/* Options */}
                            <div className="relative max-h-80 overflow-y-auto">
                              {positionFilters.map((pos) => (
                                <button
                                  key={pos.id}
                                  type="button"
                                  onClick={() => {
                                    setPositionFilter(pos.id);
                                    setIsPositionOpen(false);
                                  }}
                                  className={`
                                    w-full px-4 py-3 flex items-center justify-between transition-all border-l-2 font-medium text-sm
                                    ${positionFilter === pos.id
                                      ? 'bg-cyan-500/20 text-white border-l-cyan-400'
                                      : 'text-white/70 hover:bg-cyan-500/10 hover:text-white border-l-transparent hover:border-l-cyan-500/30'}
                                  `}
                                >
                                  <span className="flex items-center gap-2">
                                    {pos.icon && <pos.icon className="w-4 h-4" />}
                                    <span className="font-mono">{pos.label}</span>
                                    <span className={`text-xs ${positionFilter === pos.id ? 'text-cyan-400' : 'text-white/40'}`}>
                                      ({positionStats[pos.id] || 0})
                                    </span>
                                  </span>
                                  {positionFilter === pos.id && <Check className="w-4 h-4 text-cyan-400" />}
                                </button>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Sort - Custom Dropdown */}
                      <div className="relative" ref={sortDropdownRef}>
                        <button
                          type="button"
                          onClick={() => setIsSortOpen(!isSortOpen)}
                          className="px-4 py-2 rounded-sm bg-slate-900/60 border-2 border-cyan-500/30 text-white text-sm w-full md:w-auto hover:border-cyan-500/50 transition-all font-medium font-mono uppercase tracking-wider cursor-pointer flex items-center justify-between gap-3 min-w-[160px]"
                          style={{
                            backgroundImage: `
                              linear-gradient(rgba(6, 182, 212, 0.05) 0%, rgba(6, 182, 212, 0.02) 100%)
                            `
                          }}
                        >
                          <span>
                            {sortBy === 'rating' && '평점 높은 순'}
                            {sortBy === 'name' && '이름순'}
                            {sortBy === 'number' && '번호순'}
                          </span>
                          <ChevronDown
                            className={`w-4 h-4 transition-transform duration-200 ${isSortOpen ? 'rotate-180' : ''}`}
                          />
                        </button>

                        {/* Dropdown Menu */}
                        {isSortOpen && (
                          <div className="absolute z-[9999] w-full mt-2 bg-slate-900 border border-cyan-500/40 rounded-sm overflow-hidden backdrop-blur-md" style={{ boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)' }}>
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
                            {/* Options */}
                            <div className="relative">
                              <button
                                type="button"
                                onClick={() => {
                                  setSortBy('rating');
                                  setIsSortOpen(false);
                                }}
                                className={`
                                  w-full px-4 py-3 flex items-center justify-between transition-all border-l-2 font-medium font-mono text-sm
                                  ${sortBy === 'rating'
                                    ? 'bg-cyan-500/20 text-white border-l-cyan-400'
                                    : 'text-white/70 hover:bg-cyan-500/10 hover:text-white border-l-transparent hover:border-l-cyan-500/30'}
                                `}
                              >
                                <span>평점 높은 순</span>
                                {sortBy === 'rating' && <Check className="w-4 h-4 text-cyan-400" />}
                              </button>
                              <button
                                type="button"
                                onClick={() => {
                                  setSortBy('name');
                                  setIsSortOpen(false);
                                }}
                                className={`
                                  w-full px-4 py-3 flex items-center justify-between transition-all border-l-2 font-medium font-mono text-sm
                                  ${sortBy === 'name'
                                    ? 'bg-cyan-500/20 text-white border-l-cyan-400'
                                    : 'text-white/70 hover:bg-cyan-500/10 hover:text-white border-l-transparent hover:border-l-cyan-500/30'}
                                `}
                              >
                                <span>이름순</span>
                                {sortBy === 'name' && <Check className="w-4 h-4 text-cyan-400" />}
                              </button>
                              <button
                                type="button"
                                onClick={() => {
                                  setSortBy('number');
                                  setIsSortOpen(false);
                                }}
                                className={`
                                  w-full px-4 py-3 flex items-center justify-between transition-all border-l-2 font-medium font-mono text-sm
                                  ${sortBy === 'number'
                                    ? 'bg-cyan-500/20 text-white border-l-cyan-400'
                                    : 'text-white/70 hover:bg-cyan-500/10 hover:text-white border-l-transparent hover:border-l-cyan-500/30'}
                                `}
                              >
                                <span>번호순</span>
                                {sortBy === 'number' && <Check className="w-4 h-4 text-cyan-400" />}
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
            </div>
          </motion.div>

          {/* 선수 목록 또는 빈 상태 */}
          {filteredPlayers.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-6xl mb-4 opacity-50">🔍</div>
              <p className="text-white/60 text-lg">
                해당 포지션에 선수가 없어요.
              </p>
            </div>
          ) : (
            <div className="space-y-8">
              {/* Starters Section */}
              {starters.length > 0 && (
                <div>
                  <motion.div
                    className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
                    variants={containerVariants}
                    initial="hidden"
                    animate="visible"
                  >
                    {starters.map(player => (
                      <motion.div key={player.id} variants={itemVariants}>
                        <PlayerCard
                          player={player}
                          darkMode={darkMode}
                          onClick={() => onPlayerSelect(player)}
                          averageRating={getAverageRating(player.id, player.position)}
                          compact={false}
                          injury={getPlayerInjury(player.name)}
                        />
                      </motion.div>
                    ))}
                  </motion.div>
                </div>
              )}

              {/* Substitutes Section (후보 선수) */}
              {substitutes.length > 0 && (
                <div>
                  <motion.div
                    className="flex items-center gap-3 mb-4"
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.2 }}
                  >
                    <div className="w-1.5 h-1.5 rounded-full bg-warning shadow-glow"></div>
                    <h3 className="text-lg font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-400 flex items-center gap-2 tracking-wide uppercase">
                      후보 선수
                      <span className="text-sm text-cyan-400/70 font-mono ml-1">({substitutes.length})</span>
                    </h3>
                  </motion.div>

                  <motion.div
                    className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
                    variants={containerVariants}
                    initial="hidden"
                    animate="visible"
                  >
                    {substitutes.map((player, i) => (
                      <motion.div
                        key={player.id}
                        variants={itemVariants}
                        transition={{ delay: i * 0.03 }}
                      >
                        <PlayerCard
                          player={player}
                          darkMode={darkMode}
                          onClick={() => onPlayerSelect(player)}
                          averageRating={getAverageRating(player.id, player.position)}
                          compact={false}
                          injury={getPlayerInjury(player.name)}
                        />
                      </motion.div>
                    ))}
                  </motion.div>
                </div>
              )}

              {/* Others Section (전력 외) */}
              {others.length > 0 && (
                <div>
                  <motion.div
                    className="flex items-center gap-3 mb-4"
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 }}
                  >
                    <div className="w-1.5 h-1.5 rounded-full bg-white/30"></div>
                    <h3 className="text-lg font-bold text-white/70 flex items-center gap-2 tracking-wide uppercase">
                      전력 외
                      <span className="text-sm text-white/50 font-mono ml-1">({others.length})</span>
                    </h3>
                  </motion.div>

                  <motion.div
                    className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
                    variants={containerVariants}
                    initial="hidden"
                    animate="visible"
                  >
                    {others.map((player, i) => (
                      <motion.div
                        key={player.id}
                        variants={itemVariants}
                        transition={{ delay: i * 0.03 }}
                      >
                        <PlayerCard
                          player={player}
                          darkMode={darkMode}
                          onClick={() => onPlayerSelect(player)}
                          averageRating={getAverageRating(player.id, player.position)}
                          compact={false}
                          injury={getPlayerInjury(player.name)}
                        />
                      </motion.div>
                    ))}
                  </motion.div>
                </div>
              )}
            </div>
          )}
        </motion.div>
      </AnimatePresence>
      </div>
    </div>
  );
};

export default PlayerList;
