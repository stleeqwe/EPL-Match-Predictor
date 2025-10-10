# ⚡ 스쿼드 빌더 2.0 빠른 시작 가이드

**5분 안에 엔터프라이즈급 스쿼드 빌더 사용하기**

---

## 🚀 즉시 시작하기

### Step 1: 백엔드 실행 (1분)

```bash
# 터미널 1
cd /Users/pukaworks/Desktop/soccer-predictor/backend
source venv/bin/activate
python api/app.py
```

**예상 출력:**
```
✅ EPL Player Analysis API Server initialized
 * Running on http://0.0.0.0:5001
```

### Step 2: 프론트엔드 실행 (1분)

```bash
# 터미널 2 (새 터미널)
cd /Users/pukaworks/Desktop/soccer-predictor/frontend/epl-predictor
npm start
```

**예상 출력:**
```
Compiled successfully!
Local:            http://localhost:3000
```

### Step 3: 브라우저 접속 (1분)

1. 브라우저가 자동으로 열림
2. `http://localhost:3000` 접속
3. "팀 분석" 탭 클릭
4. "스쿼드 짜기" 서브탭 선택

---

## 🎯 첫 스쿼드 만들기 (2분)

### 방법 1: AI 자동 배치 (10초)

1. **"AI Fill"** 버튼 클릭
2. ✨ 자동으로 최적 라인업 생성!
3. "Save" 버튼으로 저장

**결과:**
- 포지션별 최고 평점 선수 배치
- 주전 선수 우선
- 나머지 선수 자동 후보 배치

### 방법 2: 수동 드래그 앤 드롭 (2분)

1. **포메이션 선택** (예: 4-3-3)
2. **Available Players**에서 선수 드래그
3. 축구장의 **빈 포지션**으로 드롭
4. 반복하여 11명 배치

**TIP:**
- 포지션이 맞지 않으면 경고 표시
- 기존 선수는 자동으로 후보로 이동
- 선수 카드 클릭하면 상세 정보 모달

---

## 📊 팀 분석 확인

### 우측 사이드바 "Team Analysis"

**5가지 지표:**

1. **Overall** (0-5)
   - 전체 팀 평균 능력치
   - 파란색 바

2. **Attack** (0-5)
   - ST, WG, CAM 평균
   - 빨간색 바

3. **Midfield** (0-5)
   - CM, DM 평균
   - 노란색 바

4. **Defense** (0-5)
   - CB, FB, GK 평균
   - 초록색 바

5. **Chemistry** (0-5)
   - 팀 폼/케미스트리
   - 보라색 바

**목표:** 모든 바를 4.0 이상으로!

---

## 🎨 주요 기능 가이드

### 1. 포메이션 변경

**5가지 선택지:**

| 포메이션 | 스타일 | 추천 상황 |
|---------|--------|----------|
| 4-4-2 | 균형 | 기본 전술 |
| 4-3-3 | 공격 | 측면 활용 |
| 3-5-2 | 윙백 | 지배력 |
| 4-2-3-1 | 현대 | 압박 저항 |
| 3-4-3 | 초공격 | 역전 필요 |

**변경 방법:**
- Formation 드롭다운 클릭
- 원하는 포메이션 선택
- 기존 선수 자동 재배치 (호환 시)

### 2. 선수 상세 정보

**보는 방법:**
- 축구장의 선수 카드 클릭
- 모달 창 표시

**정보:**
- 이름, 포지션, 나이, 등번호
- Rating (평점)
- Form (최근 폼)
- Goals, Assists
- Appearances, Minutes
- 주전 여부 (⭐/🔶)

### 3. 후보 선수 관리

**추가:**
1. Available Players에서 선수 선택
2. "Substitutes" 영역으로 드래그

**제거:**
- "×" 버튼 클릭

**제한:**
- 최소 3명 권장
- 최대 7명

### 4. 스쿼드 저장/불러오기

**저장:**
```javascript
1. "Save" 버튼 클릭
2. localStorage에 자동 저장
3. 팀별로 관리
```

**자동 불러오기:**
- 같은 팀 재방문 시 자동 로드

---

## 🔧 트러블슈팅

### 문제 1: 백엔드 연결 실패

**증상:**
```
❌ 백엔드 서버 연결 실패
```

**해결:**
```bash
# 1. 백엔드 실행 확인
lsof -i :5001

# 2. 없으면 실행
cd backend
source venv/bin/activate
python api/app.py
```

### 문제 2: 드래그 앤 드롭 안됨

**원인:**
- 브라우저 호환성 (Safari 일부 버전)

**해결:**
1. Chrome/Firefox 사용 권장
2. 또는 클릭 → 선택 → 배치 (대체 UI)

### 문제 3: 선수 데이터 안 보임

**확인:**
```bash
# API 테스트
curl http://localhost:5001/api/teams

# 응답 확인
{"teams": [...]}
```

**해결:**
- 백엔드 재시작
- 브라우저 캐시 삭제

### 문제 4: 포메이션 변경 안됨

**원인:**
- 포지션 불일치 선수

**해결:**
1. "Reset" 버튼 클릭
2. 다시 배치
3. 또는 "AI Fill" 사용

---

## 📚 추가 자료

### 상세 문서
- [📖 SQUAD_BUILDER_DOCS.md](./SQUAD_BUILDER_DOCS.md) - 전체 문서
- [🚀 SQUAD_BUILDER_UPGRADE.md](./SQUAD_BUILDER_UPGRADE.md) - 업그레이드 가이드

### 코드 참조
- `src/components/SquadBuilder.js` - 메인 컴포넌트
- `src/utils/squadUtils.js` - 헬퍼 함수
- `src/components/SquadBuilder.css` - 스타일

### API 문서
- `backend/api/app.py` - API 엔드포인트
- [Fantasy Premier League API](https://fantasy.premierleague.com/api/)

---

## 🎓 예제: Manchester City 라인업

### 4-3-3 포메이션

**선발 11명:**
```
        Haaland (ST)
Grealish (LW)   Foden (RW)

  Bernardo   De Bruyne
        Rodri

Gvardiol  Dias  Stones  Walker
        
        Ederson
```

**후보 7명:**
- Ortega (GK)
- Akanji (CB)
- Ake (CB)
- Kovacic (CM)
- Nunes (CM)
- Doku (WG)
- Savinho (WG)

**팀 분석:**
- Overall: 4.6
- Attack: 4.8
- Midfield: 4.7
- Defense: 4.4
- Chemistry: 4.5

---

## ⚡ 고급 팁

### 팁 1: 최적 포메이션 찾기

```javascript
// squadUtils.js의 recommendFormation 사용
import { recommendFormation } from '../utils/squadUtils';

const suggested = recommendFormation(players);
console.log('추천 포메이션:', suggested);
```

### 팁 2: 스쿼드 검증

```javascript
// 저장 전 검증
import { validateSquad } from '../utils/squadUtils';

const validation = validateSquad(squad, formation);
if (!validation.isValid) {
  console.error('에러:', validation.errors);
}
```

### 팁 3: 스쿼드 익스포트/임포트

```javascript
// 익스포트
import { exportSquad } from '../utils/squadUtils';
const json = exportSquad(squad, formation, team);
console.log(json); // JSON 문자열

// 임포트
import { importSquad } from '../utils/squadUtils';
const imported = importSquad(jsonString);
```

### 팁 4: 디버그 모드

```javascript
// 콘솔에서 디버그 정보 출력
import { debugSquad } from '../utils/squadUtils';
debugSquad(squad, players);
```

**출력 예시:**
```
🔍 Squad Debug Info
Total Starters: 11
Total Substitutes: 7
Starter Positions: Haaland (ST), Foden (WG), ...
Average Rating: 4.58
```

---

## 🎯 다음 단계

### 기능 탐색
1. ✅ 모든 포메이션 시도
2. ✅ AI Fill vs 수동 배치 비교
3. ✅ 팀 분석 최적화 (4.5+ 목표)
4. ✅ 여러 팀 스쿼드 저장

### 고급 사용
1. 커스텀 평점 알고리즘 작성
2. 전술 분석 추가
3. 상대 팀 대응 라인업
4. 부상/출전정지 관리

### 기여하기
1. GitHub Issues에 피드백
2. Pull Request 제출
3. 문서 개선 제안

---

## ✅ 체크리스트

시작 전 확인:
- [ ] Node.js 설치됨
- [ ] Python 3.9+ 설치됨
- [ ] 백엔드 실행 중 (port 5001)
- [ ] 프론트엔드 실행 중 (port 3000)

첫 스쿼드:
- [ ] 팀 선택 완료
- [ ] 포메이션 선택
- [ ] 11명 선수 배치
- [ ] 후보 3명 이상
- [ ] 스쿼드 저장

---

## 🎉 완료!

**축하합니다! 🏆**

이제 엔터프라이즈급 스쿼드 빌더를 사용할 수 있습니다.

**다음 해볼 것:**
- 다른 EPL 팀 스쿼드 만들기
- 친구와 라인업 비교
- 경기 전 최적 라인업 시뮬레이션

**Happy Squad Building! ⚽**

---

**문의:**
- GitHub Issues
- Discord 커뮤니티
- Email: support@example.com

**버전:** 2.0.0  
**최종 업데이트:** 2025-10-06
