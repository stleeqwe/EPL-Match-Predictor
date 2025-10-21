# PostgreSQL 환경 구축 가이드

**목표:** 로컬에서 PostgreSQL 환경을 구축하고 검증한 후 GCP로 배포

---

## 🚀 Step 1: PostgreSQL 시작 (1분)

### Docker Compose로 PostgreSQL 실행

```bash
# EPL-Match-Predictor 프로젝트 루트에서
docker compose -f docker-compose.dev.yml up -d
```

**출력 확인:**
```
✅ Creating epl_postgres_dev ... done
✅ Creating epl_pgadmin_dev  ... done
```

**상태 확인:**
```bash
docker-compose -f docker-compose.dev.yml ps

# 출력 예시:
# epl_postgres_dev   Up   0.0.0.0:5432->5432/tcp
# epl_pgadmin_dev    Up   0.0.0.0:5050->80/tcp
```

---

## 📊 Step 2: 데이터 마이그레이션 (2분)

### SQLite → PostgreSQL 자동 마이그레이션

```bash
# 가상환경 활성화 (이미 되어있으면 생략)
cd backend
source venv/bin/activate

# 마이그레이션 스크립트 실행
cd ..
python scripts/migrate_sqlite_to_postgres.py
```

**성공 출력:**
```
╔══════════════════════════════════════════════════════════╗
║   SQLite → PostgreSQL Migration Tool                    ║
║   EPL Match Predictor v2.0                              ║
╚══════════════════════════════════════════════════════════╝

ℹ️  Found SQLite DB: backend/data/epl_data.db (148000 bytes)
✅ Connected to SQLite
✅ Connected to PostgreSQL
ℹ️  Creating PostgreSQL schema...
✅ PostgreSQL schema created
ℹ️  Migrating table: teams
✅ Migrated 20 rows from teams
ℹ️  Migrating table: players
✅ Migrated 500 rows from players
ℹ️  Migrating table: player_ratings  ← 사용자 평가 데이터!
✅ Migrated 150 rows from player_ratings
ℹ️  Migrating table: position_attributes
✅ Migrated 27 rows from position_attributes
ℹ️  Verifying migration...
✅ teams: 20 rows ✓
✅ players: 500 rows ✓
✅ player_ratings: 150 rows ✓
✅ position_attributes: 27 rows ✓
ℹ️  Sample user ratings:
  - default: Erling Haaland → finishing = 4.8
  - default: Kevin De Bruyne → passing = 4.7
  ...
✅ Migration completed! Total 697 rows migrated
ℹ️  PostgreSQL connection string:
  postgresql://epl_user:epl_dev_password_123@localhost:5432/epl_predictor
ℹ️  Database connections closed
```

---

## 🔧 Step 3: Backend 설정 변경 (1분)

### 환경 변수로 PostgreSQL 연결

```bash
# backend/.env.dev 파일이 이미 생성되어 있음
cat backend/.env.dev

# 출력:
# DATABASE_URL=postgresql://epl_user:epl_dev_password_123@localhost:5432/epl_predictor
# FLASK_ENV=development
# FLASK_DEBUG=True
# API_PORT=5001
```

### Backend 시작 (PostgreSQL 사용)

```bash
cd backend
source venv/bin/activate

# 환경 변수 로드 후 실행
export $(cat .env.dev | xargs) && python api/app.py
```

**성공 출력:**
```
* Serving Flask app 'app'
* Debug mode: on
* Running on http://127.0.0.1:5001
* Using database: postgresql://epl_user:***@localhost:5432/epl_predictor
```

---

## ✅ Step 4: 기능 테스트 (5분)

### 4-1. API 테스트 (새 터미널)

```bash
# Health check
curl http://localhost:5001/api/health

# 팀 목록
curl http://localhost:5001/api/teams | jq '.[0:3]'

# Arsenal 선수 목록
curl http://localhost:5001/api/squad/Arsenal | jq '.[0:2]'
```

### 4-2. 사용자 평가 데이터 확인

```bash
# 선수 평가 조회
curl http://localhost:5001/api/ratings/1 | jq
```

**예상 출력:**
```json
{
  "player_id": 1,
  "player_name": "Bukayo Saka",
  "ratings": {
    "pace": 4.5,
    "finishing": 4.2,
    "dribbling": 4.7,
    ...
  }
}
```

### 4-3. Frontend 테스트

```bash
# 새 터미널에서
cd frontend

# React 앱 시작
npm start
```

브라우저에서 http://localhost:3000 접속

**테스트 시나리오:**
1. ✅ 팀 선택 (Arsenal)
2. ✅ 선수 목록 표시
3. ✅ 선수 평가 입력 (손흥민 → 슈팅 4.5)
4. ✅ 저장 클릭
5. ✅ 새로고침 후 평가 유지 확인 ← **중요!**
6. ✅ 시뮬레이션 실행

---

## 🔍 Step 5: 데이터 확인 (선택)

### pgAdmin으로 DB 확인 (GUI)

브라우저에서 http://localhost:5050 접속

**로그인:**
- Email: `admin@epl.local`
- Password: `admin123`

**서버 추가:**
1. Add New Server 클릭
2. General 탭: Name = `EPL Local`
3. Connection 탭:
   - Host: `postgres` (Docker 네트워크)
   - Port: `5432`
   - Database: `epl_predictor`
   - Username: `epl_user`
   - Password: `epl_dev_password_123`
4. Save

**테이블 확인:**
```
epl_predictor → Schemas → public → Tables
→ player_ratings (사용자 평가 데이터)
→ players
→ teams
→ position_attributes
```

### SQL로 직접 확인 (CLI)

```bash
# PostgreSQL 컨테이너 접속
docker exec -it epl_postgres_dev psql -U epl_user -d epl_predictor

# SQL 쿼리
SELECT COUNT(*) FROM player_ratings;  -- 사용자 평가 개수
SELECT * FROM player_ratings LIMIT 5;

# 사용자별 평가 통계
SELECT
  user_id,
  COUNT(*) as num_ratings,
  AVG(rating) as avg_rating
FROM player_ratings
GROUP BY user_id;

\q  -- 종료
```

---

## 🛑 Step 6: 정리

### PostgreSQL 중지

```bash
docker-compose -f docker-compose.dev.yml down
```

### PostgreSQL 완전 삭제 (데이터 포함)

```bash
docker-compose -f docker-compose.dev.yml down -v
```

---

## 🐛 트러블슈팅

### 문제 1: PostgreSQL 연결 실패

**증상:**
```
psycopg2.OperationalError: could not connect to server
```

**해결:**
```bash
# Docker 컨테이너 확인
docker ps | grep postgres

# 로그 확인
docker logs epl_postgres_dev

# 재시작
docker-compose -f docker-compose.dev.yml restart postgres
```

### 문제 2: 마이그레이션 오류

**증상:**
```
Failed to connect to PostgreSQL
```

**해결:**
```bash
# PostgreSQL이 실행 중인지 확인
docker-compose -f docker-compose.dev.yml ps

# 포트 충돌 확인
lsof -i :5432

# 다른 PostgreSQL이 실행 중이면 종료
brew services stop postgresql  # (Mac에 Homebrew PostgreSQL 설치된 경우)
```

### 문제 3: Backend가 SQLite 사용함

**증상:**
```
* Using database: sqlite:///epl_data.db
```

**해결:**
```bash
# 환경 변수 확인
echo $DATABASE_URL

# 없으면 설정
export DATABASE_URL="postgresql://epl_user:epl_dev_password_123@localhost:5432/epl_predictor"

# 또는 .env.dev 파일 사용
cd backend
export $(cat .env.dev | xargs)
python api/app.py
```

### 문제 4: 사용자 평가 데이터 손실

**증상:**
평가를 입력했는데 새로고침하면 사라짐

**확인:**
```sql
-- PostgreSQL에서 확인
SELECT COUNT(*) FROM player_ratings;
-- 0이면 마이그레이션 실패

-- SQLite에 데이터가 있는지 확인
sqlite3 backend/data/epl_data.db "SELECT COUNT(*) FROM player_ratings"
```

**해결:**
```bash
# 마이그레이션 재실행
python scripts/migrate_sqlite_to_postgres.py
```

---

## 📝 다음 단계

PostgreSQL 로컬 환경에서 모든 기능이 정상 작동하면:

1. ✅ **GCP Cloud SQL 설정**
2. ✅ **Backend Dockerfile 작성**
3. ✅ **Cloud Run 배포**
4. ✅ **Frontend 배포**

---

## 🎯 핵심 체크리스트

```
□ PostgreSQL 컨테이너 실행 완료
□ SQLite → PostgreSQL 마이그레이션 성공
□ Backend가 PostgreSQL 연결 확인
□ API 테스트 통과 (팀, 선수, 평가 조회)
□ Frontend에서 평가 입력/저장 성공
□ 새로고침 후 데이터 유지 확인 ← 가장 중요!
□ 시뮬레이션 실행 성공
```

모두 체크되면 GCP 배포 준비 완료! 🚀

---

**문의사항이 있으면 언제든 물어보세요!**
