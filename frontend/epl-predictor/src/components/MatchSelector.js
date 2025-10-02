import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, ChevronRight, Search, Filter, X } from 'lucide-react';

const MatchSelector = ({
  fixtures,
  selectedFixtureIndex,
  setSelectedFixtureIndex,
  darkMode,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showSearch, setShowSearch] = useState(false);
  const [filterGameweek, setFilterGameweek] = useState('all');

  const cardBg = darkMode ? 'bg-gray-800' : 'bg-white';
  const borderColor = darkMode ? 'border-gray-700' : 'border-gray-200';

  // 안전한 fixtures 배열 체크
  const safeFixtures = Array.isArray(fixtures) ? fixtures : [];

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

  // 고유한 게임위크 목록
  const gameweeks = [...new Set(safeFixtures.map(f => f.gameweek).filter(gw => gw != null))].sort((a, b) => a - b);

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
    </motion.div>
  );
};

export default MatchSelector;
