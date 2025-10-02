/**
 * 평가 메트릭 대시보드 컴포넌트
 * RPS, Brier Score, Log Loss 등 모델 평가 지표 시각화
 */

import React, { useState, useEffect } from 'react';
import { advancedAPI, predictionsAPI } from '../services/api';

const EvaluationDashboard = () => {
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadEvaluationMetrics();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadEvaluationMetrics = async () => {
    setLoading(true);
    setError(null);

    try {
      // 최근 예측 데이터 가져오기
      const history = await predictionsAPI.getHistory(100);

      // 완료된 경기만 필터링 (실제 결과가 있는 경기)
      const completedPredictions = history.filter(
        (pred) => pred.actual_result !== null && pred.actual_result !== undefined
      );

      if (completedPredictions.length === 0) {
        setError('평가할 완료된 경기가 없습니다.');
        setLoading(false);
        return;
      }

      // 예측 및 실제 결과 변환
      const predictions = completedPredictions.map((pred) => [
        pred.home_win_prob || 0,
        pred.draw_prob || 0,
        pred.away_win_prob || 0,
      ]);

      const actuals = completedPredictions.map((pred) => {
        if (pred.actual_result === 'home_win') return [1, 0, 0];
        if (pred.actual_result === 'draw') return [0, 1, 0];
        if (pred.actual_result === 'away_win') return [0, 0, 1];
        return [0, 0, 0];
      });

      // 평가 메트릭 계산
      const result = await advancedAPI.evaluate({
        predictions,
        actuals,
      });

      setMetrics(result);
    } catch (err) {
      setError(err.response?.data?.error || '평가 중 오류가 발생했습니다.');
      console.error('Evaluation error:', err);
    } finally {
      setLoading(false);
    }
  };

  const renderMetricCard = (title, value, description, color = 'blue') => {
    const colorClasses = {
      blue: 'bg-blue-50 border-blue-200 text-blue-700',
      green: 'bg-green-50 border-green-200 text-green-700',
      purple: 'bg-purple-50 border-purple-200 text-purple-700',
      orange: 'bg-orange-50 border-orange-200 text-orange-700',
    };

    return (
      <div className={`border-2 rounded-lg p-4 ${colorClasses[color]}`}>
        <div className="text-sm font-semibold mb-1">{title}</div>
        <div className="text-3xl font-bold mb-2">
          {value !== null && value !== undefined ? value.toFixed(4) : 'N/A'}
        </div>
        <div className="text-xs opacity-80">{description}</div>
      </div>
    );
  };

  const renderModelComparison = () => {
    if (!metrics?.model_comparison) return null;

    return (
      <div className="mt-6">
        <h3 className="text-xl font-bold mb-4">모델별 성능 비교</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white border rounded-lg">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-4 py-2 text-left">모델</th>
                <th className="px-4 py-2 text-right">정확도</th>
                <th className="px-4 py-2 text-right">RPS</th>
                <th className="px-4 py-2 text-right">Brier Score</th>
                <th className="px-4 py-2 text-right">Log Loss</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(metrics.model_comparison).map(([model, stats]) => (
                <tr key={model} className="border-t hover:bg-gray-50">
                  <td className="px-4 py-2 font-semibold">{model}</td>
                  <td className="px-4 py-2 text-right">
                    {(stats.accuracy * 100).toFixed(1)}%
                  </td>
                  <td className="px-4 py-2 text-right">{stats.rps?.toFixed(4) || 'N/A'}</td>
                  <td className="px-4 py-2 text-right">
                    {stats.brier_score?.toFixed(4) || 'N/A'}
                  </td>
                  <td className="px-4 py-2 text-right">
                    {stats.log_loss?.toFixed(4) || 'N/A'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">모델 평가 대시보드</h2>
        <button
          onClick={loadEvaluationMetrics}
          disabled={loading}
          className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
            loading
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 text-white'
          }`}
        >
          {loading ? '계산 중...' : '새로고침'}
        </button>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {loading && (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">평가 메트릭 계산 중...</p>
        </div>
      )}

      {metrics && !loading && (
        <div className="space-y-6">
          {/* 주요 메트릭 */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {renderMetricCard(
              'Ranked Probability Score (RPS)',
              metrics.rps,
              '순위 확률 점수 (낮을수록 좋음)',
              'blue'
            )}
            {renderMetricCard(
              'Brier Score',
              metrics.brier_score,
              '브라이어 점수 (낮을수록 좋음)',
              'green'
            )}
            {renderMetricCard(
              'Log Loss',
              metrics.log_loss,
              '로그 손실 (낮을수록 좋음)',
              'purple'
            )}
            {renderMetricCard(
              'Overall Accuracy',
              metrics.accuracy ? metrics.accuracy * 100 : null,
              '전체 정확도 (%)',
              'orange'
            )}
          </div>

          {/* 모델별 비교 */}
          {renderModelComparison()}

          {/* 설명 섹션 */}
          <div className="bg-gray-50 p-4 rounded-lg space-y-3">
            <h4 className="font-semibold">📊 평가 메트릭 설명</h4>
            <div className="text-sm space-y-2 text-gray-700">
              <p>
                <strong>RPS (Ranked Probability Score):</strong> 순위형 범주 예측의 정확도를 측정합니다.
                0에 가까울수록 우수한 예측입니다. (범위: 0-1)
              </p>
              <p>
                <strong>Brier Score:</strong> 확률 예측의 정확도를 측정하는 지표입니다.
                0에 가까울수록 완벽한 예측입니다. (범위: 0-2)
              </p>
              <p>
                <strong>Log Loss:</strong> 확률 예측의 불확실성을 측정합니다.
                낮을수록 모델의 확신도가 높고 정확합니다.
              </p>
              <p>
                <strong>Accuracy:</strong> 가장 높은 확률로 예측한 결과가 실제 결과와 일치하는 비율입니다.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EvaluationDashboard;
