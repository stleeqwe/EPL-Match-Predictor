import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, Save, RotateCcw, TrendingUp, Shield, Target, Activity, Award, Flame, X, Search, Filter, ChevronDown, AlertCircle, Check, User } from 'lucide-react';
import './SquadBuilder.css';
import { getPlayerPhotoUrl } from '../utils/playerPhoto';

/**
 * 컴팩트 선수 카드 컴포넌트 (Squad Builder용) - 프로필 사진 + 핵심 정보
 */
const PlayerCardCompact = ({
  player,
  isStarter,
  onDragStart,
  onDragEnd,
  onClick,
  getRatingBadgeColor,
  getPlayerRole,
  getPositionBadgeColor
}) => {
  const [photoError, setPhotoError] = useState(false);
  const photoUrl = player.photo ? getPlayerPhotoUrl(player.photo, '110x140') : null;
  const playerRole = getPlayerRole(player.position);

  return (
    <motion.div
      draggable
      onDragStart={(e) => onDragStart(e, player)}
      onDragEnd={onDragEnd}
      onClick={onClick}
      className={`group rounded-sm border cursor-move transition-all duration-200 overflow-hidden ${
        isStarter
          ? 'bg-cyan-500/10 border-cyan-500/40 shadow-lg shadow-cyan-500/20'
          : 'bg-slate-900/40 border-cyan-500/20 hover:border-cyan-400/40'
      }`}
      whileHover={{ scale: 1.02, y: -2 }}
      whileTap={{ scale: 0.98 }}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      <div className="flex items-center gap-2 p-2">
        {/* 프로필 사진 */}
        <div className="relative w-20 h-20 rounded-sm flex-shrink-0 overflow-hidden pointer-events-none">
          {photoUrl && !photoError ? (
            <img
              src={photoUrl}
              alt={player.name}
              crossOrigin="anonymous"
              referrerPolicy="no-referrer"
              draggable={false}
              className="w-32 h-32 object-cover object-[center_35%] rounded-sm border-2 border-white/20 group-hover:border-cyan-400/60 transition-all duration-300"
              onError={() => setPhotoError(true)}
            />
          ) : (
            <div className={`w-20 h-20 rounded-sm flex items-center justify-center border-2 transition-all ${
              isStarter
                ? 'bg-cyan-500/20 border-cyan-400/50'
                : 'bg-slate-800/60 border-white/20 group-hover:border-cyan-400/40'
            }`}>
              <User className="w-10 h-10 text-white/30" />
            </div>
          )}
        </div>

        {/* 선수 정보 */}
        <div className="flex-1 min-w-0">
          {/* 이름 */}
          <p className="font-bold text-base text-white leading-tight group-hover:text-cyan-300 transition-colors mb-2 line-clamp-2">
            {player.name}
          </p>

          {/* 포지션 & Rating */}
          <div className="flex items-center gap-2">
            {/* 포지션 배지 - 축약어 + 포지션별 색상 */}
            <span className={`px-2 py-0.5 rounded text-xs font-bold font-mono uppercase border ${
              getPositionBadgeColor(playerRole)
            }`}>
              {playerRole}
            </span>

            {/* Rating */}
            {player.rating !== null && (
              <span className={`text-sm font-black font-mono ${
                player.rating >= 4.5 ? 'text-cyan-300' :
                player.rating >= 4.0 ? 'text-cyan-400' :
                player.rating >= 3.0 ? 'text-purple-400' :
                'text-amber-400'
              }`}>
                {player.rating.toFixed(1)}
              </span>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
};

/**
 * 프로페셔널 스쿼드 빌더 - 수학적 좌표 시스템
 * 실제 축구장 비율 (FIFA 표준: 105m x 68m)을 기반으로 정확한 포지션 계산
 */
const PremiumSquadBuilder = ({ team = "Manchester City", playerRatings = {} }) => {
  const [formation, setFormation] = useState('4-3-3');
  const [squad, setSquad] = useState({ starters: {}, substitutes: [] });
  const [draggedPlayer, setDraggedPlayer] = useState(null);
  const [hoveredPos, setHoveredPos] = useState(null);
  const [selectedPlayer, setSelectedPlayer] = useState(null);
  const [clickPosition, setClickPosition] = useState({ x: 0, y: 0 }); // 클릭 위치 저장
  const [rawPlayers, setRawPlayers] = useState([]); // API에서 받은 원본 데이터
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [positionFilter, setPositionFilter] = useState('ALL');
  const [showFormationMenu, setShowFormationMenu] = useState(false);
  const [pitchDimensions, setPitchDimensions] = useState({ width: 0, height: 0 });
  const [saveStatus, setSaveStatus] = useState('idle'); // 'idle', 'saving', 'success'
  const [positionPickerOpen, setPositionPickerOpen] = useState(null); // { posKey, role } or null

  const pitchRef = useRef(null);
  const formationMenuRef = useRef(null);
  const formationDropdownRef = useRef(null);
  const selectedFormationRef = useRef(null);

  // Calculate player rating from playerRatings
  const calculatePlayerRating = useCallback((player) => {
    const savedRatings = playerRatings[player.id];

    if (savedRatings && typeof savedRatings === 'object') {
      const ratingValues = Object.entries(savedRatings)
        .filter(([key, value]) => !key.startsWith('_') && typeof value === 'number')
        .map(([_, value]) => value);

      if (ratingValues.length > 0) {
        const average = ratingValues.reduce((sum, val) => sum + val, 0) / ratingValues.length;
        return Math.round(average * 10) / 10;
      }
    }

    // 측정값이 없으면 기본값 2.5 반환
    return 2.5;
  }, [playerRatings]);

  const calculatePlayerForm = useCallback((player) => {
    const baseForm = 3.5;
    const minutesBonus = (player.minutes || 0) > 500 ? 0.5 : 0;
    const statsBonus = ((player.goals || 0) + (player.assists || 0)) * 0.15;
    return Math.min(5.0, baseForm + minutesBonus + statsBonus);
  }, []);

  // Fetch players from API
  const fetchPlayers = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:5001/api/squad/${encodeURIComponent(team)}`);
      const data = await response.json();

      setRawPlayers(data.squad || []);
    } catch (error) {
      console.error('Error fetching players:', error);
      // Fallback to mock data
      setRawPlayers([
        { id: 1, name: 'Erling Haaland', position: 'ST', number: 9, nationality: '🇳🇴', goals: 27, assists: 5 },
        { id: 2, name: 'Kevin De Bruyne', position: 'CAM', number: 17, nationality: '🇧🇪', goals: 4, assists: 18 },
        { id: 3, name: 'Phil Foden', position: 'WG', number: 47, nationality: '🏴󠁧󠁢󠁥󠁮󠁧󠁿', goals: 11, assists: 8 },
        { id: 4, name: 'Rodri', position: 'DM', number: 16, nationality: '🇪🇸', goals: 5, assists: 4 },
        { id: 5, name: 'Ruben Dias', position: 'CB', number: 3, nationality: '🇵🇹', goals: 1, assists: 0 },
        { id: 6, name: 'John Stones', position: 'CB', number: 5, nationality: '🏴󠁧󠁢󠁥󠁮󠁧󠁿', goals: 2, assists: 1 },
        { id: 7, name: 'Kyle Walker', position: 'FB', number: 2, nationality: '🏴󠁧󠁢󠁥󠁮󠁧󠁿', goals: 0, assists: 3 },
        { id: 8, name: 'Ederson', position: 'GK', number: 31, nationality: '🇧🇷', goals: 0, assists: 0 },
        { id: 9, name: 'Jack Grealish', position: 'WG', number: 10, nationality: '🏴󠁧󠁢󠁥󠁮󠁧󠁿', goals: 3, assists: 7 },
        { id: 10, name: 'Bernardo Silva', position: 'CM', number: 20, nationality: '🇵🇹', goals: 6, assists: 9 },
        { id: 11, name: 'Nathan Aké', position: 'FB', number: 6, nationality: '🇳🇱', goals: 0, assists: 1 },
      ]);
    } finally {
      setLoading(false);
    }
  }, [team]);

  // Fetch players from API
  useEffect(() => {
    fetchPlayers();
  }, [fetchPlayers]);

  // Load saved squad from localStorage
  useEffect(() => {
    if (team) {
      const savedSquad = localStorage.getItem(`squad_${team}`);
      if (savedSquad) {
        try {
          const squadData = JSON.parse(savedSquad);
          setFormation(squadData.formation || '4-3-3');
          setSquad({
            starters: squadData.starters || {},
            substitutes: squadData.substitutes || []
          });
        } catch (error) {
          console.error('Failed to load saved squad:', error);
        }
      }
    }
  }, [team]);

  // rawPlayers와 playerRatings를 조합하여 최종 players 계산
  const players = useMemo(() => {
    return rawPlayers.map(player => ({
      ...player,
      rating: calculatePlayerRating(player),
      form: calculatePlayerForm(player)
    }));
  }, [rawPlayers, calculatePlayerRating, calculatePlayerForm]);

  // Close formation menu on outside click
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (formationMenuRef.current && !formationMenuRef.current.contains(event.target)) {
        setShowFormationMenu(false);
      }
    };

    if (showFormationMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showFormationMenu]);

  // Scroll to selected formation when menu opens (dropdown only, not page)
  useEffect(() => {
    if (showFormationMenu && selectedFormationRef.current && formationDropdownRef.current) {
      const dropdown = formationDropdownRef.current;
      const selectedItem = selectedFormationRef.current;

      // Calculate scroll position to center the selected item
      const dropdownHeight = dropdown.clientHeight;
      const itemTop = selectedItem.offsetTop;
      const itemHeight = selectedItem.clientHeight;

      // Center the selected item in the dropdown
      const scrollTop = itemTop - (dropdownHeight / 2) + (itemHeight / 2);

      dropdown.scrollTo({
        top: scrollTop,
        behavior: 'smooth'
      });
    }
  }, [showFormationMenu]);

  // 경기장 크기 측정 및 반응형 처리
  useEffect(() => {
    const updatePitchDimensions = () => {
      if (pitchRef.current) {
        const rect = pitchRef.current.getBoundingClientRect();
        const { width, height } = rect;
        setPitchDimensions({ width, height });
      }
    };

    // 초기 로드 시 약간의 지연을 둠 (DOM 완전히 렌더링 대기)
    setTimeout(updatePitchDimensions, 100);

    const resizeObserver = new ResizeObserver(updatePitchDimensions);

    if (pitchRef.current) {
      resizeObserver.observe(pitchRef.current);
    }

    window.addEventListener('resize', updatePitchDimensions);

    return () => {
      resizeObserver.disconnect();
      window.removeEventListener('resize', updatePitchDimensions);
    };
  }, []);

  /**
   * 실제 축구장 기준 좌표 (FIFA 표준: 105m x 68m)
   * x축: 0m (왼쪽) ~ 68m (오른쪽)
   * y축: 0m (상대 골라인) ~ 105m (자기 골라인)
   *
   * 주요 구역:
   * - 골라인: y=0, y=105
   * - 페널티 에리어: y=0~16.5, y=88.5~105
   * - 하프라인: y=52.5
   */
  const PITCH_LENGTH = 105; // 미터
  const PITCH_WIDTH = 68;   // 미터

  const formations = {
    '4-3-3': {
      name: '4-3-3 Attack',
      positions: {
        GK: { x: 34, y: 99 },
        LB: { x: 8, y: 76 },
        CB1: { x: 24, y: 80 },
        CB2: { x: 44, y: 80 },
        RB: { x: 60, y: 76 },
        DM: { x: 34, y: 63 },
        CM1: { x: 15, y: 48 },
        CM2: { x: 53, y: 48 },
        LW: { x: 8, y: 23 },
        ST: { x: 34, y: 16 },
        RW: { x: 60, y: 23 }
      }
    },
    '4-3-3 Defend': {
      name: '4-3-3 Defensive',
      positions: {
        GK: { x: 34, y: 99 },
        LB: { x: 8, y: 76 },
        CB1: { x: 24, y: 80 },
        CB2: { x: 44, y: 80 },
        RB: { x: 60, y: 76 },
        DM1: { x: 22, y: 65 },
        DM2: { x: 46, y: 65 },
        CM: { x: 34, y: 50 },
        LW: { x: 8, y: 28 },
        ST: { x: 34, y: 18 },
        RW: { x: 60, y: 28 }
      }
    },
    '4-3-3 False 9': {
      name: '4-3-3 False 9',
      positions: {
        GK: { x: 34, y: 99 },
        LB: { x: 8, y: 76 },
        CB1: { x: 24, y: 80 },
        CB2: { x: 44, y: 80 },
        RB: { x: 60, y: 76 },
        DM: { x: 34, y: 63 },
        CM1: { x: 18, y: 48 },
        CM2: { x: 50, y: 48 },
        LW: { x: 8, y: 21 },
        CAM: { x: 34, y: 28 }, // False 9
        RW: { x: 59, y: 21 }
      }
    },
    '4-2-3-1': {
      name: '4-2-3-1 Modern',
      positions: {
        GK: { x: 34, y: 99 },
        LB: { x: 8, y: 76 },
        CB1: { x: 24, y: 80 },
        CB2: { x: 44, y: 80 },
        RB: { x: 60, y: 76 },
        DM1: { x: 22, y: 63 },
        DM2: { x: 46, y: 63 },
        LAM: { x: 10, y: 35 },
        CAM: { x: 34, y: 32 },
        RAM: { x: 58, y: 35 },
        ST: { x: 34, y: 16 }
      }
    },
    '4-4-2': {
      name: '4-4-2 Classic',
      positions: {
        GK: { x: 34, y: 99 },
        LB: { x: 8, y: 76 },
        CB1: { x: 24, y: 80 },
        CB2: { x: 44, y: 80 },
        RB: { x: 60, y: 76 },
        WG1: { x: 8, y: 50 },
        CM1: { x: 24, y: 52 },
        CM2: { x: 44, y: 52 },
        WG2: { x: 59, y: 50 },
        ST1: { x: 26, y: 20 },
        ST2: { x: 42, y: 20 }
      }
    },
    '4-4-2 Diamond': {
      name: '4-4-2 Diamond',
      positions: {
        GK: { x: 34, y: 99 },
        LB: { x: 8, y: 76 },
        CB1: { x: 24, y: 80 },
        CB2: { x: 44, y: 80 },
        RB: { x: 60, y: 76 },
        DM: { x: 34, y: 63 },
        CM1: { x: 20, y: 48 },
        CM2: { x: 48, y: 48 },
        CAM: { x: 34, y: 32 },
        ST1: { x: 26, y: 18 },
        ST2: { x: 42, y: 18 }
      }
    },
    '4-1-4-1': {
      name: '4-1-4-1 Defensive',
      positions: {
        GK: { x: 34, y: 99 },
        LB: { x: 8, y: 76 },
        CB1: { x: 24, y: 80 },
        CB2: { x: 44, y: 80 },
        RB: { x: 60, y: 76 },
        DM: { x: 34, y: 63 },
        WG1: { x: 8, y: 45 },
        CM1: { x: 24, y: 48 },
        CM2: { x: 44, y: 48 },
        WG2: { x: 59, y: 45 },
        ST: { x: 34, y: 18 }
      }
    },
    '4-5-1': {
      name: '4-5-1 Ultra Defensive',
      positions: {
        GK: { x: 34, y: 99 },
        LB: { x: 8, y: 76 },
        CB1: { x: 24, y: 80 },
        CB2: { x: 44, y: 80 },
        RB: { x: 60, y: 76 },
        WG1: { x: 6, y: 52 },
        CM1: { x: 20, y: 55 },
        DM: { x: 34, y: 60 },
        CM2: { x: 48, y: 55 },
        WG2: { x: 61, y: 52 },
        ST: { x: 34, y: 20 }
      }
    },
    '3-4-3': {
      name: '3-4-3 Attack',
      positions: {
        GK: { x: 34, y: 99 },
        CB1: { x: 17, y: 80 },
        CB2: { x: 34, y: 83 },
        CB3: { x: 51, y: 80 },
        WG1: { x: 6, y: 55 },
        CM1: { x: 24, y: 52 },
        CM2: { x: 44, y: 52 },
        WG2: { x: 61, y: 55 },
        LW: { x: 10, y: 23 },
        ST: { x: 34, y: 16 },
        RW: { x: 58, y: 23 }
      }
    },
    '3-5-2': {
      name: '3-5-2 Wing',
      positions: {
        GK: { x: 34, y: 99 },
        CB1: { x: 17, y: 80 },
        CB2: { x: 34, y: 83 },
        CB3: { x: 51, y: 80 },
        WG1: { x: 7, y: 58 },
        CM1: { x: 20, y: 50 },
        CM2: { x: 34, y: 46 },
        CM3: { x: 48, y: 50 },
        WG2: { x: 60, y: 58 },
        ST1: { x: 24, y: 19 },
        ST2: { x: 44, y: 19 }
      }
    },
    '3-4-2-1': {
      name: '3-4-2-1 Christmas Tree',
      positions: {
        GK: { x: 34, y: 99 },
        CB1: { x: 17, y: 80 },
        CB2: { x: 34, y: 83 },
        CB3: { x: 51, y: 80 },
        WG1: { x: 6, y: 58 },
        CM1: { x: 24, y: 54 },
        CM2: { x: 44, y: 54 },
        WG2: { x: 61, y: 58 },
        CAM1: { x: 22, y: 30 },
        CAM2: { x: 46, y: 30 },
        ST: { x: 34, y: 16 }
      }
    },
    '3-4-1-2': {
      name: '3-4-1-2',
      positions: {
        GK: { x: 34, y: 99 },
        CB1: { x: 17, y: 80 },
        CB2: { x: 34, y: 83 },
        CB3: { x: 51, y: 80 },
        WG1: { x: 6, y: 58 },
        CM1: { x: 24, y: 54 },
        CM2: { x: 44, y: 54 },
        WG2: { x: 61, y: 58 },
        CAM: { x: 34, y: 32 },
        ST1: { x: 26, y: 18 },
        ST2: { x: 42, y: 18 }
      }
    },
    '5-3-2': {
      name: '5-3-2 Defensive',
      positions: {
        GK: { x: 34, y: 99 },
        FB1: { x: 6, y: 76 },
        CB1: { x: 20, y: 80 },
        CB2: { x: 34, y: 83 },
        CB3: { x: 48, y: 80 },
        FB2: { x: 61, y: 76 },
        CM1: { x: 20, y: 50 },
        DM: { x: 34, y: 55 },
        CM2: { x: 48, y: 50 },
        ST1: { x: 26, y: 20 },
        ST2: { x: 42, y: 20 }
      }
    },
    '5-4-1': {
      name: '5-4-1 Ultra Defensive',
      positions: {
        GK: { x: 34, y: 99 },
        FB1: { x: 6, y: 76 },
        CB1: { x: 20, y: 80 },
        CB2: { x: 34, y: 83 },
        CB3: { x: 48, y: 80 },
        FB2: { x: 61, y: 76 },
        CM1: { x: 14, y: 52 },
        DM1: { x: 26, y: 56 },
        DM2: { x: 42, y: 56 },
        CM2: { x: 54, y: 52 },
        ST: { x: 34, y: 20 }
      }
    },
    '4-1-2-3': {
      name: '4-1-2-3 Wide',
      positions: {
        GK: { x: 34, y: 99 },
        LB: { x: 8, y: 76 },
        CB1: { x: 24, y: 80 },
        CB2: { x: 44, y: 80 },
        RB: { x: 60, y: 76 },
        DM: { x: 34, y: 63 },
        CM1: { x: 22, y: 48 },
        CM2: { x: 46, y: 48 },
        LW: { x: 8, y: 28 },
        ST: { x: 34, y: 18 },
        RW: { x: 60, y: 28 }
      }
    },
    '4-3-1-2': {
      name: '4-3-1-2 Narrow',
      positions: {
        GK: { x: 34, y: 99 },
        LB: { x: 8, y: 76 },
        CB1: { x: 24, y: 80 },
        CB2: { x: 44, y: 80 },
        RB: { x: 60, y: 76 },
        DM: { x: 34, y: 63 },
        CM1: { x: 22, y: 50 },
        CM2: { x: 46, y: 50 },
        CAM: { x: 34, y: 32 },
        ST1: { x: 26, y: 18 },
        ST2: { x: 42, y: 18 }
      }
    },
    '4-2-2-2': {
      name: '4-2-2-2 Box',
      positions: {
        GK: { x: 34, y: 99 },
        LB: { x: 8, y: 76 },
        CB1: { x: 24, y: 80 },
        CB2: { x: 44, y: 80 },
        RB: { x: 60, y: 76 },
        DM1: { x: 22, y: 60 },
        DM2: { x: 46, y: 60 },
        CAM1: { x: 22, y: 35 },
        CAM2: { x: 46, y: 35 },
        ST1: { x: 26, y: 18 },
        ST2: { x: 42, y: 18 }
      }
    },
    '4-2-4': {
      name: '4-2-4 Ultra Attack',
      positions: {
        GK: { x: 34, y: 99 },
        LB: { x: 8, y: 76 },
        CB1: { x: 24, y: 80 },
        CB2: { x: 44, y: 80 },
        RB: { x: 60, y: 76 },
        DM1: { x: 24, y: 58 },
        DM2: { x: 44, y: 58 },
        WG1: { x: 8, y: 22 },
        ST1: { x: 25, y: 17 },
        ST2: { x: 43, y: 17 },
        WG2: { x: 60, y: 22 }
      }
    },
    '3-2-5': {
      name: '3-2-5 Guardiola',
      positions: {
        GK: { x: 34, y: 99 },
        CB1: { x: 17, y: 80 },
        CB2: { x: 34, y: 83 },
        CB3: { x: 51, y: 80 },
        DM1: { x: 24, y: 60 },
        DM2: { x: 44, y: 60 },
        WG1: { x: 6, y: 25 },
        CAM1: { x: 22, y: 30 },
        ST: { x: 34, y: 16 },
        CAM2: { x: 46, y: 30 },
        WG2: { x: 61, y: 25 }
      }
    },
    '4-3-2-1': {
      name: '4-3-2-1 Christmas Tree',
      positions: {
        GK: { x: 34, y: 99 },
        LB: { x: 8, y: 76 },
        CB1: { x: 24, y: 80 },
        CB2: { x: 44, y: 80 },
        RB: { x: 60, y: 76 },
        DM: { x: 34, y: 63 },
        CM1: { x: 20, y: 50 },
        CM2: { x: 48, y: 50 },
        CAM1: { x: 22, y: 32 },
        CAM2: { x: 46, y: 32 },
        ST: { x: 34, y: 16 }
      }
    }
  };

  /**
   * 실제 축구장 좌표(미터)를 화면 좌표(픽셀)로 변환
   * @param {number} meterX - 축구장 X 좌표 (0-68m)
   * @param {number} meterY - 축구장 Y 좌표 (0-105m)
   * @param {string} posKey - 포지션 키 (디버그용)
   * @returns {object} 화면 픽셀 좌표 {x, y}
   */
  const convertToPixelCoords = (meterX, meterY, posKey = '') => {
    if (!pitchDimensions.width || !pitchDimensions.height) {
      console.warn('⚠️ Pitch dimensions not available yet');
      return { x: 0, y: 0 };
    }

    // 패딩을 고려한 실제 경기장 영역
    const padding = { x: 0, y: 0 };
    const usableWidth = pitchDimensions.width - (padding.x * 2);
    const usableHeight = pitchDimensions.height - (padding.y * 2);

    // 오프셋 (미터 단위로 조정)
    const X_OFFSET = 5; // 5m 왼쪽으로 이동
    const Y_OFFSET = 8; // 8m 위쪽으로 이동

    // 미터를 픽셀로 변환 (오프셋 적용)
    const pixelX = padding.x + ((meterX - X_OFFSET) / PITCH_WIDTH) * usableWidth;
    const pixelY = padding.y + ((meterY - Y_OFFSET) / PITCH_LENGTH) * usableHeight;

    return { x: pixelX, y: pixelY };
  };

  /**
   * 포메이션의 모든 포지션을 픽셀 좌표로 변환 (메모이제이션)
   * pitchDimensions나 formation이 변경될 때만 재계산
   */
  const pixelPositions = useMemo(() => {
    // pitchDimensions가 아직 측정되지 않았으면 빈 객체 반환
    if (!pitchDimensions.width || !pitchDimensions.height) {
      return {};
    }

    const currentFormation = formations[formation];
    const positions = {};

    Object.entries(currentFormation.positions).forEach(([posKey, meterCoords]) => {
      positions[posKey] = convertToPixelCoords(meterCoords.x, meterCoords.y, posKey);
    });

    return positions;
  }, [pitchDimensions.width, pitchDimensions.height, formation, formations, convertToPixelCoords]);

  // 포메이션 포지션 키 → 역할 변환 (GK, CB1, LB 등 → GK, CB, FB 등)
  const getRole = (posKey) => {
    if (posKey === 'GK') return 'GK';

    // 센터백
    if (posKey.includes('CB')) return 'CB';

    // 풀백 (LB, RB, FB1, FB2)
    if (posKey === 'LB' || posKey === 'RB' || posKey.startsWith('FB')) return 'FB';

    // 윙백 (LWB, RWB) - 풀백으로 처리
    if (posKey.includes('WB')) return 'FB';

    // 수비형 미드필더 (DM, DM1, DM2)
    if (posKey.includes('DM')) return 'DM';

    // 중앙 미드필더 (CM, CM1, CM2, CM3)
    if (posKey.includes('CM')) return 'CM';

    // 공격형 미드필더 (CAM, LAM, RAM, CAM1, CAM2)
    if (posKey.includes('AM')) return 'CAM';

    // 윙어 (LW, RW, WG1, WG2)
    if (posKey.includes('W') && !posKey.includes('WB')) return 'WG';

    // 스트라이커 (ST, ST1, ST2)
    if (posKey.includes('ST')) return 'ST';

    // 기본값
    return 'CM';
  };

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

  // 포지션별 테두리 색상 (카드 박스용)
  const getPositionBorderColor = (role) => {
    switch (role) {
      case 'GK':
        return 'border-amber-500/30';  // 골키퍼: 노란색
      case 'CB':
        return 'border-emerald-500/30';  // 센터백: 녹색
      case 'FB':
        return 'border-teal-500/30';  // 풀백: 청록색
      case 'DM':
        return 'border-blue-500/30';  // 수비형 미드필더: 파란색
      case 'CM':
        return 'border-purple-500/30';  // 중앙 미드필더: 보라색
      case 'CAM':
        return 'border-pink-500/30';  // 공격형 미드필더: 핑크
      case 'WG':
        return 'border-orange-500/30';  // 윙어: 주황색
      case 'ST':
        return 'border-red-500/30';  // 스트라이커: 빨간색
      default:
        return 'border-gray-500/30';  // 기본: 회색
    }
  };

  // 포지션별 hover 테두리 색상
  const getPositionBorderHoverColor = (role) => {
    switch (role) {
      case 'GK':
        return 'border-amber-400';
      case 'CB':
        return 'border-emerald-400';
      case 'FB':
        return 'border-teal-400';
      case 'DM':
        return 'border-blue-400';
      case 'CM':
        return 'border-purple-400';
      case 'CAM':
        return 'border-pink-400';
      case 'WG':
        return 'border-orange-400';
      case 'ST':
        return 'border-red-400';
      default:
        return 'border-gray-400';
    }
  };

  // 포지션별 그라데이션 색상 (카드 배경용)
  const getPositionGradientColor = (role) => {
    switch (role) {
      case 'GK':
        return 'from-amber-500 to-amber-600';
      case 'CB':
        return 'from-emerald-500 to-emerald-600';
      case 'FB':
        return 'from-teal-500 to-teal-600';
      case 'DM':
        return 'from-blue-500 to-blue-600';
      case 'CM':
        return 'from-purple-500 to-purple-600';
      case 'CAM':
        return 'from-pink-500 to-pink-600';
      case 'WG':
        return 'from-orange-500 to-orange-600';
      case 'ST':
        return 'from-red-500 to-red-600';
      default:
        return 'from-gray-500 to-gray-600';
    }
  };

  const handleDragStart = (e, player) => {
    setDraggedPlayer(player);
    e.dataTransfer.effectAllowed = 'move';
    // 드래그 중 투명도 설정
    e.currentTarget.style.opacity = '0.5';
  };

  const handleDragEnd = (e) => {
    // 투명도 원복
    if (e.currentTarget) {
      e.currentTarget.style.opacity = '1';
    }
    setDraggedPlayer(null);
    setHoveredPos(null);
  };

  const handleDrop = (e, posKey) => {
    e.preventDefault();
    e.stopPropagation();

    if (!draggedPlayer) return;

    const role = getRole(posKey);
    const playerRole = getPlayerRole(draggedPlayer.position);
    if (playerRole !== role) {
      setDraggedPlayer(null);
      setHoveredPos(null);
      return;
    }

    // 이미 배치된 선수인지 확인 (중복 방지)
    const isAlreadyPlaced = Object.values(squad.starters).includes(draggedPlayer.id);
    if (isAlreadyPlaced) {
      setDraggedPlayer(null);
      setHoveredPos(null);
      return;
    }

    setSquad(prev => ({
      ...prev,
      starters: { ...prev.starters, [posKey]: draggedPlayer.id }
    }));

    setDraggedPlayer(null);
    setHoveredPos(null);
  };

  // 빈 포지션 클릭 시 선수 선택 팝업
  const handlePositionClick = (posKey) => {
    const role = getRole(posKey);
    setPositionPickerOpen({ posKey, role });
  };

  // 포지션에 선수 배치
  const assignPlayerToPosition = (player, posKey) => {
    // 이미 배치된 선수인지 확인 (중복 방지)
    const isAlreadyPlaced = Object.values(squad.starters).includes(player.id);
    if (isAlreadyPlaced) {
      setPositionPickerOpen(null);
      return;
    }

    setSquad(prev => ({
      ...prev,
      starters: { ...prev.starters, [posKey]: player.id }
    }));
    setPositionPickerOpen(null);
  };

  const removePlayer = (posKey) => {
    setSquad(prev => {
      const newStarters = { ...prev.starters };
      delete newStarters[posKey];
      return { ...prev, starters: newStarters };
    });
  };

  const autoFill = () => {
    const positions = formations[formation].positions;
    const newStarters = {};

    Object.keys(positions).forEach(posKey => {
      const role = getRole(posKey);
      const available = players
        .filter(p => getPlayerRole(p.position) === role && !Object.values(newStarters).includes(p.id));

      const best = available.sort((a, b) => {
        if (a.rating === null && b.rating !== null) return 1;
        if (a.rating !== null && b.rating === null) return -1;
        if (a.rating === null && b.rating === null) return 0;
        return b.rating - a.rating;
      })[0];

      if (best) newStarters[posKey] = best.id;
    });

    setSquad({ starters: newStarters, substitutes: [] });
  };

  const handleSave = async () => {
    try {
      setSaveStatus('saving');

      // localStorage에 스쿼드 저장
      const squadData = {
        team,
        formation,
        starters: squad.starters,
        substitutes: squad.substitutes,
        savedAt: new Date().toISOString()
      };

      localStorage.setItem(`squad_${team}`, JSON.stringify(squadData));

      // 약간의 지연 후 성공 상태로 변경 (사용자가 인지할 수 있도록)
      await new Promise(resolve => setTimeout(resolve, 300));
      setSaveStatus('success');

      // 2초 후 다시 idle 상태로
      setTimeout(() => {
        setSaveStatus('idle');
      }, 2000);
    } catch (error) {
      console.error('Failed to save squad:', error);
      setSaveStatus('idle');
      alert('저장에 실패했습니다.');
    }
  };

  const getPlayer = (id) => players.find(p => p.id === id);

  const calcStats = () => {
    const starterIds = Object.values(squad.starters);
    const starters = starterIds.map(id => getPlayer(id)).filter(Boolean);

    if (!starters.length) return {
      overall: 0, attack: 0, midfield: 0, defense: 0, chemistry: 0,
      totalRating: 0, avgRating: 0, ratedCount: 0, unratedCount: 0
    };

    const startersWithRating = starters.filter(p => p.rating !== null);
    const totalRating = startersWithRating.reduce((s, p) => s + p.rating, 0);

    const calculateAverage = (filteredPlayers) => {
      const playersWithRating = filteredPlayers.filter(p => p.rating !== null);
      if (playersWithRating.length === 0) return 0;
      return playersWithRating.reduce((s, p) => s + p.rating, 0) / playersWithRating.length;
    };

    return {
      overall: startersWithRating.length > 0 ? totalRating / startersWithRating.length : 0,
      attack: calculateAverage(starters.filter(p => ['ST', 'WG', 'CAM'].includes(getPlayerRole(p.position)))),
      midfield: calculateAverage(starters.filter(p => ['CM', 'DM'].includes(getPlayerRole(p.position)))),
      defense: calculateAverage(starters.filter(p => ['CB', 'FB', 'GK'].includes(getPlayerRole(p.position)))),
      chemistry: starters.reduce((s, p) => s + p.form, 0) / starters.length,
      totalRating: totalRating,
      avgRating: startersWithRating.length > 0 ? totalRating / startersWithRating.length : 0,
      ratedCount: startersWithRating.length,
      unratedCount: starters.length - startersWithRating.length
    };
  };

  const stats = calcStats();

  const filteredPlayers = players
    .filter(p => positionFilter === 'ALL' || getPlayerRole(p.position) === positionFilter)
    .filter(p => p.name.toLowerCase().includes(searchTerm.toLowerCase()))
    .sort((a, b) => {
      const aIsStarter = Object.values(squad.starters).includes(a.id);
      const bIsStarter = Object.values(squad.starters).includes(b.id);

      // 주전 선수가 먼저
      if (aIsStarter && !bIsStarter) return -1;
      if (!aIsStarter && bIsStarter) return 1;

      // 같은 그룹 내에서는 rating으로 정렬
      if (a.rating === null && b.rating !== null) return 1;
      if (a.rating !== null && b.rating === null) return -1;
      if (a.rating === null && b.rating === null) return 0;
      return b.rating - a.rating;
    });

  // 대조적인 색상 시스템 (평균 기준 양방향)
  const getRatingColor = (rating) => {
    if (rating === null) return 'from-gray-600 to-gray-700';
    if (rating >= 4.5) return 'from-[#00FFFF] to-[#00FFFF]/70';  // 형광 사이언 - 월드클래스
    if (rating >= 4.0) return 'from-[#60A5FA] to-[#60A5FA]/70';  // 밝은 파랑 - 상위
    if (rating >= 3.0) return 'from-[#A855F7] to-[#A855F7]/70';  // 보라색 - 중상위
    if (rating >= 2.0) return 'from-[#FBBF24] to-[#FBBF24]/70';  // 노랑색 - 평균
    if (rating >= 1.5) return 'from-[#FB923C] to-[#FB923C]/70';  // 빛바랜 주황색 - 평균 이하
    return 'from-[#9CA3AF] to-[#9CA3AF]/70';  // 무채색 회색 - 하위
  };

  const getRatingBadgeColor = (rating) => {
    if (rating === null) return 'bg-gray-600/30 text-gray-400';
    if (rating >= 4.5) return 'bg-[#00FFFF]/20 text-[#00FFFF] border-[#00FFFF]/30';  // 형광 사이언
    if (rating >= 4.0) return 'bg-[#60A5FA]/20 text-[#60A5FA] border-[#60A5FA]/30';  // 밝은 파랑
    if (rating >= 3.0) return 'bg-[#A855F7]/20 text-[#A855F7] border-[#A855F7]/30';  // 보라색
    if (rating >= 2.0) return 'bg-[#FBBF24]/20 text-[#FBBF24] border-[#FBBF24]/30';  // 노랑색
    if (rating >= 1.5) return 'bg-[#FB923C]/20 text-[#FB923C] border-[#FB923C]/30';  // 주황색
    return 'bg-[#9CA3AF]/20 text-[#9CA3AF] border-[#9CA3AF]/30';  // 회색
  };

  // 포지션 축약어로 변환
  const getPositionAbbreviation = (position) => {
    const abbreviations = {
      'Goalkeeper': 'GK',
      'Defender': 'DF',
      'Midfielder': 'MF',
      'Forward': 'FW',
      'Centre-Back': 'CB',
      'Right-Back': 'RB',
      'Left-Back': 'LB',
      'Defensive Midfield': 'DM',
      'Central Midfield': 'CM',
      'Attacking Midfield': 'AM',
      'Right Midfield': 'RM',
      'Left Midfield': 'LM',
      'Right Winger': 'RW',
      'Left Winger': 'LW',
      'Centre-Forward': 'CF',
      'Striker': 'ST'
    };
    return abbreviations[position] || position;
  };

  if (loading) {
    return (
      <div className="card p-12 text-center">
        <motion.div
          className="w-20 h-20 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-6"
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        />
        <p className="text-white/60 font-medium">스쿼드 데이터 로딩 중...</p>
      </div>
    );
  }

  return (
    <div className="text-white font-sans antialiased">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3">
        {/* Main Pitch Area */}
        <div className="lg:col-span-7 space-y-3">
          {/* Team Overall Stats */}
          <div className="relative bg-gradient-to-br from-slate-900/80 via-blue-950/60 to-slate-900/80 backdrop-blur-sm border border-cyan-500/20 rounded p-3 overflow-hidden">
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
            <div className="grid grid-cols-5 gap-3">
              {[
                { label: 'Overall', value: stats.overall, color: 'from-blue-500 to-cyan-400', icon: Award },
                { label: 'Attack', value: stats.attack, color: 'from-rose-500 to-orange-400', icon: Target },
                { label: 'Midfield', value: stats.midfield, color: 'from-amber-500 to-yellow-400', icon: Activity },
                { label: 'Defense', value: stats.defense, color: 'from-emerald-500 to-teal-400', icon: Shield },
                { label: 'Chemistry', value: stats.chemistry, color: 'from-violet-500 to-purple-400', icon: Flame }
              ].map(({ label, value, color, icon: Icon }) => (
                <div key={label} className="rounded-sm bg-white/[0.04] border border-white/[0.08] p-3">
                  <div className="flex items-center gap-1.5 mb-2">
                    <Icon className="w-4 h-4 text-white/50" />
                    <span className="text-xs text-white/70 font-medium">{label}</span>
                  </div>
                  <div className="text-2xl font-black mb-2 tabular-nums">{value.toFixed(1)}</div>
                  <div className="h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
                    <motion.div
                      className={`h-full bg-gradient-to-r ${color} rounded-full`}
                      initial={{ width: 0 }}
                      animate={{ width: `${(value / 5) * 100}%` }}
                      transition={{ duration: 0.6, ease: [0.34, 1.56, 0.64, 1] }}
                    />
                  </div>
                </div>
              ))}
            </div>

            {stats.unratedCount > 0 && (
              <div className="mt-3 p-2 rounded-sm bg-amber-500/10 border border-amber-500/30 flex items-center gap-2">
                <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
                <p className="text-[10px] text-amber-300 font-medium">
                  {stats.unratedCount}명 미평가
                </p>
              </div>
            )}
            </div>
          </div>

          {/* Pitch */}
          <div
            ref={pitchRef}
            className="rounded-sm overflow-hidden w-full"
              style={{
                aspectRatio: `${PITCH_WIDTH * 1.15}/${PITCH_LENGTH}`, // 가로 15% 증가
                maxHeight: '750px',
                border: '2px solid #06b6d4',
                boxShadow: '0 0 10px rgba(6, 182, 212, 0.4), 0 0 20px rgba(6, 182, 212, 0.2), inset 0 0 10px rgba(6, 182, 212, 0.05)'
              }}
            >
              <div className="relative w-full h-full bg-[#0d3d2a]">
                {/* Checkerboard pattern */}
                <div className="absolute inset-0" style={{
                  backgroundImage: `
                    linear-gradient(45deg, rgba(0,30,15,0.15) 25%, transparent 25%),
                    linear-gradient(-45deg, rgba(0,30,15,0.15) 25%, transparent 25%),
                    linear-gradient(45deg, transparent 75%, rgba(0,30,15,0.15) 75%),
                    linear-gradient(-45deg, transparent 75%, rgba(0,30,15,0.15) 75%)
                  `,
                  backgroundSize: '110px 110px',
                  backgroundPosition: '0 0, 0 55px, 55px -55px, -55px 0px'
                }} />

                {/* Subtle gradient overlay */}
                <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-black/10" />

                {/* Pitch markings - FIFA Standard (105m x 68m) */}
                <svg className="absolute inset-0 w-full h-full opacity-30" style={{ filter: 'drop-shadow(0 1px 2px rgba(0,0,0,0.3))' }}>
                  {/*
                    FIFA 표준 규격:
                    - 경기장: 105m x 68m
                    - 페널티 에리어: 36m x 14m (세로 x 가로)
                    - 골 에리어: 16m x 4.5m
                    - 페널티 스팟: 골라인으로부터 11m
                    - 센터 서클: 반지름 7m
                  */}

                  {/* Center circle - 반지름 7m */}
                  <circle cx="50%" cy="50%" r={`${(7 / PITCH_WIDTH) * 100}%`} fill="none" stroke="rgba(255,255,255,0.4)" strokeWidth="2.5" />
                  <circle cx="50%" cy="50%" r="4" fill="rgba(255,255,255,0.4)" />

                  {/* Center line - y=52.5m (정확히 중앙) */}
                  <line x1="0" y1="50%" x2="100%" y2="50%" stroke="rgba(255,255,255,0.4)" strokeWidth="2.5" />

                  {/* Penalty area - 상단 (0~14m) */}
                  <rect
                    x={`${((68 - 36) / 2 / PITCH_WIDTH) * 100}%`}
                    y="0"
                    width={`${(36 / PITCH_WIDTH) * 100}%`}
                    height={`${(14 / PITCH_LENGTH) * 100}%`}
                    fill="none"
                    stroke="rgba(255,255,255,0.4)"
                    strokeWidth="2.5"
                  />

                  {/* Penalty area - 하단 (91~105m) */}
                  <rect
                    x={`${((68 - 36) / 2 / PITCH_WIDTH) * 100}%`}
                    y={`${(91 / PITCH_LENGTH) * 100}%`}
                    width={`${(36 / PITCH_WIDTH) * 100}%`}
                    height={`${(14 / PITCH_LENGTH) * 100}%`}
                    fill="none"
                    stroke="rgba(255,255,255,0.4)"
                    strokeWidth="2.5"
                  />

                  {/* Goal area - 상단 (0~4.5m) */}
                  <rect
                    x={`${((68 - 16) / 2 / PITCH_WIDTH) * 100}%`}
                    y="0"
                    width={`${(16 / PITCH_WIDTH) * 100}%`}
                    height={`${(4.5 / PITCH_LENGTH) * 100}%`}
                    fill="none"
                    stroke="rgba(255,255,255,0.4)"
                    strokeWidth="2.5"
                  />

                  {/* Goal area - 하단 (100.5~105m) */}
                  <rect
                    x={`${((68 - 16) / 2 / PITCH_WIDTH) * 100}%`}
                    y={`${(100.5 / PITCH_LENGTH) * 100}%`}
                    width={`${(16 / PITCH_WIDTH) * 100}%`}
                    height={`${(4.5 / PITCH_LENGTH) * 100}%`}
                    fill="none"
                    stroke="rgba(255,255,255,0.4)"
                    strokeWidth="2.5"
                  />

                  {/* Penalty spots - 골라인으로부터 11m */}
                  <circle cx="50%" cy={`${(11 / PITCH_LENGTH) * 100}%`} r="3" fill="rgba(255,255,255,0.4)" />
                  <circle cx="50%" cy={`${(94 / PITCH_LENGTH) * 100}%`} r="3" fill="rgba(255,255,255,0.4)" />
                </svg>

                {/* Players */}
                {(() => {
                  // pitchDimensions가 유효하지 않으면 아무것도 렌더링하지 않음
                  if (!pitchDimensions.width || !pitchDimensions.height) {
                    return null;
                  }

                  return Object.entries(pixelPositions).map(([posKey, pixelPos]) => {
                    const playerId = squad.starters[posKey];
                    const player = playerId ? getPlayer(playerId) : null;

                    if (player) {
                      return (
                        <motion.div
                          key={posKey}
                          draggable
                          onDragStart={(e) => handleDragStart(e, player)}
                          onDragEnd={handleDragEnd}
                          onClick={(e) => {
                            e.stopPropagation();
                            const rect = e.currentTarget.getBoundingClientRect();
                            const clickY = rect.top + rect.height / 2; // 카드 중앙 위치
                            setClickPosition({ x: e.clientX, y: clickY });
                            setSelectedPlayer(player);
                          }}
                          className="absolute -translate-x-1/2 -translate-y-1/2 cursor-move group"
                          style={{
                            left: `${pixelPos.x}px`,
                            top: `${pixelPos.y}px`
                          }}
                          initial={{ scale: 0, opacity: 0 }}
                          animate={{ scale: 1, opacity: 1 }}
                          transition={{ type: "spring", stiffness: 300, damping: 25 }}
                          whileHover={{ scale: 1.08, zIndex: 50 }}
                          whileTap={{ scale: 0.95 }}
                        >
                        <div className="relative">
                          {/* Glow effect */}
                          <div className={`absolute -inset-3 bg-gradient-to-r ${getPositionGradientColor(getRole(posKey))} rounded-sm blur-xl opacity-0 group-hover:opacity-40 transition-opacity duration-300`} />

                          {/* Square Card */}
                          <div
                            className={`relative w-20 h-20 rounded-sm bg-gradient-to-br ${getPositionGradientColor(getRole(posKey))} shadow-2xl transform transition-all duration-200 border-2 border-dashed ${getPositionBorderColor(getRole(posKey))} group-hover:${getPositionBorderHoverColor(getRole(posKey))}`}
                            style={{
                              transition: 'all 0.2s'
                            }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.boxShadow = '0 0 10px rgba(6, 182, 212, 0.6), 0 0 20px rgba(6, 182, 212, 0.3)';
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.boxShadow = '';
                            }}
                          >
                            <div className="w-full h-full rounded-sm bg-slate-900/95 backdrop-blur-sm flex flex-col items-center justify-center p-1.5">
                              {/* 선수 이름 */}
                              <div className="text-[10px] font-bold text-white leading-tight text-center mb-1 line-clamp-2 px-1" style={{ textShadow: '0 1px 3px rgba(0,0,0,0.6)' }}>
                                {player.name}
                              </div>

                              {/* Rating - 포지션 기반 색상 */}
                              <div className={`px-1.5 py-0 rounded-md text-base font-black ${getPositionBadgeColor(getRole(posKey))} border shadow-sm`}>
                                {player.rating !== null ? player.rating.toFixed(1) : '-'}
                              </div>

                              {/* Remove button */}
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  removePlayer(posKey);
                                }}
                                className="absolute -top-1 -left-1 w-5 h-5 rounded-md bg-rose-600 hover:bg-rose-500 border border-rose-400/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-200 shadow-lg"
                              >
                                <X className="w-3 h-3" />
                              </button>
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    );
                  }

                    // Empty position
                    return (
                      <motion.div
                        key={posKey}
                        onDragOver={(e) => { e.preventDefault(); setHoveredPos(posKey); }}
                        onDragLeave={() => setHoveredPos(null)}
                        onDrop={(e) => handleDrop(e, posKey)}
                        onClick={() => handlePositionClick(posKey)}
                        className="absolute -translate-x-1/2 -translate-y-1/2 cursor-pointer group"
                        style={{
                          left: `${pixelPos.x}px`,
                          top: `${pixelPos.y}px`
                        }}
                        initial={{ scale: 0, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        whileHover={{ scale: 1.05 }}
                      >
                      <div
                        className={`w-20 h-20 rounded-sm flex flex-col items-center justify-center backdrop-blur-sm transition-all duration-200 relative border-2 border-dashed group-hover:border-cyan-400 ${
                          hoveredPos === posKey
                            ? 'bg-cyan-400/15 scale-105 shadow-lg shadow-cyan-400/20 border-cyan-400/40'
                            : 'bg-white/[0.07] border-white/20'
                        }`}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.boxShadow = '0 0 10px rgba(6, 182, 212, 0.6), 0 0 20px rgba(6, 182, 212, 0.3)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.boxShadow = '';
                        }}
                      >
                        <div
                          className={`w-10 h-10 rounded-full flex items-center justify-center transition-all mb-1 ${
                            hoveredPos === posKey ? 'bg-cyan-400/25 scale-110' : ''
                          }`}
                          style={{
                            backgroundColor: hoveredPos === posKey ? '' : 'rgba(15, 23, 42, 0.8)'
                          }}
                        >
                          <span className={`text-2xl ${hoveredPos === posKey ? 'text-cyan-300' : 'text-white/50'}`}>+</span>
                        </div>
                        <span className={`text-[10px] font-bold uppercase tracking-wider ${
                          hoveredPos === posKey ? 'text-cyan-300' : 'text-white/50'
                        }`}>{getRole(posKey)}</span>
                      </div>
                      </motion.div>
                    );
                  });
                })()}
              </div>
            </div>

        </div>

        {/* Right Sidebar */}
        <div className="lg:col-span-5 space-y-3">
          {/* Control Buttons */}
          <div className="relative bg-gradient-to-br from-slate-900/80 via-blue-950/60 to-slate-900/80 backdrop-blur-sm border border-cyan-500/30 rounded-sm p-3 overflow-visible z-50">
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
            <div className="flex items-center gap-2.5">
              {/* Formation Selector */}
              <div className="relative flex-1" ref={formationMenuRef}>
                <button
                  onClick={() => setShowFormationMenu(!showFormationMenu)}
                  className="w-full h-10 px-3.5 rounded-sm bg-slate-900/60 hover:bg-slate-800/80 border border-cyan-500/30 hover:border-cyan-400/50 font-mono font-semibold text-xs transition-all duration-200 flex items-center justify-between gap-2 shadow-sm active:scale-[0.98] group/btn"
                >
                  <span className="text-cyan-300 group-hover/btn:text-cyan-200 transition-colors">{formation}</span>
                  <ChevronDown className={`w-4 h-4 text-cyan-400 group-hover/btn:text-cyan-300 transition-all ${showFormationMenu ? 'rotate-180' : ''}`} />
                </button>

                {showFormationMenu && (
                  <div
                    ref={formationDropdownRef}
                    className="absolute top-full mt-2 left-0 right-0 rounded-sm bg-slate-900 border border-cyan-500/40 shadow-2xl shadow-cyan-500/20 z-[100] max-h-[500px] overflow-y-auto scrollbar-thin scrollbar-thumb-cyan-500/30 scrollbar-track-transparent"
                  >
                    {Object.entries(formations).map(([key, { name }]) => (
                      <button
                        key={key}
                        ref={formation === key ? selectedFormationRef : null}
                        onClick={() => {
                          setFormation(key);
                          setShowFormationMenu(false);
                        }}
                        className={`w-full px-4 py-2.5 text-left font-mono transition-all border-b border-cyan-500/10 last:border-0 ${
                          formation === key
                            ? 'bg-cyan-600/30 text-cyan-300 shadow-sm shadow-cyan-500/20 border-l-2 border-l-cyan-400'
                            : 'hover:bg-cyan-500/10 text-white/70 hover:text-cyan-300 hover:border-l-2 hover:border-l-cyan-500/50'
                        }`}
                      >
                        <div className="font-bold text-sm">{name}</div>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <button
                onClick={autoFill}
                className="h-10 px-4 rounded-sm bg-slate-900/60 hover:bg-slate-800/80 border border-cyan-500/30 hover:border-cyan-400/50 font-mono font-bold text-xs shadow-sm transition-all duration-200 flex items-center gap-2 active:scale-95 whitespace-nowrap group/btn"
              >
                <Sparkles className="w-4 h-4 text-cyan-400 group-hover/btn:animate-pulse" />
                <span className="text-cyan-300">AUTO</span>
              </button>

              <button
                onClick={() => setSquad({ starters: {}, substitutes: [] })}
                className="h-10 w-10 rounded-sm bg-slate-900/60 hover:bg-slate-800/80 border border-cyan-500/30 hover:border-cyan-400/50 transition-all duration-200 flex items-center justify-center active:scale-95 shadow-sm group/btn"
                title="초기화"
              >
                <RotateCcw className="w-4 h-4 text-cyan-400 group-hover/btn:text-cyan-300 group-hover/btn:rotate-[-90deg] transition-all duration-200" />
              </button>

              <button
                onClick={handleSave}
                disabled={saveStatus !== 'idle'}
                className={`h-10 w-[80px] rounded-sm font-mono font-bold text-xs shadow-sm transition-all duration-200 flex items-center justify-center gap-2 whitespace-nowrap border group/btn ${
                  saveStatus === 'success'
                    ? 'bg-slate-900/60 border-cyan-500/30'
                    : saveStatus === 'saving'
                    ? 'bg-slate-800/60 border-cyan-400/30 cursor-wait'
                    : 'bg-slate-900/60 hover:bg-slate-800/80 border-cyan-500/30 hover:border-cyan-400/50 active:scale-95'
                }`}
              >
                {saveStatus === 'saving' ? (
                  <>
                    <motion.div
                      className="w-4 h-4 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full"
                      animate={{ rotate: 360 }}
                      transition={{ duration: 0.8, repeat: Infinity, ease: "linear" }}
                    />
                    <span className="text-cyan-300">...</span>
                  </>
                ) : saveStatus === 'success' ? (
                  <>
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ type: "spring", stiffness: 500, damping: 15 }}
                    >
                      <Check className="w-4 h-4 text-cyan-400" />
                    </motion.div>
                    <span className="text-cyan-300">OK</span>
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 text-cyan-400" />
                    <span className="text-cyan-300">SAVE</span>
                  </>
                )}
              </button>
            </div>
            </div>
          </div>

          {/* Player Pool */}
          <div className="relative bg-gradient-to-br from-slate-900/80 via-blue-950/60 to-slate-900/80 backdrop-blur-sm border border-cyan-500/20 rounded p-4 overflow-hidden z-10">
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
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-bold text-sm flex items-center gap-2 font-mono">
                <Filter className="w-4 h-4 text-cyan-400" />
                <span className="text-cyan-300">PLAYERS</span>
              </h3>
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cyan-400/50" />
                  <input
                    type="text"
                    placeholder="선수 검색..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="h-10 pl-10 pr-4 rounded-sm bg-slate-900/60 border border-cyan-500/30 text-sm placeholder:text-white/40 focus:border-cyan-400/50 focus:bg-slate-800/80 transition-all outline-none w-40 font-mono"
                  />
                </div>
                <select
                  value={positionFilter}
                  onChange={(e) => setPositionFilter(e.target.value)}
                  className="h-10 px-3 rounded-sm bg-slate-900/60 border border-cyan-500/30 text-sm focus:border-cyan-400/50 focus:bg-slate-800/80 transition-all outline-none font-mono text-cyan-300"
                >
                  <option value="ALL">전체</option>
                  <option value="GK">GK</option>
                  <option value="FB">FB</option>
                  <option value="CB">CB</option>
                  <option value="DM">DM</option>
                  <option value="CM">CM</option>
                  <option value="CAM">CAM</option>
                  <option value="WG">WG</option>
                  <option value="ST">ST</option>
                </select>
              </div>
            </div>

            {/* 주전 선수 섹션 (role === 'starter') */}
            {filteredPlayers.filter(p => p.role === 'starter').length > 0 && (
              <>
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse shadow-lg shadow-cyan-400/50" />
                  <h4 className="text-xs font-bold text-cyan-300 uppercase tracking-wider font-mono">
                    주전 선수 ({filteredPlayers.filter(p => p.role === 'starter').length})
                  </h4>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 mb-4">
                  {filteredPlayers.filter(p => p.role === 'starter').map(player => (
                    <PlayerCardCompact
                      key={player.id}
                      player={player}
                      isStarter={true}
                      onDragStart={handleDragStart}
                      onDragEnd={handleDragEnd}
                      onClick={(e) => {
                        e.stopPropagation();
                        const rect = e.currentTarget.getBoundingClientRect();
                        const clickY = rect.top + rect.height / 2; // 카드 중앙 위치
                        setClickPosition({ x: e.clientX, y: clickY });
                        setSelectedPlayer(player);
                      }}
                      getRatingBadgeColor={getRatingBadgeColor}
                      getPlayerRole={getPlayerRole}
                      getPositionBadgeColor={getPositionBadgeColor}
                    />
                  ))}
                </div>
              </>
            )}

            {/* 후보 선수 섹션 (role === 'substitute') */}
            {filteredPlayers.filter(p => p.role === 'substitute').length > 0 && (
              <>
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-amber-400/60" />
                  <h4 className="text-xs font-bold text-amber-300/80 uppercase tracking-wider font-mono">
                    후보 선수 ({filteredPlayers.filter(p => p.role === 'substitute').length})
                  </h4>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 max-h-[300px] overflow-y-auto scrollbar-thin scrollbar-thumb-cyan-500/30 scrollbar-track-transparent pr-2 mb-4">
                  {filteredPlayers.filter(p => p.role === 'substitute').map(player => (
                    <PlayerCardCompact
                      key={player.id}
                      player={player}
                      isStarter={false}
                      onDragStart={handleDragStart}
                      onDragEnd={handleDragEnd}
                      onClick={(e) => {
                        e.stopPropagation();
                        const rect = e.currentTarget.getBoundingClientRect();
                        const clickY = rect.top + rect.height / 2; // 카드 중앙 위치
                        setClickPosition({ x: e.clientX, y: clickY });
                        setSelectedPlayer(player);
                      }}
                      getRatingBadgeColor={getRatingBadgeColor}
                      getPlayerRole={getPlayerRole}
                      getPositionBadgeColor={getPositionBadgeColor}
                    />
                  ))}
                </div>
              </>
            )}

            {/* 전력 외 섹션 (role === 'other') */}
            {filteredPlayers.filter(p => p.role === 'other').length > 0 && (
              <>
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-white/20" />
                  <h4 className="text-xs font-bold text-white/40 uppercase tracking-wider font-mono">
                    전력 외 ({filteredPlayers.filter(p => p.role === 'other').length})
                  </h4>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 max-h-[200px] overflow-y-auto scrollbar-thin scrollbar-thumb-cyan-500/30 scrollbar-track-transparent pr-2">
                  {filteredPlayers.filter(p => p.role === 'other').map(player => (
                    <PlayerCardCompact
                      key={player.id}
                      player={player}
                      isStarter={false}
                      onDragStart={handleDragStart}
                      onDragEnd={handleDragEnd}
                      onClick={(e) => {
                        e.stopPropagation();
                        const rect = e.currentTarget.getBoundingClientRect();
                        const clickY = rect.top + rect.height / 2; // 카드 중앙 위치
                        setClickPosition({ x: e.clientX, y: clickY });
                        setSelectedPlayer(player);
                      }}
                      getRatingBadgeColor={getRatingBadgeColor}
                      getPlayerRole={getPlayerRole}
                      getPositionBadgeColor={getPositionBadgeColor}
                    />
                  ))}
                </div>
              </>
            )}
            </div>
          </div>
        </div>
      </div>

      {/* Position Picker Modal */}
      <AnimatePresence>
        {positionPickerOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className={`fixed inset-0 bg-black/80 backdrop-blur-md flex items-start justify-center z-[100] p-6 ${
              // 포지션별 팝업 위치 조정
              ['GK', 'CB', 'FB'].includes(positionPickerOpen.role)
                ? 'pt-32'  // 수비수/골키퍼: 더 아래로 (128px)
                : ['DM', 'CM', 'CAM'].includes(positionPickerOpen.role)
                  ? 'pt-24'  // 미드필더: 조금 아래로 (96px)
                  : 'pt-16'  // 공격수(WG, ST): 현재 위치 (64px)
            }`}
            onClick={() => setPositionPickerOpen(null)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: -20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -20 }}
              className="bg-gradient-to-br from-slate-900/95 via-blue-950/60 to-slate-900/95 backdrop-blur-xl rounded-sm border border-cyan-500/30 shadow-2xl p-4 max-w-lg w-full relative overflow-hidden max-h-[85vh] flex flex-col"
              onClick={(e) => e.stopPropagation()}
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

              <div className="relative flex-1 flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-lg font-bold text-cyan-300 font-mono uppercase tracking-wide">
                      {positionPickerOpen.posKey} 포지션
                    </h2>
                    <p className="text-xs text-white/60 mt-0.5">
                      {positionPickerOpen.role} 선수를 선택하세요
                    </p>
                  </div>
                  <button
                    onClick={() => setPositionPickerOpen(null)}
                    className="w-9 h-9 rounded-sm bg-white/5 hover:bg-cyan-500/20 border border-white/10 hover:border-cyan-500/40 flex items-center justify-center transition-all"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                {/* Player List */}
                <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-cyan-500/30 scrollbar-track-transparent pr-2">
                  <div className="grid grid-cols-1 gap-1.5">
                    {players
                      .filter(p => getPlayerRole(p.position) === positionPickerOpen.role)
                      .filter(p => !Object.values(squad.starters).includes(p.id)) // 이미 배치된 선수 제외
                      .sort((a, b) => {
                        // rating이 있는 선수 우선
                        if (a.rating === null && b.rating !== null) return 1;
                        if (a.rating !== null && b.rating === null) return -1;
                        if (a.rating === null && b.rating === null) return 0;
                        return b.rating - a.rating;
                      })
                      .map(player => {
                        const photoUrl = player.photo ? getPlayerPhotoUrl(player.photo, '110x140') : null;

                        return (
                          <motion.div
                            key={player.id}
                            className="group rounded-sm border border-cyan-500/20 hover:border-cyan-400/50 bg-slate-900/40 hover:bg-cyan-500/10 p-2 cursor-pointer transition-all"
                            whileHover={{ scale: 1.01, x: 4 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={() => assignPlayerToPosition(player, positionPickerOpen.posKey)}
                          >
                            <div className="flex items-center gap-2">
                              {/* 프로필 사진 */}
                              <div className="relative w-16 h-16 rounded-sm flex-shrink-0 overflow-hidden">
                                {photoUrl ? (
                                  <img
                                    src={photoUrl}
                                    alt={player.name}
                                    crossOrigin="anonymous"
                                    referrerPolicy="no-referrer"
                                    className="w-24 h-24 object-cover object-[center_35%] rounded-sm border-2 border-cyan-500/30 group-hover:border-cyan-400/60 transition-all duration-300"
                                    onError={(e) => {
                                      // 이미지 로드 실패 시 fallback UI로 교체
                                      e.target.style.display = 'none';
                                      e.target.nextSibling.style.display = 'flex';
                                    }}
                                  />
                                ) : null}
                                {/* Fallback (사진이 없거나 로드 실패 시) */}
                                <div
                                  className="w-16 h-16 rounded-sm flex items-center justify-center bg-slate-800/60 border-2 border-cyan-500/30 group-hover:border-cyan-400/60 transition-all"
                                  style={{ display: photoUrl ? 'none' : 'flex' }}
                                >
                                  <User className="w-8 h-8 text-white/30" />
                                </div>
                              </div>

                              {/* 선수 정보 - 가운데 */}
                              <div className="flex-1 min-w-0">
                                <p className="font-bold text-sm text-white leading-tight group-hover:text-cyan-300 transition-colors mb-1.5 line-clamp-2">
                                  {player.name}
                                </p>
                                <span className={`inline-block px-2 py-0.5 rounded text-xs font-bold font-mono uppercase border ${
                                  getRatingBadgeColor(player.rating)
                                }`}>
                                  {player.position}
                                </span>
                              </div>

                              {/* Rating - 오른쪽에 크게 독립적으로 */}
                              {player.rating !== null ? (
                                <div className="flex flex-col items-center justify-center px-3 py-2 rounded-sm bg-gradient-to-br from-cyan-500/20 to-blue-500/20 border border-cyan-500/40 min-w-[60px]">
                                  <span className={`text-2xl font-black font-mono leading-none ${
                                    player.rating >= 4.5 ? 'text-cyan-300' :
                                    player.rating >= 4.0 ? 'text-cyan-400' :
                                    player.rating >= 3.0 ? 'text-purple-400' :
                                    'text-amber-400'
                                  }`}>
                                    {player.rating.toFixed(1)}
                                  </span>
                                  <span className="text-[10px] text-white/50 uppercase tracking-wider font-bold mt-0.5">
                                    Rating
                                  </span>
                                </div>
                              ) : (
                                <div className="flex flex-col items-center justify-center px-3 py-2 rounded-sm bg-slate-800/40 border border-white/10 min-w-[60px]">
                                  <span className="text-xl font-black font-mono leading-none text-white/30">
                                    -
                                  </span>
                                  <span className="text-[10px] text-white/30 uppercase tracking-wider font-bold mt-0.5">
                                    Rating
                                  </span>
                                </div>
                              )}
                            </div>
                          </motion.div>
                        );
                      })}
                    {players.filter(p => getPlayerRole(p.position) === positionPickerOpen.role && !Object.values(squad.starters).includes(p.id)).length === 0 && (
                      <div className="text-center py-12 text-white/50">
                        <AlertCircle className="w-12 h-12 mx-auto mb-3 text-white/30" />
                        <p className="text-sm">해당 포지션에 사용 가능한 선수가 없습니다</p>
                        <p className="text-xs mt-2 text-white/40">모든 선수가 이미 배치되었거나 평가가 필요합니다</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Player Detail Modal */}
      <AnimatePresence>
        {selectedPlayer && (() => {
          // 팝업 위치 계산: 가로는 중앙 고정, 세로만 동적 계산
          const popupWidth = 384; // max-w-sm
          const popupHeight = 450; // 예상 높이
          const padding = 20;

          // 가로: 화면 중앙 고정
          const left = (window.innerWidth - popupWidth) / 2;

          // 세로: 클릭 위치를 기반으로 스마트하게 계산
          const screenHeight = window.innerHeight;
          const clickY = clickPosition.y;

          let top;

          // 클릭 위치가 화면 상단 1/3 영역
          if (clickY < screenHeight / 3) {
            top = clickY + 20; // 클릭 위치 아래에 표시
          }
          // 클릭 위치가 화면 하단 1/3 영역
          else if (clickY > (screenHeight * 2) / 3) {
            top = clickY - popupHeight - 20; // 클릭 위치 위에 표시
          }
          // 클릭 위치가 화면 중앙 영역
          else {
            top = clickY - popupHeight / 2; // 클릭 위치 중심에 표시
          }

          // 하단 경계 체크
          if (top + popupHeight > screenHeight - padding) {
            top = screenHeight - popupHeight - padding;
          }

          // 상단 경계 체크
          if (top < padding) {
            top = padding;
          }

          return (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/80 backdrop-blur-md z-[100]"
              onClick={() => setSelectedPlayer(null)}
            >
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="absolute bg-gradient-to-br from-slate-900/95 via-blue-950/60 to-slate-900/95 backdrop-blur-xl rounded-sm border border-cyan-500/30 shadow-2xl p-5 w-[384px] overflow-hidden"
                style={{
                  left: `${left}px`,
                  top: `${top}px`,
                }}
                onClick={(e) => e.stopPropagation()}
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
              <button
                onClick={() => setSelectedPlayer(null)}
                className="absolute top-0 right-0 w-10 h-10 rounded-sm bg-white/5 hover:bg-cyan-500/20 border border-white/10 hover:border-cyan-500/40 flex items-center justify-center transition-all"
              >
                <X className="w-5 h-5" />
              </button>

              <div className="flex items-start gap-3 mb-5">
                {/* 프로필 사진 */}
                <div className="w-24 h-24 flex-shrink-0 rounded-sm overflow-hidden border-2 border-cyan-500/30 shadow-2xl bg-slate-800/60">
                  {selectedPlayer.photo ? (
                    <img
                      src={getPlayerPhotoUrl(selectedPlayer.photo, '110x140')}
                      alt={selectedPlayer.name}
                      crossOrigin="anonymous"
                      referrerPolicy="no-referrer"
                      className="w-full h-full object-cover object-[center_20%]"
                      onError={(e) => {
                        e.target.style.display = 'none';
                        e.target.nextSibling.style.display = 'flex';
                      }}
                    />
                  ) : null}
                  <div
                    className="w-24 h-24 flex items-center justify-center bg-slate-800/60"
                    style={{ display: selectedPlayer.photo ? 'none' : 'flex' }}
                  >
                    <User className="w-12 h-12 text-white/30" />
                  </div>
                </div>

                {/* 선수 정보 */}
                <div className="flex-1">
                  <h2 className="text-xl font-bold mb-2 leading-tight">{selectedPlayer.name}</h2>
                  <div className="flex items-center gap-2">
                    <span className={`px-2.5 py-0.5 rounded-sm text-sm font-bold font-mono uppercase border ${getRatingBadgeColor(selectedPlayer.rating)}`}>
                      {getPositionAbbreviation(selectedPlayer.position)}
                    </span>
                    <span className="px-2.5 py-0.5 rounded-sm text-sm font-bold font-mono bg-gradient-to-r from-purple-500/20 to-blue-500/20 border border-purple-500/40 text-purple-300">
                      #{selectedPlayer.number || '?'}
                    </span>
                  </div>
                </div>
              </div>

              {/* 통계 그리드 */}
              <div className="grid grid-cols-2 gap-3 mb-4">
                {[
                  { label: '나이', value: selectedPlayer.age || '-', color: 'from-cyan-500 to-blue-600' },
                  { label: '출전', value: selectedPlayer.appearances || 0, color: 'from-cyan-500 to-blue-600' },
                  { label: '골', value: selectedPlayer.goals || 0, color: 'from-rose-500 to-pink-600' },
                  { label: '어시스트', value: selectedPlayer.assists || 0, color: 'from-cyan-400 to-cyan-600' }
                ].map(({ label, value, color }) => (
                  <div key={label} className="rounded-sm bg-white/[0.04] border border-white/[0.08] p-3">
                    <p className="text-xs text-white/50 font-medium mb-1 font-mono">{label}</p>
                    <p className={`text-2xl font-black font-mono ${value === '-' ? 'text-white/30' : `bg-gradient-to-br ${color} bg-clip-text text-transparent`}`}>{value}</p>
                  </div>
                ))}
              </div>

              {/* AVG RATING 프로그레스 바 */}
              <div className="bg-white/[0.04] border border-white/[0.08] rounded-sm p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold font-mono text-cyan-400 uppercase tracking-wider">AVG Rating</span>
                  <span className="text-xl font-black font-mono bg-gradient-to-br from-cyan-400 to-blue-500 bg-clip-text text-transparent">
                    {selectedPlayer.rating !== null ? selectedPlayer.rating.toFixed(2) : '-'} <span className="text-xs text-white/40">/5.0</span>
                  </span>
                </div>
                {/* 프로그레스 바 */}
                <div className="relative h-2 bg-slate-800/60 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: selectedPlayer.rating !== null ? `${(selectedPlayer.rating / 5.0) * 100}%` : '0%' }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                    className="absolute inset-y-0 left-0 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-full shadow-lg shadow-cyan-500/50"
                  />
                </div>
              </div>
              </div>
            </motion.div>
          </motion.div>
          );
        })()}
      </AnimatePresence>
    </div>
  );
};

export default PremiumSquadBuilder;
