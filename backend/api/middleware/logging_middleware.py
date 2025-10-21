"""
Logging Middleware
요청/응답 로깅
"""
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """로깅 미들웨어"""

    async def dispatch(self, request: Request, call_next):
        """요청 처리 및 로깅"""
        # 시작 시간
        start_time = time.time()

        # 요청 정보
        request_info = {
            "method": request.method,
            "url": str(request.url),
            "client": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent")
        }

        logger.info(f"Request started: {request_info}")

        # 요청 처리
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"Request failed: {e}", exc_info=True)
            raise

        # 처리 시간
        process_time = time.time() - start_time

        # 응답 로깅
        logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"status={response.status_code} duration={process_time:.3f}s"
        )

        # 응답 헤더에 처리 시간 추가
        response.headers["X-Process-Time"] = str(process_time)

        return response
