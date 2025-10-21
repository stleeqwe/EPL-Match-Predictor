# EPL Match Predictor - GCP 배포 가이드

## 전제 조건

1. **GCP 계정** - https://cloud.google.com
2. **Billing 활성화** - 신용카드 등록 필요
3. **로컬 환경 준비**:
   - Docker Desktop 실행 중
   - PostgreSQL 로컬 데이터 있음 (migrate_sqlite_to_postgres.py 실행 완료)
   - gcloud CLI 설치

---

## gcloud CLI 설치 (최초 1회)

### macOS
```bash
brew install google-cloud-sdk
```

### Linux
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

### 인증
```bash
gcloud auth login
```

브라우저가 열리면 구글 계정으로 로그인하세요.

---

## 배포 방법

### 방법 1: 한 번에 전체 배포 (권장)

```bash
./scripts/gcp-deploy-all.sh
```

- 실행 시간: 30-40분
- 모든 단계 자동 진행
- 중간에 프롬프트 입력 필요 (프로젝트 ID, 리전 등)

---

### 방법 2: 단계별 배포

각 Day를 순차적으로 실행:

```bash
# Day 1: GCP 프로젝트 생성 및 API 활성화 (5분)
./scripts/gcp-deploy-day1.sh

# Day 2: Cloud SQL 생성 및 데이터 마이그레이션 (10-15분)
./scripts/gcp-deploy-day2.sh

# Day 3: Backend Docker 빌드 및 배포 (10-15분)
./scripts/gcp-deploy-day3.sh

# Day 4: Frontend 빌드 및 배포 (5-10분)
./scripts/gcp-deploy-day4.sh
```

---

## 배포 후 확인사항

### 1. Frontend 접속
```bash
source scripts/.gcp-config
echo $GCP_FRONTEND_URL
```

브라우저에서 URL 접속 → 선수 목록 확인

### 2. Backend API 테스트
```bash
curl $GCP_BACKEND_URL/api/teams
```

팀 목록 JSON 응답 확인

### 3. 모니터링 대시보드
- Cloud Run: https://console.cloud.google.com/run
- Cloud SQL: https://console.cloud.google.com/sql
- 비용: https://console.cloud.google.com/billing

---

## 예상 비용

### Phase 1: Lift & Shift
- **Cloud Run (Backend)**: $5-10/월
  - 100 users, 월 10,000 요청 가정
  - 최소 인스턴스 0 (serverless)

- **Cloud SQL (PostgreSQL)**: $25-35/월
  - db-f1-micro (0.6GB RAM)
  - 10GB SSD 스토리지

- **Cloud Storage (Frontend)**: $1-2/월
  - 정적 파일 호스팅
  - 월 1GB 트래픽 가정

- **Artifact Registry**: $0-1/월
  - Docker 이미지 저장소

**총 예상 비용: $42-62/월**

---

## 트러블슈팅

### gcloud 인증 오류
```bash
gcloud auth login
gcloud auth application-default login
```

### Docker 빌드 실패
```bash
# Docker Desktop이 실행 중인지 확인
docker ps
```

### Cloud SQL 접속 실패
```bash
# Cloud SQL Proxy 로그 확인
tail -f /tmp/cloud-sql-proxy.log

# Proxy 재시작
source scripts/.gcp-config
pkill -f cloud-sql-proxy
cloud-sql-proxy $CONNECTION_NAME --port 5433 &
```

### Backend 배포 실패
```bash
# Cloud Run 로그 확인
gcloud run logs read epl-predictor-backend --region=asia-northeast3 --limit=50
```

---

## 배포 중단 및 삭제

### 모든 리소스 삭제
```bash
source scripts/.gcp-config

# Cloud Run 삭제
gcloud run services delete $GCP_SERVICE_NAME --region=$GCP_REGION

# Cloud SQL 삭제
gcloud sql instances delete $GCP_DB_INSTANCE

# Cloud Storage 삭제
gsutil rm -r gs://$GCP_BUCKET_NAME

# 프로젝트 전체 삭제 (모든 리소스 완전 제거)
gcloud projects delete $GCP_PROJECT_ID
```

---

## 다음 단계 (Phase 2 - 선택적)

배포 후 안정화되면 다음 기능 추가 가능:

1. **커스텀 도메인 연결**
   - Cloud DNS + HTTPS 인증서

2. **Redis 캐싱**
   - Cloud Memorystore 추가

3. **CDN 활성화**
   - Load Balancer + Cloud CDN

4. **모니터링 강화**
   - Cloud Logging + Monitoring
   - Slack/Email 알림

5. **CI/CD 파이프라인**
   - Cloud Build 자동 배포

---

## 지원

- GCP 콘솔: https://console.cloud.google.com
- GCP 문서: https://cloud.google.com/docs
- 프로젝트 설정: `scripts/.gcp-config`
