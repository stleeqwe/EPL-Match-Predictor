import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import axios from 'axios';
import { History, TrendingUp, Calendar, Filter } from 'lucide-react';

const API_BASE_URL = 'http://localhost:5001/api';

const PredictionHistory = ({ darkMode }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('all'); // 'all', 'correct', 'incorrect'
  const [limit, setLimit] = useState(10);

  const cardBg = darkMode ? 'bg-gray-800' : 'bg-white';
  const textColor = darkMode ? 'text-gray-100' : 'text-gray-900';

  useEffect(() => {
    fetchHistory();
  }, [limit]);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/predictions/history?limit=${limit}`);
      setHistory(response.data);
    } catch (error) {
      console.error('Error fetching history:', error);
      // 더미 데이터
      setHistory([
        {
          id: 1,
          home_team: 'Manchester City',
          away_team: 'Liverpool',
          predicted_home_win: 55.0,
          predicted_draw: 25.0,
          predicted_away_win: 20.0,
          actual_result: 'home_win',
          actual_score: '2-1',
          model_type: 'statistical',
          created_at: '2024-10-01 15:00',
          correct: true
        },
        {
          id: 2,
          home_team: 'Arsenal',
          away_team: 'Chelsea',
          predicted_home_win: 45.0,
          predicted_draw: 30.0,
          predicted_away_win: 25.0,
          actual_result: 'draw',
          actual_score: '2-2',
          model_type: 'hybrid',
          created_at: '2024-10-01 17:30',
          correct: false
        },
        {
          id: 3,
          home_team: 'Tottenham',
          away_team: 'Manchester United',
          predicted_home_win: 50.0,
          predicted_draw: 25.0,
          predicted_away_win: 25.0,
          actual_result: 'home_win',
          actual_score: '3-0',
          model_type: 'statistical',
          created_at: '2024-09-30 15:00',
          correct: true
        }
      ]);
    }
    setLoading(false);
  };

  const filteredHistory = history.filter(item => {
    if (filter === 'all') return true;
    if (filter === 'correct') return item.correct;
    if (filter === 'incorrect') return !item.correct;
    return true;
  });

  const getResultBadge = (result) => {
    const badges = {
      home_win: { text: '홈 승', color: 'bg-green-500' },
      draw: { text: '무승부', color: 'bg-yellow-500' },
      away_win: { text: '어웨이 승', color: 'bg-red-500' }
    };
    const badge = badges[result] || badges.home_win;
    return (
      <span className={`${badge.color} text-white text-xs px-2 py-1 rounded-full font-semibold`}>
        {badge.text}
      </span>
    );
  };

  const getModelBadge = (modelType) => {
    const colors = {
      statistical: 'bg-blue-500',
      personal: 'bg-purple-500',
      hybrid: 'bg-gradient-to-r from-blue-500 to-purple-500'
    };
    const labels = {
      statistical: '📊 Data',
      personal: '⚙️ 개인',
      hybrid: '🎯 하이브리드'
    };
    return (
      <span className={`${colors[modelType]} text-white text-xs px-2 py-1 rounded font-semibold`}>
        {labels[modelType]}
      </span>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className={`${cardBg} border rounded-xl p-6 shadow-lg`}
    >
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <History className="w-6 h-6 text-blue-500" />
          <h2 className="text-2xl font-bold">예측 히스토리</h2>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4" />
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className={`px-3 py-1 rounded border ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}`}
            >
              <option value="all">전체</option>
              <option value="correct">정확한 예측</option>
              <option value="incorrect">틀린 예측</option>
            </select>
          </div>
          <select
            value={limit}
            onChange={(e) => setLimit(parseInt(e.target.value))}
            className={`px-3 py-1 rounded border ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}`}
          >
            <option value="10">최근 10개</option>
            <option value="20">최근 20개</option>
            <option value="50">최근 50개</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500 dark:text-gray-400">로딩 중...</div>
        </div>
      ) : filteredHistory.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-gray-500 dark:text-gray-400">
          <History className="w-16 h-16 opacity-20 mb-4" />
          <p>예측 히스토리가 없습니다</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredHistory.map((item, index) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className={`p-4 rounded-lg border ${
                item.correct
                  ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
                  : 'border-red-500 bg-red-50 dark:bg-red-900/20'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 opacity-50" />
                    <span className="text-sm opacity-75">
                      {new Date(item.created_at).toLocaleString('ko-KR')}
                    </span>
                  </div>
                  {getModelBadge(item.model_type)}
                </div>
                <div className="flex items-center gap-2">
                  {item.correct ? (
                    <span className="text-green-600 dark:text-green-400 font-semibold">✓ 정확</span>
                  ) : (
                    <span className="text-red-600 dark:text-red-400 font-semibold">✗ 오답</span>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <div className="text-sm opacity-75 mb-1">경기</div>
                  <div className="font-bold">
                    {item.home_team} vs {item.away_team}
                  </div>
                  <div className="text-sm mt-1">
                    실제 결과: <strong>{item.actual_score}</strong> {getResultBadge(item.actual_result)}
                  </div>
                </div>

                <div className="md:col-span-2">
                  <div className="text-sm opacity-75 mb-2">예측 확률</div>
                  <div className="grid grid-cols-3 gap-2">
                    <div className="text-center p-2 bg-white dark:bg-gray-800 rounded">
                      <div className="text-xs opacity-75">홈 승</div>
                      <div className="text-lg font-bold text-green-600 dark:text-green-400">
                        {item.predicted_home_win?.toFixed(1)}%
                      </div>
                    </div>
                    <div className="text-center p-2 bg-white dark:bg-gray-800 rounded">
                      <div className="text-xs opacity-75">무승부</div>
                      <div className="text-lg font-bold text-yellow-600 dark:text-yellow-400">
                        {item.predicted_draw?.toFixed(1)}%
                      </div>
                    </div>
                    <div className="text-center p-2 bg-white dark:bg-gray-800 rounded">
                      <div className="text-xs opacity-75">어웨이 승</div>
                      <div className="text-lg font-bold text-red-600 dark:text-red-400">
                        {item.predicted_away_win?.toFixed(1)}%
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {filteredHistory.length > 0 && (
        <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-5 h-5 text-blue-500" />
            <span className="font-semibold">통계 요약</span>
          </div>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {filteredHistory.length}
              </div>
              <div className="text-sm opacity-75">총 예측</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                {filteredHistory.filter(h => h.correct).length}
              </div>
              <div className="text-sm opacity-75">정확</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                {filteredHistory.length > 0
                  ? ((filteredHistory.filter(h => h.correct).length / filteredHistory.length) * 100).toFixed(1)
                  : 0}%
              </div>
              <div className="text-sm opacity-75">정확도</div>
            </div>
          </div>
        </div>
      )}
    </motion.div>
  );
};

export default PredictionHistory;
