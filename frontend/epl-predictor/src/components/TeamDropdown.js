import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Check } from 'lucide-react';

/**
 * TeamDropdown Component
 * 프리미엄 스타일의 커스텀 드롭다운
 */
const TeamDropdown = ({
  value,
  onChange,
  teams = [],
  teamScores = {},
  placeholder = "-- 팀 선택 --",
  disabled = false,
  disabledTeams = [] // 선택 불가한 팀 목록
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const dropdownRef = useRef(null);

  // 외부 클릭 감지
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    const handleEscape = (event) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen]);

  // 필터링된 팀 목록
  const filteredTeams = teams.filter(team =>
    team.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleSelect = (team) => {
    onChange(team);
    setIsOpen(false);
    setSearchTerm('');
  };

  const selectedTeam = teams.find(t => t === value);

  return (
    <div ref={dropdownRef} className="relative w-full">
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={`
          w-full px-4 py-3 text-lg font-semibold text-left
          bg-slate-950/80 text-white border-2 rounded
          focus:outline-none focus:ring-2 focus:ring-cyan-400/20
          transition-all duration-200
          ${disabled
            ? 'opacity-50 cursor-not-allowed border-cyan-500/20'
            : isOpen
              ? 'border-cyan-400 ring-2 ring-cyan-400/20'
              : 'border-cyan-500/30 hover:border-cyan-500/50'
          }
          flex items-center justify-between
        `}
      >
        {!value ? (
          <span className="text-white/60">{placeholder}</span>
        ) : (
          <div className="flex items-center gap-2">
            <span className="text-white">{selectedTeam}</span>
            {teamScores[selectedTeam]?.hasData ? (
              <span className="text-cyan-400 font-semibold text-base">
                {teamScores[selectedTeam].overall.toFixed(1)}점
              </span>
            ) : (
              <span className="text-amber-400 font-medium text-sm">
                미평가
              </span>
            )}
          </div>
        )}
        <motion.div
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <ChevronDown className="w-5 h-5 text-cyan-400" />
        </motion.div>
      </button>

      {/* Dropdown Menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.15, ease: 'easeOut' }}
            className="absolute z-50 w-full mt-2 bg-slate-950/95 backdrop-blur-xl border-2 border-cyan-500/30 rounded shadow-2xl shadow-cyan-500/10 overflow-hidden"
          >
            {/* Search Box */}
            <div className="p-3 border-b border-cyan-500/20">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="팀 검색..."
                className="w-full px-3 py-2 text-sm bg-slate-900/80 text-white border border-cyan-500/30 rounded focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400/20 placeholder-white/40"
                onClick={(e) => e.stopPropagation()}
              />
            </div>

            {/* Options List */}
            <div className="max-h-64 overflow-y-auto custom-scrollbar">
              {filteredTeams.length === 0 ? (
                <div className="px-4 py-8 text-center text-white/40 text-sm">
                  팀을 찾을 수 없습니다
                </div>
              ) : (
                filteredTeams.map((team) => {
                  const isSelected = team === value;
                  const hasData = teamScores[team]?.hasData;
                  const score = teamScores[team]?.overall;
                  const isDisabled = disabledTeams.includes(team);

                  return (
                    <motion.button
                      key={team}
                      onClick={() => !isDisabled && handleSelect(team)}
                      disabled={isDisabled}
                      className={`
                        w-full px-4 py-3 text-left flex items-center justify-between gap-3
                        transition-colors duration-150
                        ${isDisabled
                          ? 'opacity-40 cursor-not-allowed bg-slate-800/40'
                          : isSelected
                            ? 'bg-cyan-500/20 text-white'
                            : 'text-white/90 hover:bg-cyan-500/10'
                        }
                      `}
                      whileHover={!isDisabled ? { x: 4 } : {}}
                      transition={{ duration: 0.1 }}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className={`font-semibold ${
                            isDisabled
                              ? 'text-white/40'
                              : isSelected
                                ? 'text-cyan-400'
                                : 'text-white'
                          }`}>
                            {team}
                          </span>
                          {hasData && (
                            <span className={`text-xs font-medium ${
                              isDisabled ? 'text-cyan-400/30' : 'text-cyan-400/70'
                            }`}>
                              {score.toFixed(1)}점
                            </span>
                          )}
                          {!hasData && (
                            <span className={`text-xs ${
                              isDisabled ? 'text-amber-400/30' : 'text-amber-400/70'
                            }`}>
                              미평가
                            </span>
                          )}
                        </div>
                      </div>
                      {isSelected && !isDisabled && (
                        <Check className="w-4 h-4 text-cyan-400 flex-shrink-0" />
                      )}
                    </motion.button>
                  );
                })
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Custom Scrollbar Styles */}
      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(15, 23, 42, 0.5);
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(6, 182, 212, 0.3);
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(6, 182, 212, 0.5);
        }
      `}</style>
    </div>
  );
};

export default TeamDropdown;
