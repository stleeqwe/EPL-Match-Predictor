# ⚽ 실시간 경기 중계 기능 개선 완료

## 📝 사용자 요구사항

> "실시간 시뮬레이션을 중계(실제로 AI가 시나리오를 구동시키면서 발생하는 이벤트들)를 텍스트 프롬프트로 표시"

**목표**: 토큰 생성 진행률이 아닌, **실제 축구 경기 이벤트**(골, 슈팅, 패스, 태클 등)를 실시간으로 텍스트로 표시

---

## ✅ 개선 사항 요약

### **이미 구현되어 있던 기능**
- ✅ AI 프롬프트에 MATCH_EVENTS 섹션 지시사항 포함
- ✅ 백엔드 스트리밍 파싱 로직 (`simulate_match_enriched_stream`)
- ✅ 이벤트 파싱 함수 (`_parse_match_event_line`)
- ✅ 프론트엔드 UI (SimulationDashboard.js)

### **새로 개선한 사항**
1. ✅ AI 프롬프트 강화 - 이벤트 생성 강제 + 명확한 예시
2. ✅ 섹션 마커 감지 로직 강화 - 더 robust한 detection
3. ✅ 이벤트 파싱 로직 개선 - HT/FT 지원, 로그 추가
4. ✅ 프론트엔드 UI 개선 - 이모지, LIVE 인디케이터, 최신 이벤트 강조

---

## 🔧 세부 수정 내역

### 1️⃣ AI 프롬프트 강화

**파일**: `backend/ai/enriched_qwen_client.py:132-167`

**변경 전**:
```
**SECTION 1: MATCH_EVENTS**
Generate 15-20 realistic match events...
```

**변경 후**:
```
===== SECTION 1: MATCH_EVENTS =====
Generate 15-25 realistic match events that simulate the actual flow of the game.

REQUIRED FORMAT (one event per line):
[MINUTE'] EVENT_TYPE: Detailed description with player names

Mandatory Event Types (use these EXACTLY):
- KICK_OFF, PASS, SHOT, GOAL, SAVE, TACKLE, FOUL, CORNER, YELLOW_CARD, SUBSTITUTION

EXAMPLE EVENTS (copy this format):
[1'] KICK_OFF: Match begins! Arsenal kicks off with possession in the center circle
[3'] PASS: Odegaard receives the ball and plays a brilliant through ball to Saka
[5'] SHOT: Salah cuts inside and unleashes a powerful shot, but Ramsdale saves
[23'] GOAL: Martinelli heads home from Saka's pinpoint cross! Arsenal 1-0 Liverpool

Generate AT LEAST 15 events. Include goals, near-misses, tactical moments.
```

**효과**:
- ✅ AI가 반드시 이벤트를 생성하도록 강제
- ✅ 더 명확한 형식 지정
- ✅ 풍부한 예시 제공 (10개)

---

### 2️⃣ 섹션 마커 감지 강화

**파일**: `backend/ai/enriched_qwen_client.py:476-490`

**변경 전**:
```python
if 'MATCH_EVENTS' in full_response and not in_match_events:
    in_match_events = True
elif 'JSON_PREDICTION' in full_response and in_match_events:
    in_match_events = False
    in_json = True
```

**변경 후**:
```python
if not in_match_events and not in_json:
    # Look for MATCH_EVENTS marker
    if 'SECTION 1' in full_response or 'MATCH_EVENTS' in full_response:
        in_match_events = True
        logger.info("✓ Detected MATCH_EVENTS section start")

if in_match_events and not in_json:
    # Look for JSON_PREDICTION marker
    if 'SECTION 2' in full_response or 'JSON_PREDICTION' in full_response:
        in_match_events = False
        in_json = True
        logger.info("✓ Detected JSON_PREDICTION section start")
```

**효과**:
- ✅ 더 유연한 마커 감지 (SECTION 1 또는 MATCH_EVENTS)
- ✅ 로그로 디버깅 가능

---

### 3️⃣ 이벤트 파싱 로직 개선

**파일**: `backend/ai/enriched_qwen_client.py:556-598`

**변경 전**:
```python
def _parse_match_event_line(self, line: str) -> Optional[Dict]:
    pattern = r'\[(\d+)\'?\]\s*(\w+):\s*(.+)'
    match = re.match(pattern, line)
    if match:
        # ...
    return None
```

**변경 후**:
```python
def _parse_match_event_line(self, line: str) -> Optional[Dict]:
    # Pattern 1: Standard minute format [5'] or [5]
    pattern1 = r'\[(\d+)\'?\]\s*(\w+):\s*(.+)'
    match = re.match(pattern1, line)
    if match:
        minute = int(match.group(1))
        event_type = match.group(2).lower().replace('_', ' ')
        description = match.group(3).strip()
        return {...}

    # Pattern 2: Half-time/Full-time markers [HT] or [FT]
    pattern2 = r'\[(HT|FT)\]\s*(\w+):\s*(.+)'
    match = re.match(pattern2, line)
    if match:
        time_marker = match.group(1)
        minute = 45 if time_marker == 'HT' else 90
        # ...
        return {...}

    return None
```

**파일**: `backend/ai/enriched_qwen_client.py:493-512`

**로그 추가**:
```python
if clean_line and not clean_line.startswith('='):
    event = self._parse_match_event_line(clean_line)
    if event:
        logger.debug(f"⚽ Match event: {event['minute']}' {event['event_type']}")
        yield {'type': 'match_event', 'event': event}
    else:
        # Log unparseable lines for debugging
        if len(clean_line) > 5:
            logger.debug(f"Could not parse line: {clean_line[:80]}")
```

**효과**:
- ✅ [HT], [FT] 마커 지원
- ✅ 언더스코어 → 공백 변환 (yellow_card → yellow card)
- ✅ 상세한 디버그 로그

---

### 4️⃣ 프론트엔드 UI 개선

**파일**: `frontend/src/components/SimulationDashboard.js:273-331`

**변경 사항**:

1. **LIVE 인디케이터 추가**:
```jsx
<h2 className="card-title">
  <span className="text-gradient">⚽ Live Match Commentary</span>
  <span className="live-indicator">🔴 LIVE</span>
</h2>
```

2. **이벤트 역순 표시** (최신 이벤트가 위로):
```jsx
{matchEvents.slice().reverse().map((matchEvent, index) => {
```

3. **이벤트 타입별 이모지**:
```jsx
const eventEmoji = {
  'kick_off': '⚽',
  'pass': '🎯',
  'shot': '🚀',
  'goal': '⚽🎉',
  'save': '🧤',
  'tackle': '💪',
  'foul': '⚠️',
  'corner': '🚩',
  'yellow_card': '🟨',
  'red_card': '🟥',
  'substitution': '🔄',
  'half_time': '⏸️'
}[matchEvent.event_type?.toLowerCase()] || '⚡';
```

4. **최신 이벤트 강조**:
```jsx
className={`match-event-item ${index === 0 ? 'latest' : ''}`}
```

**파일**: `frontend/src/components/SimulationDashboard.css:694-767`

**CSS 추가**:
- `live-indicator`: 펄스 애니메이션 (빨간 불빛 깜빡임)
- `match-event-item.latest`: 최신 이벤트 강조 (더 밝은 배경, 테두리)
- `flash-in` 애니메이션: 새 이벤트 등장 효과

---

## 🧪 테스트 방법

### 1단계: 백엔드 재시작

```bash
cd /Users/stlee/Desktop/EPL-Match-Predictor/backend
python app.py
```

### 2단계: 프론트엔드 실행

```bash
cd /Users/stlee/Desktop/EPL-Match-Predictor/frontend
npm start
```

### 3단계: 시뮬레이션 실행

1. 브라우저에서 `http://localhost:3000` 접속
2. Arsenal vs Liverpool 시뮬레이션 시작
3. **기대 결과**:

#### ✅ 정상 동작 확인 사항

- **LIVE 인디케이터**: 🔴 LIVE 빨간 불빛 펄스 애니메이션
- **실시간 이벤트 표시**:
  ```
  ⚽ 1' KICK OFF: Match begins! Arsenal starts with possession
  🎯 3' PASS: Odegaard finds Saka on the right wing
  🚀 7' SHOT: Salah shoots from distance
  ⚽🎉 23' GOAL: Martinelli heads home! Arsenal 1-0 Liverpool
  ```
- **최신 이벤트 강조**: 가장 위의 이벤트가 더 밝게 표시
- **애니메이션**: 이벤트가 왼쪽에서 슬라이드 인

#### 🔍 백엔드 로그 확인

터미널에서 다음 로그를 확인:
```
INFO - ✓ Detected MATCH_EVENTS section start
DEBUG - ⚽ Match event: 1' kick_off - Match begins! Arsenal starts with possession
DEBUG - ⚽ Match event: 5' shot - Salah shoots from outside the box
DEBUG - ⚽ Match event: 23' goal - Martinelli heads home from Saka's cross! Ars...
INFO - ✓ Detected JSON_PREDICTION section start
```

---

## 🐛 트러블슈팅

### 문제 1: 이벤트가 표시되지 않음

**원인**: AI가 MATCH_EVENTS 섹션을 생성하지 않음

**해결책**:
1. 백엔드 로그 확인:
   - `✓ Detected MATCH_EVENTS section start` 로그 있는지 확인
   - 없으면 AI가 프롬프트를 따르지 않은 것

2. Qwen 모델 확인:
   ```bash
   ollama list  # qwen2.5:14b 있는지 확인
   ```

3. 프롬프트 테스트 (수동):
   ```bash
   curl -X POST http://localhost:11434/api/generate \
     -d '{"model":"qwen2.5:14b","prompt":"Generate match events for Arsenal vs Liverpool. Format: [1] KICK_OFF: Match begins"}'
   ```

---

### 문제 2: 이벤트 파싱 실패

**원인**: AI가 다른 형식으로 이벤트 생성

**디버깅**:

백엔드 로그에서 "Could not parse line" 확인:
```
DEBUG - Could not parse line: Event 1: Match begins with Arsenal in possession
```

**해결책**:
- AI 응답 형식이 다르면 `_parse_match_event_line` 함수 패턴 수정
- 또는 AI 프롬프트에 예시 더 강조

---

### 문제 3: UI가 업데이트되지 않음

**원인**: 프론트엔드 빌드 캐시

**해결책**:
```bash
cd frontend
rm -rf node_modules/.cache
npm start
```

또는 브라우저 강제 새로고침 (Ctrl + Shift + R)

---

## 📊 기대 효과

### Before (수정 전)
- ❌ 토큰 생성 진행률만 표시 (1234 / 2000 토큰)
- ❌ 실제 경기 이벤트 안 보임
- ❌ 사용자가 무슨 일이 일어나는지 모름

### After (수정 후)
- ✅ 실시간 경기 이벤트 표시 (골, 슈팅, 패스 등)
- ✅ 이모지로 시각적 구분
- ✅ LIVE 인디케이터로 실시간 느낌
- ✅ 최신 이벤트 강조
- ✅ 애니메이션 효과로 생동감

---

## 🎯 예상 결과물

```
┌─────────────────────────────────────────────────────────┐
│  ⚽ Live Match Commentary           🔴 LIVE   15 events │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [42'] 🚀 SHOT                                 [LATEST] │
│  Salah's curling effort from 25 yards goes just wide   │
│                                                         │
│  [35'] 🟨 YELLOW CARD                                   │
│  Robertson receives a yellow card for a late challenge │
│                                                         │
│  [28'] ⚠️ FOUL                                          │
│  Henderson brings down Odegaard just outside the box   │
│                                                         │
│  [23'] ⚽🎉 GOAL                                         │
│  Martinelli heads home! Arsenal 1-0 Liverpool          │
│                                                         │
│  [18'] 🚩 CORNER                                        │
│  Arsenal wins a corner kick after Saka's cross         │
│                                                         │
│  ... (더 많은 이벤트)                                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 수정된 파일

### Backend (1 file)
- ✅ `backend/ai/enriched_qwen_client.py` (150줄 수정)
  - AI 프롬프트 강화 (line 132-167)
  - 섹션 마커 감지 개선 (line 476-490)
  - 이벤트 파싱 로직 강화 (line 493-512, 556-598)

### Frontend (2 files)
- ✅ `frontend/src/components/SimulationDashboard.js` (50줄 수정)
  - LIVE 인디케이터 추가
  - 이벤트 역순 표시
  - 이모지 매핑
  - 최신 이벤트 강조

- ✅ `frontend/src/components/SimulationDashboard.css` (90줄 추가)
  - LIVE 인디케이터 스타일
  - 최신 이벤트 강조 스타일
  - flash-in 애니메이션

---

## 🚀 다음 단계

### 추가 개선 가능 사항 (선택사항)

1. **스코어보드 추가**
   - 골이 들어갈 때마다 점수판 업데이트
   - Arsenal 1 - 0 Liverpool

2. **이벤트 필터링**
   - "골만 보기", "경고만 보기" 필터 버튼

3. **이벤트 검색**
   - 특정 선수 이름으로 검색

4. **오디오 알림**
   - 골이 들어갈 때 효과음 재생

5. **경기 타임라인 시각화**
   - 가로 타임라인에 이벤트 표시

---

**문서 생성일**: 2025-10-17
**작성자**: Claude Code (AI Assistant)
**상태**: ✅ 구현 완료, 테스트 대기 중
