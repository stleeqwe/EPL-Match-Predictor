import React from 'react';
import { TrendingUp, Brain, BarChart3 } from 'lucide-react';

function ModelContribution({ statsWeight = 75, personalWeight = 25, prediction, darkMode }) {
  const cardBg = darkMode ? 'bg-gray-800' : 'bg-white';
  const borderColor = darkMode ? 'border-gray-700' : 'border-gray-200';

  // Safety check for prediction
  if (!prediction) {
    return null;
  }

  // Calculate model contributions
  const statsContribution = {
    home_win: (prediction.home_win || 0) * (statsWeight / 100),
    draw: (prediction.draw || 0) * (statsWeight / 100),
    away_win: (prediction.away_win || 0) * (statsWeight / 100)
  };

  const personalContribution = {
    home_win: (prediction.home_win || 0) * (personalWeight / 100),
    draw: (prediction.draw || 0) * (personalWeight / 100),
    away_win: (prediction.away_win || 0) * (personalWeight / 100)
  };

  const formatPercent = (value) => {
    if (typeof value !== 'number' || isNaN(value)) return '0.0';
    return value.toFixed(1);
  };

  return (
    <div className={`${cardBg} border ${borderColor} rounded-lg p-6`}>
      <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-6">모델 기여도 분석</h2>

      {/* Weight Distribution Bar */}
      <div className="mb-6">
        <div className="flex h-12 rounded-lg overflow-hidden border border-gray-300 dark:border-gray-600">
          <div
            className="bg-blue-500 dark:bg-blue-600 flex items-center justify-center text-white font-semibold transition-all duration-300"
            style={{ width: `${statsWeight}%` }}
          >
            {statsWeight > 15 && (
              <span className="text-sm">Data 분석 {statsWeight}%</span>
            )}
          </div>
          <div
            className="bg-gray-400 dark:bg-gray-500 flex items-center justify-center text-white font-semibold transition-all duration-300"
            style={{ width: `${personalWeight}%` }}
          >
            {personalWeight > 15 && (
              <span className="text-sm">개인 분석 {personalWeight}%</span>
            )}
          </div>
        </div>
      </div>

      {/* Contribution Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Data Analysis Model */}
        <div className={`p-4 rounded-lg border ${borderColor} ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
          <div className="flex items-center gap-2 mb-3">
            <h3 className="font-semibold text-gray-900 dark:text-white">Data 분석 모델</h3>
            <span className="ml-auto text-xs font-semibold bg-blue-500 text-white px-2 py-1 rounded">
              {statsWeight}%
            </span>
          </div>
          <div className="space-y-3">
            <div className={`p-3 rounded ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm text-gray-600 dark:text-gray-400">홈 승리 기여도</span>
                <span className="font-bold text-blue-600">{formatPercent(statsContribution.home_win)}%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${prediction.home_win ? (statsContribution.home_win / prediction.home_win) * 100 : 0}%` }}
                />
              </div>
            </div>

            <div className={`p-3 rounded ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm text-gray-600 dark:text-gray-400">무승부 기여도</span>
                <span className="font-bold text-blue-600">{formatPercent(statsContribution.draw)}%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${prediction.draw ? (statsContribution.draw / prediction.draw) * 100 : 0}%` }}
                />
              </div>
            </div>

            <div className={`p-3 rounded ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm text-gray-600 dark:text-gray-400">원정 승리 기여도</span>
                <span className="font-bold text-blue-600">{formatPercent(statsContribution.away_win)}%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${prediction.away_win ? (statsContribution.away_win / prediction.away_win) * 100 : 0}%` }}
                />
              </div>
            </div>
          </div>
          <div className={`mt-3 p-3 rounded text-xs text-gray-600 dark:text-gray-400 ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
            Dixon-Coles & XGBoost 기반 통계 모델
          </div>
        </div>

        {/* Personal Analysis Model */}
        <div className={`p-4 rounded-lg border ${borderColor} ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
          <div className="flex items-center gap-2 mb-3">
            <h3 className="font-semibold text-gray-900 dark:text-white">개인 분석 모델</h3>
            <span className="ml-auto text-xs font-semibold bg-blue-500 text-white px-2 py-1 rounded">
              {personalWeight}%
            </span>
          </div>
          <div className="space-y-3">
            <div className={`p-3 rounded ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm text-gray-600 dark:text-gray-400">홈 승리 기여도</span>
                <span className="font-bold text-purple-600">{formatPercent(personalContribution.home_win)}%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="bg-purple-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${prediction.home_win ? (personalContribution.home_win / prediction.home_win) * 100 : 0}%` }}
                />
              </div>
            </div>

            <div className={`p-3 rounded ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm text-gray-600 dark:text-gray-400">무승부 기여도</span>
                <span className="font-bold text-purple-600">{formatPercent(personalContribution.draw)}%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="bg-purple-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${prediction.draw ? (personalContribution.draw / prediction.draw) * 100 : 0}%` }}
                />
              </div>
            </div>

            <div className={`p-3 rounded ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm text-gray-600 dark:text-gray-400">원정 승리 기여도</span>
                <span className="font-bold text-purple-600">{formatPercent(personalContribution.away_win)}%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="bg-purple-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${prediction.away_win ? (personalContribution.away_win / prediction.away_win) * 100 : 0}%` }}
                />
              </div>
            </div>
          </div>
          <div className={`mt-3 p-3 rounded text-xs text-gray-600 dark:text-gray-400 ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
            선수 개별 능력치 기반 분석
          </div>
        </div>
      </div>

      {/* Final Combined Result */}
      <div className={`mt-6 p-4 rounded-lg border ${borderColor} ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
        <h3 className="font-semibold mb-3 text-gray-900 dark:text-white">최종 하이브리드 예측</h3>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">홈 승리</div>
            <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {formatPercent(prediction.home_win)}%
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">무승부</div>
            <div className="text-2xl font-bold text-gray-600 dark:text-gray-400">
              {formatPercent(prediction.draw)}%
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">원정 승리</div>
            <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {formatPercent(prediction.away_win)}%
            </div>
          </div>
        </div>
        <div className="mt-3 text-xs text-center text-gray-600 dark:text-gray-400">
          Data 분석 {statsWeight}% + 개인 분석 {personalWeight}%
        </div>
      </div>
    </div>
  );
}

export default ModelContribution;
