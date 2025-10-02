import React from 'react';
import { motion } from 'framer-motion';
import ProbabilityBar from './ProbabilityBar';

const PredictionResult = ({ prediction, homeTeam, awayTeam, darkMode }) => {
  const cardBg = darkMode ? 'bg-gray-800' : 'bg-white';

  if (!prediction) {
    return null;
  }

  const formatValue = (value) => {
    if (typeof value !== 'number' || isNaN(value)) return '0.0';
    return value.toFixed(1);
  };

  return (
    <div className={`${cardBg} rounded-2xl p-6 md:p-8 shadow-xl border-2 ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
      {/* 헤더 */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-blue-500 rounded-lg">
            <span className="text-2xl">🎯</span>
          </div>
          <div>
            <h2 className="text-2xl font-bold text-blue-600 dark:text-blue-400">예측 결과</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">{homeTeam} vs {awayTeam}</p>
          </div>
        </div>

        {/* 예상 스코어 */}
        <div className="flex items-center justify-center gap-8 py-8 px-4 bg-gradient-to-r from-blue-50 via-purple-50 to-pink-50 dark:from-gray-700 dark:via-gray-700 dark:to-gray-700 rounded-xl">
          {/* 홈팀 득점 */}
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', bounce: 0.5, delay: 0.2 }}
            className="text-center"
          >
            <div className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">{homeTeam}</div>
            <div className="text-6xl md:text-7xl font-black text-blue-600 dark:text-blue-400">
              {formatValue(prediction.expected_home_goals)}
            </div>
          </motion.div>

          {/* 구분선 */}
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.4 }}
            className="text-4xl text-gray-400 dark:text-gray-600 font-bold"
          >
            :
          </motion.div>

          {/* 원정팀 득점 */}
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', bounce: 0.5, delay: 0.2 }}
            className="text-center"
          >
            <div className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">{awayTeam}</div>
            <div className="text-6xl md:text-7xl font-black text-red-600 dark:text-red-400">
              {formatValue(prediction.expected_away_goals)}
            </div>
          </motion.div>
        </div>
      </div>

      {/* 승률 바 */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
      >
        <ProbabilityBar
          label={`${homeTeam} 승리`}
          value={formatValue(prediction.home_win)}
          color="bg-gradient-to-r from-green-500 to-green-600"
          darkMode={darkMode}
        />
        <ProbabilityBar
          label="무승부"
          value={formatValue(prediction.draw)}
          color="bg-gradient-to-r from-yellow-500 to-yellow-600"
          darkMode={darkMode}
        />
        <ProbabilityBar
          label={`${awayTeam} 승리`}
          value={formatValue(prediction.away_win)}
          color="bg-gradient-to-r from-red-500 to-red-600"
          darkMode={darkMode}
        />
      </motion.div>
    </div>
  );
};

export default PredictionResult;
