# 🔍 디버깅 가이드

**목적:** 예측 API 오류를 실시간으로 추적하고 해결하기

---

## ✅ 디버깅 시스템 설치 완료

### 추가된 기능

1. **상세한 로깅** - 모든 예측 요청을 단계별로 기록
2. **에러 추적** - 정확한 오류 위치와 원인 표시
3. **실시간 모니터링** - 로그를 실시간으로 확인 가능

---

## 🚀 디버깅 사용법

### 1. 백엔드 시작 (디버깅 활성화)

```bash
cd /Users/pukaworks/Desktop/soccer-predictor/backend

# Flask 서버 시작 (로그를 파일로 저장)
export FLASK_APP=api/app.py
export FLASK_ENV=development
source venv/bin/activate
python3 -m flask run --host=0.0.0.0 --port=5001 > /tmp/flask_debug.log 2>&1 &
```

### 2. 로그 실시간 모니터링

#### 방법 1: 전체 로그 보기
```bash
tail -f /tmp/flask_debug.log
```

#### 방법 2: 디버그 정보만 보기 (추천)
```bash
cd /Users/pukaworks/Desktop/soccer-predictor/backend
./watch_debug.sh
```

이 스크립트는 중요한 디버그 정보만 필터링해서 보여줍니다:
- 🔍 요청 시작
- 📥 입력 데이터
- 🏠 홈팀
- ✈️  원정팀
- 🤖 모델 타입
- ⚖️  가중치
- 🔧 특징 생성
- 📊 예측 진행
- ✅ 성공
- ❌ 에러

---

## 📊 로그 예시

### 성공적인 예측 로그

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
INFO:app:✅ Dixon-Coles prediction successful: {'home_win': 47.83, 'draw': 27.39, 'away_win': 24.79, ...}
INFO:app:📤 Final prediction to return: {...}
INFO:app:✅ Prediction completed successfully!
INFO:app:================================================================================
INFO:werkzeug:127.0.0.1 - - [03/Oct/2025 08:27:29] "POST /api/predict HTTP/1.1" 200 -
```

### 에러 발생 시 로그 (예시)

```
ERROR:app:================================================================================
ERROR:app:❌❌❌ CRITICAL ERROR in /api/predict ❌❌❌
ERROR:app:================================================================================
ERROR:app:Error type: KeyError
ERROR:app:Error message: 'Arsenal'
ERROR:app:
ERROR:app:Full traceback:
Traceback (most recent call last):
  File "/Users/.../api/app.py", line 211, in predict_match
    prediction = dixon_coles_model.predict_match(home_team, away_team)
  File "/Users/.../models/dixon_coles.py", line 156, in predict_match
    home_attack = self.attack_params[home_team]
KeyError: 'Arsenal'
ERROR:app:================================================================================
INFO:werkzeug:127.0.0.1 - - [03/Oct/2025 08:27:29] "POST /api/predict HTTP/1.1" 500 -
```

---

## 🛠️ 일반적인 오류 해결

### 1. 팀 이름을 찾을 수 없음 (KeyError)

**증상:**
```
ERROR:app:Error type: KeyError
ERROR:app:Error message: 'Some Team Name'
```

**원인:**
- 데이터베이스에 없는 팀 이름
- 팀 이름 철자 오류 (예: "Arsenal" vs "Arsenal FC")

**해결:**
```bash
# 데이터베이스의 팀 목록 확인
curl http://localhost:5001/api/teams | python3 -m json.tool

# 정확한 팀 이름 사용
```

### 2. 모델이 로드되지 않음

**증상:**
```
ERROR:app:🔍 dixon_coles_model object: None
ERROR:app:AttributeError: 'NoneType' object has no attribute 'predict_match'
```

**원인:** 모델 파일 누락 또는 손상

**해결:**
```bash
# 모델 재학습
cd /Users/pukaworks/Desktop/soccer-predictor/backend
python3 train_models.py
```

### 3. 특징 생성 실패

**증상:**
```
ERROR:app:❌ ERROR in feature creation: ...
```

**원인:** historical_matches 데이터 문제

**해결:**
```bash
# 데이터베이스 확인
sqlite3 soccer_predictor.db "SELECT COUNT(*) FROM matches;"

# 데이터가 없으면 재로드
python3 load_real_data.py
```

---

## 🧪 테스트 명령어

### 1. 단순 API 테스트
```bash
curl http://localhost:5001/api/health
# 예상 결과: {"status":"ok","message":"API is running"}
```

### 2. 예측 테스트 (Arsenal vs Chelsea)
```bash
curl -X POST http://localhost:5001/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "home_team": "Arsenal",
    "away_team": "Chelsea",
    "model_type": "statistical"
  }' | python3 -m json.tool
```

### 3. 팀 목록 확인
```bash
curl http://localhost:5001/api/teams | python3 -m json.tool
```

### 4. 프론트엔드에서 예측 테스트

1. 브라우저를 열고 http://localhost:3000 접속
2. F12 (개발자 도구) 열기
3. Network 탭에서 predict 요청 확인
4. Console 탭에서 JavaScript 에러 확인

---

## 📋 디버깅 체크리스트

예측이 실패할 때 다음 순서로 확인:

- [ ] Flask 서버가 실행 중인가? (`lsof -i :5001`)
- [ ] 로그 파일에서 에러 메시지 확인 (`tail -f /tmp/flask_debug.log`)
- [ ] 입력 데이터가 올바른가? (팀 이름, model_type 등)
- [ ] 팀 이름이 데이터베이스에 존재하는가? (`curl http://localhost:5001/api/teams`)
- [ ] 모델이 정상적으로 로드되었는가? (시작 로그 확인)
- [ ] 데이터베이스에 경기 데이터가 있는가? (`SELECT COUNT(*) FROM matches`)

---

## 🔧 고급 디버깅

### Python 디버거 사용

app.py에 다음 코드 추가:
```python
import pdb; pdb.set_trace()  # 이 지점에서 멈춤
```

### 상세 SQL 쿼리 로그

app.py 상단에 추가:
```python
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

---

## 📞 추가 지원

1. **로그 파일 위치**: `/tmp/flask_debug.log`
2. **디버그 모니터 스크립트**: `backend/watch_debug.sh`
3. **Flask 앱 코드**: `backend/api/app.py`

---

## ✅ 확인 사항

디버깅 시스템이 제대로 작동하는지 확인:

```bash
# 1. 테스트 요청 보내기
curl -X POST http://localhost:5001/api/predict \
  -H "Content-Type: application/json" \
  -d '{"home_team":"Arsenal","away_team":"Chelsea","model_type":"statistical"}'

# 2. 로그 확인 (새 터미널)
tail -n 100 /tmp/flask_debug.log | grep "🔍"

# 로그에 다음이 표시되어야 함:
# INFO:app:🔍 DEBUG: /api/predict endpoint called
# INFO:app:📥 Incoming request data: ...
# INFO:app:✅ Prediction completed successfully!
```

---

**작성:** Claude Code (Sonnet 4.5)
**최종 업데이트:** 2025-10-03 08:30
