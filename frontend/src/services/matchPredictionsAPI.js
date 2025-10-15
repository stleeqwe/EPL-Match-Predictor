/**
 * Match Predictions API Service
 * 배당률 기반 경기 예측 관련 API 호출
 */

import { api } from './api';

const matchPredictionsAPI = {
  /**
   * 실시간 배당률 가져오기
   * @param {boolean} useDemo - 데모 모드 사용 여부
   * @returns {Promise} 배당률 데이터
   */
  getLiveOdds: async (useDemo = true) => {
    try {
      const response = await api.get('/odds/live', {
        params: { use_demo: useDemo }
      });
      return response;  // interceptor가 이미 response.data를 반환함
    } catch (error) {
      console.error('Error fetching live odds:', error);
      throw error;
    }
  },

  /**
   * 경기 예측 분석
   * @param {number} minEdge - 최소 edge (예: 0.02 = 2%)
   * @param {number} minConfidence - 최소 신뢰도 (예: 0.65 = 65%)
   * @param {boolean} useDemo - 데모 모드 사용 여부
   * @returns {Promise} 경기 예측 목록
   */
  getPredictions: async (minEdge = 0.02, minConfidence = 0.65, useDemo = true) => {
    try {
      const response = await api.get('/value-bets', {
        params: {
          min_edge: minEdge,
          min_confidence: minConfidence,
          use_demo: useDemo
        }
      });
      return response;  // interceptor가 이미 response.data를 반환함
    } catch (error) {
      console.error('Error fetching predictions:', error);
      throw error;
    }
  },

  /**
   * 통합 대시보드 데이터
   * @param {boolean} useDemo - 데모 모드 사용 여부
   * @returns {Promise} 대시보드 데이터 (배당률, 예측 분석)
   */
  getDashboardData: async (useDemo = true) => {
    try {
      const response = await api.get('/dashboard', {
        params: { use_demo: useDemo }
      });
      return response;  // interceptor가 이미 response.data를 반환함
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      throw error;
    }
  },

  /**
   * 경기 예측 데이터
   * @param {boolean} useDemo - 데모 모드 사용 여부
   * @returns {Promise} 경기 예측 목록 (승/무/패 확률, 예상 스코어)
   */
  getMatchPredictions: async (useDemo = true) => {
    try {
      const response = await api.get('/match-predictions', {
        params: { use_demo: useDemo }
      });
      return response;  // interceptor가 이미 response.data를 반환함
    } catch (error) {
      console.error('Error fetching match predictions:', error);
      throw error;
    }
  },

  /**
   * 배당률 → 암시 확률 변환
   * @param {number} odds - 배당률
   * @returns {number} 암시 확률 (0-100%)
   */
  calculateImpliedProbability: (odds) => {
    if (!odds || odds <= 0) return 0;
    return (1 / odds) * 100;
  },

  /**
   * 여러 북메이커 배당률의 평균 암시 확률
   * @param {Array} oddsArray - 배당률 배열
   * @returns {number} 평균 암시 확률
   */
  calculateConsensusProbability: (oddsArray) => {
    if (!oddsArray || oddsArray.length === 0) return 0;

    const probabilities = oddsArray.map(odds => matchPredictionsAPI.calculateImpliedProbability(odds));
    const sum = probabilities.reduce((acc, prob) => acc + prob, 0);
    return sum / probabilities.length;
  }
};

export default matchPredictionsAPI;
