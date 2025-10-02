import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import axios from 'axios';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';

const API_BASE_URL = 'http://localhost:5001/api';

const StatsChart = ({ prediction, homeTeam, awayTeam, darkMode }) => {
  const cardBg = darkMode ? 'bg-gray-800' : 'bg-white';
  const textColor = darkMode ? '#e5e7eb' : '#1f2937';
  const [homeStats, setHomeStats] = useState(null);
  const [awayStats, setAwayStats] = useState(null);

  // 팀 통계 가져오기
  useEffect(() => {
    const fetchTeamStats = async () => {
      try {
        const [homeResponse, awayResponse] = await Promise.all([
          axios.get(`${API_BASE_URL}/team-stats/${homeTeam}`),
          axios.get(`${API_BASE_URL}/team-stats/${awayTeam}`)
        ]);
        setHomeStats(homeResponse.data);
        setAwayStats(awayResponse.data);
      } catch (error) {
        console.error('Error fetching team stats:', error);
      }
    };

    if (homeTeam && awayTeam) {
      fetchTeamStats();
    }
  }, [homeTeam, awayTeam]);

  // 확률 데이터
  const probabilityData = [
    {
      name: '홈 승',
      probability: parseFloat(prediction.home_win?.toFixed(1) || 0),
    },
    {
      name: '무승부',
      probability: parseFloat(prediction.draw?.toFixed(1) || 0),
    },
    {
      name: '어웨이 승',
      probability: parseFloat(prediction.away_win?.toFixed(1) || 0),
    },
  ];

  // 레이더 차트 데이터 (실제 API 데이터 사용)
  const radarData = homeStats && awayStats ? [
    {
      category: '공격력 (xG)',
      [homeTeam]: Math.min(100, (homeStats.home_stats?.avg_xg || 0) * 40),
      [awayTeam]: Math.min(100, (awayStats.away_stats?.avg_xg || 0) * 40),
    },
    {
      category: '수비력',
      [homeTeam]: Math.max(0, 100 - (homeStats.home_stats?.avg_goals_against || 0) * 30),
      [awayTeam]: Math.max(0, 100 - (awayStats.away_stats?.avg_goals_against || 0) * 30),
    },
    {
      category: '최근 폼',
      [homeTeam]: (homeStats.recent_form?.win_rate || 0) * 100,
      [awayTeam]: (awayStats.recent_form?.win_rate || 0) * 100,
    },
    {
      category: '득점력',
      [homeTeam]: (homeStats.home_stats?.avg_goals_for || 0) * 30,
      [awayTeam]: (awayStats.away_stats?.avg_goals_for || 0) * 30,
    },
    {
      category: 'Pi-Rating',
      [homeTeam]: Math.max(0, (homeStats.pi_ratings?.home || 0) * 50 + 50),
      [awayTeam]: Math.max(0, (awayStats.pi_ratings?.away || 0) * 50 + 50),
    },
  ] : [];

  // 로딩 중이거나 데이터가 없으면 로딩 표시
  if (!homeStats || !awayStats) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.4 }}
        className={`${cardBg} border rounded-xl p-6 shadow-lg mb-6`}
      >
        <h3 className="text-xl font-bold mb-6">📈 통계 분석</h3>
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500 dark:text-gray-400">통계 데이터 로딩 중...</div>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.4 }}
      className={`${cardBg} border rounded-xl p-6 shadow-lg mb-6`}
    >
      <h3 className="text-xl font-bold mb-6">📈 통계 분석</h3>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 확률 바 차트 */}
        <div>
          <h4 className="text-lg font-semibold mb-4 text-center">승무패 확률</h4>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={probabilityData}>
              <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? '#374151' : '#e5e7eb'} />
              <XAxis dataKey="name" stroke={textColor} />
              <YAxis stroke={textColor} />
              <Tooltip
                contentStyle={{
                  backgroundColor: darkMode ? '#1f2937' : '#ffffff',
                  borderColor: darkMode ? '#374151' : '#e5e7eb',
                  color: textColor,
                }}
              />
              <Bar
                dataKey="probability"
                fill="url(#colorGradient)"
                radius={[8, 8, 0, 0]}
              />
              <defs>
                <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#3b82f6" />
                  <stop offset="100%" stopColor="#8b5cf6" />
                </linearGradient>
              </defs>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* 레이더 차트 */}
        <div>
          <h4 className="text-lg font-semibold mb-4 text-center">팀 능력 비교</h4>
          <ResponsiveContainer width="100%" height={250}>
            <RadarChart data={radarData}>
              <PolarGrid stroke={darkMode ? '#374151' : '#e5e7eb'} />
              <PolarAngleAxis
                dataKey="category"
                stroke={textColor}
                tick={{ fill: textColor, fontSize: 12 }}
              />
              <PolarRadiusAxis stroke={textColor} />
              <Radar
                name={homeTeam}
                dataKey={homeTeam}
                stroke="#3b82f6"
                fill="#3b82f6"
                fillOpacity={0.6}
              />
              <Radar
                name={awayTeam}
                dataKey={awayTeam}
                stroke="#ef4444"
                fill="#ef4444"
                fillOpacity={0.6}
              />
              <Legend />
              <Tooltip
                contentStyle={{
                  backgroundColor: darkMode ? '#1f2937' : '#ffffff',
                  borderColor: darkMode ? '#374151' : '#e5e7eb',
                  color: textColor,
                }}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </motion.div>
  );
};

export default StatsChart;
