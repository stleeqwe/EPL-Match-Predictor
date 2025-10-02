import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, ChevronRight, Search, Filter, X, ChevronDown } from 'lucide-react';

const MatchSelector = ({
  fixtures,
  selectedFixtureIndex,
  setSelectedFixtureIndex,
  darkMode,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showSearch, setShowSearch] = useState(false);
  const [filterGameweek, setFilterGameweek] = useState('all');
  const [showDropdown, setShowDropdown] = useState(false);
  const [viewMode, setViewMode] = useState('list'); // 'list' or 'carousel'

  const cardBg = darkMode ? 'bg-gray-800' : 'bg-white';
  const borderColor = darkMode ? 'border-gray-700' : 'border-gray-200';

  // 안전한 fixtures 배열 체크
  const safeFixtures = Array.isArray(fixtures) ? fixtures : [];

  // 디버깅
  console.log('MatchSelector Debug:', {
    totalFixtures: safeFixtures.length,
    filterGameweek,
    searchTerm,
    sampleFixture: safeFixtures[0]
  });

  // 필터링된 경기 목록
  const filteredFixtures = safeFixtures.filter(fixture => {
    if (!fixture) return false;

    const matchesSearch = searchTerm === '' ||
      fixture.home_team?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      fixture.away_team?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesGameweek = filterGameweek === 'all' ||
      fixture.gameweek?.toString() === filterGameweek;

    return matchesSearch && matchesGameweek;
  });

  console.log('Filtered fixtures:', filteredFixtures.length);

  // 고유한 게임위크 목록
  const gameweeks = [...new Set(safeFixtures.map(f => f.gameweek).filter(gw => gw != null))].sort((a, b) => a - b);
  console.log('Available gameweeks:', gameweeks);

  // 현재 주차 자동 선택 제거 - 기본값을 'all'로 유지
  // useEffect(() => {
  //   if (gameweeks.length > 0 && filterGameweek === 'all') {
  //     // 가장 최근 게임위크를 기본값으로
  //     const currentGW = gameweeks[0];
  //     setFilterGameweek(currentGW.toString());
  //   }
  // }, [gameweeks, filterGameweek]);

  const selectedFixture = filteredFixtures[selectedFixtureIndex] || fixtures[0] || {};
  const homeTeam = selectedFixture.home_team || 'Manchester City';
  const awayTeam = selectedFixture.away_team || 'Liverpool';

  const handlePrevious = () => {
    if (filteredFixtures.length === 0) return;
    setSelectedFixtureIndex((prev) =>
      prev === 0 ? filteredFixtures.length - 1 : prev - 1
    );
  };

  const handleNext = () => {
    if (filteredFixtures.length === 0) return;
    setSelectedFixtureIndex((prev) =>
      prev === filteredFixtures.length - 1 ? 0 : prev + 1
    );
  };

  const handleSearchChange = (value) => {
    setSearchTerm(value);
    setSelectedFixtureIndex(0); // 검색 시 첫 번째 결과로 이동
  };

  const handleGameweekChange = (value) => {
    setFilterGameweek(value);
    setSelectedFixtureIndex(0); // 필터 변경 시 첫 번째 결과로 이동
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className={`${cardBg} border ${borderColor} rounded-xl p-4 md:p-6 mb-6 shadow-lg`}
    >
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl md:text-2xl font-bold">경기 선택</h2>
        <div className="flex items-center gap-2">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setViewMode(viewMode === 'list' ? 'carousel' : 'list')}
            className={`px-3 py-2 rounded-lg border ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'} hover:bg-blue-50 dark:hover:bg-gray-700 transition-colors text-sm`}
          >
            {viewMode === 'list' ? '캐러셀' : '목록'} 보기
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setShowSearch(!showSearch)}
            className={`p-2 rounded-lg border ${showSearch ? 'bg-blue-500 text-white' : ''} hover:bg-blue-50 dark:hover:bg-gray-700 transition-colors`}
          >
            <Search className="w-5 h-5" />
          </motion.button>
          <select
            value={filterGameweek}
            onChange={(e) => handleGameweekChange(e.target.value)}
            className={`px-3 py-2 rounded-lg border ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}`}
          >
            <option value="all">전체 GW</option>
            {gameweeks.map(gw => (
              <option key={gw} value={gw}>GW {gw}</option>
            ))}
          </select>
        </div>
      </div>

      <AnimatePresence>
        {showSearch && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="mb-4 overflow-hidden"
          >
            <div className="relative">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => handleSearchChange(e.target.value)}
                placeholder="팀 이름으로 검색..."
                className={`w-full px-4 py-2 pl-10 pr-10 rounded-lg border ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}`}
              />
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 opacity-50" />
              {searchTerm && (
                <button
                  onClick={() => handleSearchChange('')}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2"
                >
                  <X className="w-5 h-5 opacity-50 hover:opacity-100" />
                </button>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {viewMode === 'list' ? (
        // 리스트 뷰 - 모든 경기를 그리드로 표시
        <div className="space-y-3">
          {filteredFixtures.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              선택 가능한 경기가 없습니다.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 max-h-96 overflow-y-auto pr-2">
              {filteredFixtures.map((fixture, index) => (
                <motion.div
                  key={index}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setSelectedFixtureIndex(index)}
                  className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                    index === selectedFixtureIndex
                      ? 'border-blue-500 bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-900/50 dark:to-purple-900/50 shadow-lg'
                      : `border-gray-300 dark:border-gray-600 ${darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-50'}`
                  }`}
                >
                  <div className="flex flex-col gap-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-xs px-2 py-1 rounded bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300">
                        GW {fixture.gameweek}
                      </span>
                      {fixture.date && (
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {fixture.date}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center justify-center gap-2">
                      <div className="text-sm font-semibold text-center flex-1">
                        {fixture.home_team}
                      </div>
                      <div className="text-xs font-bold text-gray-400">vs</div>
                      <div className="text-sm font-semibold text-center flex-1">
                        {fixture.away_team}
                      </div>
                    </div>
                    {fixture.Time && (
                      <div className="text-xs text-center text-gray-500 dark:text-gray-400">
                        {fixture.Time}
                      </div>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          )}
          <div className="text-center mt-4 text-sm text-gray-600 dark:text-gray-400">
            총 {filteredFixtures.length}개 경기
            {(searchTerm || filterGameweek !== 'all') && (
              <span className="ml-2 text-blue-500 dark:text-blue-400">
                (필터링됨)
              </span>
            )}
          </div>
        </div>
      ) : (
        // 캐러셀 뷰 - 기존 방식
        <div>
          <div className="flex items-center gap-4">
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={handlePrevious}
          className="p-3 rounded-lg border hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        >
          <ChevronLeft className="w-6 h-6" />
        </motion.button>

        <motion.div
          key={selectedFixtureIndex}
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.3 }}
          className="flex-1 p-4 md:p-6 rounded-xl border-2 bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-900/30 dark:to-purple-900/30"
        >
          <div className="flex flex-col md:flex-row items-center justify-center gap-4 md:gap-6">
            <motion.div
              whileHover={{ scale: 1.05 }}
              className="text-center"
            >
              <div className="text-xl md:text-2xl font-bold">{homeTeam}</div>
            </motion.div>
            <div className="text-2xl md:text-3xl font-bold text-gray-500">VS</div>
            <motion.div
              whileHover={{ scale: 1.05 }}
              className="text-center"
            >
              <div className="text-xl md:text-2xl font-bold">{awayTeam}</div>
            </motion.div>
          </div>
          {selectedFixture.date && (
            <div className="text-center mt-3 text-sm text-gray-600 dark:text-gray-400">
              {selectedFixture.date}
            </div>
          )}
        </motion.div>

        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={handleNext}
          className="p-3 rounded-lg border hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        >
          <ChevronRight className="w-6 h-6" />
        </motion.button>
      </div>

          {/* 경기 카운터 */}
          <div className="text-center mt-4 text-sm text-gray-600 dark:text-gray-400">
            {filteredFixtures.length > 0 ? selectedFixtureIndex + 1 : 0} / {filteredFixtures.length}
            {(searchTerm || filterGameweek !== 'all') && (
              <span className="ml-2 text-blue-500 dark:text-blue-400">
                (필터링됨)
              </span>
            )}
          </div>
        </div>
      )}
    </motion.div>
  );
};

export default MatchSelector;
