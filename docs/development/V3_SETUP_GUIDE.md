# V3 AI Simulation System - Setup Guide

## 🚀 Quick Start

V3 시스템을 활성화하려면 다음 단계를 순서대로 진행하세요.

---

## 1️⃣ Claude API Key 설정 (필수)

### 1.1 API Key 발급

1. **Anthropic Console 접속**: https://console.anthropic.com/
2. **로그인 또는 회원가입**
3. **API Keys 메뉴**로 이동
4. **"Create Key"** 버튼 클릭
5. **Key 이름 입력** (예: "soccer-predictor-dev")
6. **생성된 Key 복사** (한 번만 표시됩니다!)

### 1.2 환경 변수 설정

`backend/.env` 파일을 열고 다음 라인을 수정하세요:

```bash
# 현재 (비어있음)
ANTHROPIC_API_KEY=

# 수정 후 (발급받은 키 입력)
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 1.3 확인

백엔드 서버 재시작 후 로그 확인:

```bash
# 성공 시
✅ V3 Simulation routes registered
🚀 V3 System activated: Auth, Simulation

# 실패 시
WARNING: V3 Simulation routes not available: Configuration error: CLAUDE_API_KEY not set
```

---

## 2️⃣ PostgreSQL 데이터베이스 설정 (필수)

### 2.1 PostgreSQL 설치 확인

```bash
# 설치 확인
psql --version

# 없으면 설치 (macOS)
brew install postgresql@15
brew services start postgresql@15
```

### 2.2 데이터베이스 생성

```bash
# PostgreSQL 접속
psql postgres

# 데이터베이스 생성
CREATE DATABASE soccer_predictor_v3;

# 사용자 확인 (현재 .env의 POSTGRES_USER 사용)
\du

# 종료
\q
```

### 2.3 데이터베이스 초기화

```bash
cd backend
source venv/bin/activate
python init_database_v3.py
```

**성공 메시지:**
```
✅ Database schema created successfully
✅ Initial data inserted
✅ Database initialization complete
```

### 2.4 환경 변수 확인

`.env` 파일에서 PostgreSQL 설정 확인:

```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=soccer_predictor_v3
POSTGRES_USER=pukaworks          # 현재 macOS 사용자명
POSTGRES_PASSWORD=                # 로컬 개발 시 비어있음
```

---

## 3️⃣ Redis 설정 (선택사항 - 성능 향상)

### 3.1 Redis 설치

```bash
# macOS
brew install redis
brew services start redis

# 확인
redis-cli ping
# 응답: PONG
```

### 3.2 환경 변수 (기본값 사용)

```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=                   # 로컬 개발 시 비어있음
```

**Note**: Redis가 없어도 메모리 캐시로 대체되므로 동작합니다.

---

## 4️⃣ Stripe 설정 (선택사항 - 구독 기능)

### 4.1 Stripe 계정

1. **Stripe Dashboard 접속**: https://dashboard.stripe.com/
2. **Test mode 활성화** (우측 상단 토글)
3. **API keys 복사**:
   - Publishable key: `pk_test_...`
   - Secret key: `sk_test_...`

### 4.2 Price ID 생성

1. **Products** 메뉴 → **Create product**
2. **이름**: "PRO Subscription"
3. **가격**: $19.99/month (recurring)
4. **생성 후 Price ID 복사**: `price_xxxxx`

### 4.3 환경 변수 설정

```bash
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxxxxx
STRIPE_PRICE_PRO_MONTHLY=price_xxxxxxxxxxxxx
```

### 4.4 Webhook 설정 (로컬 테스트)

```bash
# Stripe CLI 설치
brew install stripe/stripe-cli/stripe

# Webhook 포워딩
stripe listen --forward-to localhost:5001/api/v1/payment/webhook
```

**출력된 Webhook Secret을 .env에 추가:**
```bash
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
```

---

## 5️⃣ 백엔드 서버 시작

```bash
cd backend
source venv/bin/activate
FLASK_APP=api/app.py FLASK_DEBUG=1 python -m flask run --host=0.0.0.0 --port=5001
```

**활성화 확인 (로그):**
```
✅ V3 Auth routes registered
✅ V3 Simulation routes registered
✅ V3 Payment routes registered
🚀 V3 System activated: Auth, Simulation, Payment
```

---

## 6️⃣ 프론트엔드 설정

### 6.1 React Router 설치

```bash
cd frontend/epl-predictor
npm install react-router-dom
```

### 6.2 환경 변수 설정

`.env` 파일 생성:
```bash
REACT_APP_API_URL=http://localhost:5001
```

### 6.3 서버 시작

```bash
npm start
```

---

## 📊 시스템 구성 확인

### 백엔드 엔드포인트 테스트

```bash
# Health Check
curl http://localhost:5001/api/health

# V3 Auth - 회원가입
curl -X POST http://localhost:5001/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "display_name": "Test User"
  }'

# V3 Auth - 로그인
curl -X POST http://localhost:5001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'
```

**성공 응답:**
```json
{
  "success": true,
  "access_token": "eyJ0eXAiOiJKV1QiLCJh...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJh...",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "test@example.com",
    "display_name": "Test User",
    "tier": "BASIC"
  }
}
```

---

## 🎯 최소 구성 (Claude AI만 활성화)

시간이 없다면 Claude API Key만 설정해도 됩니다:

1. ✅ **Claude API Key 설정** (.env 파일)
2. ⏭️ PostgreSQL - 나중에 (메모리 DB로 대체)
3. ⏭️ Redis - 선택사항
4. ⏭️ Stripe - 구독 기능 필요 시

**활성화 결과:**
```
🚀 V3 System activated: Auth, Simulation
```

---

## 🔧 문제 해결

### 1. "CLAUDE_API_KEY not set"

**원인**: .env 파일에 API Key가 없음

**해결**:
```bash
# .env 파일 확인
cat backend/.env | grep ANTHROPIC_API_KEY

# 비어있으면 추가
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
```

### 2. "Cannot connect to PostgreSQL"

**원인**: PostgreSQL 서버가 실행되지 않음

**해결**:
```bash
# PostgreSQL 시작
brew services start postgresql@15

# 또는 임시로 실행
postgres -D /usr/local/var/postgres
```

### 3. "Redis connection failed"

**원인**: Redis 서버가 실행되지 않음 (선택사항)

**해결**:
```bash
# Redis 시작
brew services start redis

# 또는 메모리 캐시 사용 (설정 변경 불필요)
```

### 4. "Stripe configuration invalid"

**원인**: Stripe API Key 또는 Price ID 누락 (구독 기능용)

**해결**: 구독 기능이 필요 없으면 무시하세요. Auth와 Simulation은 작동합니다.

---

## 💰 비용 안내

### Claude API 사용료

- **모델**: Claude Sonnet 3.5 (BASIC), Claude Sonnet 4.5 (PRO)
- **입력**: $3 / 1M tokens
- **출력**: $15 / 1M tokens
- **예상 비용**: 시뮬레이션 1회당 약 $0.02-$0.035

### 예산 설정 (.env)

```bash
CLAUDE_MONTHLY_BUDGET=1000    # 월 $1000 제한
CLAUDE_DAILY_BUDGET=50        # 일 $50 제한
```

### Stripe 수수료

- **거래 수수료**: 2.9% + $0.30 / 건
- **구독**: $19.99/month → Stripe 수수료 약 $0.88

---

## 📚 관련 문서

- **프로젝트 완료 보고서**: `PROJECT_V3_COMPLETE.md`
- **구현 상태**: `IMPLEMENTATION_STATUS_V3.md`
- **백엔드 API 문서**: `backend/api/v1/`
- **프론트엔드 컴포넌트**: `frontend/epl-predictor/src/components/`

---

## ✅ 설정 체크리스트

최종 확인:

- [ ] Claude API Key 설정 (.env)
- [ ] PostgreSQL 데이터베이스 생성
- [ ] 데이터베이스 초기화 (`init_database_v3.py`)
- [ ] 백엔드 서버 시작 (V3 라우트 활성화 확인)
- [ ] 프론트엔드 서버 시작
- [ ] API 엔드포인트 테스트 (회원가입/로그인)

---

**🎉 설정 완료 후 V3 시스템 활성화 메시지:**

```
INFO:app:🚀 V3 System activated: Auth, Simulation, Payment
```

**문의 또는 문제 발생 시**: 백엔드 로그를 확인하세요 (`backend/logs/` 또는 터미널 출력)
