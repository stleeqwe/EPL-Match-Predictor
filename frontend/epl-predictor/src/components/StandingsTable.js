import React, { useState, useEffect } from 'react';
import axios from 'axios';
import LoadingSkeleton from './LoadingSkeleton';

const API_BASE_URL = 'http://localhost:5001/api';

function StandingsTable({ darkMode }) {
  const [standings, setStandings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortConfig, setSortConfig] = useState({ key: 'rank', direction: 'asc' });

  useEffect(() => {
    fetchStandings();
  }, []);

  const fetchStandings = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE_URL}/standings`);
      setStandings(response.data);
    } catch (error) {
      console.error('Error fetching standings:', error);
      setError('순위표를 불러올 수 없습니다.');
    }
    setLoading(false);
  };

  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const sortedStandings = React.useMemo(() => {
    const sorted = [...standings];
    sorted.sort((a, b) => {
      const aVal = a[sortConfig.key];
      const bVal = b[sortConfig.key];

      if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
    return sorted;
  }, [standings, sortConfig]);

  const getRowColor = (rank) => {
    if (rank <= 4) {
      // Champions League (Top 4) - Blue
      return darkMode
        ? 'bg-blue-900/30 border-l-4 border-blue-500'
        : 'bg-blue-50 border-l-4 border-blue-500';
    } else if (rank >= 18) {
      // Relegation Zone (Bottom 3) - Red
      return darkMode
        ? 'bg-red-900/30 border-l-4 border-red-500'
        : 'bg-red-50 border-l-4 border-red-500';
    }
    return '';
  };

  const cardBg = darkMode ? 'bg-gray-800' : 'bg-white';
  const borderColor = darkMode ? 'border-gray-700' : 'border-gray-200';
  const textColor = darkMode ? 'text-gray-100' : 'text-gray-900';
  const headerBg = darkMode ? 'bg-gray-700' : 'bg-gray-100';
  const hoverBg = darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-50';

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto">
        <LoadingSkeleton />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto">
        <div className={`${cardBg} border ${borderColor} rounded-2xl p-8 shadow-lg text-center`}>
          <p className="text-red-500 text-lg">{error}</p>
          <button
            onClick={fetchStandings}
            className="mt-4 px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  const SortIcon = ({ columnKey }) => {
    if (sortConfig.key !== columnKey) return null;
    return sortConfig.direction === 'asc' ? '↑' : '↓';
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className={`${cardBg} border ${borderColor} rounded-2xl shadow-lg overflow-hidden`}>
        {/* Header */}
        <div className={`${headerBg} px-6 py-4 border-b ${borderColor}`}>
          <div className="flex items-center justify-between">
            <h2 className={`text-2xl font-bold ${textColor}`}>
              📊 프리미어리그 순위표
            </h2>
            <button
              onClick={fetchStandings}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm"
            >
              🔄 새로고침
            </button>
          </div>
          <p className={`text-sm mt-2 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            2024-2025 시즌 • 최종 업데이트: {standings[0]?.updated_at ? new Date(standings[0].updated_at).toLocaleString('ko-KR') : 'N/A'}
          </p>
        </div>

        {/* Legend */}
        <div className={`px-6 py-3 border-b ${borderColor} flex gap-6 text-sm`}>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-blue-500 rounded"></div>
            <span className={darkMode ? 'text-gray-300' : 'text-gray-600'}>
              챔피언스리그 (1-4위)
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-red-500 rounded"></div>
            <span className={darkMode ? 'text-gray-300' : 'text-gray-600'}>
              강등권 (18-20위)
            </span>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className={`${headerBg} text-sm ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              <tr>
                <th
                  className={`px-4 py-3 text-center cursor-pointer ${hoverBg}`}
                  onClick={() => handleSort('rank')}
                >
                  순위 <SortIcon columnKey="rank" />
                </th>
                <th
                  className={`px-4 py-3 text-left cursor-pointer ${hoverBg}`}
                  onClick={() => handleSort('team')}
                >
                  팀 <SortIcon columnKey="team" />
                </th>
                <th
                  className={`px-4 py-3 text-center cursor-pointer ${hoverBg}`}
                  onClick={() => handleSort('matches_played')}
                  title="경기수"
                >
                  경기 <SortIcon columnKey="matches_played" />
                </th>
                <th
                  className={`px-4 py-3 text-center cursor-pointer ${hoverBg}`}
                  onClick={() => handleSort('wins')}
                  title="승"
                >
                  승 <SortIcon columnKey="wins" />
                </th>
                <th
                  className={`px-4 py-3 text-center cursor-pointer ${hoverBg}`}
                  onClick={() => handleSort('draws')}
                  title="무"
                >
                  무 <SortIcon columnKey="draws" />
                </th>
                <th
                  className={`px-4 py-3 text-center cursor-pointer ${hoverBg}`}
                  onClick={() => handleSort('losses')}
                  title="패"
                >
                  패 <SortIcon columnKey="losses" />
                </th>
                <th
                  className={`px-4 py-3 text-center cursor-pointer ${hoverBg}`}
                  onClick={() => handleSort('goals_for')}
                  title="득점"
                >
                  득점 <SortIcon columnKey="goals_for" />
                </th>
                <th
                  className={`px-4 py-3 text-center cursor-pointer ${hoverBg}`}
                  onClick={() => handleSort('goals_against')}
                  title="실점"
                >
                  실점 <SortIcon columnKey="goals_against" />
                </th>
                <th
                  className={`px-4 py-3 text-center cursor-pointer ${hoverBg}`}
                  onClick={() => handleSort('goal_difference')}
                  title="득실차"
                >
                  득실차 <SortIcon columnKey="goal_difference" />
                </th>
                <th
                  className={`px-4 py-3 text-center cursor-pointer ${hoverBg} font-bold`}
                  onClick={() => handleSort('points')}
                  title="승점"
                >
                  승점 <SortIcon columnKey="points" />
                </th>
              </tr>
            </thead>
            <tbody className={`${textColor}`}>
              {sortedStandings.map((team, index) => (
                <tr
                  key={team.team + index}
                  className={`
                    border-b ${borderColor} transition-colors
                    ${getRowColor(team.rank)}
                    ${!getRowColor(team.rank) ? hoverBg : ''}
                  `}
                >
                  <td className="px-4 py-4 text-center font-semibold">
                    {team.rank}
                  </td>
                  <td className="px-4 py-4 font-medium">
                    {team.team}
                  </td>
                  <td className="px-4 py-4 text-center">
                    {team.matches_played}
                  </td>
                  <td className="px-4 py-4 text-center text-green-600 dark:text-green-400">
                    {team.wins}
                  </td>
                  <td className="px-4 py-4 text-center text-gray-500">
                    {team.draws}
                  </td>
                  <td className="px-4 py-4 text-center text-red-600 dark:text-red-400">
                    {team.losses}
                  </td>
                  <td className="px-4 py-4 text-center">
                    {team.goals_for}
                  </td>
                  <td className="px-4 py-4 text-center">
                    {team.goals_against}
                  </td>
                  <td className={`px-4 py-4 text-center font-medium ${
                    team.goal_difference > 0
                      ? 'text-green-600 dark:text-green-400'
                      : team.goal_difference < 0
                      ? 'text-red-600 dark:text-red-400'
                      : 'text-gray-500'
                  }`}>
                    {team.goal_difference > 0 ? '+' : ''}{team.goal_difference}
                  </td>
                  <td className="px-4 py-4 text-center font-bold text-lg">
                    {team.points}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Footer */}
        <div className={`px-6 py-4 border-t ${borderColor} text-center text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
          총 {standings.length}개 팀 • 데이터 출처: FBref
        </div>
      </div>
    </div>
  );
}

export default StandingsTable;
