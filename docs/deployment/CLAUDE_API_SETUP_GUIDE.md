# 🔑 Claude API Key Setup Guide
**EPL Predictor - AI Simulation Integration**

Last Updated: 2025-10-09

---

## 📋 Step 1: Claude API 키 발급

### 1. Anthropic Console 접속

브라우저에서 다음 URL로 이동:
```
https://console.anthropic.com/
```

### 2. 계정 생성 또는 로그인

- 새 계정: **Sign Up** 버튼 클릭
- 기존 계정: **Sign In** 버튼 클릭

**필요한 정보**:
- 이메일 주소
- 비밀번호
- (선택) Google 계정으로 로그인

### 3. API Keys 메뉴로 이동

로그인 후:
1. 왼쪽 사이드바에서 **API Keys** 클릭
2. 또는 직접 URL 접속:
   ```
   https://console.anthropic.com/settings/keys
   ```

### 4. API 키 생성

1. **Create Key** 버튼 클릭
2. 키 이름 입력 (예: "EPL-Predictor-Production")
3. **Create Key** 확인
4. ⚠️ **중요**: 생성된 키를 안전한 곳에 복사/저장
   - 키는 한 번만 표시됩니다!
   - 다시 볼 수 없으므로 즉시 저장하세요

**생성된 키 형식**:
```
sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 💳 Step 2: 결제 정보 설정

### Claude API는 사용량 기반 과금입니다

1. **Settings** → **Billing** 메뉴로 이동
2. **Add payment method** 클릭
3. 신용카드 정보 입력
4. 초기 크레딧 $5 추가 (테스트용)

**가격 (2025년 기준)**:
```
Claude Sonnet 3.5:
- Input:  $3.00 per 1M tokens
- Output: $15.00 per 1M tokens

Claude Sonnet 4.5:
- Input:  $3.00 per 1M tokens
- Output: $15.00 per 1M tokens

예상 비용:
- Standard AI 시뮬레이션: ~$0.08/회
- Deep AI 시뮬레이션: ~$0.29/회
```

### Usage Limits 설정 (권장)

1. **Settings** → **Limits** 메뉴
2. **Monthly spending limit** 설정
   - 테스트 단계: $50/월
   - 운영 단계: $500/월
3. **Notification threshold** 설정
   - 80% 도달 시 이메일 알림

---

## 🔧 Step 3: 환경변수 설정

### Backend 환경변수 설정

#### Option 1: `.env` 파일 생성 (로컬 개발)

```bash
cd /Users/pukaworks/Desktop/soccer-predictor/backend
nano .env
```

**`.env` 파일 내용**:
```bash
# Claude API Configuration
CLAUDE_API_KEY=sk-ant-api03-your-actual-key-here
CLAUDE_ENABLED=true
CLAUDE_TIMEOUT=60
CLAUDE_MAX_RETRIES=3
CLAUDE_CACHE_TTL=3600

# Model Selection
CLAUDE_MODEL_BASIC=claude-sonnet-3-5-20250219
CLAUDE_MODEL_PRO=claude-sonnet-4-5-20250514

# Feature Flags
ENABLE_STANDARD_AI=true
ENABLE_DEEP_AI=true
ENABLE_MONTE_CARLO=false

# Rate Limiting
MAX_SIMULATIONS_BASIC_HOURLY=5
MAX_SIMULATIONS_BASIC_DAILY=10
MAX_SIMULATIONS_PRO_DAILY=200

# Cost Tracking
TRACK_TOKEN_USAGE=true
LOG_API_COSTS=true
```

#### Option 2: 환경변수 직접 설정 (터미널)

```bash
export CLAUDE_API_KEY="sk-ant-api03-your-actual-key-here"
export CLAUDE_ENABLED="true"
export CLAUDE_TIMEOUT="60"
```

#### Option 3: AWS Secrets Manager (프로덕션)

프로덕션 배포 시 사용:
```bash
aws secretsmanager create-secret \
  --name epl-predictor/claude-api-key \
  --secret-string "sk-ant-api03-your-actual-key-here"
```

---

## ✅ Step 4: API 키 테스트

### 간단한 테스트 스크립트 작성

```bash
cd /Users/pukaworks/Desktop/soccer-predictor/backend
nano test_claude_api.py
```

**`test_claude_api.py` 내용**:
```python
#!/usr/bin/env python3
"""
Claude API Connection Test
Tests if the API key is valid and working
"""

import os
from anthropic import Anthropic

def test_claude_api():
    """Test Claude API connection"""

    # Load API key
    api_key = os.getenv('CLAUDE_API_KEY')

    if not api_key:
        print("❌ CLAUDE_API_KEY not found in environment variables")
        print("Please set it using: export CLAUDE_API_KEY='your-key-here'")
        return False

    print(f"✅ API Key found: {api_key[:20]}...")

    try:
        # Initialize client
        client = Anthropic(api_key=api_key)
        print("✅ Client initialized")

        # Test API call
        print("\n🧪 Testing API call...")
        response = client.messages.create(
            model="claude-sonnet-3-5-20250219",
            max_tokens=100,
            messages=[
                {
                    "role": "user",
                    "content": "Say 'Hello from EPL Predictor!' in one sentence."
                }
            ]
        )

        # Display results
        print(f"\n✅ API call successful!")
        print(f"📊 Model: {response.model}")
        print(f"📊 Input tokens: {response.usage.input_tokens}")
        print(f"📊 Output tokens: {response.usage.output_tokens}")
        print(f"\n💬 Response: {response.content[0].text}")

        # Calculate cost
        cost = (response.usage.input_tokens / 1_000_000 * 3.0) + \
               (response.usage.output_tokens / 1_000_000 * 15.0)
        print(f"\n💰 Cost: ${cost:.6f}")

        return True

    except Exception as e:
        print(f"\n❌ API call failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Claude API Connection Test")
    print("=" * 60)

    success = test_claude_api()

    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed! API key is working correctly.")
        print("You can now proceed with AI simulation development.")
    else:
        print("❌ Tests failed. Please check your API key and try again.")
    print("=" * 60)
```

### 테스트 실행

```bash
# 1. Anthropic SDK 설치 (아직 안했다면)
pip install anthropic

# 2. 환경변수 설정
export CLAUDE_API_KEY="sk-ant-api03-your-actual-key-here"

# 3. 테스트 실행
python test_claude_api.py
```

**예상 출력**:
```
============================================================
Claude API Connection Test
============================================================
✅ API Key found: sk-ant-api03-xxxxx...
✅ Client initialized

🧪 Testing API call...

✅ API call successful!
📊 Model: claude-sonnet-3-5-20250219
📊 Input tokens: 15
📊 Output tokens: 12

💬 Response: Hello from EPL Predictor!

💰 Cost: $0.000225

============================================================
✅ All tests passed! API key is working correctly.
You can now proceed with AI simulation development.
============================================================
```

---

## 🔒 Step 5: API 키 보안

### ⚠️ 중요: API 키는 절대 노출하지 마세요!

#### ❌ 하지 말아야 할 것

```python
# ❌ 코드에 직접 하드코딩
api_key = "sk-ant-api03-xxxxxxxx"

# ❌ Git에 커밋
git add .env
git commit -m "Added API key"

# ❌ 프론트엔드에서 직접 사용
const CLAUDE_KEY = "sk-ant-api03-xxxxxxxx"
```

#### ✅ 해야 할 것

```python
# ✅ 환경변수에서 로드
api_key = os.getenv('CLAUDE_API_KEY')

# ✅ .env 파일을 .gitignore에 추가
echo ".env" >> .gitignore

# ✅ 백엔드 API에서만 사용
# 프론트엔드 → 백엔드 API → Claude API
```

### `.gitignore` 업데이트

```bash
cd /Users/pukaworks/Desktop/soccer-predictor
nano .gitignore
```

**추가할 내용**:
```
# Environment variables
.env
.env.local
.env.production
.env.*.local

# API Keys
**/claude_api_key.txt
**/api_keys.json
**/*secret*
**/*credentials*

# Python
__pycache__/
*.py[cod]
venv/
```

---

## 📊 Step 6: Usage Monitoring

### Anthropic Console에서 모니터링

1. **Console** → **Usage** 메뉴로 이동
2. 실시간 사용량 확인:
   - 총 토큰 사용량
   - API 호출 횟수
   - 비용 누적
   - 모델별 사용량

### 알림 설정

1. **Settings** → **Notifications**
2. 알림 받을 조건 설정:
   - 예산 80% 도달 시
   - 일일 사용량 임계값 초과 시
   - 오류율 증가 시

---

## 🚀 Step 7: Integration Checklist

프로젝트 통합 전 체크리스트:

- [ ] Claude API 키 발급 완료
- [ ] 결제 정보 등록 완료
- [ ] 사용량 제한 설정 완료
- [ ] `.env` 파일 생성 및 API 키 추가
- [ ] `.gitignore`에 `.env` 추가
- [ ] Anthropic SDK 설치 (`pip install anthropic`)
- [ ] API 키 테스트 스크립트 실행 성공
- [ ] Backend config에서 API 키 로드 확인
- [ ] 첫 API 호출 성공 및 비용 확인

**모두 완료되면 AI 시뮬레이션 개발 시작 가능! 🎉**

---

## 🆘 Troubleshooting

### 문제 1: "Invalid API Key" 오류

**원인**:
- API 키가 잘못 복사됨
- 환경변수가 제대로 설정되지 않음

**해결**:
```bash
# 환경변수 확인
echo $CLAUDE_API_KEY

# 다시 설정
export CLAUDE_API_KEY="sk-ant-api03-correct-key-here"

# Python에서 확인
python -c "import os; print(os.getenv('CLAUDE_API_KEY'))"
```

### 문제 2: "Insufficient Credits" 오류

**원인**:
- 결제 정보 미등록
- 크레딧 부족

**해결**:
1. Console → Billing
2. Add payment method
3. Add credits ($5 최소)

### 문제 3: "Rate Limit Exceeded" 오류

**원인**:
- 너무 많은 요청
- Free tier 제한 (분당 5회)

**해결**:
- 요청 간격 추가 (time.sleep)
- Rate limiting 구현
- Paid tier로 업그레이드

### 문제 4: Timeout 오류

**원인**:
- 네트워크 느림
- 프롬프트가 너무 김

**해결**:
```python
client = Anthropic(
    api_key=api_key,
    timeout=60.0  # 60초로 증가
)
```

---

## 💡 Best Practices

### 1. API 키 로테이션
- 3개월마다 새 키 생성
- 구 키는 1주일 후 삭제

### 2. 환경별 키 분리
- Development: 테스트용 키
- Production: 운영용 키
- Testing: CI/CD용 키

### 3. 비용 최적화
- Prompt caching 활용 (50% 절감)
- 불필요한 토큰 제거
- 응답 길이 제한 (max_tokens)

### 4. 에러 핸들링
```python
from anthropic import APIError, APITimeoutError

try:
    response = client.messages.create(...)
except APITimeoutError:
    # 타임아웃 재시도
    pass
except APIError as e:
    # API 오류 로깅
    logger.error(f"Claude API error: {e}")
```

---

## 📞 Support

**Anthropic Support**:
- Email: support@anthropic.com
- Documentation: https://docs.anthropic.com
- Status: https://status.anthropic.com

**프로젝트 문의**:
- GitHub Issues
- Team Slack Channel

---

**Document Version**: 1.0
**Last Updated**: 2025-10-09
**Status**: ✅ Setup Guide Complete
**Next Step**: Run test_claude_api.py
