# ⚡ Quick Start Guide

**로컬 환경에서 1분 안에 EPL Predictor 실행하기**

---

## 🚀 빠른 실행 (3단계)

### 1단계: 백엔드 실행

```bash
./start_backend.sh
```

**대기:** 다음 메시지가 나올 때까지 기다리세요
```
✅ API READY with REAL trained models!
Running on http://localhost:5001
```

---

### 2단계: 프론트엔드 실행 (새 터미널)

```bash
./start_frontend.sh
```

**대기:** 브라우저가 자동으로 열립니다
```
Compiled successfully!
Local: http://localhost:3000
```

---

### 3단계: 브라우저에서 사용

```
http://localhost:3000
```

1. **팀 선택**: 드롭다운에서 홈팀/원정팀 선택
2. **예측 보기**: 자동으로 예측 결과 표시
3. **완료!** 🎉

---

## 🛠️ 문제 발생 시

### 백엔드가 시작 안 됨
```bash
# Python 가상환경 확인
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 -m flask run --port=5001
```

### 프론트엔드가 시작 안 됨
```bash
# npm 재설치
cd frontend/epl-predictor
rm -rf node_modules
npm install
npm start
```

### 포트 충돌 (5001 이미 사용 중)
```bash
# 포트 사용 프로세스 종료
lsof -i :5001
kill -9 <PID>
```

---

## 📖 상세 문서

- **통합 가이드**: [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)
- **프로젝트 README**: [README_PRODUCTION.md](README_PRODUCTION.md)
- **데이터 보고서**: [REAL_DATA_INTEGRATION_COMPLETE.md](REAL_DATA_INTEGRATION_COMPLETE.md)

---

## ✅ 확인 사항

**백엔드 정상:**
- ✅ `http://localhost:5001/api/health` 접속 시 `{"status":"ok"}` 응답

**프론트엔드 정상:**
- ✅ `http://localhost:3000` 접속 시 앱 로드
- ✅ 브라우저 콘솔 (F12) 에러 없음

**연동 정상:**
- ✅ 팀 목록 드롭다운에 팀 이름 표시
- ✅ 예측 버튼 클릭 시 결과 표시

---

**Happy Predicting! ⚽📊**
