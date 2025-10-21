#!/bin/bash

# GCP 배포 Day 1: 프로젝트 설정 및 API 활성화
# 실행 전 요구사항: gcloud auth login 완료

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
echo "║   EPL Match Predictor - GCP 배포 Day 1                  ║"
echo "║   프로젝트 생성 및 API 활성화                            ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# 1. gcloud 인증 확인
log_info "gcloud 인증 상태 확인..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" > /dev/null 2>&1; then
    log_error "gcloud 인증 필요. 'gcloud auth login' 실행 후 다시 시도하세요."
    exit 1
fi

CURRENT_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1)
log_success "인증된 계정: $CURRENT_ACCOUNT"

# 2. 프로젝트 설정
log_info "GCP 프로젝트를 입력하거나 새로 생성합니다."
echo ""
echo "기존 프로젝트 목록:"
gcloud projects list --format="table(projectId,name,projectNumber)" || true
echo ""

read -p "사용할 프로젝트 ID (새로 생성하려면 새 ID 입력): " PROJECT_ID

# 프로젝트 존재 확인
if gcloud projects describe "$PROJECT_ID" > /dev/null 2>&1; then
    log_info "기존 프로젝트 사용: $PROJECT_ID"
else
    log_info "새 프로젝트 생성: $PROJECT_ID"
    read -p "프로젝트 이름: " PROJECT_NAME
    gcloud projects create "$PROJECT_ID" --name="$PROJECT_NAME"
    log_success "프로젝트 생성 완료"
fi

# 프로젝트 설정
gcloud config set project "$PROJECT_ID"
log_success "현재 프로젝트: $PROJECT_ID"

# 3. Billing 계정 연결 확인
log_info "Billing 계정 확인..."
BILLING_ACCOUNTS=$(gcloud billing accounts list --format="value(name)" | head -1)

if [ -z "$BILLING_ACCOUNTS" ]; then
    log_error "Billing 계정이 없습니다."
    log_warning "https://console.cloud.google.com/billing 에서 Billing 계정을 생성하세요."
    exit 1
fi

# Billing 연결
if ! gcloud billing projects describe "$PROJECT_ID" > /dev/null 2>&1; then
    log_info "Billing 계정 연결 중..."
    gcloud billing projects link "$PROJECT_ID" --billing-account="$BILLING_ACCOUNTS"
fi
log_success "Billing 계정 연결됨"

# 4. 필요한 API 활성화
log_info "필요한 GCP API 활성화 중..."

APIS=(
    "cloudbuild.googleapis.com"
    "run.googleapis.com"
    "sql-component.googleapis.com"
    "sqladmin.googleapis.com"
    "storage.googleapis.com"
    "artifactregistry.googleapis.com"
    "compute.googleapis.com"
    "cloudresourcemanager.googleapis.com"
)

for api in "${APIS[@]}"; do
    log_info "활성화: $api"
    gcloud services enable "$api"
done

log_success "모든 API 활성화 완료"

# 5. 리전 설정
echo ""
log_info "배포 리전을 선택하세요:"
echo "1) asia-northeast3 (서울) - 권장"
echo "2) asia-northeast1 (도쿄)"
echo "3) us-central1 (미국 중부 - 저렴)"
read -p "선택 (1-3): " REGION_CHOICE

case $REGION_CHOICE in
    1) REGION="asia-northeast3" ;;
    2) REGION="asia-northeast1" ;;
    3) REGION="us-central1" ;;
    *) REGION="asia-northeast3" ;;
esac

log_success "배포 리전: $REGION"

# 6. 환경 설정 저장
CONFIG_FILE="scripts/.gcp-config"
cat > "$CONFIG_FILE" << EOF
# GCP 배포 설정
export GCP_PROJECT_ID="$PROJECT_ID"
export GCP_REGION="$REGION"
export GCP_ZONE="${REGION}-a"
export GCP_SERVICE_NAME="epl-predictor-backend"
export GCP_DB_INSTANCE="epl-db-prod"
export GCP_BUCKET_NAME="${PROJECT_ID}-epl-frontend"
export GCP_ARTIFACT_REPO="epl-docker-repo"
EOF

log_success "설정 저장: $CONFIG_FILE"

# 7. Artifact Registry 생성 (Docker 이미지 저장소)
log_info "Artifact Registry 생성..."
if ! gcloud artifacts repositories describe "$GCP_ARTIFACT_REPO" \
    --location="$REGION" > /dev/null 2>&1; then
    gcloud artifacts repositories create epl-docker-repo \
        --repository-format=docker \
        --location="$REGION" \
        --description="EPL Predictor Docker images"
    log_success "Artifact Registry 생성 완료"
else
    log_info "Artifact Registry 이미 존재"
fi

# 완료 메시지
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   Day 1 완료! ✅                                         ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
log_success "프로젝트 ID: $PROJECT_ID"
log_success "리전: $REGION"
log_info "다음 단계: ./scripts/gcp-deploy-day2.sh 실행"
