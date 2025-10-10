import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { TrendingUp, TrendingDown, RefreshCw } from 'lucide-react';
import { eplAPI } from '../services/api';

/**
 * Standings Component
 * EPL 리그 순위표
 */
const Standings = ({ darkMode = false, onTeamClick }) => {
  const [standings, setStandings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStandings();
  }, []);

  const fetchStandings = async () => {
    try {
      setLoading(true);
      const data = await eplAPI.getStandings();
      setStandings(data.standings || []);
      setError(null);
    } catch (err) {
      console.error('Error fetching standings:', err);
      setError('순위표를 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  const getPositionColor = (position) => {
    if (position <= 4) return 'bg-epl-ucl'; // Champions League
    if (position === 5) return 'bg-epl-uel'; // Europa League
    if (position >= 18) return 'bg-epl-relegation'; // Relegation
    return 'bg-white/20';
  };

  const getPositionStyle = (position) => {
    return '';
  };

  if (loading) {
    return (
      <div className="rounded-sm shadow-lg p-6 bg-slate-900/60 backdrop-blur-sm border border-cyan-500/20">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-white/10 rounded-sm w-1/3 mb-6"></div>
          {[...Array(20)].map((_, i) => (
            <div key={i} className="h-12 bg-white/5 rounded-sm"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-sm shadow-lg p-6 bg-slate-900/60 backdrop-blur-sm border border-cyan-500/20">
        <div className="text-center">
          <p className="text-error mb-4">{error}</p>
          <button onClick={fetchStandings} className="btn btn-primary">
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="relative rounded-sm shadow-lg overflow-hidden bg-gradient-to-br from-slate-900/80 via-blue-950/60 to-slate-900/80 backdrop-blur-sm border border-cyan-500/20">
      {/* Tech Grid Pattern */}
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
      <div className="relative px-6 py-1.5 border-b border-white/10">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold flex items-center gap-3">
            <div className="flex items-center justify-center">
              <img src="/premier-league-logo-white.svg" alt="Premier League" className="w-24 h-24 object-contain" />
            </div>
            <span className="text-brand-accent">Table</span>
          </h2>

          {/* Update Info */}
          <div className="flex items-center gap-2 text-xs">
            <RefreshCw className="w-3.5 h-3.5 text-brand-accent" />
            <span className="text-white/50 font-medium">UPDATED</span>
            <span className="text-white/70 font-semibold">
              {new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
            </span>
            <span className="text-white/40">•</span>
            <span className="text-white/70 font-mono">
              {new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })}
            </span>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="relative overflow-x-auto">
        <table className="w-full">
          <thead className="bg-white/5 sticky top-0">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-semibold text-white/80">순위</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-white/80">팀</th>
              <th className="px-4 py-3 text-center text-sm font-semibold text-white/80">경기</th>
              <th className="px-4 py-3 text-center text-sm font-semibold text-white/80">승</th>
              <th className="px-4 py-3 text-center text-sm font-semibold text-white/80">무</th>
              <th className="px-4 py-3 text-center text-sm font-semibold text-white/80">패</th>
              <th className="px-4 py-3 text-center text-sm font-semibold text-white/80">득점</th>
              <th className="px-4 py-3 text-center text-sm font-semibold text-white/80">실점</th>
              <th className="px-4 py-3 text-center text-sm font-semibold text-white/80">득실차</th>
              <th className="px-4 py-3 text-center text-sm font-semibold text-white/80">승점</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {standings.map((team) => (
              <tr
                key={team.id}
                className={`
                  group cursor-pointer transition-all duration-200
                  hover:bg-white/5
                  ${getPositionStyle(team.position)}
                `}
                onClick={() => onTeamClick && onTeamClick(team.name)}
                title={`${team.name} 선수 분석 보기`}
              >
                {/* 순위 */}
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div className={`w-1 h-8 ${getPositionColor(team.position)}`}></div>
                    <span className="font-bold text-white font-numeric">{team.position}</span>
                  </div>
                </td>
                
                {/* 팀명 */}
                <td className="px-4 py-3">
                  <span className="font-medium text-white group-hover:text-brand-accent transition-colors">
                    {team.name}
                  </span>
                </td>
                
                {/* 통계 */}
                <td className="px-4 py-3 text-center font-numeric text-white/70">{team.played}</td>
                <td className="px-4 py-3 text-center font-numeric text-white/70">{team.won}</td>
                <td className="px-4 py-3 text-center font-numeric text-white/70">{team.drawn}</td>
                <td className="px-4 py-3 text-center font-numeric text-white/70">{team.lost}</td>
                <td className="px-4 py-3 text-center font-numeric text-white/70">{team.goals_for}</td>
                <td className="px-4 py-3 text-center font-numeric text-white/70">{team.goals_against}</td>
                
                {/* 득실차 */}
                <td className="px-4 py-3 text-center">
                  <span
                    className={`
                      font-semibold font-numeric
                      ${team.goal_difference > 0 ? 'text-success' :
                        team.goal_difference < 0 ? 'text-error' :
                        'text-white/70'}
                    `}
                  >
                    {team.goal_difference > 0 ? '+' : ''}{team.goal_difference}
                  </span>
                </td>
                
                {/* 승점 */}
                <td className="px-4 py-3 text-center">
                  <span className="font-bold text-white font-numeric text-lg">
                    {team.points}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="p-4 border-t border-white/10 bg-white/5">
        <div className="flex flex-wrap gap-4 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-epl-ucl"></div>
            <span className="text-white/70">챔피언스리그</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-epl-uel"></div>
            <span className="text-white/70">유로파리그</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-epl-relegation"></div>
            <span className="text-white/70">강등권</span>
          </div>
        </div>
      </div>
    </div>
  );
};

Standings.propTypes = {
  darkMode: PropTypes.bool,
  onTeamClick: PropTypes.func
};

Standings.defaultProps = {
  darkMode: false,
  onTeamClick: null
};

export default Standings;
