# ⚡ 즉시 실행 계획 (Immediate Action Plan)
## 24시간 내 착수 가능한 작업

**작성일**: 2025-10-08
**우선순위**: 🔴 CRITICAL
**목표**: 배포 차단 요소 제거 및 핵심 기능 작동

---

## 🎯 오늘 할 일 (Today's Mission)

### 목표
- ✅ PostgreSQL 연결 성공
- ✅ Redis 작동 확인
- ✅ 환경 변수 완전 설정
- ✅ Claude API 기본 호출 성공

**소요 시간**: 약 6시간

---

## 📋 PHASE 1: 환경 설정 (2시간)

### TASK 1.1: PostgreSQL 설치 및 설정 (1시간)

#### Option A: Docker 사용 (권장)

```bash
# 1. PostgreSQL 컨테이너 실행
docker run --name soccer-predictor-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=soccer_predictor_v3 \
  -p 5432:5432 \
  -d postgres:14

# 2. 연결 확인
docker exec -it soccer-predictor-db psql -U postgres -c "SELECT version();"

# 3. 데이터베이스 생성 확인
docker exec -it soccer-predictor-db psql -U postgres -l
```

#### Option B: 로컬 설치 (macOS)

```bash
# 1. Homebrew로 PostgreSQL 설치
brew install postgresql@14

# 2. 서비스 시작
brew services start postgresql@14

# 3. 데이터베이스 생성
createdb soccer_predictor_v3

# 4. 연결 확인
psql -d soccer_predictor_v3 -c "SELECT version();"
```

#### Python 드라이버 설치

```bash
cd backend

# 가상환경 활성화
source venv/bin/activate

# PostgreSQL 드라이버 설치
pip install psycopg2-binary

# requirements_v3.txt 업데이트
echo "psycopg2-binary==2.9.9" >> requirements_v3.txt
```

#### 데이터베이스 마이그레이션

```bash
# 1. 환경 변수 임시 설정 (나중에 .env로 이동)
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=soccer_predictor_v3
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres

# 2. 마이그레이션 실행
python init_database_v3.py

# 성공 시 출력:
# ✅ Database connection successful
# ✅ Running migration: 001_initial_schema.sql
# ✅ Migration completed successfully
# ✅ Created 7 tables, 25+ indexes
```

#### 검증

```bash
# 테이블 생성 확인
python -c "
from database.connection import get_connection
conn = get_connection()
cursor = conn.cursor()
cursor.execute(\"SELECT tablename FROM pg_tables WHERE schemaname='public'\")
tables = cursor.fetchall()
print('Created tables:', tables)
cursor.close()
conn.close()
"

# 예상 출력:
# Created tables: [('users',), ('subscriptions',), ('usage_tracking',), ...]
```

✅ **완료 기준**: `python init_database_v3.py` 에러 없이 성공

---

### TASK 1.2: Redis 설치 및 설정 (30분)

#### Option A: Docker (권장)

```bash
# 1. Redis 컨테이너 실행
docker run --name soccer-predictor-redis \
  -p 6379:6379 \
  -d redis:7

# 2. 연결 확인
docker exec -it soccer-predictor-redis redis-cli ping
# 출력: PONG
```

#### Option B: 로컬 설치 (macOS)

```bash
# 1. Homebrew로 설치
brew install redis

# 2. 서비스 시작
brew services start redis

# 3. 연결 확인
redis-cli ping
# 출력: PONG
```

#### Python 클라이언트 설치

```bash
cd backend
source venv/bin/activate

pip install redis

# requirements_v3.txt 업데이트
echo "redis==5.0.1" >> requirements_v3.txt
```

#### 검증

```bash
# Rate Limiter 테스트
python -c "
from middleware.rate_limiter import RateLimiter
limiter = RateLimiter()
print('Redis connection:', limiter.redis_available)
"

# 예상 출력:
# Redis connection: True
```

✅ **완료 기준**: Redis 연결 성공, `redis.ping()` 응답

---

### TASK 1.3: 환경 변수 설정 (30분)

#### .env 파일 생성

```bash
cd backend

# 템플릿 복사
cp .env.v3.example .env

# 편집기로 열기
code .env  # 또는 vim .env
```

#### 필수 변수 설정

```bash
# .env 파일 내용 (최소 설정)

# =============================================================================
# DATABASE - PostgreSQL
# =============================================================================
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=soccer_predictor_v3
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# =============================================================================
# CACHE - Redis
# =============================================================================
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# =============================================================================
# AUTHENTICATION
# =============================================================================
# 🔥 중요: 프로덕션에서는 반드시 변경!
SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-this

# 강력한 시크릿 키 생성 (Python):
# python -c "import secrets; print(secrets.token_urlsafe(32))"

# =============================================================================
# AI - CLAUDE API (나중에 설정)
# =============================================================================
ANTHROPIC_API_KEY=  # 비워둬도 일단 OK
CLAUDE_MODEL_BASIC=claude-sonnet-3-5-20241022
CLAUDE_MODEL_PRO=claude-sonnet-4-5-20250929

# =============================================================================
# PAYMENT - STRIPE (테스트 모드)
# =============================================================================
STRIPE_SECRET_KEY=sk_test_  # Stripe Dashboard에서 복사
STRIPE_PUBLISHABLE_KEY=pk_test_
STRIPE_WEBHOOK_SECRET=whsec_

# =============================================================================
# EXTERNAL APIs
# =============================================================================
ODDS_API_KEY=  # 비워둬도 일단 OK (데모 모드 사용 가능)
```

#### 시크릿 키 생성

```bash
# SECRET_KEY 생성
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"

# JWT_SECRET_KEY 생성
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"

# 출력된 값을 .env 파일에 복사
```

#### 검증

```bash
# 환경 변수 로드 테스트
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('PostgreSQL DB:', os.getenv('POSTGRES_DB'))
print('Secret Key set:', 'SECRET_KEY' in os.environ)
"

# 예상 출력:
# PostgreSQL DB: soccer_predictor_v3
# Secret Key set: True
```

✅ **완료 기준**: .env 파일 존재, 필수 변수 설정 완료

---

## 📋 PHASE 2: 핵심 의존성 설치 (30분)

### TASK 2.1: Python 패키지 설치

```bash
cd backend
source venv/bin/activate

# 핵심 패키지 설치
pip install anthropic stripe redis psycopg2-binary

# 전체 requirements 설치
pip install -r requirements_v3.txt

# 설치 확인
pip list | grep -E "(anthropic|stripe|redis|psycopg2)"
```

**예상 출력**:
```
anthropic      0.18.0
psycopg2-binary 2.9.9
redis          5.0.1
stripe         8.7.0
```

### TASK 2.2: 테스트 실행 (기존 완성 모듈)

```bash
# Phase 1-3 테스트 (33개)
pytest tests/test_auth_handlers.py -v
pytest tests/test_payment_system.py -v

# 전체 테스트
pytest tests/ -v --tb=short

# 예상: 33/33 tests PASSED
```

✅ **완료 기준**: 모든 기존 테스트 통과 (33/33)

---

## 📋 PHASE 3: Claude API 기본 통합 (3시간)

### TASK 3.1: Anthropic API 키 발급 (15분)

#### 단계

1. **계정 생성**
   - 방문: https://console.anthropic.com/
   - Sign Up (이메일 또는 Google 계정)
   - 이메일 인증

2. **API 키 발급**
   - Dashboard → API Keys
   - "Create Key" 클릭
   - 키 이름: "soccer-predictor-dev"
   - 키 복사 (한 번만 표시됨!)

3. **크레딧 확인**
   - 신규 계정: $5 무료 크레딧
   - 테스트에 충분 (약 200회 호출)

4. **.env 파일 업데이트**
   ```bash
   ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
   ```

### TASK 3.2: Claude Client 구현 (2시간)

#### 파일 생성: `backend/services/claude_client.py`

```python
"""
Claude API Client
AI Match Simulation v3.0

Handles all interactions with Anthropic Claude API.
"""

import anthropic
import os
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class ClaudeError(Exception):
    """Base exception for Claude API errors."""
    pass


class ClaudeClient:
    """
    Claude API client for AI match simulation.

    Features:
    - Tier-based model selection (BASIC/PRO)
    - Cost tracking
    - Error handling and retries
    - Prompt engineering for football analysis
    """

    def __init__(self):
        """Initialize Claude client with API key from environment."""
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ClaudeError("ANTHROPIC_API_KEY not set in environment")

        self.client = anthropic.Anthropic(api_key=self.api_key)

        # Model configuration
        self.models = {
            'BASIC': os.getenv('CLAUDE_MODEL_BASIC', 'claude-sonnet-3-5-20241022'),
            'PRO': os.getenv('CLAUDE_MODEL_PRO', 'claude-sonnet-4-5-20250929')
        }

    def simulate_match(
        self,
        home_team: str,
        away_team: str,
        home_data: Dict,
        away_data: Dict,
        tier: str = 'BASIC'
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Simulate a match using Claude AI.

        Args:
            home_team: Home team name
            away_team: Away team name
            home_data: Home team data (squad, form, etc.)
            away_data: Away team data
            tier: User tier ('BASIC' or 'PRO')

        Returns:
            Tuple of (success, result_dict, error_message)

        Example result_dict:
        {
            'home_win': 45.5,
            'draw': 28.0,
            'away_win': 26.5,
            'predicted_score': '2-1',
            'confidence': 0.78,
            'key_insights': ['...']
        }
        """
        try:
            # 1. Select model based on tier
            model = self.models.get(tier, self.models['BASIC'])

            # 2. Construct prompt
            prompt = self._build_match_prompt(
                home_team, away_team, home_data, away_data
            )

            # 3. Call Claude API
            logger.info(f"Calling Claude API (model={model}) for {home_team} vs {away_team}")
            start_time = datetime.now()

            response = self.client.messages.create(
                model=model,
                max_tokens=2048,
                temperature=0.3,  # Lower temperature for more consistent predictions
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"Claude API responded in {elapsed:.2f}s")

            # 4. Parse response
            result = self._parse_response(response)

            # 5. Log usage (for cost tracking)
            self._log_usage(response, model, tier)

            return True, result, None

        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            return False, None, f"API Error: {str(e)}"

        except Exception as e:
            logger.error(f"Unexpected error in simulate_match: {e}")
            return False, None, f"Internal Error: {str(e)}"

    def _build_match_prompt(
        self,
        home_team: str,
        away_team: str,
        home_data: Dict,
        away_data: Dict
    ) -> str:
        """
        Build optimized prompt for match simulation.

        Prompt engineering principles:
        - Clear structure
        - Specific output format (JSON)
        - Domain expertise context
        - Numerical precision
        """
        return f"""You are a professional football (soccer) analyst with expertise in EPL match prediction.

**Match Details:**
- Home Team: {home_team}
- Away Team: {away_team}

**Home Team Data:**
{self._format_team_data(home_data)}

**Away Team Data:**
{self._format_team_data(away_data)}

**Task:**
Analyze this EPL match and provide probabilities for:
1. Home Win
2. Draw
3. Away Win

**Output Format (JSON only):**
{{
    "home_win": 45.5,
    "draw": 28.0,
    "away_win": 26.5,
    "predicted_score": "2-1",
    "confidence": 0.78,
    "key_insights": [
        "Home team has stronger attack (avg rating 4.2 vs 3.8)",
        "Away team weak in defense (3.1 rating)",
        "Home advantage worth ~5% probability boost"
    ]
}}

**Requirements:**
- Probabilities must sum to 100
- Confidence: 0.0 to 1.0 (1.0 = very confident)
- Predicted score: most likely scoreline
- Key insights: 3-5 bullet points

Respond with JSON only, no additional text.
"""

    def _format_team_data(self, data: Dict) -> str:
        """Format team data for prompt."""
        # TODO: Implement based on actual data structure
        # For now, simple formatting
        return f"""
- Squad Strength: {data.get('avg_rating', 'N/A')}
- Recent Form: {data.get('form', 'N/A')}
- Key Players: {data.get('key_players', [])}
"""

    def _parse_response(self, response) -> Dict:
        """
        Parse Claude API response into structured result.

        Handles:
        - JSON extraction
        - Validation
        - Error recovery
        """
        import json

        try:
            # Extract text content
            text = response.content[0].text

            # Try to parse as JSON
            result = json.loads(text)

            # Validate required fields
            required = ['home_win', 'draw', 'away_win']
            for field in required:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")

            # Validate probabilities sum to ~100
            total = result['home_win'] + result['draw'] + result['away_win']
            if not 99.0 <= total <= 101.0:
                logger.warning(f"Probabilities sum to {total}, not 100")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {e}")
            logger.debug(f"Response text: {text}")

            # Fallback: return default values
            return {
                'home_win': 33.3,
                'draw': 33.3,
                'away_win': 33.3,
                'predicted_score': '1-1',
                'confidence': 0.3,
                'key_insights': ['Error parsing AI response']
            }

        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return {
                'home_win': 33.3,
                'draw': 33.3,
                'away_win': 33.3,
                'predicted_score': '1-1',
                'confidence': 0.3,
                'key_insights': ['Internal error']
            }

    def _log_usage(self, response, model: str, tier: str):
        """
        Log API usage for cost tracking.

        Cost calculation:
        - Claude Sonnet 3.5/4.5: $3/M input, $15/M output
        """
        usage = response.usage

        input_tokens = usage.input_tokens
        output_tokens = usage.output_tokens

        # Cost per 1M tokens
        input_cost_per_m = 3.0
        output_cost_per_m = 15.0

        # Calculate cost
        input_cost = (input_tokens / 1_000_000) * input_cost_per_m
        output_cost = (output_tokens / 1_000_000) * output_cost_per_m
        total_cost = input_cost + output_cost

        logger.info(
            f"Claude API usage - "
            f"Model: {model}, "
            f"Tier: {tier}, "
            f"Tokens: {input_tokens} in + {output_tokens} out, "
            f"Cost: ${total_cost:.4f}"
        )

        # TODO: Store in database (usage_tracking table)
        # This will be implemented in Phase 4


# Singleton instance
_claude_client = None


def get_claude_client() -> ClaudeClient:
    """Get singleton Claude client instance."""
    global _claude_client
    if _claude_client is None:
        _claude_client = ClaudeClient()
    return _claude_client
```

### TASK 3.3: 테스트 스크립트 작성 (30분)

#### 파일 생성: `backend/tests/test_claude_client.py`

```python
"""
Test Claude API Client
"""

import pytest
import os
from services.claude_client import ClaudeClient, get_claude_client


@pytest.fixture
def skip_if_no_api_key():
    """Skip tests if ANTHROPIC_API_KEY not set."""
    if not os.getenv('ANTHROPIC_API_KEY'):
        pytest.skip("ANTHROPIC_API_KEY not set")


def test_client_initialization(skip_if_no_api_key):
    """Test Claude client can be initialized."""
    client = ClaudeClient()
    assert client.api_key is not None
    assert client.client is not None


def test_simulate_match_basic_tier(skip_if_no_api_key):
    """Test basic match simulation (BASIC tier)."""
    client = get_claude_client()

    # Simple test data
    home_data = {
        'avg_rating': 4.2,
        'form': 'WWDWL',
        'key_players': ['Saka', 'Odegaard']
    }

    away_data = {
        'avg_rating': 3.8,
        'form': 'LWLDD',
        'key_players': ['Bruno Fernandes']
    }

    success, result, error = client.simulate_match(
        home_team='Arsenal',
        away_team='Manchester United',
        home_data=home_data,
        away_data=away_data,
        tier='BASIC'
    )

    assert success is True
    assert error is None
    assert result is not None

    # Validate result structure
    assert 'home_win' in result
    assert 'draw' in result
    assert 'away_win' in result
    assert 'predicted_score' in result
    assert 'confidence' in result

    # Validate probabilities
    total = result['home_win'] + result['draw'] + result['away_win']
    assert 99.0 <= total <= 101.0

    print(f"\n✅ Simulation Result:")
    print(f"   Home Win: {result['home_win']}%")
    print(f"   Draw: {result['draw']}%")
    print(f"   Away Win: {result['away_win']}%")
    print(f"   Predicted: {result['predicted_score']}")
    print(f"   Confidence: {result['confidence']}")


def test_simulate_match_pro_tier(skip_if_no_api_key):
    """Test match simulation with PRO tier (better model)."""
    client = get_claude_client()

    home_data = {'avg_rating': 4.5, 'form': 'WWWWW'}
    away_data = {'avg_rating': 3.5, 'form': 'LLLLL'}

    success, result, error = client.simulate_match(
        home_team='Manchester City',
        away_team='Sheffield United',
        home_data=home_data,
        away_data=away_data,
        tier='PRO'
    )

    assert success is True
    assert result['home_win'] > 50  # City should be heavy favorites
    print(f"\n✅ PRO Tier Simulation: {result}")


def test_singleton_pattern():
    """Test that get_claude_client returns same instance."""
    client1 = get_claude_client()
    client2 = get_claude_client()
    assert client1 is client2
```

### TASK 3.4: 실행 및 검증 (15분)

```bash
cd backend
source venv/bin/activate

# 1. 환경 변수 확인
echo $ANTHROPIC_API_KEY
# (키가 출력되어야 함)

# 2. 테스트 실행
pytest tests/test_claude_client.py -v -s

# 예상 출력:
# test_claude_client.py::test_client_initialization PASSED
# test_claude_client.py::test_simulate_match_basic_tier PASSED
#   ✅ Simulation Result:
#      Home Win: 52.3%
#      Draw: 25.1%
#      Away Win: 22.6%
#      Predicted: 2-1
#      Confidence: 0.76
# test_claude_client.py::test_simulate_match_pro_tier PASSED

# 3개 테스트 통과 확인
```

✅ **완료 기준**: Claude API 호출 성공, 테스트 통과 (3/3)

---

## 🎯 완료 체크리스트

### Phase 1: 환경 설정
- [ ] PostgreSQL 설치 및 연결 (Docker 또는 로컬)
- [ ] Redis 설치 및 연결
- [ ] .env 파일 생성 (필수 변수 설정)
- [ ] 시크릿 키 생성 (SECRET_KEY, JWT_SECRET_KEY)
- [ ] 데이터베이스 마이그레이션 실행 (`python init_database_v3.py`)

### Phase 2: 의존성
- [ ] psycopg2-binary 설치
- [ ] anthropic 설치
- [ ] stripe 설치
- [ ] redis 설치
- [ ] 기존 테스트 통과 (33/33)

### Phase 3: Claude API
- [ ] Anthropic API 키 발급
- [ ] claude_client.py 구현
- [ ] test_claude_client.py 작성
- [ ] 테스트 실행 성공 (3/3)

---

## 📊 성공 지표

### 기술적 검증
- ✅ PostgreSQL 7 테이블 생성 확인
- ✅ Redis PING 응답
- ✅ .env 파일 변수 로드 성공
- ✅ Claude API 호출 성공 (응답 <5초)
- ✅ 전체 테스트 통과 (36/36: 기존 33 + Claude 3)

### 다음 단계 준비
- ✅ 핵심 인프라 작동 (DB, Cache, AI)
- ✅ API 엔드포인트 구현 준비 완료
- ✅ 통합 테스트 시작 가능

---

## 🚨 문제 발생 시 (Troubleshooting)

### PostgreSQL 연결 실패

**증상**: `psycopg2.OperationalError: could not connect`

**해결**:
```bash
# 1. PostgreSQL 실행 확인
docker ps | grep postgres
# 또는
brew services list | grep postgres

# 2. 포트 충돌 확인
lsof -i :5432

# 3. 연결 설정 확인 (.env)
echo $POSTGRES_HOST
echo $POSTGRES_PORT
```

### Redis 연결 실패

**증상**: `redis.exceptions.ConnectionError`

**해결**:
```bash
# 1. Redis 실행 확인
docker ps | grep redis
# 또는
brew services list | grep redis

# 2. 연결 테스트
redis-cli ping
```

### Claude API 오류

**증상**: `anthropic.APIError: invalid_api_key`

**해결**:
```bash
# 1. API 키 확인
echo $ANTHROPIC_API_KEY

# 2. .env 파일 확인
cat backend/.env | grep ANTHROPIC

# 3. 키 재발급
# https://console.anthropic.com/ → API Keys
```

---

## 📞 지원 채널

### 공식 문서
- PostgreSQL: https://www.postgresql.org/docs/
- Redis: https://redis.io/docs/
- Anthropic: https://docs.anthropic.com/
- Stripe: https://stripe.com/docs/api

### 커뮤니티
- Stack Overflow: [postgresql], [redis], [anthropic-claude]
- Discord: [서버 링크 필요]
- GitHub Issues: [프로젝트 리포지토리]

---

## 🎉 완료 후 다음 단계

### Immediate (내일)
1. API 엔드포인트 구현 시작
   - `backend/api/v1/simulation.py`
   - POST /api/v1/simulate

2. 프론트엔드 연동
   - SimulationForm 컴포넌트
   - API 호출 및 결과 표시

3. 통합 테스트
   - E2E 시나리오 작성
   - 사용자 회원가입 → 결제 → AI 시뮬레이션

### Short-term (이번 주)
1. Stripe 프로덕션 테스트
2. Rate Limiting 검증
3. 성능 최적화 (캐싱)
4. 에러 모니터링 (Sentry)

---

**작성자**: PMO
**업데이트**: 완료 시 체크박스 업데이트
**다음 보고**: 내일 (진행률 공유)

---

**END OF IMMEDIATE ACTION PLAN**

*"설정부터 완벽하게, 실행은 빠르게."*
