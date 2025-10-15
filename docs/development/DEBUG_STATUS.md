# 🔍 디버깅 시스템 설치 완료

**날짜:** 2025-10-03 08:30
**상태:** ✅ 완료

---

## 📋 설치된 디버깅 기능

### 1. 실시간 로깅 시스템

**파일:** `backend/api/app.py`

#### 추가된 로깅 포인트:

✅ 요청 수신 시점
```python
logger.info("🔍 DEBUG: /api/predict endpoint called")
logger.info(f"📥 Incoming request data: {data}")
```

✅ 입력 파라미터
```python
logger.info(f"🏠 Home team: {home_team}")
logger.info(f"✈️  Away team: {away_team}")
logger.info(f"🤖 Model type: {model_type}")
logger.info(f"⚖️  Weights - Stats: {stats_weight}, Personal: {personal_weight}")
```

✅ 특징 생성 단계
```python
logger.info(f"🔧 Creating match features...")
logger.info(f"✅ Features created successfully")
# 또는 에러 시:
logger.error(f"❌ ERROR in feature creation: {error}")
```

✅ 예측 진행 상황
```python
logger.info(f"📊 Using statistical (Dixon-Coles) model")
logger.info(f"✅ Dixon-Coles prediction successful")
# 또는:
logger.info(f"👤 Using personal (player ratings) model")
logger.info(f"🔀 Using hybrid model")
```

✅ 최종 결과
```python
logger.info(f"📤 Final prediction to return: {prediction}")
logger.info(f"✅ Prediction completed successfully!")
```

✅ 에러 발생 시 상세 추적
```python
logger.error(f"❌❌❌ CRITICAL ERROR in /api/predict ❌❌❌")
logger.error(f"Error type: {type(e).__name__}")
logger.error(f"Error message: {str(e)}")
logger.error(traceback.format_exc())
```

---

## 🛠️ 모니터링 도구

### 1. 로그 파일
- **위치:** `/tmp/flask_debug.log`
- **내용:** 모든 Flask 출력 (startup, requests, errors)
- **확인:** `tail -f /tmp/flask_debug.log`

### 2. 디버그 모니터 스크립트
- **파일:** `backend/watch_debug.sh`
- **기능:** 중요한 디버그 정보만 필터링하여 표시
- **사용법:**
  ```bash
  cd backend
  ./watch_debug.sh
  ```

---

## 🧪 테스트 결과

### curl 테스트 (성공)

```bash
$ curl -X POST http://localhost:5001/api/predict \
  -H "Content-Type: application/json" \
  -d '{"home_team":"Arsenal","away_team":"Chelsea","model_type":"statistical"}'

✅ 응답: 200 OK
⏱️  시간: <0.1초
📊 결과:
{
  "home_win": 47.83,
  "draw": 27.39,
  "away_win": 24.79,
  "expected_home_goals": 1.38,
  "expected_away_goals": 0.91
}
```

### 로그 출력 (성공 케이스)

```
INFO:app:================================================================================
INFO:app:🔍 DEBUG: /api/predict endpoint called
INFO:app:================================================================================
INFO:app:📥 Incoming request data: {'home_team': 'Arsenal', 'away_team': 'Chelsea', 'model_type': 'statistical'}
INFO:app:🏠 Home team: Arsenal
INFO:app:✈️  Away team: Chelsea
INFO:app:🤖 Model type: statistical
INFO:app:⚖️  Weights - Stats: 0.75, Personal: 0.25
INFO:app:⏰ Temporal - Recent5: 0.5, Current: 0.35, Last: 0.15
INFO:app:🔧 Creating match features...
INFO:app:✅ Features created successfully
INFO:app:🎯 Starting prediction with model_type: statistical
INFO:app:📊 Using statistical (Dixon-Coles) model
INFO:app:🔍 dixon_coles_model object: <models.dixon_coles.DixonColesModel object at 0x1507995b0>
INFO:app:🔍 Has predict_match method: True
INFO:app:✅ Dixon-Coles prediction successful
INFO:app:📤 Final prediction to return: {...}
INFO:app:✅ Prediction completed successfully!
INFO:app:================================================================================
INFO:werkzeug:127.0.0.1 - - [03/Oct/2025 08:27:29] "POST /api/predict HTTP/1.1" 200 -
```

---

## 📖 사용 방법

### 실시간 디버깅 워크플로우

1. **백엔드 시작 (디버깅 활성화)**
   ```bash
   cd backend
   export FLASK_APP=api/app.py
   export FLASK_ENV=development
   source venv/bin/activate
   python3 -m flask run --host=0.0.0.0 --port=5001 > /tmp/flask_debug.log 2>&1 &
   ```

2. **디버그 모니터 시작 (별도 터미널)**
   ```bash
   cd backend
   ./watch_debug.sh
   ```

3. **프론트엔드에서 예측 시도**
   - 브라우저: http://localhost:3000
   - 팀 선택
   - 예측 버튼 클릭

4. **로그 확인**
   - watch_debug.sh 터미널에서 실시간 로그 확인
   - 에러 발생 시 정확한 위치와 원인 표시됨

---

## 🎯 다음 단계

이제 프론트엔드에서 예측을 시도하면 다음을 확인할 수 있습니다:

### 성공 시:
- ✅ 모든 단계가 순차적으로 로그에 표시
- ✅ 200 응답 코드
- ✅ 예측 결과 반환

### 실패 시:
- ❌ 정확한 오류 발생 지점 표시
- ❌ 오류 타입 (KeyError, AttributeError 등)
- ❌ 전체 스택 트레이스
- ❌ 실패한 팀 이름 또는 파라미터

---

## 🔍 디버깅 시나리오별 대응

### 시나리오 1: "팀을 찾을 수 없습니다"
```
ERROR:app:❌ ERROR in Dixon-Coles prediction: KeyError: 'Some Team'
```
**해결:** API에서 팀 목록을 확인하고 정확한 팀 이름 사용

### 시나리오 2: "모델이 예측에 실패했습니다"
```
ERROR:app:❌ ERROR in Dixon-Coles prediction: AttributeError: ...
```
**해결:** 모델 로드 상태 확인, 필요 시 재학습

### 시나리오 3: "특징을 생성할 수 없습니다"
```
ERROR:app:❌ ERROR in feature creation: ...
```
**해결:** historical_matches 데이터 확인

---

## ✅ 시스템 상태

| 항목 | 상태 |
|------|------|
| **디버깅 로깅** | ✅ 설치 완료 |
| **로그 파일** | ✅ `/tmp/flask_debug.log` |
| **모니터 스크립트** | ✅ `backend/watch_debug.sh` |
| **백엔드 서버** | ✅ 실행 중 (port 5001) |
| **프론트엔드** | ✅ 실행 중 (port 3000) |
| **curl 테스트** | ✅ 성공 (<0.1초) |
| **로그 출력** | ✅ 정상 작동 |

---

## 📝 관련 문서

- **디버깅 가이드:** [DEBUGGING_GUIDE.md](DEBUGGING_GUIDE.md)
- **성능 수정 보고서:** [PERFORMANCE_FIX_COMPLETE.md](PERFORMANCE_FIX_COMPLETE.md)
- **빠른 시작 가이드:** [QUICK_START.md](QUICK_START.md)

---

**작성:** Claude Code (Sonnet 4.5)
**날짜:** 2025-10-03 08:30
