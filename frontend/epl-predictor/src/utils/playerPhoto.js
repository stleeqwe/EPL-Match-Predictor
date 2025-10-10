/**
 * Player Photo Utility
 * 백엔드 프록시를 통한 선수 사진 URL 생성 (CORS 우회)
 */

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

/**
 * 선수 사진 URL 생성
 * @param {string} photoCode - FPL photo code (예: "446008")
 * @param {string} size - 이미지 사이즈 ('110x140' | '250x250' | '400x400')
 * @returns {string} 선수 사진 URL
 */
export const getPlayerPhotoUrl = (photoCode, size = '250x250') => {
  if (!photoCode) return null;

  // 백엔드 프록시를 통한 이미지 URL (CORS 우회)
  return `${API_URL}/player-photo/${photoCode}?size=${size}`;
};

/**
 * 선수 사진 폴백 처리
 * @param {Event} e - 이미지 로드 실패 이벤트
 */
export const handlePhotoError = (e) => {
  // 기본 아바타 이미지로 대체 (또는 숨김 처리)
  e.target.style.display = 'none';
};

/**
 * 선수 사진 preload (성능 최적화)
 * @param {string} photoCode - FPL photo code
 * @param {string} size - 이미지 사이즈
 */
export const preloadPlayerPhoto = (photoCode, size = '250x250') => {
  if (!photoCode) return;

  const img = new Image();
  img.src = getPlayerPhotoUrl(photoCode, size);
};
