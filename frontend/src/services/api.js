/**
 * API Service - EPL Player Analysis Platform
 * Version 3.0 (Player Rating System)
 */

import axios from 'axios';
import { handleError, retryWithExponentialBackoff } from '../utils/errorHandler';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

// 재시도 설정
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1초

// Axios 인스턴스 생성
const api = axios.create({
  baseURL: API_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 재시도 가능한 에러인지 확인
const shouldRetry = (error) => {
  // 타임아웃이나 네트워크 에러는 재시도
  if (!error.response) return true;

  // 5xx 서버 에러는 재시도
  const status = error.response.status;
  return status >= 500 && status <= 599;
};

// 대기 함수
const wait = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Response interceptor (에러 핸들링 + 재시도 로직)
api.interceptors.response.use(
  response => response.data,
  async (error) => {
    const config = error.config;

    // 재시도 가능한지 확인
    if (!config || !shouldRetry(error)) {
      // 전역 에러 핸들러 사용
      handleError(error, {
        showToast: false, // API 레벨에서는 Toast 표시하지 않음 (컴포넌트에서 처리)
        logError: true
      });

      // 원본 에러 그대로 throw (컴포넌트에서 처리하도록)
      throw error;
    }

    // 재시도 로직
    config.metadata = config.metadata || { retryCount: 0 };
    config.metadata.retryCount += 1;

    if (config.metadata.retryCount <= MAX_RETRIES) {
      const delay = RETRY_DELAY * Math.pow(2, config.metadata.retryCount - 1); // Exponential backoff

      if (process.env.NODE_ENV === 'development') {
        console.warn(
          `⚠️ Retrying request (${config.metadata.retryCount}/${MAX_RETRIES}) after ${delay}ms:`,
          config.url
        );
      }

      await wait(delay);
      return api(config);
    }

    // 최대 재시도 초과
    handleError(new Error(`Maximum retry attempts exceeded for: ${config.url}`), {
      showToast: false,
      logError: true
    });
    throw error;
  }
);

// ============================================================
// Health & Status
// ============================================================

export const healthAPI = {
  check: () => api.get('/health')
};

// ============================================================
// Teams API
// ============================================================

export const teamsAPI = {
  /**
   * 전체 EPL 팀 목록 조회
   */
  getAll: () => api.get('/teams'),

  /**
   * 특정 팀의 선수 명단 조회
   * @param {string} teamName - 팀 이름
   */
  getSquad: (teamName) => api.get(`/squad/${encodeURIComponent(teamName)}`)
};

// ============================================================
// Players API
// ============================================================

export const playersAPI = {
  /**
   * 특정 선수 정보 조회
   * @param {number} playerId - 선수 ID
   */
  getById: (playerId) => api.get(`/player/${playerId}`),

  /**
   * 선수 검색 (선택적 구현)
   * @param {string} query - 검색어
   */
  search: (query) => api.get('/players/search', { params: { q: query } })
};

// ============================================================
// Ratings API
// ============================================================

export const ratingsAPI = {
  /**
   * 선수 능력치 조회
   * @param {number} playerId - 선수 ID
   * @param {string} userId - 사용자 ID (기본값: 'default')
   */
  get: (playerId, userId = 'default') =>
    api.get(`/ratings/${playerId}`, { params: { user_id: userId } }),

  /**
   * 선수 능력치 저장 (여러 능력치 일괄 저장)
   * @param {number} playerId - 선수 ID
   * @param {Object} ratings - { attribute_name: rating_value, ... }
   * @param {string} userId - 사용자 ID (기본값: 'default')
   */
  save: (playerId, ratings, userId = 'default') =>
    api.post('/ratings', {
      player_id: playerId,
      user_id: userId,
      ratings: ratings
    }),

  /**
   * 단일 능력치 업데이트
   * @param {number} playerId - 선수 ID
   * @param {string} attribute - 능력치 이름
   * @param {number} rating - 평점 (0.0 ~ 5.0)
   * @param {string} notes - 메모 (선택)
   * @param {string} userId - 사용자 ID (기본값: 'default')
   */
  update: (playerId, attribute, rating, notes = '', userId = 'default') =>
    api.put(`/ratings/${playerId}/${attribute}`, {
      rating: rating,
      notes: notes,
      user_id: userId
    }),

  /**
   * 선수 능력치 삭제
   * @param {number} playerId - 선수 ID
   * @param {string} userId - 사용자 ID (기본값: 'default')
   */
  delete: (playerId, userId = 'default') =>
    api.delete(`/ratings/${playerId}`, { params: { user_id: userId } })
};

// ============================================================
// Positions API
// ============================================================

export const positionsAPI = {
  /**
   * 포지션별 능력치 템플릿 조회
   */
  getAttributes: () => api.get('/positions'),

  /**
   * 평가 범위 정보 조회 (0.0 ~ 5.0, 0.25 step)
   */
  getRatingScale: () => api.get('/rating-scale')
};

// ============================================================
// Analytics API (Phase 5에서 구현 예정)
// ============================================================

export const analyticsAPI = {
  /**
   * 팀 전체 능력치 분석
   * @param {string} teamName - 팀 이름
   * @param {string} userId - 사용자 ID
   */
  getTeamAnalysis: (teamName, userId = 'default') =>
    api.get(`/analytics/team/${encodeURIComponent(teamName)}`, { params: { user_id: userId } }),

  /**
   * 포지션별 평균 능력치
   * @param {string} position - 포지션 (GK/DF/MF/FW)
   * @param {string} userId - 사용자 ID
   */
  getPositionAverage: (position, userId = 'default') =>
    api.get(`/analytics/position/${position}`, { params: { user_id: userId } })
};

// ============================================================
// Export/Import API (Phase 5에서 구현 예정)
// ============================================================

export const dataAPI = {
  /**
   * 능력치 데이터 내보내기
   * @param {string} userId - 사용자 ID
   */
  exportRatings: (userId = 'default') =>
    api.get('/data/export', { params: { user_id: userId } }),

  /**
   * 능력치 데이터 가져오기
   * @param {Object} data - JSON 데이터
   * @param {string} userId - 사용자 ID
   */
  importRatings: (data, userId = 'default') =>
    api.post('/data/import', { data, user_id: userId })
};

// ============================================================
// Utility Functions
// ============================================================

/**
 * 능력치 유효성 검증
 * @param {number} rating - 평점
 * @returns {boolean} 유효 여부
 */
export const validateRating = (rating) => {
  if (typeof rating !== 'number') return false;
  if (rating < 0.0 || rating > 5.0) return false;
  // 0.25 단위 검증
  return Math.round(rating * 4) === rating * 4;
};

/**
 * 평균 능력치 계산
 * @param {Object} ratings - { attribute: value, ... }
 * @returns {number} 평균 능력치
 */
export const calculateAverageRating = (ratings) => {
  const values = Object.values(ratings).filter(v => typeof v === 'number');
  if (values.length === 0) return 0;
  return values.reduce((sum, val) => sum + val, 0) / values.length;
};

// ============================================================
// Legacy/Deprecated APIs (for backward compatibility)
// ============================================================

// Temporary stub for old components that haven't been deleted yet
export const advancedAPI = {
  analyze: () => Promise.resolve({ error: 'This API is deprecated' })
};

// ============================================================
// EPL API (Official Data)
// ============================================================

export const eplAPI = {
  /**
   * EPL 리그 순위표 조회
   */
  getStandings: () => api.get('/epl/standings'),

  /**
   * EPL 경기 일정 및 결과 조회
   * @param {Object} params - { event, team }
   */
  getFixtures: (params = {}) => api.get('/epl/fixtures', { params }),

  /**
   * EPL 리더보드 (득점왕, 도움왕 등)
   */
  getLeaderboard: () => api.get('/epl/leaderboard')
};

// ============================================================
// Injuries API
// ============================================================

export const injuriesAPI = {
  /**
   * 팀의 부상자 정보 조회
   * @param {string} teamName - 팀 이름
   * @param {boolean} forceRefresh - 강제 갱신 여부
   */
  getTeamInjuries: (teamName, forceRefresh = false) =>
    api.get(`/teams/${encodeURIComponent(teamName)}/injuries`, {
      params: { force_refresh: forceRefresh }
    }),

  /**
   * 팀의 부상자 정보 강제 갱신
   * @param {string} teamName - 팀 이름
   */
  refreshTeamInjuries: (teamName) =>
    api.post(`/teams/${encodeURIComponent(teamName)}/injuries/refresh`),

  /**
   * 모든 팀의 부상자 정보 일괄 업데이트
   * @param {boolean} force - 강제 갱신 여부
   */
  updateAllInjuries: (force = false) =>
    api.post('/injuries/update-all', { force }),

  /**
   * 현재 업데이트 빈도 정보 조회
   */
  getUpdateFrequency: () => api.get('/injuries/frequency')
};

// ============================================================
// Default Export
// ============================================================

const apiClient = {
  health: healthAPI,
  teams: teamsAPI,
  players: playersAPI,
  ratings: ratingsAPI,
  positions: positionsAPI,
  analytics: analyticsAPI,
  data: dataAPI,
  epl: eplAPI,
  injuries: injuriesAPI,

  // Utilities
  validateRating,
  calculateAverageRating
};

export default apiClient;

// Export raw axios instance for custom API calls
export { api };
