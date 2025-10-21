#!/bin/bash

# GCP 배포 Day 3: Backend 컨테이너 빌드 및 Cloud Run 배포
# 실행 전 요구사항: gcp-deploy-day2.sh 완료

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
echo "║   EPL Match Predictor - GCP 배포 Day 3                  ║"
echo "║   Backend Docker 빌드 및 Cloud Run 배포                  ║"
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

# 1. Docker 이미지 태그 생성
IMAGE_TAG="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${GCP_ARTIFACT_REPO}/backend:latest"
log_info "이미지 태그: $IMAGE_TAG"

# 2. Docker 인증 설정
log_info "Docker 인증 설정..."
gcloud auth configure-docker "${GCP_REGION}-docker.pkg.dev" --quiet

# 3. Backend Dockerfile이 있는지 확인
if [ ! -f "backend/Dockerfile" ]; then
    log_error "backend/Dockerfile이 없습니다."
    exit 1
fi

# 4. .dockerignore 생성 (빌드 속도 최적화)
log_info ".dockerignore 생성..."
cat > backend/.dockerignore << EOF
__pycache__
*.pyc
*.pyo
*.pyd
.Python
venv/
env/
.env
.env.dev
*.log
.git
.gitignore
*.md
tests/
.pytest_cache/
*.db
data/
EOF

log_success ".dockerignore 생성 완료"

# 5. Docker 이미지 빌드
log_info "Docker 이미지 빌드 중 (5-10분 소요)..."
cd backend
docker build -t "$IMAGE_TAG" .
cd ..

log_success "Docker 이미지 빌드 완료"

# 6. 이미지를 Artifact Registry에 푸시
log_info "이미지를 Artifact Registry에 푸시 중..."
docker push "$IMAGE_TAG"

log_success "이미지 푸시 완료"

# 7. Cloud SQL Connection Name 가져오기
CONNECTION_NAME=$(gcloud sql instances describe "$GCP_DB_INSTANCE" --format="value(connectionName)")
log_info "Cloud SQL Connection: $CONNECTION_NAME"

# 8. 환경 변수 생성
log_info "환경 변수 설정..."

# DATABASE_URL 생성 (Unix socket 방식)
DATABASE_URL="postgresql://postgres:${GCP_DB_PASSWORD}@/epl_predictor?host=/cloudsql/${CONNECTION_NAME}"

# Anthropic API Key 입력
if [ -z "$ANTHROPIC_API_KEY" ]; then
    log_warning "Anthropic API Key를 입력하세요 (없으면 Enter):"
    read -p "ANTHROPIC_API_KEY: " ANTHROPIC_API_KEY
    if [ -n "$ANTHROPIC_API_KEY" ]; then
        echo "export ANTHROPIC_API_KEY='$ANTHROPIC_API_KEY'" >> "$CONFIG_FILE"
    fi
fi

# 9. Cloud Run 배포
log_info "Cloud Run에 배포 중..."

DEPLOY_CMD="gcloud run deploy $GCP_SERVICE_NAME \
    --image=$IMAGE_TAG \
    --platform=managed \
    --region=$GCP_REGION \
    --allow-unauthenticated \
    --port=8080 \
    --cpu=1 \
    --memory=512Mi \
    --min-instances=0 \
    --max-instances=10 \
    --timeout=60 \
    --set-env-vars='FLASK_ENV=production,DATABASE_URL=$DATABASE_URL' \
    --add-cloudsql-instances=$CONNECTION_NAME"

# Anthropic API Key가 있으면 추가
if [ -n "$ANTHROPIC_API_KEY" ]; then
    DEPLOY_CMD="$DEPLOY_CMD --set-env-vars='ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY'"
fi

eval $DEPLOY_CMD

log_success "Cloud Run 배포 완료"

# 10. 배포된 서비스 URL 가져오기
SERVICE_URL=$(gcloud run services describe "$GCP_SERVICE_NAME" \
    --region="$GCP_REGION" \
    --format="value(status.url)")

log_success "Backend URL: $SERVICE_URL"

# 설정 파일에 저장
echo "export GCP_BACKEND_URL='$SERVICE_URL'" >> "$CONFIG_FILE"

# 11. 헬스 체크
log_info "헬스 체크 중..."
sleep 5

if curl -f "${SERVICE_URL}/api/health" > /dev/null 2>&1; then
    log_success "헬스 체크 성공 ✓"
else
    log_warning "헬스 체크 실패 - 로그를 확인하세요:"
    log_info "gcloud run logs read $GCP_SERVICE_NAME --region=$GCP_REGION --limit=50"
fi

# 12. API 테스트
log_info "API 테스트: 팀 목록 조회..."
TEAMS_RESPONSE=$(curl -s "${SERVICE_URL}/api/teams")

if echo "$TEAMS_RESPONSE" | grep -q "Arsenal\|Liverpool\|Manchester"; then
    log_success "API 테스트 성공 ✓"
    echo "응답: $(echo $TEAMS_RESPONSE | head -c 100)..."
else
    log_warning "API 응답이 예상과 다릅니다:"
    echo "$TEAMS_RESPONSE"
fi

# 완료 메시지
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   Day 3 완료! ✅                                         ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
log_success "Backend URL: $SERVICE_URL"
log_info "API 엔드포인트:"
echo "  - GET  ${SERVICE_URL}/api/teams"
echo "  - GET  ${SERVICE_URL}/api/players"
echo "  - POST ${SERVICE_URL}/api/ratings"
echo ""
log_info "다음 단계: ./scripts/gcp-deploy-day4.sh 실행"
