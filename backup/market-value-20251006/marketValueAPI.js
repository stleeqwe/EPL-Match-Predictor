/**
 * Market Value API Service
 * Value Betting 관련 API 호출
 */

import api from './api';

const marketValueAPI = {
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
      return response.data;
    } catch (error) {
      console.error('Error fetching live odds:', error);
      throw error;
    }
  },

  /**
   * Value Bet 탐지
   * @param {number} minEdge - 최소 edge (예: 0.02 = 2%)
   * @param {number} minConfidence - 최소 신뢰도 (예: 0.65 = 65%)
   * @param {boolean} useDemo - 데모 모드 사용 여부
   * @returns {Promise} Value Bet 목록
   */
  getValueBets: async (minEdge = 0.02, minConfidence = 0.65, useDemo = true) => {
    try {
      const response = await api.get('/value-bets', {
        params: {
          min_edge: minEdge,
          min_confidence: minConfidence,
          use_demo: useDemo
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching value bets:', error);
      throw error;
    }
  },

  /**
   * Arbitrage 기회 탐지
   * @param {number} minProfit - 최소 수익률 (예: 0.005 = 0.5%)
   * @param {boolean} useDemo - 데모 모드 사용 여부
   * @returns {Promise} Arbitrage 기회 목록
   */
  getArbitrageOpportunities: async (minProfit = 0.005, useDemo = true) => {
    try {
      const response = await api.get('/arbitrage', {
        params: {
          min_profit: minProfit,
          use_demo: useDemo
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching arbitrage opportunities:', error);
      throw error;
    }
  },

  /**
   * Kelly Criterion 계산
   * @param {object} params - { win_probability, decimal_odds, bankroll }
   * @returns {Promise} Kelly 계산 결과
   */
  calculateKelly: async (params) => {
    try {
      const response = await api.post('/kelly/calculate', params);
      return response.data;
    } catch (error) {
      console.error('Error calculating Kelly:', error);
      throw error;
    }
  },

  /**
   * 포트폴리오 배분 계산
   * @param {Array} valueBets - Value Bet 목록
   * @param {number} bankroll - 총 자금
   * @returns {Promise} 포트폴리오 배분 결과
   */
  calculatePortfolio: async (valueBets, bankroll) => {
    try {
      const response = await api.post('/kelly/portfolio', {
        value_bets: valueBets,
        bankroll: bankroll
      });
      return response.data;
    } catch (error) {
      console.error('Error calculating portfolio:', error);
      throw error;
    }
  },

  /**
   * 통합 대시보드 데이터
   * @param {boolean} useDemo - 데모 모드 사용 여부
   * @returns {Promise} 대시보드 데이터 (배당률, Value Bets, Arbitrage)
   */
  getDashboardData: async (useDemo = true) => {
    try {
      const response = await api.get('/dashboard', {
        params: { use_demo: useDemo }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      throw error;
    }
  }
};

export default marketValueAPI;
