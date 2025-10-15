/**
 * 전역 에러 핸들링 유틸리티
 * 일관된 에러 처리를 위한 중앙 집중식 에러 핸들러
 */

import { toast } from '../contexts/ToastContext';

// 에러 타입 정의
export const ErrorTypes = {
  NETWORK: 'NETWORK',
  API: 'API',
  VALIDATION: 'VALIDATION',
  AUTH: 'AUTH',
  PERMISSION: 'PERMISSION',
  SERVER: 'SERVER',
  UNKNOWN: 'UNKNOWN'
};

// 에러 메시지 매핑
const errorMessages = {
  NETWORK: '네트워크 연결을 확인해주세요',
  API: 'API 요청 중 오류가 발생했습니다',
  VALIDATION: '입력값을 확인해주세요',
  AUTH: '인증이 필요합니다',
  PERMISSION: '권한이 없습니다',
  SERVER: '서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요',
  UNKNOWN: '예상치 못한 오류가 발생했습니다'
};

/**
 * 에러 타입 판별
 */
const getErrorType = (error) => {
  if (!error.response) {
    // 네트워크 에러 또는 타임아웃
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      return ErrorTypes.NETWORK;
    }
    if (error.request) {
      return ErrorTypes.NETWORK;
    }
    return ErrorTypes.UNKNOWN;
  }

  const status = error.response.status;

  // HTTP 상태 코드별 에러 타입 분류
  if (status === 400) return ErrorTypes.VALIDATION;
  if (status === 401) return ErrorTypes.AUTH;
  if (status === 403) return ErrorTypes.PERMISSION;
  if (status === 404) return ErrorTypes.API;
  if (status >= 500) return ErrorTypes.SERVER;

  return ErrorTypes.API;
};

/**
 * 에러 메시지 추출
 */
const extractErrorMessage = (error) => {
  // 백엔드에서 보낸 에러 메시지 우선 사용
  if (error.response?.data?.error) {
    if (typeof error.response.data.error === 'string') {
      return error.response.data.error;
    }
    if (error.response.data.error.message) {
      return error.response.data.error.message;
    }
  }

  // Axios 에러 메시지
  if (error.message) {
    return error.message;
  }

  return '알 수 없는 오류가 발생했습니다';
};

/**
 * 중앙 에러 핸들러
 */
export const handleError = (error, options = {}) => {
  const {
    showToast = true,
    logError = true,
    customMessage = null,
    onError = null,
    severity = 'error' // 'error', 'warning', 'info'
  } = options;

  const errorType = getErrorType(error);
  const errorMessage = customMessage || extractErrorMessage(error);
  const defaultMessage = errorMessages[errorType];

  // 콘솔 로깅
  if (logError) {
    console.error(`[${errorType}] ${errorMessage}`, error);
  }

  // Toast 알림 표시
  if (showToast) {
    const toastMessage = customMessage || errorMessage || defaultMessage;

    // ToastContext를 사용할 수 없는 경우 대체 방안
    if (typeof toast !== 'undefined' && toast.show) {
      toast.show(toastMessage, severity);
    } else {
      // fallback: console warning
      console.warn(`[Toast ${severity}] ${toastMessage}`);
    }
  }

  // 커스텀 에러 핸들러 실행
  if (onError && typeof onError === 'function') {
    onError(error, errorType, errorMessage);
  }

  // 에러 객체 반환 (필요시 활용)
  return {
    type: errorType,
    message: errorMessage,
    originalError: error,
    statusCode: error.response?.status
  };
};

/**
 * 비동기 함수 래퍼 (에러 처리 자동화)
 */
export const withErrorHandler = (asyncFn, options = {}) => {
  return async (...args) => {
    try {
      return await asyncFn(...args);
    } catch (error) {
      handleError(error, options);
      throw error; // 에러를 다시 throw하여 호출자가 처리할 수 있도록
    }
  };
};

/**
 * React 컴포넌트용 에러 바운더리 props
 */
export const getErrorBoundaryProps = (error) => {
  const errorType = getErrorType(error);
  const message = extractErrorMessage(error);

  return {
    hasError: true,
    errorType,
    errorMessage: message,
    onRetry: () => window.location.reload()
  };
};

/**
 * API 재시도 로직
 */
export const retryWithExponentialBackoff = async (
  fn,
  maxRetries = 3,
  initialDelay = 1000
) => {
  let lastError;

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      // 재시도 불가능한 에러는 즉시 throw
      const errorType = getErrorType(error);
      if ([ErrorTypes.AUTH, ErrorTypes.PERMISSION, ErrorTypes.VALIDATION].includes(errorType)) {
        throw error;
      }

      // 마지막 시도가 아니면 대기 후 재시도
      if (i < maxRetries - 1) {
        const delay = initialDelay * Math.pow(2, i) + Math.random() * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
        console.log(`재시도 중... (${i + 2}/${maxRetries})`);
      }
    }
  }

  throw lastError;
};

export default handleError;