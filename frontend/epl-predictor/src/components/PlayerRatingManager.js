import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Save, Star, ArrowLeft, Search, Download, Upload, Users } from 'lucide-react';

const API_BASE_URL = 'http://localhost:5001/api';

const POSITIONS = {
  'ST': '스트라이커',
  'W': '윙어',
  'AM': '공격형 미드필더',
  'DM': '수비형 미드필더',
  'MF': '미드필더',
  'CB': '센터백',
  'FB': '풀백',
  'DF': '수비수',
  'FW': '공격수',
  'GK': '골키퍼'
};

const ATTRIBUTES_BY_POSITION = {
  'ST': ['슈팅', '위치선정', '퍼스트터치', '스피드', '피지컬'],
  'W': ['드리블', '스피드', '크로스', '슈팅', '민첩성'],
  'AM': ['패스', '비전', '드리블', '슈팅', '창조력'],
  'DM': ['태클', '인터셉트', '패스', '체력', '포지셔닝'],
  'CB': ['태클', '마크', '헤더', '포지셔닝', '피지컬'],
  'FB': ['스피드', '크로스', '태클', '체력', '오버래핑'],
  'GK': ['반응속도', '포지셔닝', '핸들링', '발재간', '공중볼']
};

function PlayerRatingManager({ homeTeam, awayTeam, darkMode }) {
  const [allTeams, setAllTeams] = useState([]);
  const [selectedTeam, setSelectedTeam] = useState(homeTeam || '');
  const [players, setPlayers] = useState([]);
  const [selectedPlayer, setSelectedPlayer] = useState(null);
  const [showPlayerDetail, setShowPlayerDetail] = useState(false);
  const [ratings, setRatings] = useState({});
  const [searchQuery, setSearchQuery] = useState('');
  const [filterPosition, setFilterPosition] = useState('all');

  // 전체 팀 목록 가져오기
  useEffect(() => {
    fetchAllTeams();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 선택된 팀이 변경되면 선수 목록 가져오기
  useEffect(() => {
    if (selectedTeam) {
      fetchSquad();
      loadTeamRatings();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedTeam]);

  const fetchAllTeams = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/teams`);
      setAllTeams(response.data);
    } catch (error) {
      console.error('Error fetching teams:', error);
    }
  };

  const fetchSquad = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/squad/${selectedTeam}`);
      setPlayers(response.data);
    } catch (error) {
      console.error('Error fetching squad:', error);
    }
  };

  const loadTeamRatings = () => {
    const savedRatings = localStorage.getItem(`team_ratings_${selectedTeam}`);
    if (savedRatings) {
      setRatings(JSON.parse(savedRatings));
    } else {
      setRatings({});
    }
  };

  const saveTeamRatings = () => {
    localStorage.setItem(`team_ratings_${selectedTeam}`, JSON.stringify(ratings));
    alert('팀 전체 능력치가 저장되었습니다!');
  };

  const exportRatings = () => {
    const dataStr = JSON.stringify(ratings, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${selectedTeam}_ratings.json`;
    link.click();
  };

  const importRatings = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const imported = JSON.parse(e.target.result);
          setRatings(imported);
          alert('능력치를 불러왔습니다!');
        } catch (error) {
          alert('파일을 읽을 수 없습니다.');
        }
      };
      reader.readAsText(file);
    }
  };

  const handlePlayerSelect = (player) => {
    setSelectedPlayer(player);
    setShowPlayerDetail(true);
    // 기존 능력치 로드
    if (!ratings[player.id]) {
      const initialRatings = {};
      const attrs = ATTRIBUTES_BY_POSITION[player.position] || [];
      attrs.forEach(attr => {
        initialRatings[attr] = 0;
      });
      setRatings({
        ...ratings,
        [player.id]: initialRatings
      });
    }
  };

  const handleBackToSquad = () => {
    setShowPlayerDetail(false);
    setSelectedPlayer(null);
  };

  const getPlayerAverage = (playerId) => {
    if (!ratings[playerId]) return 0;
    const values = Object.values(ratings[playerId]);
    if (values.length === 0) return 0;
    const avg = values.reduce((sum, val) => sum + val, 0) / values.length;
    return avg;
  };

  const getTeamAverage = () => {
    if (players.length === 0) return 0;
    let totalAvg = 0;
    let count = 0;

    players.forEach(player => {
      const playerAvg = getPlayerAverage(player.id);
      totalAvg += playerAvg;
      count++;
    });

    return count > 0 ? (totalAvg / count) : 0;
  };

  const getPositionColor = (position) => {
    const colors = {
      'ST': 'bg-red-500',
      'W': 'bg-orange-500',
      'AM': 'bg-yellow-500',
      'DM': 'bg-green-500',
      'CB': 'bg-blue-500',
      'FB': 'bg-indigo-500',
      'GK': 'bg-purple-500'
    };
    return colors[position] || 'bg-gray-500';
  };

  const handleRatingChange = (attribute, value) => {
    setRatings(prev => ({
      ...prev,
      [selectedPlayer.id]: {
        ...(prev[selectedPlayer.id] || {}),
        [attribute]: parseFloat(value)
      }
    }));
  };

  const saveRatings = async () => {
    try {
      await axios.post(`${API_BASE_URL}/player-ratings`, {
        player_id: selectedPlayer.id,
        ratings: ratings[selectedPlayer.id]
      });
      alert('능력치가 저장되었습니다!');
    } catch (error) {
      console.error('Error saving ratings:', error);
    }
  };

  const cardBg = darkMode ? 'bg-gray-800' : 'bg-white';
  const textColor = darkMode ? 'text-gray-100' : 'text-gray-900';
  const borderColor = darkMode ? 'border-gray-700' : 'border-gray-200';

  // 선수 필터링
  const filteredPlayers = players.filter(player => {
    const matchesSearch = player.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         player.number.toString().includes(searchQuery);
    const matchesPosition = filterPosition === 'all' || player.position === filterPosition;
    return matchesSearch && matchesPosition;
  });

  // Detail View - Full screen player editor
  if (showPlayerDetail && selectedPlayer) {
    const playerRatings = ratings[selectedPlayer.id] || {};
    const playerAvg = getPlayerAverage(selectedPlayer.id);

    return (
      <div className={`${cardBg} ${textColor} rounded-xl p-6 shadow-lg`}>
        {/* Back Button */}
        <button
          onClick={handleBackToSquad}
          className="flex items-center gap-2 mb-6 px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          팀 목록으로 돌아가기
        </button>

        {/* Player Header */}
        <div className="flex items-center justify-between mb-8 pb-6 border-b border-gray-300 dark:border-gray-700">
          <div className="flex items-center gap-4">
            <div className="text-5xl">{selectedPlayer.nationality}</div>
            <div>
              <h2 className="text-3xl font-bold">{selectedPlayer.name}</h2>
              <div className="flex items-center gap-3 mt-2">
                <span className={`${getPositionColor(selectedPlayer.position)} text-white px-3 py-1 rounded-full text-sm font-semibold`}>
                  {POSITIONS[selectedPlayer.position] || selectedPlayer.position}
                </span>
                <span className="text-gray-500">#{selectedPlayer.number}</span>
                <span className="text-gray-500">{selectedPlayer.age}세</span>
              </div>
            </div>
          </div>
          <button
            onClick={saveRatings}
            className="flex items-center gap-2 px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors font-semibold"
          >
            <Save className="w-5 h-5" />
            저장
          </button>
        </div>

        {/* Attribute Sliders */}
        <div className="space-y-6 mb-8">
          {ATTRIBUTES_BY_POSITION[selectedPlayer.position]?.map(attribute => (
            <div key={attribute} className="space-y-2">
              <div className="flex justify-between items-center">
                <label className="font-semibold text-lg">{attribute}</label>
                <span className="text-2xl font-bold">
                  {playerRatings[attribute] > 0 ? `+${playerRatings[attribute].toFixed(1)}` : playerRatings[attribute]?.toFixed(1) || '0.0'}
                </span>
              </div>
              <input
                type="range"
                min="-5"
                max="5"
                step="0.5"
                value={playerRatings[attribute] || 0}
                onChange={(e) => handleRatingChange(attribute, e.target.value)}
                className="w-full h-4 rounded-lg appearance-none cursor-pointer"
                style={{
                  background: `linear-gradient(to right,
                    #ef4444 0%,
                    #f59e0b 25%,
                    #84cc16 50%,
                    #10b981 75%,
                    #3b82f6 100%)`
                }}
              />
              <div className="flex justify-between text-sm opacity-60">
                <span>-5.0</span>
                <span>0.0</span>
                <span>+5.0</span>
              </div>
            </div>
          ))}
        </div>

        {/* Average Rating Display */}
        <div className="p-6 bg-gradient-to-r from-blue-500/10 to-purple-500/10 dark:from-blue-900/30 dark:to-purple-900/30 rounded-xl border-2 border-blue-500/30">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Star className="w-8 h-8 text-blue-500" />
              <span className="text-xl font-semibold">선수 평균 능력치</span>
            </div>
            <div className="text-5xl font-bold text-blue-600 dark:text-blue-400">
              {playerAvg > 0 ? `+${playerAvg.toFixed(2)}` : playerAvg.toFixed(2)}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // List View - Team power + Player cards
  return (
    <div className="space-y-6">
      {/* Team Selector & Controls */}
      <div className={`${cardBg} border ${borderColor} rounded-xl p-6 shadow-lg`}>
        <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
          <div className="flex-1">
            <label className="block text-sm font-semibold mb-2">팀 선택</label>
            <select
              value={selectedTeam}
              onChange={(e) => setSelectedTeam(e.target.value)}
              className={`w-full px-4 py-3 rounded-lg border ${borderColor} ${cardBg} ${textColor} font-semibold text-lg`}
            >
              <option value="">팀을 선택하세요</option>
              {allTeams.map(team => (
                <option key={team} value={team}>{team}</option>
              ))}
            </select>
          </div>

          {/* Control Buttons */}
          <div className="flex gap-2">
            <button
              onClick={saveTeamRatings}
              className="flex items-center gap-2 px-4 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors font-semibold"
              disabled={!selectedTeam}
            >
              <Save className="w-5 h-5" />
              저장
            </button>
            <button
              onClick={exportRatings}
              className="flex items-center gap-2 px-4 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors font-semibold"
              disabled={!selectedTeam}
            >
              <Download className="w-5 h-5" />
              내보내기
            </button>
            <label className="flex items-center gap-2 px-4 py-3 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors font-semibold cursor-pointer">
              <Upload className="w-5 h-5" />
              가져오기
              <input type="file" accept=".json" onChange={importRatings} className="hidden" />
            </label>
          </div>
        </div>
      </div>

      {selectedTeam && (
        <>
          {/* Team Power Card */}
          <div className={`${cardBg} border-2 ${borderColor} rounded-xl p-6 shadow-lg`}>
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-bold mb-2">{selectedTeam} 팀 전체 전력</h3>
                <p className="text-sm opacity-60">전체 선수 평균 능력치</p>
              </div>
              <div className="text-right">
                <div className="text-5xl font-bold text-blue-600 dark:text-blue-400">
                  {getTeamAverage() > 0 ? `+${getTeamAverage().toFixed(2)}` : getTeamAverage().toFixed(2)}
                </div>
                <div className="text-sm opacity-60 mt-1">{players.length}명</div>
              </div>
            </div>
          </div>

          {/* Search & Filter */}
          <div className={`${cardBg} border ${borderColor} rounded-xl p-4 shadow-lg`}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="선수 이름 또는 등번호 검색..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className={`w-full pl-10 pr-4 py-3 rounded-lg border ${borderColor} ${cardBg} ${textColor}`}
                />
              </div>

              {/* Position Filter */}
              <select
                value={filterPosition}
                onChange={(e) => setFilterPosition(e.target.value)}
                className={`px-4 py-3 rounded-lg border ${borderColor} ${cardBg} ${textColor} font-semibold`}
              >
                <option value="all">모든 포지션</option>
                <option value="GK">골키퍼 (GK)</option>
                <option value="CB">센터백 (CB)</option>
                <option value="FB">풀백 (FB)</option>
                <option value="DM">수비형 미드필더 (DM)</option>
                <option value="AM">공격형 미드필더 (AM)</option>
                <option value="W">윙어 (W)</option>
                <option value="ST">스트라이커 (ST)</option>
              </select>
            </div>
            <div className="mt-3 text-sm opacity-60">
              {filteredPlayers.length}명의 선수 표시 중
            </div>
          </div>

          {/* Player Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredPlayers.map(player => {
          const playerAvg = getPlayerAverage(player.id);
          return (
            <button
              key={player.id}
              onClick={() => handlePlayerSelect(player)}
              className={`${cardBg} border ${borderColor} rounded-xl p-5 text-left transition-all hover:shadow-lg hover:scale-105 hover:border-blue-500`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="text-3xl">{player.nationality}</div>
                  <div>
                    <div className="font-bold text-lg">{player.name}</div>
                    <div className="text-sm opacity-60">#{player.number} · {player.age}세</div>
                  </div>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className={`${getPositionColor(player.position)} text-white px-3 py-1 rounded-full text-xs font-semibold`}>
                  {POSITIONS[player.position] || player.position}
                </span>
                <div className="text-right">
                  <div className="text-xs opacity-60">평균 능력치</div>
                  <div className="text-xl font-bold text-blue-600 dark:text-blue-400">
                    {playerAvg > 0 ? `+${playerAvg.toFixed(1)}` : playerAvg.toFixed(1)}
                  </div>
                </div>
              </div>
            </button>
          );
        })}
          </div>
        </>
      )}

      {!selectedTeam && (
        <div className={`${cardBg} border ${borderColor} rounded-xl p-12 text-center`}>
          <Users className="w-16 h-16 mx-auto mb-4 opacity-40" />
          <p className="text-xl font-semibold opacity-60">팀을 선택하여 선수 능력치를 관리하세요</p>
        </div>
      )}
    </div>
  );
}

export default PlayerRatingManager;
