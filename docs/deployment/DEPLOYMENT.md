# 🚀 배포 가이드

## 프로덕션 배포 체크리스트

### 1. 환경 변수 설정

`.env` 파일 생성:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/soccer_predictor
SQLITE_PATH=sqlite:///soccer_predictor.db

# API
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=your-secret-key-here

# 스크래핑
FBREF_DELAY=3
UNDERSTAT_DELAY=3
USER_AGENT=Mozilla/5.0 (compatible; SoccerPredictor/1.0)

# 모델
MODEL_PATH=models/xgboost_model.pkl
DIXON_COLES_XI=0.0065
DIXON_COLES_RHO=-0.15

# 프론트엔드
REACT_APP_API_URL=http://localhost:5001/api
```

---

### 2. Docker 컨테이너화

#### Dockerfile (Backend)

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 시스템 의존성
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libomp-dev \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 복사
COPY backend/ ./backend/
COPY venv/ ./venv/

EXPOSE 5001

CMD ["python", "backend/api/app.py"]
```

#### Dockerfile (Frontend)

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY frontend/epl-predictor/package*.json ./
RUN npm ci --only=production

COPY frontend/epl-predictor/ .

RUN npm run build

FROM nginx:alpine
COPY --from=0 /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: soccer_user
      POSTGRES_PASSWORD: soccer_pass
      POSTGRES_DB: soccer_predictor
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    environment:
      DATABASE_URL: postgresql://soccer_user:soccer_pass@postgres:5432/soccer_predictor
    depends_on:
      - postgres
    ports:
      - "5001:5001"
    volumes:
      - ./models:/app/models

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "80:80"
    depends_on:
      - backend

  scheduler:
    build:
      context: .
      dockerfile: Dockerfile.backend
    command: python backend/utils/data_scheduler.py
    environment:
      DATABASE_URL: postgresql://soccer_user:soccer_pass@postgres:5432/soccer_predictor
    depends_on:
      - postgres

volumes:
  postgres_data:
```

---

### 3. PostgreSQL 마이그레이션

#### 데이터베이스 초기화

```bash
# PostgreSQL 접속
psql -U postgres

# 데이터베이스 생성
CREATE DATABASE soccer_predictor;
CREATE USER soccer_user WITH PASSWORD 'soccer_pass';
GRANT ALL PRIVILEGES ON DATABASE soccer_predictor TO soccer_user;

# 테이블 생성
python -c "from backend.database.schema import init_db; init_db('postgresql://soccer_user:soccer_pass@localhost/soccer_predictor')"
```

#### SQLite → PostgreSQL 마이그레이션

```python
import sqlite3
import psycopg2
from backend.database.schema import init_db, get_session, Team, Match

# SQLite 연결
sqlite_conn = sqlite3.connect('soccer_predictor.db')

# PostgreSQL 연결
pg_engine = init_db('postgresql://soccer_user:soccer_pass@localhost/soccer_predictor')
pg_session = get_session(pg_engine)

# 데이터 이동
sqlite_cursor = sqlite_conn.cursor()
sqlite_cursor.execute("SELECT * FROM teams")

for row in sqlite_cursor.fetchall():
    team = Team(id=row[0], name=row[1], short_name=row[2], league=row[3])
    pg_session.add(team)

pg_session.commit()
```

---

### 4. Nginx 설정

`nginx.conf`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # 프론트엔드
    location / {
        root /usr/share/nginx/html;
        try_files $uri /index.html;
    }

    # 백엔드 프록시
    location /api {
        proxy_pass http://backend:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 정적 파일 캐싱
    location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

---

### 5. AWS 배포

#### EC2 인스턴스 설정

```bash
# 인스턴스 접속
ssh -i soccer-key.pem ubuntu@ec2-xx-xx-xx-xx.compute.amazonaws.com

# Docker 설치
sudo apt-get update
sudo apt-get install docker.io docker-compose -y
sudo usermod -aG docker ubuntu

# 프로젝트 복사
git clone https://github.com/yourusername/soccer-predictor.git
cd soccer-predictor

# 환경 변수 설정
cp .env.example .env
nano .env

# Docker Compose 실행
docker-compose up -d
```

#### RDS (PostgreSQL) 설정

1. AWS RDS 콘솔에서 PostgreSQL 인스턴스 생성
2. 보안 그룹 설정 (포트 5432 오픈)
3. 엔드포인트 복사

```bash
# .env 업데이트
DATABASE_URL=postgresql://admin:password@soccer-db.xxxx.rds.amazonaws.com:5432/soccer_predictor
```

#### S3 (모델 저장소)

```bash
# AWS CLI 설치
sudo apt-get install awscli -y

# S3 버킷 생성
aws s3 mb s3://soccer-predictor-models

# 모델 업로드
aws s3 cp models/xgboost_model.pkl s3://soccer-predictor-models/
```

---

### 6. CI/CD (GitHub Actions)

`.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest

    - name: Run tests
      run: pytest backend/tests/

    - name: Build Docker images
      run: docker-compose build

    - name: Deploy to EC2
      env:
        SSH_KEY: ${{ secrets.EC2_SSH_KEY }}
        HOST: ${{ secrets.EC2_HOST }}
      run: |
        echo "$SSH_KEY" > key.pem
        chmod 600 key.pem
        ssh -i key.pem ubuntu@$HOST "cd soccer-predictor && git pull && docker-compose up -d --build"
```

---

### 7. 모니터링

#### 로그 수집

```bash
# Docker 로그
docker-compose logs -f backend
docker-compose logs -f scheduler

# Nginx 로그
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

#### 성능 모니터링

```python
# backend/api/app.py에 추가
from flask import request
import time
import logging

@app.before_request
def log_request():
    request.start_time = time.time()

@app.after_request
def log_response(response):
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time
        logging.info(f"{request.method} {request.path} - {response.status_code} - {duration:.3f}s")
    return response
```

---

### 8. 보안

#### HTTPS (Let's Encrypt)

```bash
# Certbot 설치
sudo apt-get install certbot python3-certbot-nginx -y

# SSL 인증서 발급
sudo certbot --nginx -d yourdomain.com

# 자동 갱신
sudo crontab -e
# 추가: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### API Rate Limiting

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/predict', methods=['POST'])
@limiter.limit("10 per minute")
def predict_match():
    # ...
```

---

### 9. 백업

#### 데이터베이스 백업

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# PostgreSQL 백업
pg_dump -U soccer_user soccer_predictor > $BACKUP_DIR/db_backup_$DATE.sql

# S3 업로드
aws s3 cp $BACKUP_DIR/db_backup_$DATE.sql s3://soccer-predictor-backups/

# 7일 이상 된 백업 삭제
find $BACKUP_DIR -type f -mtime +7 -delete

# Crontab: 0 2 * * * /path/to/backup.sh
```

---

### 10. 실행 명령어

#### 로컬 개발
```bash
# 백엔드
source venv/bin/activate
python backend/api/app.py

# 프론트엔드
cd frontend/epl-predictor
npm start
```

#### 프로덕션 (Docker)
```bash
# 전체 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 중지
docker-compose down

# 재빌드
docker-compose up -d --build
```

---

## 체크리스트

- [ ] 환경 변수 설정
- [ ] PostgreSQL 설정
- [ ] Docker 이미지 빌드
- [ ] Nginx 설정
- [ ] SSL 인증서 설치
- [ ] Rate Limiting 설정
- [ ] 백업 스크립트 설정
- [ ] 모니터링 설정
- [ ] CI/CD 파이프라인 설정
- [ ] 도메인 연결
- [ ] 성능 테스트
- [ ] 보안 감사

---

**배포 담당자:** DevOps Team
**최종 업데이트:** 2025-10-01
