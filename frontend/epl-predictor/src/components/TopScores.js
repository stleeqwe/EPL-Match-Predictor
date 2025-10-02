import React from 'react';

function TopScores({ topScores, darkMode }) {
  const cardBg = darkMode ? 'bg-gray-800' : 'bg-white';
  const borderColor = darkMode ? 'border-gray-700' : 'border-gray-200';

  if (!topScores || !Array.isArray(topScores) || topScores.length === 0) {
    return null;
  }

  const formatProbability = (prob) => {
    if (typeof prob !== 'number' || isNaN(prob)) return '0.0';
    return prob.toFixed(1);
  };

  return (
    <div className={`${cardBg} border ${borderColor} rounded-lg p-6`}>
      <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4">가능성 높은 스코어</h2>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {topScores.slice(0, 5).map((scoreData, index) => {
          if (!scoreData || !scoreData.score) return null;

          return (
            <div
              key={`${scoreData.score}-${index}`}
              className={`border ${borderColor} rounded-lg p-3 text-center ${
                index === 0 ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-500' : darkMode ? 'bg-gray-700' : 'bg-gray-50'
              }`}
            >
              <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">#{index + 1}</div>
              <div className="text-xl font-bold text-gray-900 dark:text-white mb-1">{scoreData.score}</div>
              <div className="text-sm text-blue-600 dark:text-blue-400 font-medium">
                {formatProbability(scoreData.probability)}%
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default TopScores;
