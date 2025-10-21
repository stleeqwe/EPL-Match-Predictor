#!/bin/bash

# GCP 배포 Day 2: Cloud SQL 생성 및 데이터 마이그레이션
# 실행 전 요구사항: gcp-deploy-day1.sh 완료

set -e

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

echo "╔══════════════════════════════════════════════════════════╗"
echo "║   EPL Match Predictor - GCP 배포 Day 2                  ║"
echo "║   Cloud SQL 생성 및 데이터 마이그레이션                  ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# 설정 파일 로드
CONFIG_FILE="scripts/.gcp-config"
if [ ! -f "$CONFIG_FILE" ]; then
    log_error "설정 파일 없음. gcp-deploy-day1.sh를 먼저 실행하세요."
    exit 1
fi

source "$CONFIG_FILE"
log_info "프로젝트: $GCP_PROJECT_ID"
log_info "리전: $GCP_REGION"

# 1. Cloud SQL 인스턴스 생성
log_info "Cloud SQL PostgreSQL 인스턴스 생성 (약 5-10분 소요)..."

if gcloud sql instances describe "$GCP_DB_INSTANCE" > /dev/null 2>&1; then
    log_warning "Cloud SQL 인스턴스 이미 존재: $GCP_DB_INSTANCE"
else
    # 데이터베이스 비밀번호 생성
    DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

    gcloud sql instances create "$GCP_DB_INSTANCE" \
        --database-version=POSTGRES_14 \
        --tier=db-f1-micro \
        --region="$GCP_REGION" \
        --storage-type=SSD \
        --storage-size=10GB \
        --storage-auto-increase \
        --backup \
        --backup-start-time=03:00 \
        --enable-bin-log=false \
        --maintenance-window-day=SUN \
        --maintenance-window-hour=4 \
        --root-password="$DB_PASSWORD"

    log_success "Cloud SQL 인스턴스 생성 완료"

    # 비밀번호 저장
    echo "export GCP_DB_PASSWORD='$DB_PASSWORD'" >> "$CONFIG_FILE"
    log_warning "DB 비밀번호가 $CONFIG_FILE 에 저장되었습니다."
fi

# 설정 재로드 (비밀번호 포함)
source "$CONFIG_FILE"

# 2. 데이터베이스 생성
log_info "데이터베이스 생성..."
if ! gcloud sql databases describe epl_predictor --instance="$GCP_DB_INSTANCE" > /dev/null 2>&1; then
    gcloud sql databases create epl_predictor --instance="$GCP_DB_INSTANCE"
    log_success "데이터베이스 생성 완료"
else
    log_info "데이터베이스 이미 존재"
fi

# 3. Cloud SQL Proxy 설치 확인
log_info "Cloud SQL Proxy 확인..."
if ! command -v cloud-sql-proxy &> /dev/null; then
    log_info "Cloud SQL Proxy 설치 중..."

    # OS 확인
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.darwin.amd64
        chmod +x cloud-sql-proxy
        sudo mv cloud-sql-proxy /usr/local/bin/
    else
        # Linux
        curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.linux.amd64
        chmod +x cloud-sql-proxy
        sudo mv cloud-sql-proxy /usr/local/bin/
    fi

    log_success "Cloud SQL Proxy 설치 완료"
else
    log_success "Cloud SQL Proxy 이미 설치됨"
fi

# 4. Cloud SQL 연결 정보
CONNECTION_NAME=$(gcloud sql instances describe "$GCP_DB_INSTANCE" --format="value(connectionName)")
log_info "Connection Name: $CONNECTION_NAME"

# 5. Cloud SQL Proxy 시작
log_info "Cloud SQL Proxy 시작 (백그라운드)..."
pkill -f cloud-sql-proxy || true
sleep 2

cloud-sql-proxy "$CONNECTION_NAME" --port 5433 > /tmp/cloud-sql-proxy.log 2>&1 &
PROXY_PID=$!

echo "export GCP_SQL_PROXY_PID=$PROXY_PID" >> "$CONFIG_FILE"
log_success "Cloud SQL Proxy 실행 중 (PID: $PROXY_PID, Port: 5433)"

# Proxy 연결 대기
log_info "Proxy 연결 대기..."
sleep 5

# 6. 로컬 PostgreSQL 데이터 확인
log_info "로컬 PostgreSQL 데이터 확인..."
if ! docker ps | grep epl_postgres_dev > /dev/null; then
    log_warning "로컬 PostgreSQL이 실행되지 않음"
    log_info "로컬 PostgreSQL 시작..."
    docker compose -f docker-compose.dev.yml up -d postgres
    sleep 5
fi

# 로컬 데이터 카운트
LOCAL_COUNT=$(docker exec epl_postgres_dev psql -U epl_user -d epl_predictor -t -c "SELECT COUNT(*) FROM players;" 2>/dev/null | xargs || echo "0")
log_info "로컬 선수 데이터: $LOCAL_COUNT 명"

if [ "$LOCAL_COUNT" -eq "0" ]; then
    log_error "로컬 데이터 없음. 마이그레이션을 먼저 실행하세요:"
    log_info "python scripts/migrate_sqlite_to_postgres.py"
    pkill -P $PROXY_PID
    exit 1
fi

# 7. pg_dump로 로컬 데이터 백업
log_info "로컬 데이터 백업 중..."
docker exec epl_postgres_dev pg_dump -U epl_user -d epl_predictor --clean --if-exists > /tmp/epl_local_backup.sql
log_success "백업 완료: /tmp/epl_local_backup.sql"

# 8. Cloud SQL로 데이터 복원
log_info "Cloud SQL로 데이터 마이그레이션 중..."
PGPASSWORD="$GCP_DB_PASSWORD" psql -h 127.0.0.1 -p 5433 -U postgres -d epl_predictor < /tmp/epl_local_backup.sql

log_success "데이터 마이그레이션 완료"

# 9. 마이그레이션 검증
log_info "마이그레이션 검증..."
CLOUD_COUNT=$(PGPASSWORD="$GCP_DB_PASSWORD" psql -h 127.0.0.1 -p 5433 -U postgres -d epl_predictor -t -c "SELECT COUNT(*) FROM players;" | xargs)

log_info "로컬: $LOCAL_COUNT 명 → Cloud SQL: $CLOUD_COUNT 명"

if [ "$LOCAL_COUNT" -eq "$CLOUD_COUNT" ]; then
    log_success "데이터 검증 성공 ✓"
else
    log_error "데이터 불일치!"
    exit 1
fi

# 10. Cloud Run에서 접속할 수 있도록 서비스 계정 권한 설정
log_info "Cloud Run 서비스 계정 권한 설정..."
PROJECT_NUMBER=$(gcloud projects describe "$GCP_PROJECT_ID" --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/cloudsql.client"

log_success "Cloud SQL 클라이언트 권한 부여 완료"

# 완료 메시지
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   Day 2 완료! ✅                                         ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
log_success "Cloud SQL 인스턴스: $GCP_DB_INSTANCE"
log_success "Connection Name: $CONNECTION_NAME"
log_success "데이터: $CLOUD_COUNT 명의 선수"
log_warning "Cloud SQL Proxy 실행 중 (PID: $PROXY_PID)"
log_info ""
log_info "다음 단계: ./scripts/gcp-deploy-day3.sh 실행"
