# Week 4-5 상세 실행 계획: AI Integration

**기간**: Day 11-24 (14일)
**목표**: AI 시나리오 생성 및 분석 시스템 구축
**상태**: 🚀 시작

---

## 📋 목표 및 범위

### 핵심 목표
1. **AI Client 추상화**: 여러 LLM 제공자를 지원하는 통합 인터페이스
2. **Claude/Qwen 통합**: Anthropic Claude 및 Alibaba Qwen API 연동
3. **Prompt Engineering**: 시나리오 생성, 분석/조정, 최종 리포트 프롬프트 설계
4. **Factory Pattern**: AI Client 생성 및 관리

### 산출물
- `backend/ai/base_client.py` (~200줄)
- `backend/ai/claude_client.py` (~150줄)
- `backend/ai/qwen_client.py` (~150줄)
- `backend/ai/ai_factory.py` (~100줄)
- `backend/ai/prompts/phase1_scenario.py` (~300줄)
- `backend/ai/prompts/phase3_analysis.py` (~250줄)
- `backend/ai/prompts/phase7_report.py` (~350줄)
- 단위 테스트 (~400줄)

**총 예상**: ~1,900줄

---

## 🏗️ 아키텍처 설계

### 컴포넌트 다이어그램
```
┌─────────────────────────────────────────┐
│     Simulation Orchestrator             │
│  (Week 6에서 구현)                      │
└──────────────┬──────────────────────────┘
               │
               ↓
┌──────────────────────────────────────────┐
│        AI Factory                         │
│  - create(provider, config)               │
│  - get_client()                          │
└──────────────┬───────────────────────────┘
               │
       ┌───────┴───────┐
       ↓               ↓
┌─────────────┐  ┌──────────────┐
│ ClaudeClient│  │  QwenClient  │
│  (Anthropic)│  │  (Alibaba)   │
└──────┬──────┘  └──────┬───────┘
       │                │
       └────────┬───────┘
                ↓
        ┌───────────────┐
        │  BaseAIClient │ (Abstract)
        │  - generate_scenario()
        │  - analyze_result()
        │  - generate_report()
        └───────────────┘
```

### 데이터 흐름
```
Phase 1: Scenario Generation
  Input: MatchInput (teams, recent_form, injuries)
    ↓
  AI Client → Prompt Template → LLM API
    ↓
  Output: Scenario (events list with boosts)

Phase 3: Analysis & Adjustment
  Input: SimulationResult + Scenario + Adherence
    ↓
  AI Client → Prompt Template → LLM API
    ↓
  Output: AdjustedScenario OR "converged"

Phase 7: Final Report
  Input: FinalResult + All Events + Stats
    ↓
  AI Client → Prompt Template → LLM API
    ↓
  Output: Markdown Report
```

---

## 📅 일정 및 작업 분해

### Day 11-12: AI Client 추상화 및 Base 클래스

**목표**: 모든 AI Client가 구현해야 하는 추상 인터페이스 정의

**작업 항목**:
1. `base_client.py` 구현
   - `BaseAIClient` 추상 클래스
   - 3개 추상 메서드: `generate_scenario()`, `analyze_result()`, `generate_report()`
   - 공통 유틸리티: `_parse_json_response()`, `_validate_scenario()`
   - 타임아웃, 재시도 로직

2. 데이터 클래스 정의
   - `MatchInput`: 경기 입력 정보
   - `Scenario`: AI 생성 시나리오
   - `SimulationResult`: 시뮬레이션 결과
   - `AnalysisResult`: 분석 결과

3. Exception 클래스
   - `AIClientError`: 기본 예외
   - `APITimeoutError`: 타임아웃
   - `InvalidScenarioError`: 시나리오 검증 실패

**검증 기준**:
- [ ] 추상 클래스 import 가능
- [ ] 데이터 클래스 타입 검증 통과
- [ ] Exception 정의 완료

---

### Day 13-14: Claude Client 구현

**목표**: Anthropic Claude API 연동

**작업 항목**:
1. `claude_client.py` 구현
   - `ClaudeClient(BaseAIClient)` 클래스
   - Anthropic SDK 사용 (`anthropic` 패키지)
   - 모델: `claude-3-5-sonnet-20241022`
   - 3개 메서드 구현

2. API 통신
   - `anthropic.Anthropic(api_key=...)` 클라이언트 생성
   - `messages.create()` 호출
   - JSON 응답 파싱

3. 에러 핸들링
   - API 키 검증
   - Rate limit 처리
   - Timeout 처리

4. 단위 테스트
   - Mock API 응답으로 테스트
   - 실제 API 호출은 통합 테스트에서

**검증 기준**:
- [ ] Mock 테스트 통과 (3개 메서드)
- [ ] API 키 없이도 import 가능
- [ ] Exception 핸들링 검증

---

### Day 15-16: Qwen Client 구현

**목표**: Alibaba Qwen API 연동 (또는 로컬 Ollama)

**작업 항목**:
1. `qwen_client.py` 구현
   - `QwenClient(BaseAIClient)` 클래스
   - 옵션 1: Alibaba Cloud API (dashscope SDK)
   - 옵션 2: 로컬 Ollama (openai 호환 API)
   - 모델: `qwen2.5:72b` (Ollama) 또는 `qwen-max` (Cloud)

2. API 통신
   - HTTP 요청 또는 SDK 사용
   - JSON 응답 파싱

3. 로컬 우선 전략
   - 환경 변수 `QWEN_MODE` 확인
   - `local`: Ollama (http://localhost:11434)
   - `cloud`: Alibaba Cloud API

4. 단위 테스트

**검증 기준**:
- [ ] Mock 테스트 통과
- [ ] 로컬/클라우드 전환 가능
- [ ] Claude와 동일한 출력 포맷

---

### Day 17-18: Phase 1 Prompt (시나리오 생성)

**목표**: 경기 입력 → AI 시나리오 생성 프롬프트

**작업 항목**:
1. `prompts/phase1_scenario.py` 구현
   - `generate_phase1_prompt(match_input: MatchInput) -> str`
   - System Prompt + User Prompt

2. System Prompt 설계
   ```
   당신은 EPL 전문 축구 분석가입니다.
   주어진 경기 정보를 바탕으로 현실적인 경기 시나리오를 생성하세요.

   시나리오는 다음 형식을 따라야 합니다:
   - 5-7개 이벤트 시퀀스
   - 각 이벤트: minute_range, type, team, probability_boost
   - boost는 1.0-3.0 범위
   ```

3. User Prompt 템플릿
   ```
   ## 경기 정보
   홈팀: {home_team}
   - 최근 폼: {home_form}
   - 부상자: {home_injuries}
   - 포메이션: {home_formation}

   원정팀: {away_team}
   - 최근 폼: {away_form}
   - 부상자: {away_injuries}
   - 포메이션: {away_formation}

   ## 요구사항
   이 경기의 가능한 시나리오를 JSON 형식으로 생성하세요.
   ```

4. Few-shot Examples
   - 3개 예시 시나리오 포함
   - 다양한 경기 상황 (강팀 vs 약팀, 라이벌전, 중위권 대결)

5. JSON 스키마 명시
   ```json
   {
     "scenario_id": "string",
     "description": "string",
     "events": [
       {
         "minute_range": [10, 25],
         "type": "wing_breakthrough",
         "team": "home",
         "actor": "Son Heung-min",
         "probability_boost": 2.5,
         "reason": "최근 5경기 연속 어시스트"
       }
     ]
   }
   ```

6. 단위 테스트
   - 프롬프트 생성 테스트
   - 토큰 수 측정 (목표 2,000 이하)

**검증 기준**:
- [ ] 프롬프트 템플릿 생성 성공
- [ ] 토큰 수 < 2,000
- [ ] Mock LLM 응답 파싱 가능

---

### Day 19-20: Phase 3 Prompt (분석/조정)

**목표**: 시뮬레이션 결과 분석 및 시나리오 조정

**작업 항목**:
1. `prompts/phase3_analysis.py` 구현

2. System Prompt
   ```
   시뮬레이션 결과를 분석하고 시나리오를 조정하세요.

   목표:
   - 서사 일치율 < 60%: 시나리오 조정 필요
   - 서사 일치율 >= 60%: "converged" 반환
   - 최대 5회 반복 허용
   ```

3. User Prompt 템플릿
   ```
   ## 원래 시나리오
   {original_scenario}

   ## 시뮬레이션 결과
   최종 스코어: {final_score}
   서사 일치율: {adherence:.0%}

   예상 이벤트 vs 실제:
   - wing_breakthrough (10-25분): 예상했으나 발생 안 함
   - goal (15-30분): 18분에 발생 ✅

   ## 지시사항
   서사 일치율이 낮으면 시나리오를 조정하세요.
   - boost 값 조정
   - minute_range 조정
   - 이벤트 타입 변경

   일치율이 60% 이상이면 "status": "converged"로 반환하세요.
   ```

4. 수렴 조건
   - adherence >= 0.6
   - 또는 5회 반복

5. 단위 테스트

**검증 기준**:
- [ ] 조정 시나리오 생성
- [ ] 수렴 신호 감지
- [ ] 토큰 수 < 1,500

---

### Day 21-22: Phase 7 Prompt (최종 리포트)

**목표**: 최종 경기 리포트 생성 (마크다운)

**작업 항목**:
1. `prompts/phase7_report.py` 구현

2. System Prompt
   ```
   최종 경기 리포트를 작성하세요.

   포함 내용:
   - 경기 요약 (3-4 문장)
   - 주요 순간 (타임라인)
   - 팀별 통계
   - 선수 평가
   - 전술 분석
   ```

3. User Prompt 템플릿
   ```
   ## 경기 결과
   {home_team} {score_home} - {score_away} {away_team}

   ## 이벤트 타임라인
   {event_timeline}

   ## 통계
   {stats}

   ## 지시사항
   이 경기에 대한 상세한 분석 리포트를 마크다운으로 작성하세요.
   ```

4. 마크다운 포맷
   ```markdown
   # 경기 리포트: Arsenal vs Tottenham

   ## 📊 경기 요약
   ...

   ## ⚽ 주요 순간
   - **18분**: 손흥민 측면 돌파 후 크로스, Kane 헤더 골
   - **34분**: ...

   ## 📈 팀별 통계
   | 항목 | Arsenal | Tottenham |
   |------|---------|-----------|
   | 슛 | 15 | 12 |
   ...

   ## 🎯 선수 평가
   ### Arsenal
   - **Saka**: 8.5/10 - 2어시스트...

   ## 🧠 전술 분석
   ...
   ```

5. 단위 테스트

**검증 기준**:
- [ ] 마크다운 리포트 생성
- [ ] 모든 섹션 포함
- [ ] 토큰 수 < 2,500

---

### Day 23-24: AI Factory Pattern 및 통합 테스트

**목표**: AI Client 생성 및 관리 시스템

**작업 항목**:
1. `ai_factory.py` 구현
   ```python
   class AIClientFactory:
       _instances = {}  # 싱글톤 패턴

       @staticmethod
       def create(provider: str, api_key: str, **kwargs) -> BaseAIClient:
           if provider == 'claude':
               return ClaudeClient(api_key, **kwargs)
           elif provider == 'qwen':
               return QwenClient(api_key, **kwargs)
           raise ValueError(f"Unknown provider: {provider}")

       @classmethod
       def get_or_create(cls, provider: str, api_key: str) -> BaseAIClient:
           key = f"{provider}:{api_key[:8]}"
           if key not in cls._instances:
               cls._instances[key] = cls.create(provider, api_key)
           return cls._instances[key]
   ```

2. 설정 관리
   ```python
   @dataclass
   class AIConfig:
       provider: str          # 'claude' or 'qwen'
       api_key: str
       model: Optional[str] = None
       timeout: int = 30
       max_retries: int = 3
   ```

3. 통합 테스트
   - 모든 Client 생성 테스트
   - 프롬프트 실행 테스트 (Mock)
   - 에러 핸들링 테스트

4. `__init__.py` 정리
   ```python
   from .base_client import BaseAIClient
   from .claude_client import ClaudeClient
   from .qwen_client import QwenClient
   from .ai_factory import AIClientFactory, AIConfig

   __all__ = [
       'BaseAIClient',
       'ClaudeClient',
       'QwenClient',
       'AIClientFactory',
       'AIConfig',
   ]
   ```

**검증 기준**:
- [ ] Factory로 모든 Client 생성 가능
- [ ] 싱글톤 패턴 작동
- [ ] 통합 테스트 통과

---

## ✅ Week 4-5 검증 기준

### 기능 검증
- [ ] Claude Client로 시나리오 생성 가능 (Mock)
- [ ] Qwen Client로 시나리오 생성 가능 (Mock)
- [ ] Phase 1 프롬프트 < 2,000 토큰
- [ ] Phase 3 프롬프트 < 1,500 토큰
- [ ] Phase 7 프롬프트 < 2,500 토큰
- [ ] 생성된 시나리오가 ScenarioGuide에서 파싱 가능

### 코드 품질
- [ ] 모든 클래스에 docstring
- [ ] Type hints 100%
- [ ] 단위 테스트 커버리지 > 80%
- [ ] 에러 핸들링 완료

### 통합 검증
- [ ] Factory Pattern 작동
- [ ] Mock API 응답으로 전체 플로우 실행 가능
- [ ] 실제 API 키 없이도 import 가능

---

## 🎯 성공 지표

### 정량 지표
- 코드 라인: ~1,900줄
- 단위 테스트: > 15개
- 테스트 통과율: 100%
- 프롬프트 토큰 효율: Phase1(2K) + Phase3(1.5K) + Phase7(2.5K) = 6K total

### 정성 지표
- AI 생성 시나리오가 ScenarioGuide와 호환
- 프롬프트가 명확하고 재현 가능
- 에러 메시지가 이해하기 쉬움
- 다른 LLM 추가가 용이 (확장성)

---

## 🚧 리스크 및 완화 전략

### 리스크 1: API 키 관리
**문제**: Claude/Qwen API 키가 필요
**완화**:
- Mock 테스트로 API 키 없이도 개발 가능
- 환경 변수로 API 키 관리
- 실제 API 호출은 통합 테스트에서만

### 리스크 2: LLM 응답 불확실성
**문제**: AI가 항상 정확한 JSON을 반환하지 않을 수 있음
**완화**:
- JSON 스키마 명시
- Few-shot examples 제공
- 재시도 로직 (max 3회)
- Fallback 시나리오

### 리스크 3: 프롬프트 토큰 초과
**문제**: 프롬프트가 너무 길어질 수 있음
**완화**:
- 토큰 계산기로 사전 측정
- 불필요한 설명 제거
- 변수 부분만 템플릿화

---

## 📚 참고 자료

### Anthropic Claude API
- Docs: https://docs.anthropic.com/claude/docs
- Python SDK: `pip install anthropic`
- 모델: `claude-3-5-sonnet-20241022`

### Alibaba Qwen
- Ollama: https://ollama.com/library/qwen2.5
- 로컬 실행: `ollama run qwen2.5:72b`
- API: OpenAI 호환

### Prompt Engineering
- Few-shot Learning
- JSON Mode
- System + User Prompt 구조

---

**계획 수립 완료 - Day 11 구현 시작** 🚀
