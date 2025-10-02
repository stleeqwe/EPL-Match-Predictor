/**
 * 앙상블 예측 UI 컴포넌트
 * 여러 모델의 결과를 조합한 고급 예측 제공
 */

import React, { useState } from 'react';
import { advancedAPI } from '../services/api';
import ProbabilityBar from './ProbabilityBar';

const EnsemblePredictor = () => {
  const [homeTeam, setHomeTeam] = useState('');
  const [awayTeam, setAwayTeam] = useState('');
  const [season, setSeason] = useState('2024-2025');
  const [ensembleMethod, setEnsembleMethod] = useState('weighted_average');
  const [loading, setLoading] = useState(false);
  const [prediction, setPrediction] = useState(null);
  const [error, setError] = useState(null);

  const ensembleMethods = [
    { value: 'weighted_average', label: '가중 평균 (Weighted Average)' },
    { value: 'simple_average', label: '단순 평균 (Simple Average)' },
    { value: 'voting', label: '투표 (Voting)' },
  ];

  const handlePredict = async () => {
    if (!homeTeam || !awayTeam) {
      setError('홈팀과 원정팀을 모두 입력해주세요.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await advancedAPI.ensemble({
        home_team: homeTeam,
        away_team: awayTeam,
        season: season,
        ensemble_method: ensembleMethod,
      });

      setPrediction(result);
    } catch (err) {
      setError(err.response?.data?.error || '예측 중 오류가 발생했습니다.');
      console.error('Ensemble prediction error:', err);
    } finally {
      setLoading(false);
    }
  };

  const renderModelBreakdown = () => {
    if (!prediction?.model_predictions) return null;

    return (
      <div className="mt-6">
        <h3 className="text-lg font-semibold mb-3">모델별 예측 상세</h3>
        <div className="space-y-4">
          {Object.entries(prediction.model_predictions).map(([model, probs]) => (
            <div key={model} className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-semibold mb-2 capitalize">
                {model.replace('_', ' ')}
              </h4>
              <div className="grid grid-cols-3 gap-2 text-sm">
                <div>
                  <span className="text-gray-600">홈 승:</span>
                  <span className="ml-2 font-semibold">
                    {probs.home_win?.toFixed(1)}%
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">무승부:</span>
                  <span className="ml-2 font-semibold">
                    {probs.draw?.toFixed(1)}%
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">원정 승:</span>
                  <span className="ml-2 font-semibold">
                    {probs.away_win?.toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderUncertainty = () => {
    if (!prediction?.uncertainty) return null;

    const { home_win_std, draw_std, away_win_std, avg_std } = prediction.uncertainty;

    return (
      <div className="mt-6 bg-yellow-50 p-4 rounded-lg">
        <h3 className="text-lg font-semibold mb-3">불확실성 분석</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <div className="text-gray-600">홈 승 표준편차</div>
            <div className="text-xl font-bold text-blue-600">
              {home_win_std?.toFixed(2)}%
            </div>
          </div>
          <div>
            <div className="text-gray-600">무승부 표준편차</div>
            <div className="text-xl font-bold text-gray-600">
              {draw_std?.toFixed(2)}%
            </div>
          </div>
          <div>
            <div className="text-gray-600">원정 승 표준편차</div>
            <div className="text-xl font-bold text-red-600">
              {away_win_std?.toFixed(2)}%
            </div>
          </div>
          <div>
            <div className="text-gray-600">평균 불확실성</div>
            <div className="text-xl font-bold text-purple-600">
              {avg_std?.toFixed(2)}%
            </div>
          </div>
        </div>
        <p className="mt-3 text-xs text-gray-600">
          표준편차가 낮을수록 모델들의 예측이 일치하며 신뢰도가 높습니다.
        </p>
      </div>
    );
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-4">앙상블 예측</h2>

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

        <div>
          <label className="block text-sm font-semibold mb-2">앙상블 방식</label>
          <select
            value={ensembleMethod}
            onChange={(e) => setEnsembleMethod(e.target.value)}
            className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            {ensembleMethods.map((method) => (
              <option key={method.value} value={method.value}>
                {method.label}
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={handlePredict}
          disabled={loading}
          className={`w-full md:w-auto px-6 py-2 rounded-lg font-semibold transition-colors ${
            loading
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 text-white'
          }`}
        >
          {loading ? '예측 중...' : '앙상블 예측'}
        </button>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {prediction && (
        <div className="space-y-6">
          {/* 메인 예측 결과 */}
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-6 rounded-lg">
            <h3 className="text-xl font-bold mb-4 text-center">앙상블 예측 결과</h3>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="font-semibold">홈 승리</span>
                  <span className="font-bold text-blue-600">
                    {prediction.home_win?.toFixed(1)}%
                  </span>
                </div>
                <ProbabilityBar probability={prediction.home_win} color="blue" />
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span className="font-semibold">무승부</span>
                  <span className="font-bold text-gray-600">
                    {prediction.draw?.toFixed(1)}%
                  </span>
                </div>
                <ProbabilityBar probability={prediction.draw} color="gray" />
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span className="font-semibold">원정 승리</span>
                  <span className="font-bold text-red-600">
                    {prediction.away_win?.toFixed(1)}%
                  </span>
                </div>
                <ProbabilityBar probability={prediction.away_win} color="red" />
              </div>
            </div>
          </div>

          {/* 불확실성 분석 */}
          {renderUncertainty()}

          {/* 모델별 분석 */}
          {renderModelBreakdown()}

          {/* 설명 */}
          <div className="bg-blue-50 p-4 rounded-lg">
            <h4 className="font-semibold mb-2">🤖 앙상블 예측이란?</h4>
            <p className="text-sm text-gray-700">
              앙상블 예측은 여러 예측 모델(Dixon-Coles, Random Forest, XGBoost, CatBoost)의
              결과를 통합하여 더 정확하고 안정적인 예측을 제공합니다. 각 모델의 강점을
              결합하여 단일 모델보다 우수한 성능을 발휘합니다.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default EnsemblePredictor;
