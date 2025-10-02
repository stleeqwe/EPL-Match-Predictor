import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import axios from 'axios';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { Target, TrendingUp, Award, Calendar } from 'lucide-react';

const API_BASE_URL = 'http://localhost:5001/api';

const AccuracyDashboard = ({ darkMode }) => {
  const [accuracy, setAccuracy] = useState(null);
  const [loading, setLoading] = useState(false);
  const [timeRange, setTimeRange] = useState(30); // days

  const cardBg = darkMode ? 'bg-gray-800' : 'bg-white';
  const textColor = darkMode ? '#e5e7eb' : '#1f2937';

  useEffect(() => {
    fetchAccuracy();
  }, [timeRange]);

  const fetchAccuracy = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/predictions/accuracy?days=${timeRange}`);
      setAccuracy(response.data);
    } catch (error) {
      console.error('Error fetching accuracy:', error);
      // 더미 데이터
      setAccuracy({
        overall_accuracy: 68.5,
        total_predictions: 47,
        correct_predictions: 32,
        by_model: [
          { model: 'statistical', accuracy: 71.2, count: 25 },
          { model: 'personal', accuracy: 58.3, count: 12 },
          { model: 'hybrid', accuracy: 75.0, count: 10 }
        ],
        by_outcome: [
          { outcome: 'home_win', predicted: 18, correct: 14, accuracy: 77.8 },
          { outcome: 'draw', predicted: 12, correct: 6, accuracy: 50.0 },
          { outcome: 'away_win', predicted: 17, correct: 12, accuracy: 70.6 }
        ],
        daily_accuracy: [
          { date: '2024-09-25', accuracy: 66.7, predictions: 3 },
          { date: '2024-09-26', accuracy: 75.0, predictions: 4 },
          { date: '2024-09-27', accuracy: 60.0, predictions: 5 },
          { date: '2024-09-28', accuracy: 71.4, predictions: 7 },
          { date: '2024-09-29', accuracy: 80.0, predictions: 5 },
          { date: '2024-09-30', accuracy: 66.7, predictions: 6 },
          { date: '2024-10-01', accuracy: 70.0, predictions: 10 }
        ]
      });
    }
    setLoading(false);
  };

  if (loading || !accuracy) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className={`${cardBg} border rounded-xl p-6 shadow-lg`}
      >
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500 dark:text-gray-400">정확도 데이터 로딩 중...</div>
        </div>
      </motion.div>
    );
  }

  const COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b'];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className={`${cardBg} border rounded-xl p-6 shadow-lg`}
    >
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Target className="w-6 h-6 text-blue-500" />
          <h2 className="text-2xl font-bold">예측 정확도 대시보드</h2>
        </div>
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4" />
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(parseInt(e.target.value))}
            className={`px-3 py-1 rounded border ${darkMode ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}`}
          >
            <option value="7">최근 7일</option>
            <option value="30">최근 30일</option>
            <option value="90">최근 90일</option>
            <option value="365">1년</option>
          </select>
        </div>
      </div>

      {/* 전체 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="p-6 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl text-white"
        >
          <div className="flex items-center gap-3 mb-2">
            <Target className="w-8 h-8" />
            <div className="text-sm opacity-90">전체 정확도</div>
          </div>
          <div className="text-4xl font-bold">{accuracy.overall_accuracy?.toFixed(1)}%</div>
          <div className="text-sm opacity-75 mt-2">
            {accuracy.correct_predictions}/{accuracy.total_predictions} 예측
          </div>
        </motion.div>

        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="p-6 bg-gradient-to-br from-green-500 to-green-600 rounded-xl text-white"
        >
          <div className="flex items-center gap-3 mb-2">
            <Award className="w-8 h-8" />
            <div className="text-sm opacity-90">최고 모델</div>
          </div>
          <div className="text-2xl font-bold">
            {accuracy.by_model?.reduce((best, model) =>
              model.accuracy > (best?.accuracy || 0) ? model : best
            , {})?.model || 'N/A'}
          </div>
          <div className="text-sm opacity-75 mt-2">
            {accuracy.by_model?.reduce((best, model) =>
              model.accuracy > (best?.accuracy || 0) ? model : best
            , {})?.accuracy?.toFixed(1) || 0}% 정확도
          </div>
        </motion.div>

        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="p-6 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl text-white"
        >
          <div className="flex items-center gap-3 mb-2">
            <TrendingUp className="w-8 h-8" />
            <div className="text-sm opacity-90">추세</div>
          </div>
          <div className="text-2xl font-bold">
            {accuracy.daily_accuracy && accuracy.daily_accuracy.length >= 2 ? (
              accuracy.daily_accuracy[accuracy.daily_accuracy.length - 1].accuracy >
              accuracy.daily_accuracy[accuracy.daily_accuracy.length - 2].accuracy ? (
                <span className="text-green-300">↑ 상승</span>
              ) : (
                <span className="text-red-300">↓ 하락</span>
              )
            ) : (
              'N/A'
            )}
          </div>
          <div className="text-sm opacity-75 mt-2">최근 추세</div>
        </motion.div>
      </div>

      {/* 차트 그리드 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 일별 정확도 추이 */}
        <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
          <h3 className="text-lg font-semibold mb-4">일별 정확도 추이</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={accuracy.daily_accuracy}>
              <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? '#374151' : '#e5e7eb'} />
              <XAxis
                dataKey="date"
                stroke={textColor}
                tickFormatter={(date) => new Date(date).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })}
              />
              <YAxis stroke={textColor} domain={[0, 100]} />
              <Tooltip
                contentStyle={{
                  backgroundColor: darkMode ? '#1f2937' : '#ffffff',
                  borderColor: darkMode ? '#374151' : '#e5e7eb',
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="accuracy"
                stroke="#3b82f6"
                strokeWidth={3}
                dot={{ fill: '#3b82f6', r: 5 }}
                name="정확도 (%)"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* 모델별 정확도 */}
        <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
          <h3 className="text-lg font-semibold mb-4">모델별 성능</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={accuracy.by_model}>
              <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? '#374151' : '#e5e7eb'} />
              <XAxis
                dataKey="model"
                stroke={textColor}
                tickFormatter={(model) => {
                  const labels = { statistical: 'Data', personal: '개인', hybrid: '하이브리드' };
                  return labels[model] || model;
                }}
              />
              <YAxis stroke={textColor} domain={[0, 100]} />
              <Tooltip
                contentStyle={{
                  backgroundColor: darkMode ? '#1f2937' : '#ffffff',
                  borderColor: darkMode ? '#374151' : '#e5e7eb',
                }}
              />
              <Legend />
              <Bar dataKey="accuracy" fill="#8b5cf6" name="정확도 (%)" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* 결과별 정확도 */}
        <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
          <h3 className="text-lg font-semibold mb-4">결과 유형별 정확도</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={accuracy.by_outcome}
                dataKey="accuracy"
                nameKey="outcome"
                cx="50%"
                cy="50%"
                outerRadius={80}
                label={(entry) => `${entry.outcome}: ${entry.accuracy.toFixed(1)}%`}
              >
                {accuracy.by_outcome?.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: darkMode ? '#1f2937' : '#ffffff',
                  borderColor: darkMode ? '#374151' : '#e5e7eb',
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* 상세 통계 테이블 */}
        <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
          <h3 className="text-lg font-semibold mb-4">상세 통계</h3>
          <div className="space-y-3">
            {accuracy.by_outcome?.map((outcome, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-lg">
                <div>
                  <div className="font-semibold">
                    {outcome.outcome === 'home_win' ? '홈 승' :
                     outcome.outcome === 'draw' ? '무승부' : '어웨이 승'}
                  </div>
                  <div className="text-sm opacity-75">
                    {outcome.correct}/{outcome.predicted} 예측
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold" style={{ color: COLORS[index] }}>
                    {outcome.accuracy?.toFixed(1)}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default AccuracyDashboard;
