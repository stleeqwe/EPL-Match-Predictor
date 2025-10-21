#!/bin/bash

# GCP 전체 배포 - 한 번에 실행
# Day 1-4 모든 단계를 순차적으로 실행

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
echo "║   EPL Match Predictor - GCP 전체 배포                   ║"
echo "║   Day 1-4 자동 실행                                      ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

log_warning "이 스크립트는 Day 1-4 모든 단계를 자동으로 실행합니다."
log_warning "실행 시간: 약 30-40분 소요"
log_warning "비용: 월 $42-62 예상"
echo ""
read -p "계속하시겠습니까? (y/N): " CONFIRM

if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    log_info "배포 취소됨"
    exit 0
fi

# 현재 디렉토리 확인
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

# Day 1: 프로젝트 설정
log_info "========== Day 1: 프로젝트 설정 시작 =========="
bash scripts/gcp-deploy-day1.sh
log_success "Day 1 완료"
echo ""

# Day 2: Cloud SQL
log_info "========== Day 2: Cloud SQL 설정 시작 =========="
bash scripts/gcp-deploy-day2.sh
log_success "Day 2 완료"
echo ""

# Day 3: Backend 배포
log_info "========== Day 3: Backend 배포 시작 =========="
bash scripts/gcp-deploy-day3.sh
log_success "Day 3 완료"
echo ""

# Day 4: Frontend 배포
log_info "========== Day 4: Frontend 배포 시작 =========="
bash scripts/gcp-deploy-day4.sh
log_success "Day 4 완료"
echo ""

# 완료
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   🎉 전체 배포 완료! 🎉                                  ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# 설정 파일 로드
source scripts/.gcp-config

log_success "Frontend: $GCP_FRONTEND_URL"
log_success "Backend: $GCP_BACKEND_URL"
echo ""
log_info "브라우저에서 Frontend URL로 접속하세요!"
