# v2.0 정확한 재구축 계획

**날짜**: 2025-10-15
**기반**: EPL_AI_Simulation_System_Design_v2.md (정확히 따름)

---

## 1. 이전 구현의 문제점

### 제가 만든 것 (v2.0-Lite):
```
AI 파라미터 생성 (간단한 modifiers)
  ↓
시뮬레이션 (전체 경기 레벨 몬테카를로)
  ↓
편향 감지 + 서사 분석
  ↓
반복...
```

**문제**:
- ❌ 분 단위 시뮬레이션 없음
- ❌ 다중 시나리오 없음 (단일 파라미터 세트만)
- ❌ 이벤트 시퀀스 없음
- ❌ 서사 부스트 없음

### 설계 문서가 요구하는 것:
```
Phase 1: AI가 5-7개 시나리오 생성
  - 각 시나리오마다 이벤트 시퀀스 포함
  - 예: [10-25분] wing_breakthrough, boost=2.5
       [15-30분] goal, boost=1.8

Phase 2: 각 시나리오 × 100회 분 단위 시뮬레이션
  - for minute in range(90):
      - 이벤트 확률 계산
      - 서사 부스트 적용 (해당 분에)
      - 이벤트 샘플링 (shot, goal, corner 등)
      - 상태 업데이트

Phase 3-5: 반복 개선
Phase 6: 각 시나리오 × 3,000회
Phase 7: AI 종합 리포트
```

---

## 2. 정확한 재구축 계획

### 2.1 핵심 컴포넌트 (설계대로)

#### Component 1: Event-Based Simulation Engine
**파일**: `simulation/v2/event_simulation_engine.py`

**핵심 기능**:
```python
class EventBasedSimulationEngine:
    """
    분 단위 이벤트 기반 시뮬레이션
    설계 문서 Section 4 구현
    """

    def simulate_match(self, params, scenario_guide):
        """
        90분 시뮬레이션 (1분 단위)
        """
        state = {
            "minute": 0,
            "score": {"home": 0, "away": 0},
            "events": [],
            "possession": {"home": 50, "away": 50},
            "stamina": {"home": 100, "away": 100}
        }

        for minute in range(90):
            # 1. 현재 분의 서사 부스트 가져오기
            boost = scenario_guide.get_boost_at(minute)

            # 2. 이벤트 확률 계산
            event_probs = self._calculate_event_probabilities(
                params, state, boost
            )

            # 3. 이벤트 샘플링
            event = self._sample_event(event_probs)

            # 4. 이벤트 해결 (득점, 슛 등)
            if event:
                self._resolve_event(event, state)

            # 5. 상태 업데이트
            self._update_state(state, minute)

        # 6. 서사 일치율 계산
        narrative_adherence = self._calculate_narrative_adherence(
            state, scenario_guide
        )

        return {
            "final_score": state["score"],
            "events": state["events"],
            "narrative_adherence": narrative_adherence
        }
```

#### Component 2: Scenario Structure
**파일**: `simulation/v2/scenario.py`

**데이터 구조** (설계 문서 Section 7.1):
```python
@dataclass
class ScenarioEvent:
    """단일 이벤트 정의"""
    minute_range: Tuple[int, int]  # [10, 25]
    type: str  # "wing_breakthrough", "goal", "formation_change"
    team: str  # "home" or "away"
    actor: Optional[str]  # "Son"
    probability_boost: float  # 2.5
    reason: str  # "빅매치 강세 반영"

@dataclass
class Scenario:
    """완전한 시나리오"""
    id: str
    name: str
    reasoning: str
    events: List[ScenarioEvent]
    parameter_adjustments: Dict
    expected_probability: float
```

#### Component 3: Scenario Guide
**파일**: `simulation/v2/scenario_guide.py`

```python
class ScenarioGuide:
    """
    시나리오를 분별 부스트 맵으로 변환
    설계 문서 Section 4.2
    """

    def __init__(self, scenario: Scenario):
        self.scenario = scenario
        self.boosts_by_minute = self._parse_events()

    def get_boost_at(self, minute: int) -> Optional[Dict]:
        """특정 분의 부스트 반환"""
        return self.boosts_by_minute.get(minute, None)

    def _parse_events(self):
        """이벤트 시퀀스 → 분별 부스트"""
        boosts = {}
        for event in self.scenario.events:
            for min in range(event.minute_range[0], event.minute_range[1] + 1):
                boosts[min] = {
                    "team": event.team,
                    "event_type": event.type,
                    "multiplier": event.probability_boost
                }
        return boosts
```

#### Component 4: AI Multi-Scenario Generator
**파일**: `simulation/v2/ai_scenario_generator.py`

**Phase 1 구현** (설계 문서 Section 3):
```python
class AIScenarioGenerator:
    """
    5-7개 다중 시나리오 생성
    """

    def generate_scenarios(
        self,
        match_context: Dict,
        player_stats: Dict,
        tactics: Dict,
        domain_knowledge: str
    ) -> List[Scenario]:
        """
        AI가 5-7개 시나리오 생성

        각 시나리오는:
        - 고유한 이벤트 시퀀스
        - 분 단위 부스트
        - 예상 확률
        """

        prompt = self._build_scenario_generation_prompt(
            match_context, player_stats, tactics, domain_knowledge
        )

        # AI 호출 (설계서 프롬프트 정확히 사용)
        response = self.ai_client.generate(prompt, ...)

        # JSON 파싱
        scenarios = self._parse_scenarios(response)

        # 검증: 5-7개, 확률 합 0.9-1.1
        validated = self._validate_scenarios(scenarios)

        return validated
```

#### Component 5: Multi-Scenario Validator
**파일**: `simulation/v2/multi_scenario_validator.py`

**Phase 2 구현**:
```python
class MultiScenarioValidator:
    """
    각 시나리오를 N회 시뮬레이션
    """

    def validate_scenarios(
        self,
        scenarios: List[Scenario],
        base_params: Dict,
        n: int = 100
    ) -> List[Dict]:
        """
        각 시나리오 × n회
        """
        results = []

        for scenario in scenarios:
            # 시나리오 가이드 생성
            guide = ScenarioGuide(scenario)

            # 시나리오별 파라미터
            scenario_params = self._merge_parameters(
                base_params,
                scenario.parameter_adjustments
            )

            # n회 시뮬레이션
            outcomes = []
            for _ in range(n):
                result = self.engine.simulate_match(
                    scenario_params,
                    guide
                )
                outcomes.append(result)

            # 통계 집계
            stats = self._aggregate_outcomes(outcomes, scenario)
            results.append(stats)

        return results
```

#### Component 6: AI Analyzer (Enhanced)
**파일**: `simulation/v2/ai_analyzer.py`

**Phase 3 구현** (설계 문서 정확히 따름):
```python
class AIAnalyzer:
    """
    Phase 3: AI 분석 및 조정
    설계 문서 프롬프트 정확히 사용
    """

    def analyze_and_adjust(
        self,
        scenarios: List[Scenario],
        validation_results: List[Dict],
        iteration: int
    ) -> Dict:
        """
        AI가 분석:
        1. 편향 감지 (득점, 승률, 이벤트)
        2. 서사 일치율 (< 0.75인 시나리오)
        3. 파라미터 조정 제안
        4. 시나리오 품질 평가 (중복, 비현실적)
        5. 수렴 판정
        """

        prompt = self._build_analysis_prompt(
            scenarios,
            validation_results,
            iteration
        )

        # AI 호출 (설계서 Section 3 프롬프트)
        response = self.ai_client.generate(prompt, ...)

        return {
            "iteration": iteration,
            "analysis": {
                "issues": [...],
                "global_adjustments": {...},
                "scenario_recommendations": {
                    "merge": [...],
                    "remove": [...]
                }
            },
            "convergence": {
                "converged": bool,
                "confidence": float,
                "criteria_met": [...],
                "criteria_failed": [...]
            }
        }
```

#### Component 7: Main Pipeline
**파일**: `simulation/v2/simulation_pipeline.py`

**7단계 완전 구현**:
```python
class SimulationPipeline:
    """
    Phase 1-7 완전 구현
    """

    def run(self, user_input: Dict) -> Dict:
        """
        전체 파이프라인
        """
        # Phase 1: AI 시나리오 생성 (5-7개)
        scenarios = self.scenario_generator.generate_scenarios(
            user_input["match_context"],
            user_input["player_stats"],
            user_input["tactics"],
            user_input["domain_knowledge"]
        )

        # Phase 2-5: 반복 루프
        iteration = 0
        max_iterations = 5
        converged = False
        history = []

        while not converged and iteration < max_iterations:
            # Phase 2: 시뮬레이션 (각 시나리오 × 100)
            validation_results = self.validator.validate_scenarios(
                scenarios,
                base_params,
                n=100
            )

            # Phase 3: AI 분석
            ai_analysis = self.analyzer.analyze_and_adjust(
                scenarios,
                validation_results,
                iteration
            )

            history.append({
                "iteration": iteration,
                "scenarios": scenarios,
                "results": validation_results,
                "analysis": ai_analysis
            })

            # Phase 5: 수렴 체크
            if ai_analysis["convergence"]["converged"]:
                converged = True
                break

            # Phase 4: 조정 적용
            scenarios = self._apply_adjustments(scenarios, ai_analysis)
            iteration += 1

        # Phase 6: 최종 고해상도 (각 × 3000)
        final_results = self.validator.validate_scenarios(
            scenarios,
            base_params,
            n=3000
        )

        # Phase 7: AI 최종 리포트
        final_report = self.report_generator.generate_report(
            scenarios,
            final_results,
            history,
            user_input
        )

        return {
            "scenarios": scenarios,
            "final_results": final_results,
            "report": final_report,
            "history": history,
            "converged": converged
        }
```

---

## 3. 구현 순서

### Day 1 (6-8시간):
1. ✅ 설계 문서 재분석
2. ⏳ 이벤트 기반 시뮬레이션 엔진
   - Event probability calculator
   - Event sampler
   - 90분 시뮬레이션 루프
3. ⏳ 시나리오 구조
   - Scenario, ScenarioEvent 클래스
   - ScenarioGuide

### Day 2 (6-8시간):
4. ⏳ AI 다중 시나리오 생성기
   - 설계서 프롬프트 정확히 구현
   - 5-7개 시나리오 생성
   - 이벤트 시퀀스 포함
5. ⏳ Multi-Scenario Validator
   - 각 시나리오 × N회

### Day 3 (6-8시간):
6. ⏳ AI Analyzer (Enhanced)
   - 설계서 프롬프트 정확히 구현
   - 편향 감지
   - 서사 일치율
   - 조정 제안
7. ⏳ 조정 적용 로직
   - 시나리오 병합/제거

### Day 4 (4-6시간):
8. ⏳ 7단계 파이프라인 통합
9. ⏳ AI 최종 리포트 생성
10. ⏳ 테스트

---

## 4. 핵심 차이 요약

| 구분 | v2.0-Lite (제 구현) | v2.0 Accurate (설계서) |
|------|---------------------|------------------------|
| 시뮬레이션 | 전체 경기 레벨 | 90분 분 단위 |
| 시나리오 | 단일 파라미터 세트 | 5-7개 다중 시나리오 |
| 이벤트 | 없음 | minute_range + boost |
| 서사 부스트 | 없음 | 분별 확률 조정 |
| 서사 일치율 | 간접적 | 직접 계산 (이벤트 매칭) |
| AI 역할 | 파라미터만 | 시나리오 생성 + 분석 |

---

## 5. 예상 결과

### 입력:
```python
{
    "match_context": {
        "home_team": "Tottenham",
        "away_team": "Arsenal"
    },
    "domain_knowledge": """
    손흥민은 빅매치에서 특히 강하다.
    아스날 좌측 수비가 약하다 (티에르니 부상).
    아르테타는 리드하면 5백으로 전환한다.
    """
}
```

### Phase 1 출력 (AI 생성):
```json
{
  "scenarios": [
    {
      "id": "SYNTH_001",
      "name": "손흥민 측면 우위 → 초반 선제 → 완승",
      "events": [
        {
          "minute_range": [10, 25],
          "type": "wing_breakthrough",
          "actor": "Son",
          "probability_boost": 2.5
        },
        {
          "minute_range": [15, 30],
          "type": "goal",
          "team": "home",
          "probability_boost": 1.8
        }
      ],
      "expected_probability": 0.18
    },
    {
      "id": "SYNTH_002",
      "name": "초반 선제 → 수비 전환 → 아스날 역전",
      "events": [
        {
          "minute_range": [20, 35],
          "type": "goal",
          "team": "home",
          "probability_boost": 1.6
        },
        {
          "minute_range": [65, 75],
          "type": "formation_change",
          "team": "home",
          "to": "5-3-2"
        },
        {
          "minute_range": [75, 85],
          "type": "goal",
          "team": "away",
          "probability_boost": 1.9
        }
      ],
      "expected_probability": 0.16
    }
    // ... 5-7개 총
  ]
}
```

### Phase 6 최종 결과:
```json
{
  "scenario_id": "SYNTH_001",
  "total_runs": 3000,
  "win_rate": {
    "home": 0.52,
    "away": 0.28,
    "draw": 0.20
  },
  "avg_score": {"home": 2.1, "away": 1.3},
  "narrative_adherence": {
    "mean": 0.81,
    "std": 0.11
  },
  "event_statistics": {
    "wing_breakthrough_occurred": 0.86,
    "goal_in_expected_range": 0.79
  }
}
```

---

**이제 정확히 설계 문서대로 재구축하겠습니다!**
