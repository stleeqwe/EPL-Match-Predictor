"""
FastAPI Application Entry Point
EPL Match Predictor API v2.0
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import time
import logging

from api.v1.router import api_router
from api.middleware.logging_middleware import LoggingMiddleware
from config.settings import get_settings
from shared.exceptions.base import AppException

# Logging
logger = logging.getLogger(__name__)

# Settings
settings = get_settings()


def create_app() -> FastAPI:
    """FastAPI 애플리케이션 생성"""

    app = FastAPI(
        title="EPL Match Predictor API",
        description="AI-powered EPL match prediction and player analysis platform",
        version="2.0.0",
        docs_url="/docs" if settings.api.debug else None,
        redoc_url="/redoc" if settings.api.debug else None,
        openapi_url="/openapi.json" if settings.api.debug else None
    )

    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Gzip 압축
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # 커스텀 미들웨어
    app.add_middleware(LoggingMiddleware)

    # 라우터 등록
    app.include_router(api_router, prefix="/api/v1")

    # 예외 핸들러
    register_exception_handlers(app)

    # 이벤트 핸들러
    register_event_handlers(app)

    return app


def register_exception_handlers(app: FastAPI):
    """예외 핸들러 등록"""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        """애플리케이션 예외 처리"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                    "timestamp": time.time()
                }
            }
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """일반 예외 처리"""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)

        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                    "timestamp": time.time()
                }
            }
        )


def register_event_handlers(app: FastAPI):
    """이벤트 핸들러 등록"""

    @app.on_event("startup")
    async def startup_event():
        """애플리케이션 시작 시"""
        logger.info("🚀 EPL Match Predictor API starting...")
        logger.info(f"Environment: {settings.environment}")
        logger.info(f"Debug mode: {settings.api.debug}")
        logger.info("✅ Application started successfully")

    @app.on_event("shutdown")
    async def shutdown_event():
        """애플리케이션 종료 시"""
        logger.info("🛑 EPL Match Predictor API shutting down...")
        # 리소스 정리
        logger.info("✅ Application shut down successfully")


# 애플리케이션 인스턴스
app = create_app()


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "environment": settings.environment
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.api.debug,
        log_level="info"
    )
