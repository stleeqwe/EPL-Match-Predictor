# EPL AI 시뮬레이션 시스템 완전 재구축 계획
## AI-Guided Iterative Refinement 설계 완전 구현

**작성일**: 2025-10-16
**목표**: 제안 시스템 설계서(EPL_AI_Simulation_System_Design_v2.md) 100% 구현
**기간**: 14주 (3.5개월)
**예산**: $55,000 (인건비 $50,000 + AI 비용 $5,000)

---

## 목차

1. [현재 상황 진단](#현재-상황-진단)
2. [재구축 목표 및 범위](#재구축-목표-및-범위)
3. [14주 완전 구현 로드맵](#14주-완전-구현-로드맵)
4. [Phase별 상세 구현 계획](#phase별-상세-구현-계획)
5. [기술 스택 및 아키텍처](#기술-스택-및-아키텍처)
6. [리스크 관리](#리스크-관리)
7. [검증 전략](#검증-전략)
8. [성공 기준](#성공-기준)

---

## 현재 상황 진단

### 현재 시스템의 치명적 문제점

#### ❌ 문제 1: 서사 시스템 부재

**설계 요구사항**:
```
OFFLINE: 서사 라이브러리 (500개 사전 생성 템플릿)
- 50개 핵심 서사 수동 작성
- 500개 조합 생성 알고리즘
- 인덱싱 및 매칭 시스템
```

**현재 상태**:
- ❌ 서사 라이브러리 0개
- ❌ 서사 매칭 알고리즘 없음
- ❌ 서사 기반 접근 전혀 없음

**영향**:
- 축구 전문 지식 활용 불가
- AI가 매번 처음부터 분석 (비효율)
- 일관성 없는 예측

---

#### ❌ 문제 2: AI 역할 축소

**설계 요구사항**:
```
Phase 1: AI 시나리오 생성
- 서사 라이브러리 탐색
- 5-7개 구체적 시나리오 합성
- 이벤트 시퀀스 (분 단위)
- 확률 부스트 (1.0-3.0x)

Phase 3: AI 분석 및 조정
- 편향 감지 (득점, 승률, 이벤트 빈도)
- 서사 일치율 분석
- 파라미터 조정 제안
- 시나리오 품질 평가
- 수렴 평가 (5개 기준)

Phase 7: AI 최종 리포트
- 최종 예측
- 지배적 시나리오 3개
- 핵심 변수 분석
- 사용자 통찰 검증
- 반복 과정 요약
- 리스크 분석
```

**현재 상태**:
- ⚠️ Phase 1: 단순 파라미터 생성만 (시나리오 없음)
- ⚠️ Phase 3: 규칙 기반 조정 (AI 분석 제한적)
- ❌ Phase 7: AI 리포트 없음 (JSON 결과만)

**영향**:
- AI의 추론 능력 미활용
- 투명성 부족 (사용자가 개선 과정 볼 수 없음)
- 리포트 품질 낮음

---

#### ❌ 문제 3: 이벤트 기반 확률 엔진 미구현

**설계 요구사항**:
```python
class StatisticalMatchEngine:
    def simulate_match(self, params, scenario_guide):
        # 90분 분 단위 시뮬레이션
        for minute in range(90):
            # 1. 점유 팀 결정
            # 2. 이벤트 확률 계산
            event_probs = self._calculate_event_probabilities(
                params, state, possession,
                scenario_guide.get_boost_at(minute)  # 서사 부스트!
            )
            # 3. 이벤트 샘플링 (슛 → 온타겟 → 득점)
            # 4. 서사 일치율 계산
```

**현재 상태**:
- ⚠️ 단순 확률 기반 (서사 부스트 적용 불가)
- ❌ 분 단위 시뮬레이션 없음
- ❌ 서사 일치율 계산 없음

**영향**:
- 시나리오 기반 예측 불가
- 서사 라이브러리 활용 불가
- 예측의 설명력 부족

---

#### ❌ 문제 4: 수렴 알고리즘 불완전

**설계 요구사항**:
```python
CONVERGENCE_CRITERIA = {
    "score_range": (2.2, 3.4),        # 가중치 25%
    "bias_threshold": 0.10,           # 가중치 25%
    "narrative_adherence": 0.75,      # 가중치 20%
    "win_rate_distribution": {...},   # 가중치 20%
    "stability": 0.05,                # 가중치 10%
}

수렴 신뢰도 = 가중 평균 > 0.85
```

**현재 상태**:
- ⚠️ 단순 기준 (bias < 5.0, narrative > 85%)
- ❌ 가중치 없음
- ❌ 수렴 신뢰도 계산 없음

**영향**:
- 조기 수렴 또는 과도한 반복
- 품질 보장 불확실

---

#### ❌ 문제 5: 프롬프트 설계 부족

**설계 요구사항**:
- Phase 1: 2,000 토큰 입력 (서사 라이브러리 + Few-shot)
- Phase 3: 1,500 토큰 입력 (EPL 기준 통계 + 제약 조건)
- Phase 7: 2,500 토큰 입력 (히스토리 + 사용자 입력)

**현재 상태**:
- ⚠️ 간단한 프롬프트 (~500 토큰)
- ❌ Few-shot examples 없음
- ❌ 제약 조건 불명확

**영향**:
- AI 출력 품질 낮음
- JSON 파싱 오류 가능성

---

### 현재 시스템 vs 설계 요구사항 비교

| 컴포넌트 | 설계 요구 | 현재 구현 | 완성도 |
|---------|----------|----------|--------|
| **서사 라이브러리** | 500개 템플릿 | 0개 | **0%** ❌ |
| **AI 시나리오 생성** | 5-7개, 이벤트 시퀀스 | 단순 파라미터 | **30%** ⚠️ |
| **이벤트 기반 엔진** | 분 단위, 서사 부스트 | 단순 확률 | **40%** ⚠️ |
| **AI 분석/조정** | 5가지 분석, 상세 조정 | 규칙 기반 | **50%** ⚠️ |
| **수렴 알고리즘** | 5개 기준, 가중 평균 | 2개 기준 | **40%** ⚠️ |
| **AI 최종 리포트** | 500-700자, 6개 섹션 | 없음 | **0%** ❌ |
| **프롬프트 엔지니어링** | 2,000+ 토큰, Few-shot | 500 토큰 | **25%** ⚠️ |
| **백테스트** | 20경기 검증 | 미완료 | **0%** ❌ |

**전체 완성도**: **~30%** ⚠️

---

## 재구축 목표 및 범위

### 핵심 목표

> **제안 시스템 설계서(EPL_AI_Simulation_System_Design_v2.md)의 모든 요구사항을 100% 구현한다.**

### 구체적 목표

#### 1. 서사 라이브러리 (OFFLINE)

**목표**:
```
✅ 50개 핵심 서사 수동 작성 (축구 전문가 협업)
✅ 500개 조합 생성 (알고리즘)
✅ 인덱싱 시스템 (PostgreSQL)
✅ 매칭 알고리즘 (키워드 + 임베딩)
```

**검증 기준**:
- 50개 서사 품질 검토 (축구 전문가)
- 500개 조합의 중복률 < 10%
- 매칭 정확도 > 80% (테스트 100케이스)

---

#### 2. 7단계 프로세스 완전 구현

**Phase 1: AI 시나리오 생성**
```python
✅ 서사 라이브러리 탐색 (매칭 알고리즘)
✅ 5-7개 구체적 시나리오 합성
✅ 이벤트 시퀀스 (분 단위)
✅ 확률 부스트 (1.0-3.0x)
✅ 예상 발생 확률 계산
✅ AI 추론 근거 제공
```

**Phase 2: 통계 검증**
```python
✅ 각 시나리오 × 100회 시뮬레이션
✅ 이벤트 기반 확률 엔진
   - 슛 → 온타겟 → 득점 체인
   - 전술 매치업 반영
   - 서사 부스트 적용
✅ 통계 수집
   - 승률, 득점, 편향도
   - 서사 일치율
   - 이벤트 분포
```

**Phase 3: AI 분석 및 조정**
```python
✅ 편향 감지
   - 득점 분포 편차
   - 승률 편차
   - 비정상적 스코어라인
   - 이벤트 빈도 이상
✅ 서사 일치율 분석 (< 0.75 시나리오)
✅ 파라미터 조정 제안
   - 문제 정량화
   - 근본 원인 추정
   - 구체적 조정값
   - 예상 효과
✅ 시나리오 품질 평가
   - 중복 식별
   - 비현실적 시나리오 제거
✅ 수렴 평가 (5개 기준)
```

**Phase 4-5: 재시뮬레이션 및 수렴 체크**
```python
✅ 조정된 파라미터로 Phase 2 반복
✅ 수렴 조건 (5개 기준, 가중 평균)
✅ 최대 5회 반복
```

**Phase 6: 최종 고해상도 시뮬레이션**
```python
✅ 각 시나리오 × 3,000회
✅ 정밀 확률 분포 도출
✅ 실행 시간 < 35초
```

**Phase 7: AI 최종 리포트**
```python
✅ 최종 예측 (100자)
✅ 지배적 시나리오 3개 (150자)
✅ 핵심 변수 분석 (150자)
✅ 사용자 통찰 검증 (100자)
✅ 반복 과정 요약 (100자)
✅ 리스크 분석 (100자)
✅ 총 500-700자, 전문적 톤
```

---

#### 3. 품질 목표

| 지표 | 목표 | 검증 방법 |
|------|------|----------|
| **승무패 정확도** | > 55% | 백테스트 100경기 |
| **Brier Score** | < 0.20 | 백테스트 100경기 |
| **득점 차이** | < 0.8골 | 백테스트 100경기 |
| **편향도** | < 0.10 | 수렴 시 자동 검증 |
| **서사 일치율** | > 0.75 | 수렴 시 자동 검증 |
| **캘리브레이션** | > 0.80 | 백테스트 100경기 |
| **실행 시간** | < 150초 | 성능 테스트 |
| **비용** | $0.50-1.00 | 실측 |

---

#### 4. 비기능 요구사항

**성능**:
- Phase 2 (100회): < 10초
- Phase 6 (3,000회): < 35초
- 전체: < 150초 (N=3 평균)

**확장성**:
- 동시 요청 10개 처리
- Redis 캐싱 (1시간 TTL)
- 병렬 시뮬레이션 (멀티프로세싱)

**신뢰성**:
- API 실패 시 재시도 (3회)
- 부분 수렴 허용 (8회 반복 후)
- 에러 핸들링 (Graceful degradation)

**유지보수성**:
- 모듈화된 구조 (각 Phase 독립)
- Type hints 및 docstring (100%)
- 통합 테스트 커버리지 > 80%
- 문서화 완비

---

## 14주 완전 구현 로드맵

### 전체 타임라인

```
Week 1-2   │ 통계 엔진 프로토타입
Week 3     │ 서사 가이드 시스템
Week 4-5   │ AI 통합 (Phase 1, 3, 7)
Week 6     │ 반복 루프
Week 7-8   │ 서사 라이브러리 구축 ⭐ (Critical)
Week 9-10  │ 검증 및 최적화
Week 11-12 │ 프론트엔드
Week 13-14 │ 테스트 및 런칭
```

### Phase별 의존성

```
[Week 1-2: 통계 엔진] ──┐
                        ├─→ [Week 3: 서사 가이드] ──┐
[Week 7-8: 서사 라이브러리] ─────────────────────┘
                                                  │
                                                  ├─→ [Week 4-5: AI 통합] ──→ [Week 6: 반복 루프]
                                                  │
                                                  └─→ [Week 9-10: 검증]
                                                                 │
                                                                 └─→ [Week 11-12: 프론트엔드]
                                                                                 │
                                                                                 └─→ [Week 13-14: 런칭]
```

### Critical Path

**서사 라이브러리 구축 (Week 7-8)**이 가장 중요하고 복잡합니다.
- 축구 전문가 협업 필수
- 품질이 전체 시스템 성능 결정
- 병렬 작업: Week 1-6 동안 전문가 섭외 및 초기 논의 시작

---

## Phase별 상세 구현 계획

### Week 1-2: 통계 엔진 프로토타입

#### 목표
EPL 통계 기반 이벤트 확률 엔진 구축 (서사 부스트 적용 가능)

#### 작업

**Day 1-3: Event Probability Calculator**
```python
# backend/simulation/v3/event_calculator.py

class EventProbabilityCalculator:
    """
    현재 경기 상황에서 이벤트 확률 계산
    """

    def __init__(self, epl_baseline: dict):
        self.baseline = epl_baseline

    def calculate(self, context: MatchContext, boost: Optional[NarrativeBoost]) -> dict:
        """
        확률 계산 (서사 부스트 포함)

        Returns:
            {
                'shot_rate': 0.15,
                'shot_on_target_ratio': 0.40,
                'goal_conversion': 0.11,
                'corner_rate': 0.10,
                'foul_rate': 0.08
            }
        """
        probs = self.baseline.copy()

        # 1. 팀 능력치 보정
        probs = self._adjust_for_team_strength(probs, context)

        # 2. 전술 보정
        probs = self._adjust_for_tactics(probs, context)

        # 3. 경기 상황 보정 (스코어, 시간)
        probs = self._adjust_for_match_state(probs, context)

        # 4. 체력 보정
        probs = self._adjust_for_fatigue(probs, context)

        # 5. 서사 부스트 적용 ⭐
        if boost:
            probs = self._apply_narrative_boost(probs, boost)

        return probs

    def _apply_narrative_boost(self, probs: dict, boost: NarrativeBoost) -> dict:
        """
        서사 부스트 적용

        예:
        - boost.type = 'wing_breakthrough'
        - boost.multiplier = 2.5
        → shot_rate *= 2.5 (측면 돌파 시 슈팅 증가)
        """
        if boost.type == 'wing_breakthrough':
            probs['shot_rate'] *= boost.multiplier
        elif boost.type == 'goal':
            probs['goal_conversion'] *= boost.multiplier
        elif boost.type == 'corner':
            probs['corner_rate'] *= boost.multiplier

        return probs
```

**Day 4-7: Match Simulator (90분 시뮬레이션)**
```python
# backend/simulation/v3/statistical_engine.py

class StatisticalMatchEngine:
    """
    90분 분 단위 시뮬레이션 (이벤트 기반)
    """

    def simulate_match(self, params: MatchParams, scenario_guide: ScenarioGuide) -> MatchResult:
        """
        단일 경기 시뮬레이션

        Args:
            params: 팀 능력치, 전술 등
            scenario_guide: 서사 가이드 (분별 부스트)

        Returns:
            {
                'final_score': {'home': 2, 'away': 1},
                'events': [...],  # 분 단위 이벤트 기록
                'narrative_adherence': 0.85  # 서사 일치율
            }
        """
        state = self._init_state(params)

        for minute in range(90):
            state['minute'] = minute

            # 1. 점유 팀 결정
            possession = self._determine_possession(params, state)

            # 2. 서사 부스트 가져오기
            boost = scenario_guide.get_boost_at(minute)

            # 3. 이벤트 확률 계산
            event_probs = self.calculator.calculate(
                MatchContext(params, state, possession),
                boost
            )

            # 4. 이벤트 샘플링
            event = self._sample_event(event_probs)

            # 5. 이벤트 해결
            if event:
                self._resolve_event(event, state, possession, params)

            # 6. 상태 업데이트
            self._update_state(state, minute)

        # 7. 서사 일치율 계산
        adherence = self._calculate_narrative_adherence(state, scenario_guide)

        return MatchResult(state['score'], state['events'], adherence)

    def _calculate_narrative_adherence(self, state: dict, guide: ScenarioGuide) -> float:
        """
        실제 발생 이벤트와 예상 이벤트의 일치율

        예:
        - 예상: 15-25분 손흥민 돌파 → 실제: 18분 발생 → 일치 ✅
        - 예상: 30분 득점 → 실제: 발생 안함 → 불일치 ❌

        Returns:
            일치율 0.0-1.0
        """
        matched = 0
        total = len(guide.events)

        for expected_event in guide.events:
            actual_events = [
                e for e in state['events']
                if e['type'] == expected_event['type']
                and expected_event['minute_range'][0] <= e['minute'] <= expected_event['minute_range'][1]
            ]
            if actual_events:
                matched += 1

        return matched / total if total > 0 else 0.0
```

**Day 8-10: EPL Baseline 캘리브레이션 및 테스트**
```python
# backend/simulation/shared/epl_baseline.py

EPL_BASELINE_V3 = {
    # 득점 관련
    "avg_goals_per_game": 2.8,
    "home_goals": 1.53,
    "away_goals": 1.27,
    "goal_std": 1.6,

    # 슛 관련
    "shot_per_minute": 0.15,  # 팀당
    "shot_on_target_ratio": 0.33,
    "goal_conversion_on_target": 0.11,

    # 이벤트
    "corner_per_minute": 0.10,
    "foul_per_minute": 0.08,
    "yellow_card_per_game": 3.8,
    "red_card_per_game": 0.28,

    # 승률
    "home_win_rate": 0.46,
    "draw_rate": 0.27,
    "away_win_rate": 0.27
}

# 테스트: 1,000회 시뮬레이션 → EPL 평균과 비교
# 목표: 득점 2.5-3.0, 승률 ±5%
```

#### 산출물
- ✅ `event_calculator.py` (~300줄)
- ✅ `statistical_engine.py` (~500줄)
- ✅ `epl_baseline.py` (~150줄)
- ✅ 단위 테스트 (`test_engine.py`, ~200줄)
- ✅ 캘리브레이션 리포트

#### 검증 기준
- [ ] 1,000회 시뮬 < 20초
- [ ] 평균 득점 2.5-3.0
- [ ] 홈 승률 40-50%
- [ ] 서사 부스트 적용 시 확률 변화 확인

---

### Week 3: 서사 가이드 시스템

#### 목표
시나리오를 분 단위 부스트로 변환하는 시스템

#### 작업

**Day 1-3: Scenario Guide 클래스**
```python
# backend/simulation/v3/scenario_guide.py

class ScenarioGuide:
    """
    AI 생성 시나리오를 확률 부스트로 변환
    """

    def __init__(self, scenario: dict):
        """
        Args:
            scenario: AI가 생성한 시나리오
            {
                'id': 'SYNTH_001',
                'events': [
                    {
                        'minute_range': [10, 25],
                        'type': 'wing_breakthrough',
                        'actor': 'Son',
                        'team': 'home',
                        'probability_boost': 2.5
                    },
                    {
                        'minute_range': [15, 30],
                        'type': 'goal',
                        'team': 'home',
                        'probability_boost': 1.8
                    }
                ]
            }
        """
        self.scenario = scenario
        self.boosts_by_minute = self._parse_events()

    def _parse_events(self) -> dict:
        """
        이벤트 시퀀스 → 분별 부스트 맵

        Returns:
            {
                10: NarrativeBoost(type='wing_breakthrough', multiplier=2.5, team='home'),
                11: NarrativeBoost(...),
                ...
                25: NarrativeBoost(...),
                15: NarrativeBoost(type='goal', multiplier=1.8, team='home'),
                ...
            }
        """
        boosts = {}

        for event in self.scenario['events']:
            for minute in range(event['minute_range'][0], event['minute_range'][1] + 1):
                boost = NarrativeBoost(
                    type=event['type'],
                    multiplier=event.get('probability_boost', 1.0),
                    team=event.get('team', 'home'),
                    actor=event.get('actor')
                )
                boosts[minute] = boost

        return boosts

    def get_boost_at(self, minute: int) -> Optional[NarrativeBoost]:
        """
        특정 분의 부스트 반환
        """
        return self.boosts_by_minute.get(minute)

@dataclass
class NarrativeBoost:
    """서사 부스트 데이터 클래스"""
    type: str  # 'wing_breakthrough', 'goal', 'corner', etc.
    multiplier: float  # 1.0-3.0
    team: str  # 'home' or 'away'
    actor: Optional[str] = None  # 선수 이름
```

**Day 4-5: 통합 테스트**
```python
# tests/v3/test_scenario_guide.py

def test_scenario_guide_integration():
    """
    시나리오 가이드 + 통계 엔진 통합 테스트
    """
    # 1. 테스트 시나리오 생성
    scenario = {
        'id': 'TEST_001',
        'events': [
            {
                'minute_range': [10, 20],
                'type': 'wing_breakthrough',
                'probability_boost': 2.0
            }
        ]
    }

    # 2. 서사 가이드 생성
    guide = ScenarioGuide(scenario)

    # 3. 100회 시뮬레이션
    engine = StatisticalMatchEngine()
    results = []
    for _ in range(100):
        result = engine.simulate_match(params, guide)
        results.append(result)

    # 4. 검증
    # 4a. 서사 일치율 > 70%
    avg_adherence = np.mean([r.narrative_adherence for r in results])
    assert avg_adherence > 0.70

    # 4b. 10-20분 돌파 이벤트 증가 확인
    events_10_20 = [e for r in results for e in r.events if 10 <= e['minute'] <= 20]
    wing_events = [e for e in events_10_20 if e['type'] == 'wing_breakthrough']
    # 부스트 없을 때 대비 2배 증가 예상
    assert len(wing_events) > 15  # 100회 중 15% 이상
```

#### 산출물
- ✅ `scenario_guide.py` (~250줄)
- ✅ 통합 테스트 (~150줄)
- ✅ 문서 (서사 가이드 사용법)

#### 검증 기준
- [ ] 서사 일치율 > 70% (100회 평균)
- [ ] 부스트 적용 시 확률 2배 증가 확인
- [ ] 에러 핸들링 (잘못된 시나리오 입력)

---

### Week 4-5: AI 통합 (Phase 1, 3, 7)

#### 목표
AI 프롬프트 설계 및 3개 Phase 구현

#### Week 4: Phase 1 (AI 시나리오 생성) + Phase 7 (AI 리포트)

**Day 1-3: Phase 1 프롬프트 설계**
```python
# backend/ai/prompts/scenario_generation.py

SCENARIO_GENERATION_PROMPT = """
당신은 EPL 전술 시뮬레이션 전문가입니다.

# 입력

## 경기 컨텍스트
- 홈팀: {home_team}
- 원정팀: {away_team}
- 경기장: {venue}

## 선수 능력치 (주요 선수만)
{player_stats}

## 전술 정보
홈팀 ({home_team}):
- 포메이션: {home_formation}
- 압박 강도: {home_press_intensity}/100
- 빌드업 스타일: {home_buildup_style}

원정팀 ({away_team}):
- 포메이션: {away_formation}
- 압박 강도: {away_press_intensity}/100
- 빌드업 스타일: {away_buildup_style}

## 사용자 도메인 지식
{user_domain_knowledge}

## 매칭된 서사 템플릿 (라이브러리에서 선택된 5-10개)
{matched_narratives}

---

# 작업

위 정보를 바탕으로 5-7개의 구체적 시나리오를 생성하세요.

## 각 시나리오 요구사항

1. **서사 템플릿 기반**: 위 매칭된 서사 중 하나를 기반으로 작성
2. **사용자 지식 반영**: 사용자 도메인 지식을 파라미터 조정에 반영
3. **이벤트 시퀀스**: 경기 흐름을 분 단위로 예측 (3-5개 이벤트)
4. **확률 가중치**: 각 이벤트의 probability_boost (1.0-3.0)
5. **예상 발생 확률**: 이 시나리오가 발생할 확률 (0.0-1.0)
6. **추론 근거**: 왜 이 시나리오를 생성했는지 설명

## 제약 조건

- **시나리오 수**: 정확히 5-7개
- **probability_boost 범위**: 1.0-3.0만 사용
- **예상 확률 합**: 0.9-1.1 범위 (100% 근처)
- **각 시나리오 구별성**: 예상 결과가 명확히 달라야 함

---

# Few-shot Examples

## Example 1
입력:
- 홈팀: Tottenham, 원정팀: Arsenal
- 사용자: "손흥민은 빅매치에서 강하다. 아스날 좌측 수비가 약하다."
- 매칭 서사: "NAR_142: 측면 우위 → 초반 선제"

출력:
{{
  "scenarios": [
    {{
      "id": "SYNTH_001",
      "base_narrative": "NAR_142",
      "name": "손흥민 측면 우위 → 초반 선제 → 토트넘 완승",
      "reasoning": "사용자 언급 '손흥민 빅매치 강세' + '아스날 좌측 약점'을 반영. 서사 NAR_142(측면 우위)를 기반으로 토트넘 우측 공격 강화.",
      "events": [
        {{
          "minute_range": [10, 25],
          "type": "wing_breakthrough",
          "actor": "Son",
          "team": "home",
          "probability_boost": 2.5,
          "reason": "Son(92 스피드) vs 아스날 좌측 수비 약점"
        }},
        {{
          "minute_range": [15, 30],
          "type": "goal",
          "team": "home",
          "method": "wing_attack",
          "probability_boost": 1.8,
          "reason": "측면 돌파 후 득점 가능성 증가"
        }},
        {{
          "minute_range": [70, 85],
          "type": "goal",
          "team": "home",
          "method": "counter_attack",
          "probability_boost": 1.4,
          "reason": "아스날 공세 시 역습 기회"
        }}
      ],
      "parameter_adjustments": {{
        "Son_speed_modifier": 1.15,
        "Arsenal_left_defense_modifier": 0.75,
        "Tottenham_wing_attack_modifier": 1.25
      }},
      "expected_probability": 0.18
    }},
    {{
      "id": "SYNTH_002",
      "name": "초반 우위 → 중반 역전 → 아스날 승",
      "expected_probability": 0.14,
      ...
    }},
    ...총 5-7개
  ],
  "total_probability": 0.98,
  "confidence": 0.82,
  "reasoning_summary": "손흥민의 측면 우위를 핵심 변수로 보고 3가지 시나리오(완승, 역전패, 무승부)로 분기. 아스날 좌측 약점이 결정적 요인."
}}

---

# 실제 입력 (처리할 경기)

경기 컨텍스트:
- 홈팀: {home_team}
- 원정팀: {away_team}
...

# 출력 (JSON만, 설명 제외)

"""

# 토큰 수: ~2,000 (Few-shot 포함)
```

**Day 4-5: Phase 7 프롬프트 설계**
```python
# backend/ai/prompts/final_report.py

FINAL_REPORT_PROMPT = """
당신은 EPL 전술 분석 전문가입니다.
시뮬레이션 결과를 종합하여 최종 리포트를 작성하세요.

# 입력

## 반복 과정 히스토리
{refinement_history_json}

## 최종 시뮬레이션 결과 (3,000회)
{final_results_json}

## 사용자 원본 입력
{user_input_json}

---

# 리포트 구성

## 1. 최종 예측 (100자)
- 승률 (홈/무/원정, 95% 신뢰구간)
- 가장 가능성 높은 스코어
- 예상 득점 (xG)

## 2. 지배적 시나리오 (150자)
- 확률 순 상위 3개 시나리오
- 각 시나리오의 핵심 특징
- 발생 확률

## 3. 핵심 변수 분석 (150자)
- 결과에 가장 큰 영향을 미친 요인 3가지
- 정량적 임팩트 제시 (승률 +X%)

## 4. 사용자 도메인 지식 검증 (100자)
- 사용자 통찰이 유의미했는가?
- 어떤 통찰이 승률에 영향을 주었는가?
- 정량화 (승률 +X%)

## 5. 반복 과정 요약 (100자)
- 총 몇 번 반복했는가?
- 주요 조정 내역 (간략)
- 최종 수렴도 (신뢰도 %)

## 6. 리스크 및 변수 (100자)
- 예측의 불확실성
- 주요 리스크 요인 (만약 X하면 Y)

---

# 출력 요구사항

- **총 길이**: 500-700자
- **톤**: 전문적, 명확, 간결
- **불필요한 수식어 배제**
- **구체적 수치 제시**
- **형식**: 마크다운

---

# Few-shot Example

입력:
- 홈팀: Tottenham vs 원정: Arsenal
- 사용자: "손흥민 빅매치 강세, 아스날 좌측 약점"
- 최종 결과: 토트넘 43%, 무 22%, 아스날 35%

출력:
```
=== 토트넘 vs 아스날 예측 분석 ===

[최종 예측]
토트넘 승률: 43% (95% CI: 40-46%)
아스날 승률: 35% (95% CI: 32-38%)
무승부: 22%
가장 가능성 높은 스코어: 토트넘 2-1 (14%)
예상 득점: 토트넘 xG 2.15, 아스날 xG 1.68

[지배적 시나리오]
1. "손흥민 측면 우위 → 초반 선제 → 완승" (18%)
   - 15-25분 손흥민 돌파 → 선제골
   - 후반 추가골로 승리 확정

2. "초반 우위 → 아스날 역전" (16%)
   - 토트넘 초반 리드
   - 75분 이후 아스날 중앙 공격 성공

3. "박빙 → 세트피스 결정" (14%)
   - 양팀 기회 없음
   - 코너킥/프리킥으로 승부

[핵심 변수]
1. **손흥민 빅매치 보정(+15%)**: 승률 +5.2% 기여
   - 초반 20분 내 득점 확률 19% → 28%
2. **아스날 좌측 수비 약화**: 우측 공격 성공률 41% → 54%
3. **후반 체력**: 토트넘 템포 유지 시 승률 +3%

[사용자 도메인 지식 검증]
귀하의 2가지 핵심 통찰 모두 유의미했습니다:
- "손흥민 빅매치 강세" → 승률 +5.2%
- "아스날 좌측 약점" → 우측 공격 성공률 +13%

[반복 과정]
총 3회 iteration으로 수렴 (신뢰도 89%)
- Iter 1: 득점 과다 편향 감지 → attack_modifier 10% 감소
- Iter 2: 서사 일치율 개선 → wing_boost 40% 증가
- Iter 3: 최종 검증 통과

[리스크]
- 손흥민 컨디션 기대 미달 시 승률 43% → 36%
- 아스날 좌측 수비 보강 시 승률 43% → 39%
```

---

# 실제 입력 (처리할 경기)

{actual_input}

# 출력 (마크다운 형식)

"""

# 토큰 수: ~2,500
```

#### Week 5: Phase 3 (AI 분석 및 조정)

**Day 1-3: Phase 3 프롬프트 설계**
```python
# backend/ai/prompts/analysis_adjustment.py

ANALYSIS_ADJUSTMENT_PROMPT = """
당신은 시뮬레이션 품질 관리 AI입니다.

# Context
Iteration {iteration_number}의 시뮬레이션 결과를 분석합니다.

# Input Data

## 시뮬레이션 결과 (100회 × {num_scenarios}개 시나리오)
{validation_results_json}

## EPL 기준 통계
- 평균 득점: 2.8골/경기 (±0.6)
- 득점 표준편차: 1.6
- 홈 승률: 46% (±5%)
- 무승부: 27% (±5%)
- 원정 승률: 27% (±5%)
- 평균 슛: 13회/경기
- 온타겟 비율: 33%
- 온타겟 중 득점: 11%

---

# 분석 작업

## 1. 편향 감지
각 시나리오의 비정상적 패턴 식별:

### 1.1 득점 편향
- 평균 득점이 EPL 평균 ± 0.6골을 벗어나는가?
  - 벗어나면: 심각도 "high"
  - 범위 내: 심각도 "low"
- 특정 팀에 과도한 유리/불리가 있는가?

### 1.2 승률 편향
- 홈 승률이 40-55% 범위를 벗어나는가?
- 무승부 비율이 20-35% 범위를 벗어나는가?

### 1.3 이벤트 빈도 편향
- 슛 횟수가 10-16회 범위를 벗어나는가?
- 특정 이벤트 타입이 과다/과소 발생하는가?

## 2. 서사 일치율 분석
- 일치율 < 0.75인 시나리오 식별
- 일치율이 낮은 원인 분석:
  - probability_boost가 너무 낮은가? (< 1.5)
  - 다른 파라미터가 서사를 방해하는가?
  - 서사 자체가 비현실적인가?

## 3. 파라미터 조정 제안
각 문제에 대해:
- **문제의 정량적 표현**: "평균 득점 3.2, 목표 2.8 (+14%)"
- **근본 원인 추정**: "shot_rate 기본값 과다"
- **구체적 조정값**: "shot_rate: 0.18 → 0.14 (-22%)"
- **예상 효과**: "평균 득점 3.2 → 2.9 (-9%)"

## 4. 시나리오 품질 평가
- **중복된 시나리오 식별**: 결과가 너무 유사 (승률 차이 < 5%, 스코어 차이 < 0.2골)
- **비현실적 시나리오 식별**: 서사 일치율 지속적으로 < 0.60
- **통합 또는 제거 제안**

## 5. 수렴 평가
다음 5개 기준으로 수렴 여부 판단:

1. **득점 범위**: 모든 시나리오 평균 득점 2.2-3.4 범위 (가중치 25%)
2. **편향도**: 모든 시나리오 편향도 < 0.10 (가중치 25%)
3. **서사 일치율**: 모든 시나리오 > 0.75 (가중치 20%)
4. **승률 분포**: EPL 평균 ± 10% 범위 (가중치 20%)
5. **안정성**: 이전 iteration 대비 변화 < 5% (가중치 10%)

**수렴 신뢰도**: 충족된 기준의 가중 평균
**수렴 판정**: confidence > 0.85이면 converged = true

---

# Output Format (JSON)

{{
  "iteration": {iteration_number},
  "analysis": {{
    "issues": [
      {{
        "scenario_id": "SYNTH_001",
        "issue_type": "score_bias" | "win_rate_bias" | "narrative_adherence_low" | "event_frequency_bias",
        "severity": "high" | "medium" | "low",
        "description": "홈팀 평균 득점 3.4골, EPL 평균 2.8골보다 +21% 높음",
        "root_cause": "shot_per_minute 기본값이 과도하게 높음",
        "adjustment": {{
          "parameter": "base_shot_rate" | "home_attack_modifier" | "events[0].probability_boost" | ...,
          "current_value": 0.18,
          "proposed_value": 0.14,
          "expected_impact": "평균 득점 3.4 → 2.9로 감소 (-15%)"
        }}
      }},
      ...
    ],
    "global_adjustments": {{
      "goal_rate_global_multiplier": {{
        "current": 1.0,
        "proposed": 0.88,
        "reason": "전체 평균 득점 3.2골을 EPL 2.8골로 조정"
      }}
    }},
    "scenario_recommendations": {{
      "merge": [
        {{
          "scenarios": ["SYNTH_002", "SYNTH_005"],
          "reason": "결과가 거의 동일 (승률 차이 2%, 스코어 차이 0.1골)"
        }}
      ],
      "remove": [
        {{
          "scenario": "SYNTH_007",
          "reason": "서사 일치율 지속적으로 0.60 미만, 비현실적"
        }}
      ]
    }}
  }},
  "convergence": {{
    "converged": false,
    "confidence": 0.72,
    "criteria_met": ["score_range_check", "win_rate_distribution"],
    "criteria_failed": ["bias_threshold", "narrative_adherence"],
    "scores": {{
      "score_range": 1.0,
      "bias_threshold": 0.6,
      "narrative_adherence": 0.7,
      "win_rate_distribution": 0.9,
      "stability": 0.4
    }},
    "estimated_iterations_needed": 2,
    "recommendation": "2회 추가 반복 권장, 주요 이슈 3개 해결 필요"
  }}
}}

---

# Few-shot Example

(생략, 너무 길어서)

---

# 실제 입력 (Iteration {iteration_number})

{actual_validation_results}

# 출력 (JSON만)

"""

# 토큰 수: ~1,500
```

**Day 4-5: AI Client 통합**
```python
# backend/ai/ai_simulation_client.py

class AISimulationClient:
    """
    AI 호출 통합 클라이언트 (Phase 1, 3, 7)
    """

    def __init__(self, ai_client):
        self.ai = ai_client  # Claude or GPT-4

    def generate_scenarios(self, match_context: dict, matched_narratives: list) -> dict:
        """
        Phase 1: AI 시나리오 생성
        """
        prompt = SCENARIO_GENERATION_PROMPT.format(
            home_team=match_context['home_team'],
            away_team=match_context['away_team'],
            player_stats=match_context['player_stats'],
            ...
            matched_narratives=matched_narratives
        )

        response = self.ai.complete(prompt, max_tokens=4000)
        scenarios = json.loads(response)

        # 검증
        assert 5 <= len(scenarios['scenarios']) <= 7
        assert 0.9 <= scenarios['total_probability'] <= 1.1

        return scenarios

    def analyze_and_adjust(self, validation_results: list, iteration: int,
                           previous_results: Optional[list] = None) -> dict:
        """
        Phase 3: AI 분석 및 조정
        """
        prompt = ANALYSIS_ADJUSTMENT_PROMPT.format(
            iteration_number=iteration,
            num_scenarios=len(validation_results),
            validation_results_json=json.dumps(validation_results, indent=2)
        )

        response = self.ai.complete(prompt, max_tokens=3000)
        analysis = json.loads(response)

        return analysis

    def generate_final_report(self, final_results: dict, history: list,
                             user_input: dict) -> str:
        """
        Phase 7: AI 최종 리포트
        """
        prompt = FINAL_REPORT_PROMPT.format(
            refinement_history_json=json.dumps(history, indent=2),
            final_results_json=json.dumps(final_results, indent=2),
            user_input_json=json.dumps(user_input, indent=2)
        )

        response = self.ai.complete(prompt, max_tokens=2000)

        # 검증: 500-700자
        word_count = len(response)
        assert 500 <= word_count <= 800, f"리포트 길이 {word_count}자, 목표 500-700자"

        return response
```

#### 산출물
- ✅ 프롬프트 3개 (`scenario_generation.py`, `analysis_adjustment.py`, `final_report.py`)
- ✅ AI 클라이언트 (`ai_simulation_client.py`, ~400줄)
- ✅ 프롬프트 테스트 (~200줄)
- ✅ 프롬프트 문서

#### 검증 기준
- [ ] Phase 1: 시나리오 5-7개, 확률 합 0.9-1.1
- [ ] Phase 3: JSON 파싱 성공률 > 95%
- [ ] Phase 7: 리포트 500-700자, 6개 섹션 포함
- [ ] AI 비용: $0.50-0.80/경기

---

### Week 6: 반복 루프

#### 목표
Phase 2-5를 반복하는 오케스트레이터 구현

#### 작업

**Day 1-3: Convergence Judge (수렴 판정)**
```python
# backend/simulation/v3/convergence_judge.py

class ConvergenceJudge:
    """
    수렴 판정 (5개 기준, 가중 평균)
    """

    CRITERIA_WEIGHTS = {
        "score_range": 0.25,
        "bias_threshold": 0.25,
        "narrative_adherence": 0.20,
        "win_rate_distribution": 0.20,
        "stability": 0.10
    }

    def check_convergence(self, validation_results: list,
                         previous_results: Optional[list],
                         iteration: int) -> dict:
        """
        수렴 여부 판정

        Returns:
            {
                'converged': True/False,
                'confidence': 0.87,
                'scores': {
                    'score_range': 1.0,
                    'bias_threshold': 0.8,
                    ...
                },
                'reason': 'strict_criteria_met'
            }
        """
        scores = {}

        # 1. 득점 범위 (2.2-3.4)
        scores['score_range'] = self._check_score_range(validation_results)

        # 2. 편향도 (< 0.10)
        scores['bias_threshold'] = self._check_bias_threshold(validation_results)

        # 3. 서사 일치율 (> 0.75)
        scores['narrative_adherence'] = self._check_narrative_adherence(validation_results)

        # 4. 승률 분포 (EPL ±10%)
        scores['win_rate_distribution'] = self._check_win_rate_distribution(validation_results)

        # 5. 안정성 (이전 대비 < 5%)
        if previous_results:
            scores['stability'] = self._check_stability(validation_results, previous_results)
        else:
            scores['stability'] = 0.0  # 첫 iteration은 안정성 체크 불가

        # 가중 평균 계산
        confidence = sum(
            scores[k] * self.CRITERIA_WEIGHTS[k]
            for k in self.CRITERIA_WEIGHTS
        )

        # 수렴 판정
        if iteration <= 5:
            # Strict mode
            converged = confidence > 0.85
            reason = 'strict_criteria_met' if converged else 'strict_criteria_not_met'
        elif iteration <= 7:
            # Relaxed mode
            converged = confidence > 0.75
            reason = 'relaxed_criteria_met' if converged else 'relaxed_criteria_not_met'
        else:
            # Forced convergence (8+ iterations)
            converged = True
            reason = 'forced_convergence_max_iterations'

        return {
            'converged': converged,
            'confidence': confidence,
            'scores': scores,
            'reason': reason,
            'iteration': iteration
        }
```

**Day 4-5: Match Simulator V3 (Orchestrator)**
```python
# backend/simulation/v3/match_simulator_v3.py

class MatchSimulatorV3:
    """
    AI-Guided Iterative Refinement 오케스트레이터
    """

    def __init__(self):
        self.ai_client = AISimulationClient(get_ai_client())
        self.engine = StatisticalMatchEngine()
        self.bias_detector = BiasDetector()
        self.narrative_analyzer = NarrativeAnalyzer()
        self.convergence_judge = ConvergenceJudge()
        self.parameter_adjuster = ParameterAdjuster()

    def predict(self, home_team: str, away_team: str,
                match_context: dict, user_insight: str) -> dict:
        """
        7단계 프로세스 실행
        """

        # Phase 1: AI 시나리오 생성
        logger.info("Phase 1: AI 시나리오 생성")
        matched_narratives = self._match_narratives(match_context, user_insight)
        scenarios_data = self.ai_client.generate_scenarios(match_context, matched_narratives)
        scenarios = scenarios_data['scenarios']
        logger.info(f"생성된 시나리오: {len(scenarios)}개")

        # Phase 2-5: 반복 개선 루프
        iteration = 1
        max_iterations = 8
        converged = False
        history = []
        previous_results = None

        while not converged and iteration <= max_iterations:
            logger.info(f"\nIteration {iteration}")

            # Phase 2: 통계 검증 (100회 × 시나리오 수)
            logger.info(f"Phase 2: 시뮬레이션 ({len(scenarios)}개 × 100회)")
            validation_results = self._validate_scenarios(scenarios, match_context, n=100)

            # Phase 3: AI 분석 및 조정
            logger.info("Phase 3: AI 분석 및 조정")
            ai_analysis = self.ai_client.analyze_and_adjust(
                validation_results,
                iteration,
                previous_results
            )

            # 히스토리 기록
            history.append({
                'iteration': iteration,
                'scenarios': scenarios,
                'validation_results': validation_results,
                'ai_analysis': ai_analysis
            })

            # Phase 4-5: 수렴 체크
            convergence_result = self.convergence_judge.check_convergence(
                validation_results,
                previous_results,
                iteration
            )

            logger.info(f"수렴 신뢰도: {convergence_result['confidence']:.2%}")

            if convergence_result['converged']:
                converged = True
                logger.info(f"✅ 수렴 완료 (Iteration {iteration})")
                break
            else:
                logger.info(f"→ 조정 필요 ({len(ai_analysis['analysis']['issues'])}개 이슈)")

                # 파라미터 조정
                scenarios = self.parameter_adjuster.adjust(scenarios, ai_analysis)
                previous_results = validation_results
                iteration += 1

        # Phase 6: 최종 고해상도 시뮬레이션 (3,000회)
        logger.info("\nPhase 6: 최종 시뮬레이션 (3,000회)")
        final_results = self._validate_scenarios(scenarios, match_context, n=3000)

        # Phase 7: AI 최종 리포트
        logger.info("Phase 7: AI 최종 리포트 생성")
        final_report = self.ai_client.generate_final_report(
            final_results,
            history,
            {'home_team': home_team, 'away_team': away_team, 'user_insight': user_insight}
        )

        return {
            'match': {
                'home_team': home_team,
                'away_team': away_team,
                'user_insight': user_insight
            },
            'prediction': self._aggregate_final_results(final_results),
            'ai_report': final_report,
            'convergence': {
                'total_iterations': iteration,
                'converged': converged,
                'confidence': convergence_result['confidence'],
                'history': history
            },
            'metadata': {
                'version': '3.0',
                'total_simulations': len(scenarios) * (100 * iteration + 3000),
                'elapsed_seconds': None  # TODO: 타이머 추가
            }
        }
```

#### 산출물
- ✅ `convergence_judge.py` (~200줄)
- ✅ `match_simulator_v3.py` (~400줄)
- ✅ 통합 테스트 (~300줄)

#### 검증 기준
- [ ] 수렴 성공률 > 90% (100회 테스트)
- [ ] 평균 반복 횟수 2-4회
- [ ] 전체 실행 시간 < 150초

---

### Week 7-8: 서사 라이브러리 구축 ⭐ (Critical)

#### 목표
500개 서사 템플릿 구축 (축구 전문가 협업)

#### 전제 조건
- 축구 전문가 1-2명 섭외 (Week 1-6 동안 진행)
- EPL 전문 지식 (전술, 선수, 팀 스타일)
- 시간 투입: 주 10-15시간 × 2주

#### Week 7: 핵심 서사 50개 수동 작성

**Day 1-2: 서사 차원 설계**
```python
# 서사 차원 (Narrative Dimensions)

NARRATIVE_DIMENSIONS = {
    # 1. 경기 템포
    'tempo': [
        'slow_patient',      # 느린 패스 플레이
        'balanced',          # 균형잡힌
        'high_intensity',    # 치열한 공방
        'chaotic'            # 혼란스러운
    ],

    # 2. 득점 수준
    'scoring_level': [
        'low_scoring',       # 0-1골 (수비적)
        'standard',          # 2-3골 (평균)
        'high_scoring'       # 4+골 (공격적)
    ],

    # 3. 우세 팀
    'dominance': [
        'home_dominant',     # 홈 압도
        'balanced',          # 균형
        'away_dominant',     # 원정 압도
        'momentum_swing'     # 주도권 변화
    ],

    # 4. 주요 공격 루트
    'attack_route': [
        'wing_attack',       # 측면 공격
        'central_penetration', # 중앙 돌파
        'set_piece',         # 세트피스
        'counter_attack',    # 역습
        'long_ball'          # 롱볼
    ],

    # 5. 전술 변화
    'tactical_change': [
        'none',              # 변화 없음
        'formation_shift',   # 포메이션 변경
        'substitution_impact', # 교체 효과
        'defensive_drop'     # 수비 후퇴
    ],

    # 6. 경기 흐름
    'match_flow': [
        'steady',            # 일관된 흐름
        'early_goal_impact', # 초반 골 영향
        'late_drama',        # 후반 드라마
        'first_half_dominated', # 전반 우세
        'second_half_comeback' # 후반 역전
    ]
}

# 조합 가능 수: 4 × 3 × 4 × 5 × 4 × 5 = 4,800개
# 목표: 500개 선택
```

**Day 3-10: 핵심 서사 50개 작성 (축구 전문가)**

서사 템플릿 예시:
```yaml
# narratives/NAR_001.yaml

id: NAR_001
name: "측면 우위 → 초반 선제 → 완승"
description: |
  한 팀이 측면 공격에서 명확한 우위를 점하고,
  초반 선제골로 주도권을 잡아 완승하는 시나리오

dimensions:
  tempo: high_intensity
  scoring_level: standard
  dominance: home_dominant
  attack_route: wing_attack
  tactical_change: none
  match_flow: early_goal_impact

events:
  - minute_range: [10, 25]
    type: wing_breakthrough
    description: "측면에서 돌파 시도 증가"
    probability_boost_range: [1.8, 2.5]
    success_indicator: "wing_attack_success"

  - minute_range: [15, 30]
    type: goal
    description: "측면 공격으로 선제골"
    probability_boost_range: [1.5, 2.0]
    dependency: wing_breakthrough

  - minute_range: [60, 90]
    type: defensive_stability
    description: "리드 후 안정적 수비"
    probability_boost_range: [0.7, 0.9]
    note: "상대 공격 확률 감소"

  - minute_range: [75, 90]
    type: goal
    description: "추가골로 승리 확정"
    probability_boost_range: [1.2, 1.5]

parameter_adjustments:
  home_wing_attack_modifier: [1.15, 1.30]
  away_wing_defense_modifier: [0.70, 0.85]
  home_defensive_stability_after_lead: [1.10, 1.20]

typical_outcomes:
  home_win_rate: [0.65, 0.80]
  expected_score_home: [2.0, 3.0]
  expected_score_away: [0.5, 1.5]

keywords:
  - "측면"
  - "wing"
  - "사이드"
  - "초반"
  - "선제골"
  - "완승"

applicable_conditions:
  - home_team_has_fast_wingers: true
  - away_team_weak_fullbacks: true
  - home_formation_wing_focused: true

expert_notes: |
  손흥민(토트넘), 살라(리버풀) 같은 빠른 윙어가 있고
  상대 풀백이 약한 경우 자주 발생.
  초반 20분이 결정적.

confidence: 0.85
frequency_in_epl: 0.08  # EPL 경기 중 8%

tags:
  - wing_attack
  - early_goal
  - home_advantage
  - tactical_dominance
```

**작성 프로세스**:
1. 전문가가 EPL 경기 분석 (과거 1-2시즌)
2. 반복적으로 나타나는 패턴 추출
3. 50개 핵심 서사 작성
4. 검토 및 수정 (다른 전문가 리뷰)

**Day 11-14: 검증 및 수정**
- 50개 서사 품질 검토
- 중복 제거
- 파라미터 범위 조정
- 키워드 최적화

#### Week 8: 조합 생성 및 시스템 구축

**Day 1-3: 조합 생성 알고리즘**
```python
# backend/services/narrative_library_builder.py

class NarrativeLibraryBuilder:
    """
    50개 핵심 서사 → 500개 조합 생성
    """

    def generate_combinations(self, core_narratives: list[dict]) -> list[dict]:
        """
        조합 전략:
        1. 핵심 서사 50개 (그대로 사용)
        2. 변형 450개:
           - 파라미터 조정 (±10%)
           - 이벤트 순서 변경
           - 타이밍 조정
           - 여러 서사 병합
        """
        combined = []

        # 1. 핵심 50개
        combined.extend(core_narratives)

        # 2. 파라미터 변형 (200개)
        for narrative in core_narratives[:25]:  # 인기 서사 25개
            for _ in range(8):  # 각 8개 변형
                variant = self._create_parameter_variant(narrative)
                combined.append(variant)

        # 3. 타이밍 변형 (150개)
        for narrative in core_narratives[:25]:
            for _ in range(6):
                variant = self._create_timing_variant(narrative)
                combined.append(variant)

        # 4. 서사 병합 (100개)
        for i in range(100):
            narrative1 = random.choice(core_narratives)
            narrative2 = random.choice(core_narratives)
            merged = self._merge_narratives(narrative1, narrative2)
            combined.append(merged)

        # 중복 제거
        combined = self._deduplicate(combined)

        return combined[:500]

    def _create_parameter_variant(self, narrative: dict) -> dict:
        """파라미터 ±10% 조정"""
        variant = copy.deepcopy(narrative)
        variant['id'] = f"{narrative['id']}_V{random.randint(1, 999)}"

        for key, value in variant['parameter_adjustments'].items():
            if isinstance(value, list):
                # 범위 조정
                variant['parameter_adjustments'][key] = [
                    value[0] * random.uniform(0.9, 1.1),
                    value[1] * random.uniform(0.9, 1.1)
                ]

        return variant
```

**Day 4-7: PostgreSQL 스키마 및 인덱싱**
```sql
-- backend/database/schema.sql

CREATE TABLE narratives (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Dimensions
    tempo VARCHAR(50),
    scoring_level VARCHAR(50),
    dominance VARCHAR(50),
    attack_route VARCHAR(50),
    tactical_change VARCHAR(50),
    match_flow VARCHAR(50),

    -- Data
    events JSONB NOT NULL,
    parameter_adjustments JSONB,
    typical_outcomes JSONB,
    keywords TEXT[],
    tags TEXT[],

    -- Metadata
    confidence FLOAT,
    frequency_in_epl FLOAT,
    expert_notes TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스
CREATE INDEX idx_narratives_keywords ON narratives USING GIN(keywords);
CREATE INDEX idx_narratives_tags ON narratives USING GIN(tags);
CREATE INDEX idx_narratives_dimensions ON narratives (tempo, scoring_level, dominance);

-- 임베딩 (향후 확장)
CREATE TABLE narrative_embeddings (
    narrative_id VARCHAR(50) REFERENCES narratives(id),
    embedding VECTOR(384),  -- Sentence-BERT 임베딩
    PRIMARY KEY (narrative_id)
);

CREATE INDEX idx_narrative_embeddings ON narrative_embeddings USING ivfflat (embedding vector_cosine_ops);
```

**Day 8-10: 매칭 알고리즘**
```python
# backend/services/narrative_matcher.py

class NarrativeMatcher:
    """
    사용자 입력 → 서사 템플릿 매칭
    """

    def __init__(self, db_connection):
        self.db = db_connection
        # TODO: 임베딩 모델 (향후)
        # self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    def match(self, match_context: dict, user_insight: str, top_k: int = 10) -> list[dict]:
        """
        컨텍스트 + 사용자 인사이트 → 상위 K개 서사

        전략:
        1. 키워드 매칭 (50%)
        2. 전술 매칭 (30%)
        3. 임베딩 유사도 (20%, 향후)
        """

        # 1. 키워드 추출
        keywords = self._extract_keywords(user_insight)

        # 2. SQL 쿼리 (키워드 매칭)
        query = """
        SELECT *,
               ts_rank(to_tsvector('english', description || ' ' || array_to_string(keywords, ' ')),
                       plainto_tsquery('english', %s)) AS keyword_score,
               CASE
                   WHEN tempo = %s THEN 0.3 ELSE 0
               END +
               CASE
                   WHEN attack_route = %s THEN 0.3 ELSE 0
               END AS tactical_score
        FROM narratives
        WHERE keywords && %s
        ORDER BY keyword_score * 0.5 + tactical_score * 0.5 DESC
        LIMIT %s
        """

        results = self.db.execute(
            query,
            (' '.join(keywords),
             match_context.get('tempo', 'balanced'),
             match_context.get('primary_attack_route', 'central_penetration'),
             keywords,
             top_k)
        )

        return results

    def _extract_keywords(self, text: str) -> list[str]:
        """
        텍스트에서 축구 관련 키워드 추출
        """
        # 간단한 키워드 사전
        FOOTBALL_KEYWORDS = [
            'wing', 'side', '측면', '사이드',
            'counter', 'countr attack', '역습',
            'set piece', 'corner', '세트피스', '코너킥',
            'possession', '점유율',
            'press', '압박',
            ...
        ]

        keywords = []
        text_lower = text.lower()

        for keyword in FOOTBALL_KEYWORDS:
            if keyword in text_lower:
                keywords.append(keyword)

        return keywords
```

**Day 11-14: 테스트 및 문서화**
- 500개 서사 품질 검증
- 매칭 정확도 테스트 (100케이스)
- 문서 작성 (서사 라이브러리 가이드)

#### 산출물
- ✅ 핵심 서사 50개 (YAML 파일)
- ✅ 조합 서사 450개 (자동 생성)
- ✅ PostgreSQL 스키마 및 데이터
- ✅ 매칭 알고리즘 (`narrative_matcher.py`, ~300줄)
- ✅ 서사 라이브러리 문서

#### 검증 기준
- [ ] 50개 핵심 서사 품질 검토 (전문가)
- [ ] 500개 조합 중복률 < 10%
- [ ] 매칭 정확도 > 80% (테스트 100케이스)
- [ ] 매칭 속도 < 0.5초

---

### Week 9-10: 검증 및 최적화

#### 목표
백테스트 100경기 + 성능 최적화

#### Week 9: 백테스트

**Day 1-2: 과거 경기 데이터 수집**
```python
# 2023-24 시즌 EPL 경기 100개
# 데이터: FPL API + 실제 결과
```

**Day 3-7: 백테스트 실행**
```python
# backend/scripts/backtest_v3.py

def backtest_v3(matches: list, simulator: MatchSimulatorV3):
    """
    100경기 백테스트
    """
    results = []

    for match in matches:
        # 예측
        prediction = simulator.predict(
            home_team=match['home_team'],
            away_team=match['away_team'],
            match_context=match['context'],
            user_insight=""  # 빈 인사이트
        )

        # 실제 결과와 비교
        actual_result = match['actual_result']

        # 정확도 계산
        predicted_winner = get_winner(prediction['prediction']['probabilities'])
        actual_winner = get_winner_from_score(actual_result['score'])

        correct = (predicted_winner == actual_winner)

        # Brier Score
        brier = calculate_brier_score(
            prediction['prediction']['probabilities'],
            actual_result
        )

        results.append({
            'match_id': match['id'],
            'correct': correct,
            'brier_score': brier,
            'predicted_probs': prediction['prediction']['probabilities'],
            'actual_result': actual_result
        })

    # 종합 평가
    accuracy = sum(r['correct'] for r in results) / len(results)
    avg_brier = np.mean([r['brier_score'] for r in results])

    print(f"승무패 정확도: {accuracy:.1%}")
    print(f"Brier Score: {avg_brier:.3f}")

    return results
```

**Day 8-10: 분석 및 개선**
- 정확도 < 55% 시: 프롬프트 튜닝 또는 서사 조정
- Brier Score > 0.20 시: 확률 캘리브레이션

#### Week 10: 성능 최적화

**Day 1-3: 병렬화**
```python
# 멀티프로세싱 (시나리오별 병렬 시뮬레이션)
from multiprocessing import Pool

def validate_scenario_parallel(scenario, match_context, n=100):
    with Pool(4) as pool:
        results = pool.starmap(
            simulate_single,
            [(scenario, match_context) for _ in range(n)]
        )
    return aggregate_results(results)
```

**Day 4-5: Redis 캐싱**
```python
# 동일 경기는 1시간 캐싱
cache_key = f"v3:{home_team}:{away_team}:{user_insight_hash}"
```

**Day 6-10: 프롬프트 최적화**
- 토큰 수 줄이기 (비용 감소)
- 응답 속도 개선
- JSON 파싱 안정성

#### 산출물
- ✅ 백테스트 리포트 (100경기)
- ✅ 성능 최적화 코드
- ✅ 캐싱 시스템
- ✅ 최적화 문서

#### 검증 기준
- [ ] 승무패 정확도 > 55%
- [ ] Brier Score < 0.20
- [ ] 평균 실행 시간 < 150초
- [ ] 비용 < $1.00/경기

---

### Week 11-12: 프론트엔드

#### 목표
React UI 구축 (v3 API 연동)

#### Week 11: 컴포넌트 개발

**Day 1-3: AI 시나리오 입력 폼**
```jsx
// frontend/src/components/v3/ScenarioInput.js

function ScenarioInput({ onSubmit }) {
  const [homeTeam, setHomeTeam] = useState('');
  const [awayTeam, setAwayTeam] = useState('');
  const [userInsight, setUserInsight] = useState('');

  return (
    <form onSubmit={handleSubmit}>
      <TeamSelector value={homeTeam} onChange={setHomeTeam} label="홈팀" />
      <TeamSelector value={awayTeam} onChange={setAwayTeam} label="원정팀" />

      <textarea
        value={userInsight}
        onChange={(e) => setUserInsight(e.target.value)}
        placeholder="도메인 지식 입력 (예: 손흥민은 빅매치에서 강하다)"
        rows={5}
      />

      <button type="submit">예측 시작</button>
    </form>
  );
}
```

**Day 4-7: 실시간 진행 상태 표시**
```jsx
// frontend/src/components/v3/ProgressTracker.js

function ProgressTracker({ iteration, phase, status }) {
  return (
    <div className="progress-tracker">
      <h3>Iteration {iteration}</h3>
      <div className="phases">
        <Phase name="AI 시나리오 생성" active={phase === 1} done={phase > 1} />
        <Phase name="통계 검증 (100회)" active={phase === 2} done={phase > 2} />
        <Phase name="AI 분석" active={phase === 3} done={phase > 3} />
        <Phase name="수렴 체크" active={phase === 4} done={phase > 4} />
      </div>
      <p>{status}</p>
    </div>
  );
}
```

**Day 8-10: 결과 시각화**
```jsx
// frontend/src/components/v3/PredictionResults.js

function PredictionResults({ prediction, aiReport }) {
  return (
    <div className="results">
      {/* 확률 차트 */}
      <ProbabilityChart probs={prediction.probabilities} />

      {/* AI 리포트 (마크다운 렌더링) */}
      <div className="ai-report">
        <ReactMarkdown>{aiReport}</ReactMarkdown>
      </div>

      {/* 수렴 히스토리 */}
      <ConvergenceHistory history={prediction.convergence.history} />
    </div>
  );
}
```

#### Week 12: API 연동 및 테스트

**Day 1-3: API 클라이언트**
```javascript
// frontend/src/services/v3/api.js

export async function predictMatch(homeTeam, awayTeam, userInsight) {
  const response = await fetch('/api/v3/simulation/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ homeTeam, awayTeam, userInsight })
  });

  // SSE로 실시간 진행 상태 수신
  const eventSource = new EventSource(`/api/v3/simulation/progress/${response.data.job_id}`);

  eventSource.onmessage = (event) => {
    const progress = JSON.parse(event.data);
    updateProgress(progress);
  };

  return response.data;
}
```

**Day 4-10: 통합 테스트 및 버그 수정**

#### 산출물
- ✅ React 컴포넌트 (~2,000줄)
- ✅ API 클라이언트
- ✅ UI/UX 테스트

#### 검증 기준
- [ ] 모든 컴포넌트 렌더링 정상
- [ ] API 연동 성공
- [ ] 실시간 진행 상태 표시
- [ ] AI 리포트 마크다운 렌더링

---

### Week 13-14: 테스트 및 런칭

#### Week 13: 통합 테스트

**Day 1-5: E2E 테스트**
- 전체 워크플로우 테스트 (입력 → 예측 → 결과)
- 에러 시나리오 테스트
- 성능 테스트 (동시 요청 10개)

**Day 6-10: 알파 테스트**
- 내부 테스터 5명
- 실제 EPL 경기 10개 예측
- 피드백 수집

#### Week 14: 베타 런칭

**Day 1-5: 버그 수정 및 개선**
- 알파 테스트 피드백 반영
- 문서 업데이트

**Day 6-10: 클로즈드 베타**
- 외부 베타 테스터 50명
- 모니터링 및 지원

**Day 11-14: 공개 런칭 준비**
- 서버 스케일링
- 모니터링 설정
- 런칭 공지

#### 산출물
- ✅ 통합 테스트 리포트
- ✅ 알파/베타 피드백
- ✅ 최종 문서
- ✅ 런칭

---

## 기술 스택 및 아키텍처

### 백엔드

**언어**: Python 3.9+
**프레임워크**: FastAPI (Flask 대체)
**AI**: Claude 3 Sonnet / GPT-4 Turbo
**데이터베이스**: PostgreSQL 14+ (서사 라이브러리)
**캐싱**: Redis 7+
**작업 큐**: Celery (백그라운드 작업)

### 프론트엔드

**프레임워크**: React 18.3
**상태 관리**: Zustand
**스타일링**: Tailwind CSS
**애니메이션**: Framer Motion
**차트**: Recharts

### 인프라

**배포**: AWS (EC2 t3.large)
**데이터베이스**: AWS RDS PostgreSQL
**캐싱**: AWS ElastiCache Redis
**CDN**: CloudFront
**모니터링**: DataDog

### 개발 도구

**버전 관리**: Git + GitHub
**CI/CD**: GitHub Actions
**테스트**: pytest, Jest
**문서**: Sphinx, Storybook

---

## 리스크 관리

### 기술적 리스크

| 리스크 | 확률 | 영향 | 대응 |
|--------|------|------|------|
| **서사 라이브러리 품질** | 높음 | 매우 높음 | 축구 전문가 2명 섭외, 품질 검토 프로세스 |
| **AI 비용 초과** | 중간 | 높음 | 프롬프트 최적화, 캐싱 강화, 비용 모니터링 |
| **백테스트 정확도 미달** | 중간 | 높음 | 조기 백테스트 (Week 5), 프롬프트 튜닝 |
| **프롬프트 파싱 오류** | 중간 | 중간 | Few-shot examples, 엄격한 JSON 스키마 |
| **성능 (150초 초과)** | 낮음 | 중간 | 병렬화, 프로파일링, 최적화 |

### 일정 리스크

| 리스크 | 확률 | 영향 | 대응 |
|--------|------|------|------|
| **서사 구축 지연** | 높음 | 매우 높음 | Week 1부터 전문가 섭외 시작, 병렬 작업 |
| **AI 통합 복잡도** | 중간 | 높음 | Week 4-5에 집중, 여유 시간 확보 |
| **백테스트 결과 불량** | 중간 | 높음 | Week 5 조기 테스트, 2주 버퍼 |

### 비용 리스크

| 항목 | 예상 | 최악 | 대응 |
|------|------|------|------|
| **개발 인건비** | $50,000 | $70,000 | 우선순위 조정, MVP 범위 축소 |
| **AI 비용 (개발)** | $2,000 | $5,000 | 프롬프트 최적화, 무료 Tier 활용 |
| **전문가 컨설팅** | $3,000 | $6,000 | 명확한 범위 정의 |

---

## 검증 전략

### 단위 테스트 (Unit Tests)

**커버리지 목표**: > 80%

```python
# tests/v3/test_event_calculator.py
def test_event_calculator_with_boost():
    calculator = EventProbabilityCalculator(EPL_BASELINE_V3)
    context = MatchContext(...)
    boost = NarrativeBoost(type='wing_breakthrough', multiplier=2.5)

    probs = calculator.calculate(context, boost)

    # 검증: wing_breakthrough 부스트 시 shot_rate 2.5배
    assert probs['shot_rate'] == pytest.approx(EPL_BASELINE_V3['shot_per_minute'] * 2.5, rel=0.1)
```

### 통합 테스트 (Integration Tests)

```python
# tests/v3/test_full_workflow.py
def test_full_workflow_manchester_vs_liverpool():
    simulator = MatchSimulatorV3()

    result = simulator.predict(
        home_team='Manchester City',
        away_team='Liverpool',
        match_context={...},
        user_insight='Liverpool striker injured'
    )

    # 검증
    assert result['convergence']['converged'] == True
    assert result['convergence']['confidence'] > 0.85
    assert 500 <= len(result['ai_report']) <= 800
```

### 백테스트

**목표**:
- 100경기 과거 데이터
- 승무패 정확도 > 55%
- Brier Score < 0.20

### A/B 테스트

**Control**: 단순 통계 모델 (Poisson)
**Treatment**: v3 AI 시스템

**기간**: 1개월 (런칭 후)
**샘플**: 1,000 예측

---

## 성공 기준

### Phase 1 (Week 1-8): 핵심 구현

- [x] 통계 엔진 구현 (서사 부스트 지원)
- [x] AI 프롬프트 3개 완성
- [x] 반복 루프 구현
- [x] 서사 라이브러리 500개
- [x] 매칭 알고리즘 정확도 > 80%

### Phase 2 (Week 9-14): 검증 및 런칭

- [x] 백테스트 정확도 > 55%
- [x] Brier Score < 0.20
- [x] 평균 실행 시간 < 150초
- [x] AI 비용 < $1.00/경기
- [x] 프론트엔드 완성
- [x] 베타 런칭

### Phase 3 (런칭 후 1개월): 운영

- [x] 사용자 만족도 > 4.0/5.0
- [x] 일 평균 예측 > 100건
- [x] 시스템 가동률 > 99%
- [x] AI 리포트 품질 평가 > 4.0/5.0

---

## 예산 및 리소스

### 인력

| 역할 | 인원 | 기간 | 시간 | 비용 |
|------|------|------|------|------|
| **백엔드 개발자** | 1 | 14주 | Full-time | $35,000 |
| **프론트엔드 개발자** | 1 | 4주 (Week 11-14) | Full-time | $10,000 |
| **축구 전문가** | 2 | 2주 (Week 7-8) | Part-time | $5,000 |
| **QA/테스터** | 1 | 2주 (Week 13-14) | Part-time | $3,000 |

**인건비 합계**: **$53,000**

### 기술 비용

| 항목 | 비용 |
|------|------|
| **AI 비용 (개발)** | ~$2,000 (500 예측 × $0.80 + 테스트) |
| **AWS 인프라 (개발)** | ~$500 (14주 × $35/주) |
| **데이터베이스 (RDS)** | ~$300 |
| **기타 (도메인, SSL 등)** | ~$200 |

**기술 비용 합계**: **$3,000**

### 총 예산

**총 $56,000** (인건비 $53,000 + 기술 $3,000)

---

## 다음 단계

### Week 0 (준비):
1. ✅ 이 계획 검토 및 승인
2. ✅ 팀 구성 (개발자 2명 + 전문가 2명)
3. ✅ 인프라 준비 (AWS, GitHub)
4. ✅ 프로젝트 킥오프 미팅

### Week 1 시작:
1. ✅ 통계 엔진 프로토타입 착수
2. ✅ 축구 전문가 초기 논의 (서사 차원 설계)
3. ✅ 일일 스탠드업 미팅 시작

---

**문서 버전**: 1.0
**작성일**: 2025-10-16
**승인 대기 중**

**목표**: 14주 후, 제안 시스템 설계(EPL_AI_Simulation_System_Design_v2.md)를 **100% 구현**한 프로덕션 시스템 런칭

---

END OF DOCUMENT
