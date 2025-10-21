# EPL Match Predictor Backend - Production Dockerfile

FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 도구 설치
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사
COPY requirements.txt .

# Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 환경 변수 설정 (기본값)
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# 포트 노출 (Cloud Run은 PORT 환경변수 사용)
ENV PORT=8080
EXPOSE 8080

# 헬스체크 엔드포인트
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/api/health')" || exit 1

# Gunicorn으로 Flask 앱 실행
CMD exec gunicorn --bind :$PORT --workers 2 --threads 4 --timeout 60 --access-logfile - --error-logfile - api.app:app
