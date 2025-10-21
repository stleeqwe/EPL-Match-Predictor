#!/bin/bash

#######################################################
# PostgreSQL 환경 빠른 시작 스크립트
# EPL Match Predictor v2.0
#######################################################

set -e  # 오류 발생 시 중단

GREEN='\033[0;32m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${PURPLE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║   PostgreSQL Quick Start                                 ║
║   EPL Match Predictor v2.0                               ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"
echo ""

# 프로젝트 루트로 이동
cd "$(dirname "$0")/.."

# 사전 요구사항 확인
./scripts/check-requirements.sh
if [ $? -ne 0 ]; then
    exit 1
fi

# Step 1: PostgreSQL 시작
echo -e "${BLUE}[1/4] Starting PostgreSQL...${NC}"
docker compose -f docker-compose.dev.yml up -d postgres

# 5초 대기 (PostgreSQL 부팅)
echo -e "${YELLOW}⏳ Waiting for PostgreSQL to start...${NC}"
sleep 5

# PostgreSQL health check
echo -e "${BLUE}Checking PostgreSQL health...${NC}"
docker exec epl_postgres_dev pg_isready -U epl_user > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
else
    echo -e "${RED}❌ PostgreSQL failed to start${NC}"
    echo -e "${YELLOW}Check logs: docker logs epl_postgres_dev${NC}"
    exit 1
fi

# Step 2: 데이터 마이그레이션
echo ""
echo -e "${BLUE}[2/4] Migrating SQLite → PostgreSQL...${NC}"

if [ ! -f "backend/data/epl_data.db" ]; then
    echo -e "${YELLOW}⚠️  SQLite database not found. Skipping migration.${NC}"
else
    cd backend
    source venv/bin/activate
    cd ..
    python scripts/migrate_sqlite_to_postgres.py

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Migration completed${NC}"
    else
        echo -e "${RED}❌ Migration failed${NC}"
        exit 1
    fi
fi

# Step 3: Backend 시작
echo ""
echo -e "${BLUE}[3/4] Starting Backend (PostgreSQL mode)...${NC}"
cd backend

# .env.dev가 있는지 확인
if [ ! -f ".env.dev" ]; then
    echo -e "${RED}❌ .env.dev file not found!${NC}"
    exit 1
fi

# 백그라운드에서 Backend 실행
export $(cat .env.dev | xargs)
nohup python api/app.py > ../backend-postgres.log 2>&1 &
BACKEND_PID=$!

echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"
cd ..

# Step 4: Frontend 시작
echo ""
echo -e "${BLUE}[4/4] Starting Frontend...${NC}"
cd frontend

# 백그라운드에서 Frontend 실행
nohup npm start > ../frontend-postgres.log 2>&1 &
FRONTEND_PID=$!

echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"
cd ..

# 완료
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ All services started successfully!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${PURPLE}📋 Access:${NC}"
echo -e "  • Frontend:  ${BLUE}http://localhost:3000${NC}"
echo -e "  • Backend:   ${BLUE}http://localhost:5001/api${NC}"
echo -e "  • pgAdmin:   ${BLUE}http://localhost:5050${NC} (admin@epl.local / admin123)"
echo ""
echo -e "${PURPLE}📊 Database:${NC}"
echo -e "  • PostgreSQL: localhost:5432"
echo -e "  • Database:   epl_predictor"
echo -e "  • User:       epl_user"
echo ""
echo -e "${YELLOW}📋 Logs:${NC}"
echo -e "  • Backend:  ${BLUE}tail -f backend-postgres.log${NC}"
echo -e "  • Frontend: ${BLUE}tail -f frontend-postgres.log${NC}"
echo -e "  • Postgres: ${BLUE}docker logs -f epl_postgres_dev${NC}"
echo ""
echo -e "${YELLOW}🛑 Stop all:${NC}"
echo -e "  ${BLUE}docker-compose -f docker-compose.dev.yml down${NC}"
echo -e "  ${BLUE}kill $BACKEND_PID $FRONTEND_PID${NC}"
echo ""
