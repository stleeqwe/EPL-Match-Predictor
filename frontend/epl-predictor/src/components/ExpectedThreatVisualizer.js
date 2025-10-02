/**
 * Expected Threat (xT) 시각화 컴포넌트
 * 12x8 그리드 기반 위협도 히트맵 표시
 */

import React, { useState } from 'react';
import { advancedAPI } from '../services/api';

const ExpectedThreatVisualizer = () => {
  const [homeTeam, setHomeTeam] = useState('');
  const [awayTeam, setAwayTeam] = useState('');
  const [season, setSeason] = useState('2024-2025');
  const [loading, setLoading] = useState(false);
  const [xtData, setXtData] = useState(null);
  const [error, setError] = useState(null);

  // xT 값에 따른 색상 반환 (0-1 범위)
  const getColorFromXT = (value) => {
    if (!value) return 'rgb(229, 231, 235)'; // gray-200

    // 0 (파란색) → 1 (빨간색) 그라디언트
    const red = Math.round(value * 255);
    const blue = Math.round((1 - value) * 255);
    const green = Math.round(50); // 약간의 녹색 추가

    return `rgb(${red}, ${green}, ${blue})`;
  };

  const handleCalculate = async () => {
    if (!homeTeam || !awayTeam) {
      setError('홈팀과 원정팀을 모두 선택해주세요.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await advancedAPI.expectedThreat({
        home_team: homeTeam,
        away_team: awayTeam,
        season: season
      });

      setXtData(result);
    } catch (err) {
      setError(err.response?.data?.error || '계산 중 오류가 발생했습니다.');
      console.error('xT calculation error:', err);
    } finally {
      setLoading(false);
    }
  };

  // xT 매트릭스 렌더링 (12x8)
  const renderXTMatrix = (matrix, title) => {
    if (!matrix || !Array.isArray(matrix)) return null;

    return (
      <div className="mt-6">
        <h3 className="text-lg font-semibold mb-3">{title}</h3>
        <div className="grid grid-cols-12 gap-0.5 bg-gray-300 p-1 rounded">
          {matrix.map((row, rowIdx) =>
            row.map((value, colIdx) => (
              <div
                key={`${rowIdx}-${colIdx}`}
                className="aspect-square flex items-center justify-center text-xs font-mono"
                style={{
                  backgroundColor: getColorFromXT(value),
                  color: value > 0.5 ? 'white' : 'black'
                }}
                title={`(${colIdx}, ${rowIdx}): ${value?.toFixed(3) || 0}`}
              >
                {value?.toFixed(2) || '0'}
              </div>
            ))
          )}
        </div>
        <div className="flex justify-between mt-2 text-sm text-gray-600">
          <span>← 수비 진영</span>
          <span>공격 진영 →</span>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-4">Expected Threat (xT) 분석</h2>

      <div className="mb-6 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <input
            type="text"
            placeholder="홈팀 (예: Manchester City)"
            value={homeTeam}
            onChange={(e) => setHomeTeam(e.target.value)}
            className="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
          />
          <input
            type="text"
            placeholder="원정팀 (예: Arsenal)"
            value={awayTeam}
            onChange={(e) => setAwayTeam(e.target.value)}
            className="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
          />
          <select
            value={season}
            onChange={(e) => setSeason(e.target.value)}
            className="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="2024-2025">2024-2025</option>
            <option value="2025-2026">2025-2026</option>
          </select>
        </div>

        <button
          onClick={handleCalculate}
          disabled={loading}
          className={`w-full md:w-auto px-6 py-2 rounded-lg font-semibold transition-colors ${
            loading
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 text-white'
          }`}
        >
          {loading ? '계산 중...' : 'xT 계산'}
        </button>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {xtData && (
        <div className="space-y-8">
          {/* 경기 요약 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
            <div className="text-center">
              <div className="text-sm text-gray-600">홈팀 평균 xT</div>
              <div className="text-2xl font-bold text-blue-600">
                {xtData.home_avg_xt?.toFixed(3) || 'N/A'}
              </div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-600">원정팀 평균 xT</div>
              <div className="text-2xl font-bold text-red-600">
                {xtData.away_avg_xt?.toFixed(3) || 'N/A'}
              </div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-600">xT 차이</div>
              <div className="text-2xl font-bold text-green-600">
                {xtData.xt_difference?.toFixed(3) || 'N/A'}
              </div>
            </div>
          </div>

          {/* xT 매트릭스 */}
          {xtData.xt_matrix && renderXTMatrix(xtData.xt_matrix, 'Expected Threat 매트릭스')}

          {/* 설명 */}
          <div className="bg-blue-50 p-4 rounded-lg">
            <h4 className="font-semibold mb-2">📊 Expected Threat (xT)란?</h4>
            <p className="text-sm text-gray-700">
              Expected Threat는 필드의 각 위치에서 공을 소유했을 때 골로 이어질 확률을 나타냅니다.
              값이 높을수록 (빨간색) 위협도가 높고, 낮을수록 (파란색) 위협도가 낮습니다.
              이 분석은 Karun Singh의 연구를 기반으로 합니다.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExpectedThreatVisualizer;
