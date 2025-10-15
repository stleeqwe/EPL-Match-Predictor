import React, { useState, useEffect, useRef } from 'react';
import { Check, ChevronDown } from 'lucide-react';

/**
 * TeamSelector Component
 * EPL 팀 선택 컴포넌트
 */
const TeamSelector = ({
  darkMode = false,
  onTeamSelect,
  selectedTeam = null,
  nested = false  // 통합 사이드바 내부에 있을 때 true
}) => {
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  // 팀 목록 로드
  useEffect(() => {
    fetchTeams();
  }, []);

  // 드롭다운 외부 클릭 감지
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchTeams = async () => {
    try {
      setLoading(true);

      const response = await fetch('http://localhost:5001/api/teams');

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: Failed to fetch teams`);
      }

      const data = await response.json();
      const teamsList = data.teams || [];

      // 팀 데이터가 객체 배열인지 문자열 배열인지 확인
      const normalizedTeams = teamsList.map(team =>
        typeof team === 'string' ? { name: team, emblem: '' } : team
      );

      setTeams(normalizedTeams);
      setError(null);
    } catch (err) {
      console.error('❌ [DEBUG] Error fetching teams:', err);
      setError('팀 목록을 불러오지 못했습니다');
    } finally {
      setLoading(false);
    }
  };

  // 팀 선택 핸들러
  const handleTeamSelect = (teamName) => {
    onTeamSelect(teamName);
    setIsOpen(false);
  };

  if (loading) {
    return (
      <div className={nested ? "relative" : "relative bg-slate-900/95 backdrop-blur-sm border border-cyan-500/20 rounded p-6 overflow-hidden"}>
        {!nested && (
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
        )}
        <div className="relative animate-pulse space-y-4">
          <div className="h-4 bg-cyan-500/10 rounded-sm w-1/2 border border-cyan-500/20"></div>
          <div className="space-y-2">
            {[1, 2, 3, 4, 5].map(i => (
              <div key={i} className="h-12 bg-slate-900/60 rounded-sm border border-cyan-500/20"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={nested ? "relative" : "relative bg-slate-900/95 backdrop-blur-sm border border-cyan-500/20 rounded p-6 overflow-hidden"}>
        {!nested && (
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
        )}
        <div className="relative text-center">
          <p className="text-error mb-4">{error}</p>
          <button
            onClick={fetchTeams}
            className="px-4 py-2 bg-cyan-500/20 hover:bg-cyan-500/30 text-white border border-cyan-500/40 rounded-sm transition-all font-medium"
          >
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="relative overflow-visible">
      {/* Header */}
      <div className="relative mb-3">
        <h3 className="text-xs font-bold text-cyan-400/60 uppercase tracking-wider font-mono">
          Team
        </h3>
      </div>

      {/* Custom Dropdown */}
      <div className="relative" ref={dropdownRef}>
        {/* Dropdown Button */}
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className={`
            relative w-full px-4 py-3 rounded-sm font-medium transition-all
            flex items-center justify-between overflow-hidden
            ${selectedTeam
              ? 'bg-slate-900/80 text-white border border-cyan-500/50'
              : 'bg-slate-900/80 text-white/70 border border-cyan-500/20 hover:border-cyan-500/40 hover:bg-slate-900/90 hover:text-white'}
          `}
        >
          <div className="flex items-center gap-2">
            {selectedTeam && teams.find(t => t.name === selectedTeam)?.emblem && (
              <img
                src={teams.find(t => t.name === selectedTeam).emblem}
                alt={selectedTeam}
                className="w-5 h-5 object-contain"
                onError={(e) => {
                  e.target.style.display = 'none';
                }}
              />
            )}
            <span>{selectedTeam || '팀을 선택하세요'}</span>
          </div>
          <ChevronDown
            className={`w-4 h-4 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
          />
        </button>

        {/* Dropdown Menu */}
        {isOpen && (
          <div className="absolute z-[9999] w-full mt-2 bg-slate-900 border border-cyan-500/40 rounded-sm max-h-80 overflow-hidden backdrop-blur-md" style={{ boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)' }}>
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
            {/* Team List */}
            <div className="relative overflow-y-auto max-h-64 custom-scrollbar">
              {teams.length === 0 ? (
                <div className="p-4 text-center text-white/40">
                  팀 목록이 없습니다
                </div>
              ) : (
                teams.map(team => (
                  <button
                    key={team.name}
                    type="button"
                    onClick={() => handleTeamSelect(team.name)}
                    className={`
                      w-full px-4 py-3 flex items-center gap-3 transition-all border-l-2 font-medium
                      ${selectedTeam === team.name
                        ? 'bg-cyan-500/20 text-white border-l-cyan-400'
                        : 'text-white/70 hover:bg-cyan-500/10 hover:text-white border-l-transparent hover:border-l-cyan-500/30'}
                    `}
                  >
                    {/* Team Emblem */}
                    {team.emblem && (
                      <div className="w-6 h-6 flex-shrink-0">
                        <img
                          src={team.emblem}
                          alt={team.name}
                          className="w-full h-full object-contain"
                          onError={(e) => {
                            e.target.style.display = 'none';
                          }}
                        />
                      </div>
                    )}

                    {/* Team Name */}
                    <span className="flex-1 text-left font-medium">{team.name}</span>

                    {/* Check Icon */}
                    {selectedTeam === team.name && (
                      <Check className="w-4 h-4 text-brand-accent" />
                    )}
                  </button>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TeamSelector;
