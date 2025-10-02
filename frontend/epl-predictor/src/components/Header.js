import React from 'react';
import { Moon, Sun, TrendingUp, Brain, Zap, Target } from 'lucide-react';

const Header = ({ darkMode, setDarkMode }) => {
  return (
    <div className="max-w-7xl mx-auto mb-8">
      <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-2xl p-6 shadow-lg border ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl">
              <TrendingUp className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-1">
                EPL Match Predictor
              </h1>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                프리미어리그 경기 예측 AI 시스템
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg border bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
                <Brain className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                <span className="text-xs font-medium text-blue-700 dark:text-blue-300">Dixon-Coles</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg border bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800">
                <Zap className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                <span className="text-xs font-medium text-purple-700 dark:text-purple-300">XGBoost</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg border bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800">
                <Target className="w-4 h-4 text-green-600 dark:text-green-400" />
                <span className="text-xs font-medium text-green-700 dark:text-green-300">Hybrid</span>
              </div>
            </div>

            <button
              onClick={() => setDarkMode(!darkMode)}
              className={`p-2.5 rounded-lg transition-colors ${
                darkMode
                  ? 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                  : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
              }`}
              aria-label="다크모드 토글"
            >
              {darkMode ? (
                <Sun className="w-5 h-5" />
              ) : (
                <Moon className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Header;
