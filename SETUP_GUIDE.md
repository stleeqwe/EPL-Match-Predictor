# EPL Match Predictor v2.0 - Setup Guide

**새로운 Mac/PC에서 프로젝트를 시작하는 완벽한 가이드**

---

## 🚀 Quick Start (권장)

### 원클릭 자동 설정

```bash
# 1. GitHub에서 클론
git clone https://github.com/stleeqwe/EPL-Match-Predictor.git
cd EPL-Match-Predictor

# 2. 자동 설정 실행
./setup.sh

# 3. API 키 설정 (프롬프트에 따라)
# backend/.env 파일에 API 키 입력

# 4. 앱 시작
./start.sh
```

**완료!** 🎉 http://localhost:3000 접속

---

## 📋 setup.sh 상세 설명

### 자동 설정 스크립트가 하는 일

1. ✅ **시스템 체크**
   - macOS 확인
   - Homebrew 설치/확인

2. ✅ **Python 환경**
   - Python 3.9+ 설치/확인
   - 가상환경 생성
   - 의존성 설치 (`requirements.txt`)

3. ✅ **Node.js 환경**
   - Node.js 18+ 설치/확인
   - npm 패키지 설치 (`package.json`)

4. ✅ **환경 변수**
   - `.env` 파일 생성
   - 템플릿 복사 (`.env.example`)

5. ✅ **데이터베이스**
   - SQLite 초기화
   - 테이블 생성

6. ✅ **시작 스크립트**
   - `start.sh` 생성
   - 실행 권한 부여

### 실행 옵션

```bash
# 전체 자동 설정
./setup.sh

# 특정 단계 건너뛰기 (고급 사용자)
# 스크립트 내에서 y/n 프롬프트로 선택 가능
```

---

## 🔧 수동 설정 (고급)

자동 스크립트를 사용할 수 없는 경우:

### 1. 사전 요구사항 설치

#### macOS
```bash
# Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Python 3.9+
brew install python@3.9

# Node.js 18+
brew install node
```

#### Linux (Ubuntu/Debian)
```bash
# Python 3.9+
sudo apt update
sudo apt install python3.9 python3.9-venv python3-pip

# Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

#### Windows
```powershell
# Chocolatey 패키지 매니저 사용
choco install python --version=3.9
choco install nodejs --version=18
```

### 2. Backend 설정

```bash
cd backend

# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화 (macOS/Linux)
source venv/bin/activate

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 의존성 설치
pip install --upgrade pip
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
nano .env  # 또는 선호하는 에디터

# 데이터베이스 초기화
python init_database.py
```

### 3. Frontend 설정

```bash
cd frontend/epl-predictor

# 의존성 설치
npm install

# 개발 서버 시작
npm start
```

### 4. Backend 실행

```bash
cd backend
source venv/bin/activate  # 가상환경 활성화
python api/app.py
```

---

## 🔑 환경 변수 설정

### 필수 API Keys

`backend/.env` 파일에 다음 키를 설정하세요:

```bash
# Flask 설정
FLASK_APP=api/app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here  # openssl rand -hex 32

# 데이터베이스
DATABASE_URL=sqlite:///epl_predictor.db

# API Keys
CLAUDE_API_KEY=sk-ant-api03-YOUR-KEY-HERE
ODDS_API_KEY=your-odds-api-key-here

# CORS (프론트엔드 URL)
CORS_ORIGINS=http://localhost:3000

# 로깅
LOG_LEVEL=INFO
```

### API Key 발급 방법

#### 1. Anthropic Claude API
1. https://console.anthropic.com/ 접속
2. 계정 생성/로그인
3. API Keys 섹션에서 새 키 생성
4. `CLAUDE_API_KEY`에 입력

#### 2. The Odds API (선택사항)
1. https://the-odds-api.com/ 접속
2. 계정 생성 (무료 플랜 가능)
3. Dashboard에서 API Key 확인
4. `ODDS_API_KEY`에 입력

#### 3. Flask SECRET_KEY 생성
```bash
# 터미널에서 실행
openssl rand -hex 32

# 또는 Python에서
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## 🎮 start.sh 사용법

### 기본 사용

```bash
# Backend + Frontend 동시 시작
./start.sh
```

### 내부 동작

```bash
# Backend: http://localhost:5001
# Frontend: http://localhost:3000
#
# Ctrl+C로 양쪽 모두 종료
```

### 개별 실행 (디버깅용)

```bash
# Terminal 1: Backend만
cd backend
source venv/bin/activate
python api/app.py

# Terminal 2: Frontend만
cd frontend/epl-predictor
npm start
```

---

## 🐛 문제 해결

### 자주 발생하는 문제

#### 1. Python 버전 오류
```
ERROR: Python 3.9+ required
```

**해결:**
```bash
# macOS
brew install python@3.9
brew link python@3.9

# Python 경로 확인
which python3
python3 --version
```

#### 2. Node.js 버전 오류
```
ERROR: Node.js 18+ required
```

**해결:**
```bash
# macOS
brew upgrade node

# 버전 확인
node --version
```

#### 3. pip 설치 실패
```
ERROR: Could not install packages
```

**해결:**
```bash
# pip 업그레이드
pip install --upgrade pip

# 개별 설치 시도
pip install flask
pip install anthropic
pip install flask-cors
```

#### 4. npm 설치 실패
```
ERROR: npm ERR! code EACCES
```

**해결:**
```bash
# 권한 문제 해결
sudo chown -R $(whoami) ~/.npm
sudo chown -R $(whoami) /usr/local/lib/node_modules

# 재설치
rm -rf node_modules package-lock.json
npm install
```

#### 5. 포트 충돌
```
ERROR: Address already in use (5001/3000)
```

**해결:**
```bash
# 사용 중인 프로세스 찾기
lsof -i :5001
lsof -i :3000

# 프로세스 종료
kill -9 <PID>

# 또는 포트 변경
# backend/api/app.py: app.run(port=5002)
# frontend/epl-predictor/package.json: "start": "PORT=3001 react-scripts start"
```

#### 6. .env 파일 인식 안됨
```
WARNING: CLAUDE_API_KEY not set
```

**해결:**
```bash
# .env 파일 위치 확인
ls -la backend/.env

# 없으면 생성
cp backend/.env.example backend/.env

# 권한 확인
chmod 600 backend/.env
```

#### 7. 데이터베이스 오류
```
ERROR: no such table: players
```

**해결:**
```bash
cd backend

# 기존 DB 삭제 후 재생성
rm -f epl_predictor.db
python init_database.py

# 또는 마이그레이션 실행
python database/migrate.py
```

---

## 📊 시스템 요구사항

### 최소 사양

- **OS**: macOS 11+, Linux (Ubuntu 20.04+), Windows 10+
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 2GB (의존성 포함)

### 권장 사양

- **OS**: macOS 13+ (Ventura)
- **CPU**: 4 cores (M1/M2 또는 Intel i5+)
- **RAM**: 8GB
- **Storage**: 5GB

### 소프트웨어 버전

| 소프트웨어 | 최소 버전 | 권장 버전 |
|-----------|----------|----------|
| Python    | 3.9      | 3.11     |
| Node.js   | 18.x     | 20.x LTS |
| npm       | 9.x      | 10.x     |
| Git       | 2.30     | 2.40+    |

---

## 🔍 설정 확인

### 환경 검증 스크립트

```bash
# 모든 요구사항 확인
./check_requirements.sh
```

또는 수동 확인:

```bash
# Python
python3 --version  # 3.9+

# pip
pip --version

# Node.js
node --version  # 18+

# npm
npm --version

# Git
git --version

# Backend 패키지
cd backend
source venv/bin/activate
pip list | grep -E "flask|anthropic|pandas"

# Frontend 패키지
cd frontend/epl-predictor
npm list react react-dom
```

---

## 🚦 실행 확인

### 헬스 체크

```bash
# Backend API
curl http://localhost:5001/api/health

# 응답:
{
  "status": "healthy",
  "version": "2.0.0",
  "database": "connected"
}

# Frontend
curl http://localhost:3000

# 응답: HTML 페이지
```

### 브라우저 접속

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5001/api
- **API 문서**: http://localhost:5001/api (엔드포인트 목록)

---

## 📚 추가 리소스

### 문서

- [README.md](README.md) - 프로젝트 개요
- [API 문서](backend/api/README.md) - API 엔드포인트 가이드
- [Value Betting](backend/value_betting/README.md) - Value Betting 모듈

### 커뮤니티

- **GitHub Issues**: 버그 리포트 및 기능 요청
- **Discussions**: 질문 및 아이디어 공유

### 도움이 필요하신가요?

1. **문제 해결 가이드 확인**: 위 "문제 해결" 섹션
2. **GitHub Issues 검색**: 비슷한 문제가 있는지 확인
3. **새 Issue 생성**: 해결되지 않으면 상세 정보와 함께 이슈 등록

---

## ✅ 체크리스트

설정이 완료되었는지 확인하세요:

- [ ] Python 3.9+ 설치 완료
- [ ] Node.js 18+ 설치 완료
- [ ] Git 클론 완료
- [ ] `./setup.sh` 실행 성공
- [ ] `backend/.env` 파일 생성 및 API 키 입력
- [ ] Backend 실행 확인 (http://localhost:5001/api/health)
- [ ] Frontend 실행 확인 (http://localhost:3000)
- [ ] 브라우저에서 정상 작동 확인

---

**모든 설정이 완료되었습니다!** 🎉

이제 EPL Match Predictor v2.0을 사용할 준비가 되었습니다.

Happy predicting! ⚽

---

*Built with Claude Code | Last Updated: 2025-10-11*
