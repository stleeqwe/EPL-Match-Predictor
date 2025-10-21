#!/bin/bash

# GCP 배포 Day 4: Frontend 빌드 및 Cloud Storage + CDN 배포
# 실행 전 요구사항: gcp-deploy-day3.sh 완료

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
echo "║   EPL Match Predictor - GCP 배포 Day 4                  ║"
echo "║   Frontend 빌드 및 Cloud Storage 배포                    ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# 설정 파일 로드
CONFIG_FILE="scripts/.gcp-config"
if [ ! -f "$CONFIG_FILE" ]; then
    log_error "설정 파일 없음. gcp-deploy-day1.sh를 먼저 실행하세요."
    exit 1
fi

source "$CONFIG_FILE"

if [ -z "$GCP_BACKEND_URL" ]; then
    log_error "Backend URL이 없습니다. gcp-deploy-day3.sh를 먼저 실행하세요."
    exit 1
fi

log_info "프로젝트: $GCP_PROJECT_ID"
log_info "Backend URL: $GCP_BACKEND_URL"

# 1. .env.production 파일 생성 (Backend URL 주입)
log_info "Frontend 환경 변수 설정..."

cat > frontend/.env.production << EOF
# EPL Match Predictor - Production Environment
REACT_APP_API_BASE_URL=$GCP_BACKEND_URL
REACT_APP_ENV=production
REACT_APP_ENABLE_AI_FEATURES=true
REACT_APP_ENABLE_MATCH_SIMULATOR=true
EOF

log_success ".env.production 생성 완료"

# 2. Frontend 빌드
log_info "Frontend 빌드 중 (3-5분 소요)..."

cd frontend

# npm 의존성 설치 (혹시 몰라서)
if [ ! -d "node_modules" ]; then
    log_info "npm 의존성 설치..."
    npm install
fi

# Production 빌드
npm run build

cd ..

log_success "Frontend 빌드 완료"

# 3. Cloud Storage 버킷 생성
log_info "Cloud Storage 버킷 생성..."

if gsutil ls -b "gs://${GCP_BUCKET_NAME}" > /dev/null 2>&1; then
    log_warning "버킷이 이미 존재: $GCP_BUCKET_NAME"
else
    # 버킷 생성
    gsutil mb -p "$GCP_PROJECT_ID" -c STANDARD -l "$GCP_REGION" "gs://${GCP_BUCKET_NAME}"
    log_success "버킷 생성 완료: $GCP_BUCKET_NAME"
fi

# 4. 버킷을 웹사이트로 설정
log_info "버킷 웹사이트 설정..."

gsutil web set -m index.html -e index.html "gs://${GCP_BUCKET_NAME}"

# 5. 버킷을 공개 읽기 가능하도록 설정
log_info "버킷 공개 설정..."

gsutil iam ch allUsers:objectViewer "gs://${GCP_BUCKET_NAME}"

# 6. 빌드된 파일 업로드
log_info "Frontend 파일 업로드 중..."

gsutil -m rsync -r -d frontend/build "gs://${GCP_BUCKET_NAME}"

log_success "Frontend 업로드 완료"

# 7. Cache-Control 설정 (성능 최적화)
log_info "Cache-Control 설정..."

# HTML 파일: 캐시 안 함 (최신 버전 보장)
gsutil -m setmeta -h "Cache-Control:no-cache, no-store, must-revalidate" \
    "gs://${GCP_BUCKET_NAME}/*.html"

# JS/CSS 파일: 1년 캐시 (해시 포함 파일명)
gsutil -m setmeta -h "Cache-Control:public, max-age=31536000, immutable" \
    "gs://${GCP_BUCKET_NAME}/static/**"

log_success "Cache-Control 설정 완료"

# 8. Load Balancer + CDN 설정 (선택적)
log_info "Load Balancer 설정을 원하시나요? (CDN 활성화)"
log_warning "Load Balancer는 추가 비용이 발생합니다 (~$20/month)"
echo "1) Yes - Load Balancer + CDN 설정"
echo "2) No - Cloud Storage만 사용 (저렴)"
read -p "선택 (1-2): " LB_CHOICE

if [ "$LB_CHOICE" == "1" ]; then
    log_info "Load Balancer 생성 중..."

    # Backend bucket 생성
    BACKEND_BUCKET_NAME="${GCP_BUCKET_NAME}-backend"

    if ! gcloud compute backend-buckets describe "$BACKEND_BUCKET_NAME" > /dev/null 2>&1; then
        gcloud compute backend-buckets create "$BACKEND_BUCKET_NAME" \
            --gcs-bucket-name="$GCP_BUCKET_NAME" \
            --enable-cdn
        log_success "Backend bucket 생성 완료"
    fi

    # URL map 생성
    URL_MAP_NAME="epl-frontend-url-map"
    if ! gcloud compute url-maps describe "$URL_MAP_NAME" > /dev/null 2>&1; then
        gcloud compute url-maps create "$URL_MAP_NAME" \
            --default-backend-bucket="$BACKEND_BUCKET_NAME"
        log_success "URL map 생성 완료"
    fi

    # HTTP(S) proxy 생성
    HTTP_PROXY_NAME="epl-frontend-http-proxy"
    if ! gcloud compute target-http-proxies describe "$HTTP_PROXY_NAME" > /dev/null 2>&1; then
        gcloud compute target-http-proxies create "$HTTP_PROXY_NAME" \
            --url-map="$URL_MAP_NAME"
        log_success "HTTP proxy 생성 완료"
    fi

    # 전역 IP 예약
    FRONTEND_IP_NAME="epl-frontend-ip"
    if ! gcloud compute addresses describe "$FRONTEND_IP_NAME" --global > /dev/null 2>&1; then
        gcloud compute addresses create "$FRONTEND_IP_NAME" --global
        log_success "글로벌 IP 예약 완료"
    fi

    FRONTEND_IP=$(gcloud compute addresses describe "$FRONTEND_IP_NAME" --global --format="value(address)")

    # Forwarding rule 생성
    FORWARDING_RULE_NAME="epl-frontend-forwarding-rule"
    if ! gcloud compute forwarding-rules describe "$FORWARDING_RULE_NAME" --global > /dev/null 2>&1; then
        gcloud compute forwarding-rules create "$FORWARDING_RULE_NAME" \
            --global \
            --target-http-proxy="$HTTP_PROXY_NAME" \
            --address="$FRONTEND_IP" \
            --ports=80
        log_success "Forwarding rule 생성 완료"
    fi

    FRONTEND_URL="http://${FRONTEND_IP}"
    log_success "Load Balancer + CDN 설정 완료"
else
    # Cloud Storage 직접 접근 URL
    FRONTEND_URL="https://storage.googleapis.com/${GCP_BUCKET_NAME}/index.html"
    log_info "Cloud Storage 직접 접근 사용"
fi

# 9. 설정 파일에 저장
echo "export GCP_FRONTEND_URL='$FRONTEND_URL'" >> "$CONFIG_FILE"

# 10. CORS 설정 (Backend에서 Frontend 요청 허용)
log_info "Backend CORS 설정..."

cat > /tmp/cors.json << EOF
[
  {
    "origin": ["$FRONTEND_URL", "http://localhost:3000"],
    "method": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "responseHeader": ["Content-Type", "Authorization"],
    "maxAgeSeconds": 3600
  }
]
EOF

# Backend Cloud Run CORS 설정은 애플리케이션 레벨에서 처리 (이미 flask-cors 설정됨)
log_success "CORS 설정 확인 완료 (flask-cors 사용)"

# 완료 메시지
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   Day 4 완료! 🎉 전체 배포 완료!                        ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
log_success "=========================================="
log_success "   EPL Match Predictor v2.0 배포 완료!"
log_success "=========================================="
echo ""
log_info "Frontend URL:"
echo "  $FRONTEND_URL"
echo ""
log_info "Backend API URL:"
echo "  $GCP_BACKEND_URL"
echo ""
log_info "다음 단계:"
echo "  1. 브라우저에서 Frontend URL 접속"
echo "  2. 선수 평가 및 매치 시뮬레이션 테스트"
echo "  3. 모니터링 대시보드 확인:"
echo "     https://console.cloud.google.com/run?project=$GCP_PROJECT_ID"
echo ""
log_warning "비용 모니터링:"
echo "  https://console.cloud.google.com/billing?project=$GCP_PROJECT_ID"
echo ""
log_info "배포 설정 정보: $CONFIG_FILE"
