# 외부 배포 & 가상대결 시뮬레이터 개선 보고서

**날짜**: 2025년 10월 9일
**작업 범위**: 외부 접근 설정, 개발 환경 개선, 가상대결 시뮬레이터 UX 개선

---

## 📋 목차

1. [외부 배포 설정 (ngrok)](#1-외부-배포-설정-ngrok)
2. [개발 모드 전환 (Hot Reload)](#2-개발-모드-전환-hot-reload)
3. [가상대결 시뮬레이터 개선](#3-가상대결-시뮬레이터-개선)
4. [변경된 파일 목록](#4-변경된-파일-목록)

---

## 1. 외부 배포 설정 (ngrok)

### 문제점
- 로컬 서버가 외부에서 접근 불가능
- 실제 사용자 테스트를 위해 공개 URL 필요

### 해결 방법

#### 1.1 ngrok 설치 및 설정
```bash
# Homebrew를 통한 ngrok 설치
brew install ngrok

# ngrok authtoken 설정
ngrok config add-authtoken 31PVpJyJTlLMef7C1BagKCZX5yd_3mxAEe6hAr7pk3S9ZoNxo
```

#### 1.2 ngrok 다중 터널 설정
ngrok 무료 플랜은 1개의 세션만 지원하므로, 단일 설정 파일로 백엔드/프론트엔드를 동시에 실행:

**파일**: `~/ngrok-config.yml`
```yaml
version: "2"
authtoken: 31PVpJyJTlLMef7C1BagKCZX5yd_3mxAEe6hAr7pk3S9ZoNxo

tunnels:
  backend:
    proto: http
    addr: 5001
  frontend:
    proto: http
    addr: 3000
```

#### 1.3 실행 명령어
```bash
# 백엔드와 프론트엔드를 동시에 터널링
ngrok start --all --config ~/ngrok-config.yml --log=stdout
```

#### 1.4 공개 URL
- **백엔드**: https://cd1ca89d4f17.ngrok-free.app
- **프론트엔드**: https://b33c64b2a6ce.ngrok-free.app

### 주의사항
⚠️ **ngrok 무료 플랜의 경고 페이지**
- 처음 접속 시 "You are about to visit..." 경고 페이지가 표시됨
- API 요청도 차단되므로, 백엔드 URL을 먼저 방문하여 "Visit Site" 클릭 필요
- 로컬 테스트 시에는 `http://localhost:3000` 사용 권장

---

## 2. 개발 모드 전환 (Hot Reload)

### 문제점
- 프론트엔드가 production build로 실행 중
- 코드 수정 시 매번 수동으로 빌드 필요
- 개발 생산성 저하

### 해결 방법

#### 2.1 정적 서버 중지
기존에 실행 중이던 `npx serve` 프로세스 종료:
```bash
lsof -ti:3000 | xargs kill -9
```

#### 2.2 React 개발 서버 실행
Hot Module Replacement (HMR)이 활성화된 개발 서버 실행:
```bash
cd /Users/pukaworks/Desktop/soccer-predictor/frontend/epl-predictor
BROWSER=none npm start
```

### 결과
✅ **즉시 반영 가능**
- 코드 수정 시 자동으로 브라우저에 반영
- 수동 빌드 불필요
- 개발 속도 대폭 향상

✅ **백엔드도 자동 재시작**
- Flask debug mode 활성화로 백엔드 코드 수정 시 자동 재시작

---

## 3. 가상대결 시뮬레이터 개선

### 3.1 홈팀/원정팀 중복 선택 방지

#### 기존 문제
- 홈팀과 원정팀에 같은 팀을 선택할 수 있었음
- "같은 팀은 대결할 수 없습니다!" 경고만 표시

#### 개선 내용
선택된 팀을 드롭다운에서 **음영처리 + 선택 불가**로 변경

**변경 파일**: `TeamDropdown.js`

```javascript
// 새로운 prop 추가
const TeamDropdown = ({
  value,
  onChange,
  teams = [],
  teamScores = {},
  placeholder = "-- 팀 선택 --",
  disabled = false,
  disabledTeams = [] // 선택 불가한 팀 목록
}) => {
  // ...

  const isDisabled = disabledTeams.includes(team);

  return (
    <motion.button
      disabled={isDisabled}
      className={`
        ${isDisabled
          ? 'opacity-40 cursor-not-allowed bg-slate-800/40'
          : isSelected
            ? 'bg-cyan-500/20 text-white'
            : 'text-white/90 hover:bg-cyan-500/10'
        }
      `}
    >
      {/* ... */}
    </motion.button>
  );
};
```

**변경 파일**: `MatchSimulator.js`

```javascript
// 홈팀 드롭다운: 원정팀이 선택되어 있으면 해당 팀 비활성화
<TeamDropdown
  value={homeTeam}
  onChange={setHomeTeam}
  teams={teams}
  teamScores={teamScores}
  placeholder="-- 팀 선택 --"
  disabled={simulating}
  disabledTeams={awayTeam ? [awayTeam] : []}
/>

// 원정팀 드롭다운: 홈팀이 선택되어 있으면 해당 팀 비활성화
<TeamDropdown
  value={awayTeam}
  onChange={setAwayTeam}
  teams={teams}
  teamScores={teamScores}
  placeholder="-- 팀 선택 --"
  disabled={simulating}
  disabledTeams={homeTeam ? [homeTeam] : []}
/>
```

#### 시각적 효과
- ✅ **opacity-40**: 40% 투명도로 음영처리
- ✅ **bg-slate-800/40**: 어두운 배경
- ✅ **cursor-not-allowed**: 선택 불가 커서
- ✅ **hover 효과 제거**: 마우스 오버 시 반응 없음

### 3.2 미평가 팀 평가 유도

#### 기존 문제
- 미평가 팀을 선택했을 때 경고 메시지만 표시
- 사용자가 팀 분석 탭으로 이동하는 방법을 알기 어려움

#### 개선 내용
"평가하기" 버튼 추가하여 **해당 팀 평가 화면으로 즉시 이동**

**변경 파일**: `App.js`
```javascript
// MatchSimulator에 onTeamClick 핸들러 전달
<MatchSimulator
  darkMode={darkMode}
  selectedMatch={selectedMatch}
  onTeamClick={handleTeamClick}
/>
```

**변경 파일**: `MatchSimulator.js`
```javascript
// 미평가 팀 선택 시 "평가하기" 버튼 표시
{teamScores[homeTeam].hasData ? (
  <div className="flex items-center gap-2 text-success">
    <span>✓</span>
    <span>평가 완료 - 종합 점수: {teamScores[homeTeam].overall.toFixed(1)}/100점</span>
  </div>
) : (
  <div className="flex items-center gap-2 text-warning">
    <span>⚠️</span>
    <span>이 팀은 아직 평가하지 않았습니다</span>
    {onTeamClick && (
      <button
        onClick={() => onTeamClick(homeTeam)}
        className="ml-2 text-cyan-400 hover:text-cyan-300 font-semibold underline transition-colors"
      >
        평가하기
      </button>
    )}
  </div>
)}
```

#### 사용자 흐름
1. 가상대결 시뮬레이터에서 미평가 팀 선택
2. "⚠️ 이 팀은 아직 평가하지 않았습니다" 메시지와 함께 **파란색 "평가하기"** 링크 표시
3. "평가하기" 클릭 시 **MyVision 탭**으로 이동하고 해당 팀이 자동 선택됨
4. 사용자가 팀 평가 완료 후 다시 가상대결 탭으로 돌아와 시뮬레이션 가능

---

## 4. 변경된 파일 목록

### 신규 파일
- `~/ngrok-config.yml` - ngrok 다중 터널 설정 파일

### 수정된 파일
- `frontend/epl-predictor/src/App.js`
  - Line 588: MatchSimulator에 `onTeamClick` prop 전달

- `frontend/epl-predictor/src/components/MatchSimulator.js`
  - Line 12: `onTeamClick` prop 추가
  - Lines 335, 366: `disabledTeams` prop을 TeamDropdown에 전달
  - Lines 348-355: 홈팀 미평가 시 "평가하기" 버튼 추가
  - Lines 387-394: 원정팀 미평가 시 "평가하기" 버튼 추가

- `frontend/epl-predictor/src/components/TeamDropdown.js`
  - Line 16: `disabledTeams` prop 추가
  - Line 138: `isDisabled` 체크 로직 추가
  - Lines 144-154: 비활성화된 팀 스타일링 적용
  - Lines 160-182: 비활성화 상태에 따른 텍스트 색상 조정

---

## 5. 실행 방법

### 로컬 개발 환경
```bash
# 백엔드 (터미널 1)
cd /Users/pukaworks/Desktop/soccer-predictor/backend
source venv/bin/activate
python api/app.py

# 프론트엔드 (터미널 2)
cd /Users/pukaworks/Desktop/soccer-predictor/frontend/epl-predictor
npm start

# 접속
http://localhost:3000
```

### 외부 공개 (ngrok)
```bash
# 백엔드 (터미널 1)
cd /Users/pukaworks/Desktop/soccer-predictor/backend
source venv/bin/activate
python api/app.py

# ngrok (터미널 2)
ngrok start --all --config ~/ngrok-config.yml --log=stdout

# 프론트엔드 (터미널 3)
cd /Users/pukaworks/Desktop/soccer-predictor/frontend/epl-predictor
REACT_APP_API_URL=https://cd1ca89d4f17.ngrok-free.app/api npm start

# 외부 접속
https://b33c64b2a6ce.ngrok-free.app
```

---

## 6. 개선 효과

### 개발 생산성
- ✅ **Hot Reload 활성화**: 코드 수정 시 즉시 반영
- ✅ **빌드 시간 절약**: 매번 수동 빌드 불필요
- ✅ **테스트 속도 향상**: 변경사항 확인이 빠름

### 사용자 경험
- ✅ **중복 선택 방지**: 시각적으로 선택 불가능한 팀 표시
- ✅ **직관적인 네비게이션**: "평가하기" 버튼으로 팀 평가 페이지로 즉시 이동
- ✅ **일관된 UI**: 음영처리된 비활성화 상태가 명확함

### 외부 접근성
- ✅ **공개 URL 제공**: 실제 사용자 테스트 가능
- ✅ **모바일 테스트 용이**: 모바일 기기에서도 접속 가능
- ✅ **공유 간편**: ngrok URL로 다른 사람과 공유 가능

---

## 7. 향후 개선 방안

### ngrok 유료 플랜 고려 사항
- 경고 페이지 제거
- 커스텀 도메인 사용
- 더 많은 동시 터널 지원

### 추가 UX 개선
- 시뮬레이션 결과 히스토리 저장
- 여러 모델 비교 기능
- 시뮬레이션 통계 분석

### 성능 최적화
- 코드 스플리팅
- 이미지 최적화
- API 응답 캐싱

---

## 📝 작업 완료 체크리스트

- [x] ngrok 설치 및 설정
- [x] ngrok 다중 터널 설정 파일 생성
- [x] 백엔드/프론트엔드 외부 공개 URL 생성
- [x] 프론트엔드 개발 모드 전환 (Hot Reload)
- [x] 홈팀/원정팀 중복 선택 방지 기능 구현
- [x] 선택된 팀 음영처리 + 비활성화 UI 구현
- [x] 미평가 팀 "평가하기" 버튼 추가
- [x] 팀 평가 페이지로 자동 이동 기능 구현
- [x] 문서 작성

---

**작성자**: Claude (AI Assistant)
**날짜**: 2025년 10월 9일
**버전**: v1.0
