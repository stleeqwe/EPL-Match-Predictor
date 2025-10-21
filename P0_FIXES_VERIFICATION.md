# P0 결함 수정 검증 가이드

## ✅ 수정 완료된 P0 결함

1. **P0-1**: POST body 읽기 문제 (simulation_routes.py)
2. **P0-2**: SSE Heartbeat 및 타임아웃 처리 (enriched_simulation_service.py + useSSESimulation.js)
3. **P0-3**: 인증 및 Rate limiting (simulation_routes.py)

---

## 🧪 검증 방법

### 테스트 1: POST body 읽기 정상 동작 확인

```bash
# Backend 서버 실행
cd backend
python app.py

# 별도 터미널에서 테스트
curl -X POST http://localhost:5001/api/v1/simulation/enriched/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TEST_TOKEN" \
  -d '{"home_team":"Arsenal","away_team":"Liverpool"}' \
  --no-buffer
```

**기대 결과**:
```
event: started
data: {"timestamp":"2025-10-17T...","message":"Arsenal vs Liverpool 시뮬레이션 시작",...}

event: loading_home_team
data: {"timestamp":"2025-10-17T...","message":"Arsenal 데이터 로딩 중..."}

event: home_team_loaded
data: {"timestamp":"2025-10-17T...","message":"Arsenal 데이터 로딩 완료 (11명, 4-3-3)"}

...

event: heartbeat
data: {"timestamp":"2025-10-17T...","message":"Connection keepalive","elapsed":15.2}

...

event: completed
data: {"timestamp":"2025-10-17T...","total_time":25.3,"result":{...}}
```

**❌ 실패 시 에러 메시지**:
- `Missing request body` → POST body 읽기 실패
- `HTTP 401 Unauthorized` → 인증 토큰 없음
- `HTTP 429 Rate limit exceeded` → Rate limit 초과

---

### 테스트 2: Heartbeat 동작 확인

**시나리오**: 30초 이상 걸리는 시뮬레이션에서 heartbeat 수신 확인

```bash
# 위 curl 명령어 실행 후, 출력에서 "heartbeat" 이벤트 확인
curl -X POST http://localhost:5001/api/v1/simulation/enriched/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TEST_TOKEN" \
  -d '{"home_team":"Arsenal","away_team":"Man City"}' \
  --no-buffer | grep heartbeat
```

**기대 결과**:
```
event: heartbeat
event: heartbeat
event: heartbeat
```

**검증 포인트**:
- ✅ 15초마다 heartbeat 이벤트 수신
- ✅ 연결이 끊어지지 않고 완료까지 진행
- ✅ 프론트엔드 콘솔에 `SSE heartbeat received` 로그 출력

---

### 테스트 3: 인증 및 Rate limiting 확인

#### 3-1. 인증 실패 테스트

```bash
# 토큰 없이 요청
curl -X POST http://localhost:5001/api/v1/simulation/enriched/stream \
  -H "Content-Type: application/json" \
  -d '{"home_team":"Arsenal","away_team":"Liverpool"}'
```

**기대 결과**:
```json
{
  "error": "Missing authorization token"
}
```
**HTTP Status**: `401 Unauthorized`

---

#### 3-2. Rate limiting 테스트

```bash
# 연속으로 10번 요청 (Rate limit 초과)
for i in {1..10}; do
  echo "Request $i"
  curl -X POST http://localhost:5001/api/v1/simulation/enriched/stream \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer YOUR_TEST_TOKEN" \
    -d '{"home_team":"Arsenal","away_team":"Liverpool"}' \
    --no-buffer &
done
wait
```

**기대 결과**:
- 처음 몇 개 요청: `200 OK` (정상 스트리밍)
- Rate limit 초과 후: `429 Too Many Requests`

```json
{
  "error": "Rate limit exceeded",
  "reset_at": "2025-10-17T12:34:56Z",
  "message": "SSE streaming rate limit reached. Please wait before retrying."
}
```

---

### 테스트 4: 프론트엔드 통합 테스트

```bash
# Frontend 서버 실행
cd frontend
npm start
```

**테스트 시나리오**:
1. 브라우저에서 `http://localhost:3000` 접속
2. Arsenal vs Liverpool 시뮬레이션 시작
3. 개발자 도구 콘솔 열기 (F12)

**검증 포인트**:
- ✅ 진행률 바가 0% → 100%로 증가
- ✅ 이벤트 타임라인에 heartbeat **제외** 이벤트만 표시
- ✅ 콘솔에 `SSE heartbeat received` 로그 (15초마다)
- ✅ 30초 이상 시뮬레이션도 끊김 없이 완료
- ✅ 완료 시 결과 화면 표시

**네트워크 탭 확인**:
- Request Method: `POST`
- Status: `200 OK`
- Type: `text/event-stream`
- Size: `(streaming)` (완료될 때까지 계속 증가)

---

## 🐛 트러블슈팅

### 문제 1: `Missing authorization token`

**원인**: 인증 토큰이 없음

**해결책**:
```bash
# 테스트 토큰 생성 (backend)
python -c "from middleware.auth_middleware import generate_test_token; print(generate_test_token())"

# 출력된 토큰을 Authorization 헤더에 추가
curl -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

---

### 문제 2: Heartbeat가 수신되지 않음

**원인**: AI 스트리밍이 15초 이내에 완료되어 heartbeat가 필요 없음

**해결책**:
- Man City vs Liverpool 같은 복잡한 매치업 테스트 (30초+ 소요)
- 또는 `HEARTBEAT_INTERVAL`을 5초로 변경하여 테스트

```python
# enriched_simulation_service.py (테스트용)
HEARTBEAT_INTERVAL = 5  # 5초로 변경
```

---

### 문제 3: CORS 에러 (프론트엔드)

**에러 메시지**:
```
Access to fetch at 'http://localhost:5001/api/v1/simulation/enriched/stream'
from origin 'http://localhost:3000' has been blocked by CORS policy
```

**원인**: CORS 헤더가 적용되지 않음

**해결책**:
1. 백엔드 재시작 확인
2. `simulation_routes.py:536-538` 확인:
```python
'Access-Control-Allow-Origin': '*',
'Access-Control-Allow-Headers': 'Content-Type, Authorization',
'Access-Control-Allow-Methods': 'POST, OPTIONS'
```

---

## ✅ 수정 전후 비교

| 항목 | 수정 전 | 수정 후 |
|-----|--------|--------|
| **POST body 읽기** | ❌ Generator 내부에서 읽기 실패 | ✅ 외부 스코프에서 정상 읽기 |
| **30초+ 시뮬레이션** | ❌ 타임아웃으로 연결 끊김 | ✅ Heartbeat로 연결 유지 |
| **인증** | ❌ 누구나 접근 가능 | ✅ @require_auth 보호 |
| **Rate limiting** | ❌ 무제한 호출 가능 | ✅ Tier별 제한 적용 |
| **CORS** | ❌ 프론트엔드 연결 실패 | ✅ CORS 헤더 추가 |

---

## 📊 성능 테스트 (선택사항)

### 동시 사용자 10명 테스트

```bash
# Apache Bench 사용
ab -n 10 -c 10 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -p request.json \
  http://localhost:5001/api/v1/simulation/enriched/stream
```

**request.json**:
```json
{"home_team":"Arsenal","away_team":"Liverpool"}
```

**기대 결과**:
- Rate limiting이 정상 작동하여 일부 요청은 429 응답
- 허용된 요청은 모두 정상 완료

---

## 🎉 다음 단계

P0 결함 수정 완료 후 권장 작업:

1. **P1 결함 수정** (1-3일 소요)
   - 재연결 로직 구현
   - 메모리 누수 방지
   - 진행률 역행 방지

2. **통합 테스트 작성**
   - E2E 테스트 시나리오
   - Rate limiting 테스트
   - Heartbeat 테스트

3. **프로덕션 환경 설정**
   - CORS origin을 `*`에서 특정 도메인으로 변경
   - Nginx timeout 설정 (120초)
   - Gunicorn worker 수 조정

---

**문서 생성일**: 2025-10-17
**수정 범위**: P0 결함 3건
**영향받는 파일**:
- `backend/api/v1/simulation_routes.py`
- `backend/services/enriched_simulation_service.py`
- `frontend/src/hooks/useSSESimulation.js`
