# EPL Match Predictor v2.0 - GCP 마이그레이션 리포트

**작성일**: 2025년 10월 16일
**프로젝트**: EPL Match Predictor v2.0
**목적**: 소규모 베타 테스트를 위한 GCP 클라우드 마이그레이션 연습

---

## 📋 목차

1. [프로젝트 개요](#프로젝트-개요)
2. [마이그레이션 진행 과정](#마이그레이션-진행-과정)
3. [기술 스택 및 아키텍처](#기술-스택-및-아키텍처)
4. [발생한 문제 및 해결](#발생한-문제-및-해결)
5. [비용 분석](#비용-분석)
6. [재배포 가이드](#재배포-가이드)
7. [유지보수 가이드](#유지보수-가이드)
8. [교훈 및 개선점](#교훈-및-개선점)

---

## 프로젝트 개요

### 서비스 설명

**EPL Match Predictor v2.0**은 사용자가 직접 선수와 팀의 능력치를 측정하고, 해당 도메인 지식을 기반으로 프리미어리그 경기 결과를 예측하는 플랫폼입니다.

**핵심 특징**:
- 사용자 중심 선수 평가 시스템 (0-5 점수)
- 포지션별 가중치 기반 선수 능력치 계산
- 사용자 도메인 지식 기반 매치 시뮬레이션
- AI 시뮬레이션 보조 기능

### 마이그레이션 목표

1. ✅ **로컬 환경 → GCP 클라우드** 전환
2. ✅ **SQLite → PostgreSQL** 데이터베이스 마이그레이션
3. ✅ **자동화된 배포 스크립트** 구축
4. ✅ **비용 효율적인 인프라** 설계
5. ✅ **재배포 가능한 구조** 확립

---

## 마이그레이션 진행 과정

### Phase 1: 로컬 PostgreSQL 환경 구축 (완료)

**진행 단계**:

1. **Docker 환경 설정**
   ```bash
   # docker-compose.dev.yml 생성
   # PostgreSQL 14-alpine 컨테이너 설정
   # 포트: 5432, DB: epl_predictor
   ```

2. **데이터베이스 마이그레이션 스크립트 작성**
   - 파일: `scripts/migrate_sqlite_to_postgres.py`
   - SQLite → PostgreSQL 자동 마이그레이션
   - 스키마 변환 및 데이터 타입 조정

3. **스키마 수정 사항**
   - `VARCHAR(10)` → `VARCHAR(50)` (position, nationality)
   - `INTEGER` → `BIGINT` (id 컬럼, FPL ID 지원)
   - Foreign Key 관계 유지 (원본 ID 보존)

4. **마이그레이션 결과**
   - Teams: 20개
   - Players: 840명
   - Player Ratings: 26→38개 (테스트 중 증가)
   - Position Attributes: 완전 마이그레이션

**소요 시간**: 약 2시간

---

### Phase 2: GCP 프로젝트 설정 (완료)

**진행 단계**:

1. **GCP 프로젝트 생성**
   - 프로젝트 ID: `epl-predictor-2025`
   - 리전: `asia-northeast3` (서울)
   - Billing 계정 연결

2. **필수 API 활성화**
   ```
   ✅ Cloud Run API
   ✅ Cloud SQL Admin API
   ✅ Cloud Storage API
   ✅ Artifact Registry API
   ✅ Compute Engine API
   ✅ Cloud Build API
   ```

3. **Artifact Registry 생성**
   - 저장소명: `epl-docker-repo`
   - 형식: Docker
   - 위치: asia-northeast3

**소요 시간**: 10분

---

### Phase 3: Cloud SQL 구축 및 데이터 마이그레이션 (완료)

**진행 단계**:

1. **Cloud SQL 인스턴스 생성**
   - 버전: PostgreSQL 14
   - 티어: db-f1-micro (0.6GB RAM)
   - 스토리지: 10GB SSD (자동 증가)
   - 백업: 일일 03:00
   - 생성 시간: 약 5분

2. **데이터베이스 및 사용자 생성**
   ```sql
   Database: epl_predictor
   User: postgres, epl_user
   Password: [자동 생성 25자]
   ```

3. **데이터 마이그레이션**
   - 로컬 PostgreSQL → pg_dump
   - 백업 파일 → Cloud Storage
   - Cloud Storage → Cloud SQL import
   - 검증: 840 players 일치 확인

**발생한 문제**:
- Cloud SQL Proxy 인증 문제 → gcloud sql export/import 사용
- 서비스 계정 권한 문제 → IAM 권한 추가

**소요 시간**: 30분 (문제 해결 포함)

---

### Phase 4: Backend Docker 빌드 및 Cloud Run 배포 (완료)

**진행 단계**:

1. **Dockerfile 작성**
   - Base Image: `python:3.11-slim`
   - 의존성: requirements.txt + gunicorn 추가
   - Port: 8080 (Cloud Run 표준)
   - Healthcheck: `/api/health`

2. **Docker 이미지 빌드**
   - Platform: `linux/amd64` (Cloud Run 요구사항)
   - 태그: `asia-northeast3-docker.pkg.dev/epl-predictor-2025/epl-docker-repo/backend:latest`
   - 빌드 시간: 약 8분

3. **Cloud Run 배포**
   ```bash
   Service: epl-predictor-backend
   Region: asia-northeast3
   CPU: 1
   Memory: 512Mi
   Min instances: 0 (비용 절감)
   Max instances: 10
   Timeout: 60s
   ```

4. **환경 변수 설정**
   ```
   FLASK_ENV=production
   DATABASE_URL=postgresql://postgres:***@/epl_predictor?host=/cloudsql/...
   ```

5. **Cloud SQL 연결**
   - Unix socket 방식: `/cloudsql/[CONNECTION_NAME]`
   - IAM 권한: Cloud SQL Client

**발생한 문제**:
- ARM64 아키텍처 이미지 빌드 → `--platform linux/amd64` 추가
- 첫 빌드 실패 → 재빌드 및 푸시 성공

**배포 결과**:
- URL: `https://epl-predictor-backend-481906190891.asia-northeast3.run.app`
- Health check: ✅ 성공
- API 테스트: ✅ 20개 팀 데이터 반환

**소요 시간**: 1시간 (문제 해결 포함)

---

### Phase 5: Frontend 빌드 및 Cloud Storage 배포 (완료)

**진행 단계**:

1. **Production 환경 변수 설정**
   - 파일: `frontend/.env.production`
   - Backend URL 자동 주입
   - `package.json`에 `"homepage": "."` 추가 (상대 경로)

2. **Frontend 빌드**
   ```bash
   npm run build
   빌드 크기: 4.3MB (gzip 후)
   JS: 191.39 kB
   CSS: 16.02 kB
   ```

3. **Cloud Storage 버킷 생성**
   - 버킷명: `epl-predictor-2025-frontend`
   - 위치: asia-northeast3
   - 공개 읽기 설정

4. **파일 업로드**
   - `gsutil rsync` 사용
   - Cache-Control 설정
   - 총 21개 파일 업로드

**발생한 문제**:
- Cloud Storage 직접 링크로 접속 시 흰 화면
- 원인: React SPA는 Load Balancer 필요
- 해결: Load Balancer + CDN 구성 (하단 참조)

**소요 시간**: 30분

---

### Phase 6: Load Balancer + CDN 구성 (완료 후 삭제)

**진행 단계**:

1. **Backend Bucket 생성**
   - Cloud Storage 버킷을 Load Balancer에 연결
   - CDN 활성화

2. **URL Map 및 HTTP Proxy 생성**
   - 모든 요청을 Backend Bucket으로 라우팅

3. **Global IP 및 Forwarding Rule**
   - IP: 34.49.202.56
   - Port: 80 (HTTP)

**결과**:
- Load Balancer 준비 시간: 5-10분
- CDN 글로벌 배포

**소요 시간**: 15분

---

### Phase 7: 비용 절감을 위한 리소스 삭제 (완료)

**삭제 이유**: 베타 테스트 전까지 유지 비용($43-53/월) 절감

**삭제한 리소스**:

1. ✅ Load Balancer (절감: $18/월)
   - Forwarding rule
   - HTTP proxy
   - URL map
   - Backend bucket
   - Global IP

2. ✅ Cloud SQL (절감: $25-35/월)
   - 데이터는 로컬 PostgreSQL에 백업 완료

3. ✅ Cloud Run (절감: $0-10/월)
   - 컨테이너 이미지는 Artifact Registry에 보관

4. ✅ Cloud Storage (절감: $0.20/월)
   - Frontend 빌드 파일은 로컬 보관

**유지한 리소스**:
- ⚠️ Artifact Registry: Docker 이미지 보관 (비용: $0.10/월)
  - 재배포 시 빌드 시간 단축

**최종 비용**: **$0.10/월** (거의 무료)

**소요 시간**: 10분

---

## 기술 스택 및 아키텍처

### 로컬 개발 환경

```
┌─────────────────────────────────────────┐
│        Local Development Stack          │
├─────────────────────────────────────────┤
│ Frontend: React 19 + Tailwind CSS       │
│   - Port: 3000                          │
│   - Build: Create React App             │
├─────────────────────────────────────────┤
│ Backend: Flask 3.0 + SQLAlchemy         │
│   - Port: 5001                          │
│   - WSGI: Development server            │
├─────────────────────────────────────────┤
│ Database: PostgreSQL 14 (Docker)        │
│   - Port: 5432                          │
│   - Container: epl_postgres_dev         │
└─────────────────────────────────────────┘
```

### GCP 클라우드 아키텍처 (배포 시)

```
┌────────────────────────────────────────────────────────┐
│                      Internet                          │
└────────────────┬───────────────────┬───────────────────┘
                 │                   │
         ┌───────▼───────┐   ┌──────▼──────┐
         │ Load Balancer │   │ Cloud Run   │
         │   + CDN       │   │  Backend    │
         │ (Frontend)    │   │             │
         └───────┬───────┘   └──────┬──────┘
                 │                   │
         ┌───────▼───────┐   ┌──────▼──────┐
         │ Cloud Storage │   │  Cloud SQL  │
         │   (Static)    │   │ PostgreSQL  │
         └───────────────┘   └─────────────┘
                                     │
                             ┌───────▼───────┐
                             │ Artifact Reg. │
                             │ (Docker Image)│
                             └───────────────┘
```

### 데이터베이스 스키마

```sql
-- Teams Table
CREATE TABLE teams (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    short_name VARCHAR(50),
    stadium VARCHAR(255),
    manager VARCHAR(255),
    founded INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Players Table
CREATE TABLE players (
    id BIGSERIAL PRIMARY KEY,
    team_id BIGINT NOT NULL REFERENCES teams(id),
    name VARCHAR(255) NOT NULL,
    position VARCHAR(50) NOT NULL,
    detailed_position VARCHAR(50),
    number INTEGER,
    age INTEGER,
    nationality VARCHAR(50),
    height VARCHAR(50),
    foot VARCHAR(50),
    market_value VARCHAR(100),
    contract_until VARCHAR(50),
    appearances INTEGER DEFAULT 0,
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    photo_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Player Ratings Table (핵심!)
CREATE TABLE player_ratings (
    id BIGSERIAL PRIMARY KEY,
    player_id BIGINT NOT NULL REFERENCES players(id),
    user_id VARCHAR(255) DEFAULT 'default' NOT NULL,
    attribute_name VARCHAR(100) NOT NULL,
    rating DECIMAL(3, 2) NOT NULL CHECK (rating >= 0 AND rating <= 5),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (player_id, user_id, attribute_name)
);

-- Position Attributes Table
CREATE TABLE position_attributes (
    id BIGSERIAL PRIMARY KEY,
    position VARCHAR(10) NOT NULL,
    attribute_name VARCHAR(100) NOT NULL,
    attribute_name_ko VARCHAR(100),
    attribute_name_en VARCHAR(100),
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (position, attribute_name)
);

-- Indexes (성능 최적화)
CREATE INDEX idx_players_team_id ON players(team_id);
CREATE INDEX idx_player_ratings_player_id ON player_ratings(player_id);
CREATE INDEX idx_player_ratings_user_id ON player_ratings(user_id);
```

---

## 발생한 문제 및 해결

### 1. Docker Compose 명령어 호환성

**문제**: `docker-compose: command not found`

**원인**: Docker Desktop 최신 버전은 `docker compose` (하이픈 없음) 사용

**해결**:
```bash
# 기존
docker-compose -f docker-compose.dev.yml up -d

# 수정
docker compose -f docker-compose.dev.yml up -d
```

---

### 2. PostgreSQL VARCHAR 길이 부족

**문제**:
```
psycopg2.errors.StringDataRightTruncation:
value too long for type character varying(10)
```

**원인**: `position`, `nationality` 필드가 VARCHAR(10)으로 설정되어 있었으나, 실제 데이터가 더 긴 경우 존재

**해결**:
```python
# 마이그레이션 스크립트 수정
position VARCHAR(50) NOT NULL,  # 10 → 50
nationality VARCHAR(50),         # 10 → 50
```

---

### 3. Foreign Key 제약 조건 위반

**문제**:
```
Key (player_id)=(67776) is not present in table "players"
```

**원인**: PostgreSQL이 ID를 자동 증가시켜 원본 ID와 불일치

**해결**:
```python
# players, teams 테이블은 원본 ID 유지
if table_name not in ['players', 'teams'] and 'id' in row_dict:
    del row_dict['id']  # 다른 테이블만 ID 삭제
```

---

### 4. Integer 범위 초과

**문제**:
```
psycopg2.errors.NumericValueOutOfRange: integer out of range
```

**원인**: FPL Player ID (예: 10000000737)가 INTEGER 최댓값 초과

**해결**:
```sql
-- SERIAL → BIGSERIAL 변경
id BIGSERIAL PRIMARY KEY,
team_id BIGINT NOT NULL REFERENCES teams(id),
```

---

### 5. Rating 저장 실패

**문제**: Frontend에서 선수 평가 저장 시 "Missing ratings data" 에러

**원인**: Backend가 여전히 SQLite 연결 사용 (환경 변수 미설정)

**해결**:
```bash
# 기존 프로세스 종료
kill 13721 82128

# DATABASE_URL 환경 변수 설정하여 재시작
export DATABASE_URL="postgresql://..."
python api/app.py
```

---

### 6. Frontend 페이지 전환 속도 저하

**문제**: 화면 전환이 매우 느림

**원인**: 모든 페이지 컴포넌트가 항상 마운트되어 있고, CSS opacity로만 숨김

**해결**:
```javascript
// 기존: 모든 페이지 항상 마운트
<div className={opacity-0}>
  <EPLDashboard />
</div>

// 수정: 조건부 렌더링
{currentPage === 'dashboard' && <EPLDashboard />}
{currentPage === 'ratings' && <PlayerRatingManager />}
```

---

### 7. Rating 표시 불일치 (3.8 vs 3.95)

**문제**: 카드에는 3.8, 상세 페이지에는 3.95 표시

**원인**:
- SquadBuilder: 단순 평균 + `.toFixed(1)`
- 다른 컴포넌트: 가중 평균 + `.toFixed(2)`

**해결**:
```javascript
// SquadBuilder.js 수정
import { calculateWeightedAverage, DEFAULT_SUB_POSITION } from '../config/positionAttributes';

const weightedAverage = calculateWeightedAverage(savedRatings, subPosition);
return weightedAverage.toFixed(2);  // 소수점 2자리 통일
```

---

### 8. 미평가 선수 기본값 누락

**문제**: 평가하지 않은 선수의 카드가 공란으로 표시

**해결**:
```javascript
// 기본값 2.5 반환
if (!savedRatings || Object.keys(savedRatings).length === 0) {
  return 2.5;  // null → 2.5
}
```

---

### 9. Docker Image 아키텍처 불일치

**문제**:
```
Container manifest type must support amd64/linux
```

**원인**: M 시리즈 Mac에서 ARM64 이미지 빌드, Cloud Run은 amd64 요구

**해결**:
```bash
# ARM64 → amd64로 재빌드
docker build --platform linux/amd64 -t [IMAGE_TAG] .
```

---

### 10. React SPA 흰 화면 (Cloud Storage)

**문제**: Cloud Storage 직접 링크 접속 시 흰 화면

**원인**:
1. 절대 경로 (`/static/js/...`) 참조
2. Cloud Storage는 index.html fallback 미지원

**해결 1**: `package.json`에 `"homepage": "."` 추가 (상대 경로)

**해결 2**: Load Balancer 구성
```bash
# Backend bucket 생성 → URL map → HTTP proxy → Global IP
# 모든 요청을 index.html로 라우팅
```

---

## 비용 분석

### 시간당/월간 비용 상세

| 리소스 | 스펙 | 유휴 비용 | 사용 비용 (100명/월) |
|--------|------|-----------|---------------------|
| **Cloud SQL** | db-f1-micro, 10GB | $25-35/월 | $25-35/월 |
| **Cloud Run** | 512Mi, 1 CPU, min=0 | $0/월 | $5-10/월 |
| **Cloud Storage** | 4.3MB | $0.02/월 | $1-2/월 |
| **Load Balancer** | HTTP(S) LB + CDN | $18/월 | $20-25/월 |
| **Artifact Registry** | Docker images | $0.10/월 | $0.10/월 |
| **네트워크 송신** | - | $0 | $5-10/월 |

### 시나리오별 비용

#### 시나리오 1: 리소스 유지 (사용자 0명)
```
Cloud SQL:          $30/월
Load Balancer:      $18/월
Cloud Storage:      $0.02/월
Artifact Registry:  $0.10/월
────────────────────────────
총 비용:            $48.12/월
```

#### 시나리오 2: 베타 테스트 (100명/월)
```
Cloud SQL:          $30/월
Cloud Run:          $7/월
Cloud Storage:      $1/월
Load Balancer:      $22/월
Artifact Registry:  $0.10/월
네트워크:           $7/월
────────────────────────────
총 비용:            $67.10/월
```

#### 시나리오 3: 현재 상태 (리소스 삭제)
```
Artifact Registry:  $0.10/월
────────────────────────────
총 비용:            $0.10/월
```

### 비용 절감 전략

1. **Cloud SQL**
   - ✅ 사용하지 않을 때 삭제
   - ❌ 정지 불가 (삭제만 가능)
   - 💡 재생성 시간: 5분

2. **Cloud Run**
   - ✅ `min-instances=0` 설정 (자동 절감)
   - 요청 없으면 비용 $0

3. **Load Balancer**
   - ⚠️ 시간당 과금 ($0.025/시간 = $18/월)
   - 💡 사용하지 않을 때 삭제 권장

4. **재배포 시간 최소화**
   - Docker 이미지 유지 (Artifact Registry)
   - 배포 스크립트 자동화 → 30분 내 재배포

---

## 재배포 가이드

### 사전 준비 사항

1. **GCP 인증**
   ```bash
   gcloud auth login
   gcloud config set project epl-predictor-2025
   ```

2. **로컬 데이터 확인**
   ```bash
   # 로컬 PostgreSQL 실행
   docker compose -f docker-compose.dev.yml up -d postgres

   # 데이터 확인
   docker exec epl_postgres_dev psql -U epl_user -d epl_predictor -c \
     "SELECT COUNT(*) FROM teams, COUNT(*) FROM players;"
   ```

---

### 방법 1: 자동 전체 배포 (권장)

**실행 시간**: 30-40분

```bash
cd /Users/stlee/Desktop/EPL-Match-Predictor

# 한 번에 전체 배포
./scripts/gcp-deploy-all.sh
```

**진행 과정**:
1. GCP 프로젝트 설정 확인
2. Cloud SQL 생성 (5-10분)
3. 로컬 데이터 → Cloud SQL 마이그레이션
4. Backend Docker 빌드 및 Cloud Run 배포 (10-15분)
5. Frontend 빌드 및 Cloud Storage 배포
6. Load Balancer + CDN 구성 (선택적)

**입력 필요 항목**:
- 프로젝트 ID 확인 (기본값: epl-predictor-2025)
- 리전 선택 (기본값: asia-northeast3 서울)
- Load Balancer 설정 여부 (Yes/No)

---

### 방법 2: 단계별 배포

각 단계를 개별적으로 실행하여 진행 상황 확인 가능

#### Day 1: GCP 프로젝트 설정 (5분)

```bash
./scripts/gcp-deploy-day1.sh
```

**수행 내용**:
- GCP 프로젝트 생성/확인
- Billing 계정 연결
- 필수 API 활성화
- Artifact Registry 생성
- 설정 파일 생성 (`scripts/.gcp-config`)

#### Day 2: Cloud SQL 생성 및 데이터 마이그레이션 (15-20분)

```bash
./scripts/gcp-deploy-day2.sh
```

**수행 내용**:
- Cloud SQL PostgreSQL 인스턴스 생성 (5-10분)
- 데이터베이스 및 사용자 생성
- Cloud SQL Proxy 설치
- 로컬 PostgreSQL 데이터 백업
- Cloud SQL로 데이터 import
- 마이그레이션 검증

**대기 시간**: Cloud SQL 생성 시 5-10분 소요

#### Day 3: Backend 배포 (15-20분)

```bash
./scripts/gcp-deploy-day3.sh
```

**수행 내용**:
- Docker 이미지 빌드 (amd64 아키텍처)
- Artifact Registry에 이미지 푸시
- Cloud Run 서비스 배포
- 환경 변수 설정 (DATABASE_URL 등)
- Cloud SQL 연결 설정
- Health check 및 API 테스트

**배포 결과**:
```
Backend URL: https://epl-predictor-backend-[HASH].asia-northeast3.run.app
```

#### Day 4: Frontend 배포 (10-15분)

```bash
./scripts/gcp-deploy-day4.sh
```

**수행 내용**:
- `.env.production` 파일 생성 (Backend URL 주입)
- Frontend Production 빌드
- Cloud Storage 버킷 생성
- 빌드 파일 업로드
- Cache-Control 설정
- Load Balancer + CDN 구성 (선택)

**배포 결과**:
```
# Load Balancer 사용 시
Frontend URL: http://[GLOBAL_IP]

# Cloud Storage 직접 링크 (권장하지 않음)
Frontend URL: https://storage.googleapis.com/[BUCKET]/index.html
```

---

### 배포 검증

#### 1. Backend 확인

```bash
# Health check
curl https://epl-predictor-backend-[HASH].asia-northeast3.run.app/api/health

# 예상 응답:
# {
#   "service": "EPL Player Analysis API",
#   "status": "healthy",
#   "version": "2.0.0"
# }

# Teams API
curl https://epl-predictor-backend-[HASH].asia-northeast3.run.app/api/teams

# 예상 응답: 20개 팀 데이터
```

#### 2. Frontend 확인

```bash
# Load Balancer 준비 대기 (5-10분)
# 브라우저에서 접속
http://[GLOBAL_IP]
```

**확인 사항**:
- ✅ 로고 및 레이아웃 정상 표시
- ✅ 팀 목록 로드
- ✅ 선수 목록 로드
- ✅ 선수 평가 저장/불러오기
- ✅ 페이지 전환 속도

#### 3. Database 확인

```bash
# Cloud SQL 데이터 확인
gcloud sql connect epl-db-prod --user=postgres --database=epl_predictor

# SQL 실행
SELECT COUNT(*) FROM teams;    -- 20
SELECT COUNT(*) FROM players;  -- 840
SELECT COUNT(*) FROM player_ratings;  -- 사용자 평가 수
```

---

### 문제 발생 시 트러블슈팅

#### Backend 배포 실패

**증상**: Cloud Run 배포 시 에러

**확인 사항**:
1. Docker 이미지 아키텍처 확인
   ```bash
   # amd64로 재빌드
   cd backend
   docker build --platform linux/amd64 -t [IMAGE_TAG] .
   docker push [IMAGE_TAG]
   ```

2. Cloud Run 로그 확인
   ```bash
   gcloud run logs read epl-predictor-backend \
     --region=asia-northeast3 --limit=50
   ```

3. DATABASE_URL 환경 변수 확인
   ```bash
   gcloud run services describe epl-predictor-backend \
     --region=asia-northeast3 --format="value(spec.template.spec.containers[0].env)"
   ```

#### Frontend 흰 화면

**증상**: 브라우저에서 빈 화면만 표시

**해결**:
1. 브라우저 개발자 도구 확인 (F12 → Console)
2. Load Balancer 생성 여부 확인
3. 강력 새로고침 (Ctrl+Shift+R / Cmd+Shift+R)
4. 시크릿 모드로 접속

#### Cloud SQL 연결 실패

**증상**: Backend에서 "Connection refused"

**확인 사항**:
1. Cloud SQL 인스턴스 상태
   ```bash
   gcloud sql instances describe epl-db-prod
   ```

2. Cloud Run 서비스 계정 권한
   ```bash
   # Cloud SQL Client 역할 확인
   gcloud projects get-iam-policy epl-predictor-2025 \
     --flatten="bindings[].members" \
     --filter="bindings.role:roles/cloudsql.client"
   ```

3. CONNECTION_NAME 확인
   ```bash
   # 형식: PROJECT_ID:REGION:INSTANCE_NAME
   epl-predictor-2025:asia-northeast3:epl-db-prod
   ```

---

## 유지보수 가이드

### 일상적인 모니터링

#### 1. 비용 모니터링

**GCP 콘솔 확인**:
```
https://console.cloud.google.com/billing?project=epl-predictor-2025
```

**주요 확인 사항**:
- 일일 비용 추이
- 예상 월 비용
- 리소스별 비용 분포

**알림 설정**:
```bash
# 월 $100 초과 시 이메일 알림 설정
gcloud billing budgets create \
  --billing-account=[BILLING_ACCOUNT_ID] \
  --display-name="EPL Predictor Budget" \
  --budget-amount=100 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100
```

#### 2. 서비스 상태 확인

**Cloud Run**:
```bash
# 서비스 상태
gcloud run services describe epl-predictor-backend \
  --region=asia-northeast3

# 최근 로그 (에러만)
gcloud run logs read epl-predictor-backend \
  --region=asia-northeast3 \
  --limit=50 \
  --log-filter="severity>=ERROR"
```

**Cloud SQL**:
```bash
# 인스턴스 상태
gcloud sql instances describe epl-db-prod

# 연결 수 확인
gcloud sql operations list --instance=epl-db-prod
```

#### 3. 데이터 백업

**자동 백업**:
- Cloud SQL 자동 백업: 매일 03:00 (설정됨)
- 보관 기간: 7일

**수동 백업**:
```bash
# Cloud SQL 백업 생성
gcloud sql backups create --instance=epl-db-prod

# 백업 목록 확인
gcloud sql backups list --instance=epl-db-prod

# 백업 복원
gcloud sql backups restore [BACKUP_ID] \
  --backup-instance=epl-db-prod \
  --backup-id=[BACKUP_ID]
```

**로컬 백업** (권장):
```bash
# Cloud SQL → 로컬 백업
gcloud sql export sql epl-db-prod \
  gs://[BACKUP_BUCKET]/backup_$(date +%Y%m%d).sql \
  --database=epl_predictor

# Cloud Storage → 로컬 다운로드
gsutil cp gs://[BACKUP_BUCKET]/backup_*.sql ./backups/
```

---

### 업데이트 및 배포

#### Backend 코드 업데이트

```bash
# 1. 로컬에서 테스트
cd backend
python api/app.py

# 2. Docker 이미지 빌드
docker build --platform linux/amd64 \
  -t asia-northeast3-docker.pkg.dev/epl-predictor-2025/epl-docker-repo/backend:latest .

# 3. 푸시
docker push asia-northeast3-docker.pkg.dev/epl-predictor-2025/epl-docker-repo/backend:latest

# 4. Cloud Run 재배포
gcloud run deploy epl-predictor-backend \
  --image=asia-northeast3-docker.pkg.dev/epl-predictor-2025/epl-docker-repo/backend:latest \
  --region=asia-northeast3
```

#### Frontend 코드 업데이트

```bash
# 1. 빌드
cd frontend
npm run build

# 2. Cloud Storage 업로드
gsutil -m rsync -r -d build gs://[BUCKET_NAME]

# 3. 캐시 무효화 (Load Balancer 사용 시)
gcloud compute url-maps invalidate-cdn-cache [URL_MAP_NAME] \
  --path="/*"
```

---

### 스케일링

#### Cloud Run 자동 스케일링 조정

```bash
# 최대 인스턴스 증가 (트래픽 증가 시)
gcloud run services update epl-predictor-backend \
  --region=asia-northeast3 \
  --max-instances=50

# 최소 인스턴스 설정 (콜드 스타트 방지)
gcloud run services update epl-predictor-backend \
  --region=asia-northeast3 \
  --min-instances=1  # 비용 증가: $5-10/월
```

#### Cloud SQL 스케일업

```bash
# 더 큰 인스턴스로 변경
gcloud sql instances patch epl-db-prod \
  --tier=db-g1-small  # 1.7GB RAM

# 스토리지 증가
gcloud sql instances patch epl-db-prod \
  --storage-size=20GB
```

---

### 보안 관리

#### 1. 비밀번호 변경

**Cloud SQL 비밀번호**:
```bash
# postgres 사용자 비밀번호 변경
gcloud sql users set-password postgres \
  --instance=epl-db-prod \
  --password=[NEW_PASSWORD]

# Backend 환경 변수 업데이트
gcloud run services update epl-predictor-backend \
  --region=asia-northeast3 \
  --update-env-vars="DATABASE_URL=postgresql://postgres:[NEW_PASSWORD]@/..."
```

#### 2. IAM 권한 검토

```bash
# 프로젝트 IAM 정책 확인
gcloud projects get-iam-policy epl-predictor-2025

# Cloud Run 서비스 계정 확인
gcloud run services get-iam-policy epl-predictor-backend \
  --region=asia-northeast3
```

#### 3. API 보안

- ✅ Cloud Run `--no-allow-unauthenticated` (인증 필요 시)
- ✅ CORS 설정 확인 (Flask-CORS)
- ✅ Rate Limiting (Cloud Armor 사용 시)

---

### 비용 최적화

#### 사용하지 않을 때 리소스 삭제

```bash
# 모든 리소스 삭제 (비용 $0.10/월)
# 주의: 데이터 백업 확인 후 실행!

# 1. Cloud Run 삭제
gcloud run services delete epl-predictor-backend \
  --region=asia-northeast3 --quiet

# 2. Cloud SQL 삭제
gcloud sql instances delete epl-db-prod --quiet

# 3. Cloud Storage 삭제
gsutil -m rm -r gs://[BUCKET_NAME]

# 4. Load Balancer 삭제
gcloud compute forwarding-rules delete [RULE_NAME] --global --quiet
gcloud compute target-http-proxies delete [PROXY_NAME] --quiet
gcloud compute url-maps delete [URL_MAP_NAME] --quiet
gcloud compute backend-buckets delete [BACKEND_BUCKET] --quiet
gcloud compute addresses delete [IP_NAME] --global --quiet
```

#### 재배포

```bash
# 30분 내 전체 재배포
./scripts/gcp-deploy-all.sh
```

---

## 교훈 및 개선점

### 성공 요인

1. ✅ **체계적인 단계별 접근**
   - 로컬 환경 → GCP 순차적 마이그레이션
   - 각 단계별 검증 및 테스트

2. ✅ **자동화 스크립트 구축**
   - Day 1-4 스크립트로 재배포 시간 단축
   - 수동 작업 최소화

3. ✅ **비용 효율적 설계**
   - Cloud Run min-instances=0
   - 사용하지 않을 때 리소스 삭제
   - 월 $0.10 유지 비용

4. ✅ **데이터 무결성 보장**
   - 로컬 PostgreSQL 백업 유지
   - Foreign Key 관계 보존
   - 마이그레이션 검증 절차

5. ✅ **문제 해결 역량**
   - Docker 아키텍처 불일치 해결
   - Frontend 성능 최적화
   - Rating 계산 로직 통일

---

### 개선이 필요한 부분

#### 1. HTTPS 적용

**현재**: HTTP만 지원

**개선 방법**:
```bash
# Cloud Load Balancer SSL 인증서 생성
gcloud compute ssl-certificates create epl-cert \
  --domains=[YOUR_DOMAIN]

# HTTPS Target Proxy 생성
gcloud compute target-https-proxies create epl-https-proxy \
  --url-map=[URL_MAP] \
  --ssl-certificates=epl-cert
```

**필요 사항**: 커스텀 도메인 (Google Domains, Cloudflare 등)

#### 2. 커스텀 도메인 연결

**예시**: `epl-predictor.com`

**절차**:
1. 도메인 구매 (Google Domains, Namecheap 등)
2. Cloud DNS 설정
3. Load Balancer에 도메인 연결
4. SSL 인증서 발급

**비용**: 도메인 $12/년 + Cloud DNS $0.20/월

#### 3. CI/CD 파이프라인

**현재**: 수동 빌드 및 배포

**개선 방안**:
```yaml
# .github/workflows/deploy.yml (GitHub Actions)
name: Deploy to GCP
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build and Deploy
        run: |
          docker build --platform linux/amd64 -t [IMAGE] .
          docker push [IMAGE]
          gcloud run deploy ...
```

**대안**: Cloud Build
```bash
gcloud builds submit --config cloudbuild.yaml
```

#### 4. 모니터링 및 로깅

**현재**: 수동 로그 확인

**개선 방안**:
- Cloud Monitoring 대시보드 구성
- Slack/Email 알림 설정
- Error Tracking (Sentry, Cloud Error Reporting)

```bash
# Cloud Monitoring 알림 정책 생성
gcloud alpha monitoring policies create \
  --notification-channels=[CHANNEL_ID] \
  --display-name="High Error Rate" \
  --condition-display-name="Error Rate > 5%" \
  --condition-threshold-value=0.05
```

#### 5. 데이터베이스 성능 최적화

**현재**: 기본 인덱스만 사용

**개선 방안**:
```sql
-- 복합 인덱스 추가
CREATE INDEX idx_player_ratings_user_player
  ON player_ratings(user_id, player_id);

-- 쿼리 성능 분석
EXPLAIN ANALYZE SELECT ...;

-- Connection Pooling (PgBouncer)
```

#### 6. CDN 및 캐싱 전략

**현재**: 기본 CDN 설정

**개선 방안**:
- Static 파일 Cache-Control 최적화
- API 응답 캐싱 (Redis)
- Cloud CDN 규칙 세밀화

```bash
# Redis Memorystore 추가
gcloud redis instances create epl-cache \
  --size=1 \
  --region=asia-northeast3 \
  --tier=basic
```

**비용**: $25/월 추가 (1GB Basic)

---

### 배운 점

#### 기술적 측면

1. **GCP 서비스 간 연계**
   - Cloud Run ↔ Cloud SQL (Unix socket)
   - Cloud Storage ↔ Load Balancer (Backend bucket)
   - IAM 권한 관리의 중요성

2. **Docker 멀티 아키텍처 빌드**
   - M 시리즈 Mac에서 amd64 빌드 필요성
   - `--platform` 플래그 활용

3. **React SPA 배포**
   - Cloud Storage 직접 링크 한계
   - Load Balancer 필요성
   - `homepage: "."` 설정의 중요성

4. **PostgreSQL 마이그레이션**
   - 데이터 타입 호환성 확인 필수
   - Foreign Key 관계 유지 전략
   - ID 범위 고려 (BIGINT)

#### 비즈니스 측면

1. **비용 관리의 중요성**
   - 유휴 리소스 비용 인지 ($43-53/월)
   - 필요 시 삭제/재생성 전략
   - 자동화로 재배포 시간 단축

2. **스케일 단계별 접근**
   - 베타 테스트: 소규모 인프라
   - 정식 출시: 점진적 확장
   - 비용 vs 성능 트레이드오프

3. **문서화의 가치**
   - 재배포 시 참고 자료
   - 팀원 온보딩 자료
   - 문제 해결 노하우 축적

---

## 결론

### 마이그레이션 성과

✅ **완료된 작업**:
- 로컬 개발 환경 → GCP 클라우드 성공적 마이그레이션
- SQLite → PostgreSQL 데이터베이스 전환
- 840명 선수, 20개 팀, 38개 사용자 평가 데이터 무손실 이전
- 자동화된 재배포 스크립트 구축 (30분 내 전체 배포)
- 비용 최적화 ($0.10/월 유지 비용)

✅ **획득한 역량**:
- GCP 주요 서비스 활용 능력 (Cloud Run, Cloud SQL, Cloud Storage)
- Docker 컨테이너 기반 배포 경험
- PostgreSQL 마이그레이션 및 스키마 설계
- React SPA 클라우드 배포 노하우
- 비용 효율적인 인프라 설계

✅ **구축된 자산**:
- 재사용 가능한 배포 스크립트 (Day 1-4)
- 상세한 문서화 (본 리포트)
- 검증된 아키텍처 설계
- 문제 해결 노하우 축적

### 베타 테스트 준비도

**즉시 배포 가능**: ✅

**예상 소요 시간**: 30-40분 (자동화 스크립트 실행)

**예상 월 비용**: $60-85 (100명 기준)

**필요한 작업**:
1. `./scripts/gcp-deploy-all.sh` 실행
2. Frontend URL 공유
3. 사용자 피드백 수집
4. 모니터링 및 로그 확인

### 차기 단계 로드맵

#### Phase 1: 베타 테스트 (1-2개월)
- GCP 재배포
- 10-100명 사용자 초대
- 피드백 수집 및 버그 수정
- 성능 모니터링

#### Phase 2: 정식 출시 준비 (2-3개월)
- HTTPS 적용 (커스텀 도메인)
- CI/CD 파이프라인 구축
- 모니터링 및 알림 시스템 강화
- 데이터베이스 성능 최적화

#### Phase 3: 스케일링 (3-6개월)
- Cloud Run 인스턴스 증가
- Cloud SQL 업그레이드
- Redis 캐싱 도입
- CDN 최적화

#### Phase 4: 고도화 (6개월+)
- Multi-region 배포 (글로벌 서비스)
- AI 기능 강화
- 실시간 데이터 연동
- 모바일 앱 출시

---

## 부록

### A. 주요 파일 목록

#### 배포 스크립트
```
scripts/
├── gcp-deploy-day1.sh          # GCP 프로젝트 설정
├── gcp-deploy-day2.sh          # Cloud SQL 생성
├── gcp-deploy-day3.sh          # Backend 배포
├── gcp-deploy-day4.sh          # Frontend 배포
├── gcp-deploy-all.sh           # 전체 자동 배포
├── migrate_sqlite_to_postgres.py  # DB 마이그레이션
└── .gcp-config                 # GCP 설정 정보
```

#### 설정 파일
```
backend/
├── Dockerfile                  # Backend 컨테이너 설정
├── requirements.txt            # Python 의존성 (gunicorn 포함)
└── .env.dev                    # 로컬 개발 환경 변수

frontend/
├── package.json                # homepage: "." 설정
└── .env.production             # Production 환경 변수

docker-compose.dev.yml          # 로컬 PostgreSQL 설정
```

#### 문서
```
docs/
├── GCP-MIGRATION-REPORT.md     # 본 문서
└── GCP-DEPLOYMENT-GUIDE.md     # 간단한 배포 가이드
```

---

### B. 유용한 명령어 모음

#### GCP 일반

```bash
# 프로젝트 목록
gcloud projects list

# 프로젝트 설정
gcloud config set project epl-predictor-2025

# 활성화된 API 확인
gcloud services list --enabled

# 비용 확인
gcloud billing accounts list
gcloud billing projects describe epl-predictor-2025
```

#### Cloud Run

```bash
# 서비스 목록
gcloud run services list

# 서비스 상세
gcloud run services describe epl-predictor-backend --region=asia-northeast3

# 로그 확인
gcloud run logs read epl-predictor-backend --region=asia-northeast3 --limit=100

# 환경 변수 확인
gcloud run services describe epl-predictor-backend \
  --region=asia-northeast3 \
  --format="value(spec.template.spec.containers[0].env)"

# 재배포
gcloud run deploy epl-predictor-backend \
  --image=[IMAGE_URL] \
  --region=asia-northeast3
```

#### Cloud SQL

```bash
# 인스턴스 목록
gcloud sql instances list

# 인스턴스 상세
gcloud sql instances describe epl-db-prod

# 데이터베이스 연결
gcloud sql connect epl-db-prod --user=postgres --database=epl_predictor

# 백업 목록
gcloud sql backups list --instance=epl-db-prod

# 백업 생성
gcloud sql backups create --instance=epl-db-prod

# 데이터 export
gcloud sql export sql epl-db-prod gs://[BUCKET]/backup.sql --database=epl_predictor

# 데이터 import
gcloud sql import sql epl-db-prod gs://[BUCKET]/backup.sql --database=epl_predictor
```

#### Cloud Storage

```bash
# 버킷 목록
gsutil ls

# 버킷 생성
gsutil mb -p [PROJECT_ID] -c STANDARD -l [REGION] gs://[BUCKET_NAME]

# 파일 업로드
gsutil cp [FILE] gs://[BUCKET]/[PATH]

# 폴더 동기화
gsutil -m rsync -r -d [LOCAL_DIR] gs://[BUCKET]

# 버킷 삭제
gsutil -m rm -r gs://[BUCKET]

# 공개 설정
gsutil iam ch allUsers:objectViewer gs://[BUCKET]
```

#### Docker

```bash
# 이미지 빌드 (amd64)
docker build --platform linux/amd64 -t [IMAGE_TAG] .

# Artifact Registry 인증
gcloud auth configure-docker asia-northeast3-docker.pkg.dev

# 이미지 푸시
docker push [IMAGE_TAG]

# 이미지 목록
gcloud artifacts docker images list asia-northeast3-docker.pkg.dev/epl-predictor-2025/epl-docker-repo
```

---

### C. 참고 링크

#### GCP 공식 문서
- Cloud Run: https://cloud.google.com/run/docs
- Cloud SQL: https://cloud.google.com/sql/docs
- Cloud Storage: https://cloud.google.com/storage/docs
- Artifact Registry: https://cloud.google.com/artifact-registry/docs

#### GCP 콘솔
- 프로젝트 대시보드: https://console.cloud.google.com/home/dashboard?project=epl-predictor-2025
- Cloud Run: https://console.cloud.google.com/run?project=epl-predictor-2025
- Cloud SQL: https://console.cloud.google.com/sql?project=epl-predictor-2025
- Billing: https://console.cloud.google.com/billing?project=epl-predictor-2025

#### 가격 계산기
- GCP Pricing Calculator: https://cloud.google.com/products/calculator

---

### D. 연락처 및 지원

#### GCP 지원
- GCP Support: https://cloud.google.com/support
- GCP Community: https://www.googlecloudcommunity.com/

#### 프로젝트 리포지토리
- GitHub: (프로젝트 저장소 URL)
- 이슈 트래커: (GitHub Issues URL)

---

**문서 버전**: 1.0
**최종 업데이트**: 2025년 10월 16일
**작성자**: EPL Match Predictor 개발팀
**검토자**: -

---

© 2025 EPL Match Predictor. All rights reserved.
