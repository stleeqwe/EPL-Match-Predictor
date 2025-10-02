/**
 * API Service Layer
 * 모든 백엔드 API 호출을 중앙에서 관리
 */

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

// Axios 인스턴스 생성
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30초
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터 (로깅)
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// 응답 인터셉터 (에러 처리)
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    if (error.response) {
      // 서버가 응답했지만 2xx 범위를 벗어남
      console.error(`API Error ${error.response.status}:`, error.response.data);
    } else if (error.request) {
      // 요청이 전송되었지만 응답이 없음
      console.error('API No Response:', error.request);
    } else {
      // 요청 설정 중 에러
      console.error('API Setup Error:', error.message);
    }
    return Promise.reject(error);
  }
);

/**
 * 예측 관련 API
 */
export const predictionsAPI = {
  /**
   * 경기 결과 예측
   * @param {Object} data - 예측 요청 데이터
   * @returns {Promise<Object>} 예측 결과
   */
  predict: async (data) => {
    const response = await api.post('/predict', data);
    return response.data;
  },

  /**
   * 예측 히스토리 조회
   * @param {number} limit - 조회할 개수
   * @returns {Promise<Array>} 예측 히스토리
   */
  getHistory: async (limit = 50) => {
    const response = await api.get('/predictions/history', { params: { limit } });
    return response.data;
  },

  /**
   * 예측 정확도 조회
   * @param {number} days - 조회할 일수
   * @returns {Promise<Object>} 정확도 통계
   */
  getAccuracy: async (days = 30) => {
    const response = await api.get('/predictions/accuracy', { params: { days } });
    return response.data;
  },
};

/**
 * 경기 일정 관련 API
 */
export const fixturesAPI = {
  /**
   * 전체 경기 일정 조회
   * @returns {Promise<Array>} 경기 일정 목록
   */
  getAll: async () => {
    const response = await api.get('/fixtures');
    return response.data;
  },
};

/**
 * 팀 관련 API
 */
export const teamsAPI = {
  /**
   * 전체 팀 목록 조회
   * @returns {Promise<Array>} 팀 이름 목록
   */
  getAll: async () => {
    const response = await api.get('/teams');
    return response.data;
  },

  /**
   * 특정 팀의 통계 조회
   * @param {string} teamName - 팀 이름
   * @returns {Promise<Object>} 팀 통계
   */
  getStats: async (teamName) => {
    const response = await api.get(`/team-stats/${teamName}`);
    return response.data;
  },

  /**
   * 특정 팀의 선수 명단 조회
   * @param {string} teamName - 팀 이름
   * @returns {Promise<Array>} 선수 목록
   */
  getSquad: async (teamName) => {
    const response = await api.get(`/squad/${teamName}`);
    return response.data;
  },
};

/**
 * 리그 순위표 관련 API
 */
export const standingsAPI = {
  /**
   * 리그 순위표 조회
   * @param {string} season - 시즌 (예: "2024-2025")
   * @returns {Promise<Array>} 순위표
   */
  getStandings: async (season = '2024-2025') => {
    const response = await api.get('/standings', { params: { season } });
    return response.data;
  },
};

/**
 * 선수 평가 관련 API
 */
export const ratingsAPI = {
  /**
   * 선수 능력치 저장
   * @param {number} playerId - 선수 ID
   * @param {Object} ratings - 능력치 객체
   * @returns {Promise<Object>} 저장 결과
   */
  saveRating: async (playerId, ratings) => {
    const response = await api.post('/save-rating', {
      player_id: playerId,
      ratings: ratings,
    });
    return response.data;
  },
};

/**
 * 헬스 체크
 */
export const healthAPI = {
  /**
   * API 서버 상태 확인
   * @returns {Promise<Object>} 서버 상태
   */
  check: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};

/**
 * 고급 분석 API (Advanced Analytics)
 */
export const advancedAPI = {
  /**
   * Bayesian Dixon-Coles 예측 (불확실성 정량화 포함)
   * @param {Object} data - { home_team, away_team, n_sims, credible_interval, use_cached }
   * @returns {Promise<Object>} Bayesian 예측 결과 + 신뢰구간
   */
  bayesian: async (data) => {
    const response = await api.post('/predict/bayesian', {
      home_team: data.home_team,
      away_team: data.away_team,
      n_sims: data.n_sims || 3000,
      credible_interval: data.credible_interval || 0.95,
      use_cached: data.use_cached !== undefined ? data.use_cached : true,
    });
    return response.data;
  },

  /**
   * Bayesian 모델의 팀별 능력치 조회
   * @returns {Promise<Object>} 팀별 공격력/수비력 posterior 분포
   */
  bayesianTeamRatings: async () => {
    const response = await api.get('/bayesian/team-ratings');
    return response.data;
  },

  /**
   * Bayesian 모델 재학습
   * @param {Object} data - { n_samples, burnin, thin, verbose }
   * @returns {Promise<Object>} 학습 결과
   */
  bayesianRetrain: async (data) => {
    const response = await api.post('/bayesian/retrain', data);
    return response.data;
  },

  /**
   * CatBoost 모델 예측
   * @param {Object} data - { home_team, away_team, season }
   * @returns {Promise<Object>} CatBoost 예측 결과
   */
  catboost: async (data) => {
    const response = await api.post('/predict/catboost', data);
    return response.data;
  },

  /**
   * Expected Threat (xT) 계산
   * @param {Object} data - { home_team, away_team, season }
   * @returns {Promise<Object>} xT 분석 결과
   */
  expectedThreat: async (data) => {
    const response = await api.post('/expected-threat', data);
    return response.data;
  },

  /**
   * 예측 평가 메트릭 (RPS, Brier Score 등)
   * @param {Object} data - { predictions: [...], actuals: [...] }
   * @returns {Promise<Object>} 평가 메트릭 결과
   */
  evaluate: async (data) => {
    const response = await api.post('/evaluate', data);
    return response.data;
  },

  /**
   * 앙상블 예측
   * @param {Object} data - { home_team, away_team, season, ensemble_method }
   * @returns {Promise<Object>} 앙상블 예측 결과
   */
  ensemble: async (data) => {
    const response = await api.post('/predict/ensemble', data);
    return response.data;
  },
};

export default api;
