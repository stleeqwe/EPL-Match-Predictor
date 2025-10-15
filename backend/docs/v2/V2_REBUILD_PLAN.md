# v2.0 시뮬레이터 재구축 계획

**작성일**: 2025-10-15
**목표**: AI 기반 반복 개선 시뮬레이터 구현
**MVP 품질 기준**: 결과의 정확도 및 AI 분석 깊이 (속도/리소스 아님)

---

## 1. 기존 구현 분석 (Phase 1 - 폐기 대상)

### 1.1 구현된 파일들

```
simulation/
├── statistical_engine.py      (21KB, 604줄) - ❌ 단일 패스 구조
├── qwen_analyzer.py            (13KB, ~350줄) - ❌ 단순 가중치만 제공
├── match_simulator.py          (9KB, ~280줄) - ❌ 반복 루프 없음
└── __init__.py                (455 bytes)

tests/
├── test_statistical_engine.py  (8.8KB) - ❌ 잘못된 아키텍처 테스트
├── test_qwen_analyzer.py       (9KB) - ❌ 불완전한 AI 테스트
├── test_match_simulator.py     (9.4KB) - ❌ 단일 패스 테스트
└── test_api_endpoint.py        (845 bytes)
```

### 1.2 치명적 문제점

#### 문제 1: 잘못된 아키텍처
```
Phase 1 구현:
AI 분석 (1회) → 시뮬레이션 (1000회) → 끝

v2.0 설계:
AI 파라미터 생성 → 시뮬 100회 → AI 분석/조정 → 재시뮬 → 수렴 체크 → 반복 → 최종 3000회
```

#### 문제 2: AI 기능 부족 (0% 구현)
현재 AI는 단순 승수(multiplier)만 제공:
```python
{
    'probability_weights': {
        'home_win_boost': 1.5,
        'draw_boost': 0.7,
        'away_win_boost': 0.5
    }
}
```

v2.0 AI가 해야 할 것:
- ✅ **파라미터 생성**: 전술 기반 시뮬레이션 파라미터
- ✅ **편향 감지**: 통계적 이상 탐지
- ✅ **서사 일치율**: 예상 시나리오 대비 결과 일치도
- ✅ **파라미터 조정**: 편향 보정 및 개선
- ✅ **수렴 판정**: 결과 안정화 여부 판단

#### 문제 3: 사용자 인사이트 미활용
사용자 입력이 AI에 텍스트로만 전달, 정량적 반영 불명확

v2.0 요구사항:
```python
사용자 입력: "Liverpool 공격수 부상, United 새 감독 효과"

AI 변환:
{
    "liverpool_attack_modifier": 0.75,      # 부상으로 25% 감소
    "liverpool_morale": 0.9,                # 사기 저하
    "united_morale_boost": 1.2,             # 새 감독 효과
    "united_pressing_intensity": 1.15       # 초반 압박 증가
}

시뮬레이션에 직접 적용
```

### 1.3 유지할 것

#### AI 인프라 (완벽함 - 유지)
```
ai/
├── base_client.py          - ✅ Abstract base class
├── qwen_client.py          - ✅ Qwen/Ollama integration
└── ai_factory.py           - ✅ Provider factory
```

#### 데이터 모델 (사용 가능 - 유지)
```
models/
├── player.py               - ✅ 선수 데이터 (포지션별 능력치)
└── team.py                 - ✅ 팀 데이터 (전술 프로파일)
```

#### EPL 베이스라인 (calibration 완료 - 재사용)
```python
# statistical_engine.py의 EPLBaseline 클래스 재사용
avg_goals_per_match: 2.8
home_win_rate: 0.45
shot_conversion_rate: 0.105
...
```

득점 캘리브레이션도 완료됨 (2.47 goals vs 2.8 EPL - 허용 범위)

---

## 2. v2.0 아키텍처 설계

### 2.1 핵심 원리: AI 기반 반복 개선

```
┌────────────────────────────────────────────────────────────────┐
│                     Match Prediction Request                    │
│  (home_team, away_team, user_insight)                          │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         v
┌────────────────────────────────────────────────────────────────┐
│  Step 1: AI Parameter Generator                                 │
│  - 전술 프로파일 분석                                             │
│  - 사용자 인사이트 → 파라미터 변환                                 │
│  - 초기 시뮬레이션 파라미터 생성                                   │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         v
┌────────────────────────────────────────────────────────────────┐
│  Step 2: Initial Simulation (100 runs)                         │
│  - Monte Carlo 시뮬레이션 (적은 횟수)                            │
│  - 파라미터 적용                                                 │
│  - 초기 결과 생성                                                │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         v
         ┌───────────────────────────────┐
         │   Iterative Refinement Loop   │
         │   (Max 5 iterations)          │
         └───────────┬───────────────────┘
                     │
                     v
┌────────────────────────────────────────────────────────────────┐
│  Step 3: AI Analysis & Bias Detection                          │
│  - 편향 감지 (통계적 이상 탐지)                                   │
│  - 서사 일치율 분석 (예상 vs 실제)                                │
│  - 문제 진단 (overfitting, underfitting 등)                     │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         v
┌────────────────────────────────────────────────────────────────┐
│  Step 4: Convergence Check                                     │
│  - 결과 안정화 판단                                              │
│  - Bias < 5% && Narrative_alignment > 85%                      │
└────────────────────────┬───────────────────────────────────────┘
                         │
                    수렴? │
            ┌─────────────┴─────────────┐
            │ Yes                  No   │
            v                           v
┌─────────────────────┐   ┌──────────────────────────────────┐
│  최종 시뮬레이션      │   │  Step 5: Parameter Adjustment   │
│  (3000 runs)        │   │  - 편향 보정                      │
│                     │   │  - 파라미터 조정                   │
└──────────┬──────────┘   │  - 재시뮬 준비                    │
           │               └──────────┬───────────────────────┘
           │                          │
           │                          v
           │               ┌─────────────────────────┐
           │               │  Re-simulate (100)      │
           │               │  조정된 파라미터로       │
           │               └──────────┬──────────────┘
           │                          │
           │                          └──────────┐
           │                                     │
           v                                     │
┌────────────────────────────────────────────────────────────────┐
│  Final Prediction                                               │
│  - 확률 분포                                                     │
│  - 예상 스코어                                                   │
│  - AI 분석                                                       │
│  - 수렴 리포트                                                   │
└────────────────────────────────────────────────────────────────┘
```

### 2.2 컴포넌트 설계

#### Component 1: AI Parameter Generator
**파일**: `simulation/v2/ai_parameter_generator.py`

**책임**:
- 팀 전술 프로파일 분석
- 사용자 인사이트 → 시뮬레이션 파라미터 변환
- 초기 파라미터 세트 생성

**입력**:
```python
{
    "home_team": {...},
    "away_team": {...},
    "user_insight": "Liverpool 공격수 부상, United 새 감독"
}
```

**출력**:
```python
{
    "simulation_parameters": {
        "home_attack_modifier": 0.75,        # 부상 반영
        "home_morale": 0.9,
        "away_morale_boost": 1.2,            # 새 감독
        "away_pressing_intensity": 1.15,
        "expected_scenario": "high_tempo_low_scoring"
    },
    "ai_reasoning": "Liverpool's key striker injury...",
    "confidence": "high"
}
```

#### Component 2: Iterative Simulation Engine
**파일**: `simulation/v2/iterative_engine.py`

**책임**:
- 파라미터 기반 시뮬레이션 실행
- 100회 (초기/반복) 또는 3000회 (최종)
- 결과 집계

**특징**:
- Phase 1의 `StatisticalMatchEngine`을 확장
- EPL Baseline 재사용
- 파라미터를 동적으로 적용 가능

#### Component 3: AI Bias Detector
**파일**: `simulation/v2/bias_detector.py`

**책임**:
- 시뮬레이션 결과의 통계적 편향 감지
- 이상치 탐지 (outlier detection)
- 문제 유형 분류

**분석 항목**:
```python
{
    "bias_detected": True/False,
    "bias_score": 0-100,  # 0 = 완벽, 100 = 심각한 편향
    "issues": [
        {
            "type": "goal_distribution_skew",
            "severity": "high",
            "description": "평균 득점 3.5, EPL 기준 2.8 (25% 초과)"
        },
        {
            "type": "unrealistic_scoreline",
            "severity": "medium",
            "description": "5-0 이상 스코어 15% (EPL: 2%)"
        }
    ]
}
```

#### Component 4: Narrative Analyzer
**파일**: `simulation/v2/narrative_analyzer.py`

**책임**:
- 예상 시나리오 vs 시뮬 결과 일치율
- 서사 일관성 검증

**예시**:
```python
Expected: "high_tempo_low_scoring" (치열한 저득점 경기)

Results: 평균 득점 4.2, 홈 승률 85%

Narrative Alignment: 35% (낮음)
→ 이유: 고득점 경기가 예상과 불일치
→ 조치: 득점 파라미터 하향 조정 필요
```

#### Component 5: Convergence Judge
**파일**: `simulation/v2/convergence_judge.py`

**책임**:
- 결과 안정화 여부 판단
- 반복 종료 조건 평가

**수렴 기준**:
```python
converged = (
    bias_score < 5.0 and
    narrative_alignment > 85.0 and
    iteration > 1  # 최소 1회 반복
)
```

#### Component 6: Parameter Adjuster
**파일**: `simulation/v2/parameter_adjuster.py`

**책임**:
- 편향/서사 분석 기반 파라미터 조정
- AI 추천 적용

**조정 예시**:
```python
Issue: 득점 과다 (평균 3.5 vs 2.8)

Adjustment:
{
    "home_attack_modifier": 0.90 → 0.82,  # 10% 추가 감소
    "away_attack_modifier": 0.85 → 0.78,
    "shot_conversion_rate": 0.105 → 0.095
}
```

#### Component 7: Match Simulator v2 (Orchestrator)
**파일**: `simulation/v2/match_simulator_v2.py`

**책임**:
- 전체 워크플로우 조율
- 반복 루프 관리
- 최종 결과 생성

**메인 로직**:
```python
def simulate_with_refinement(home, away, user_insight):
    # 1. AI 파라미터 생성
    params = ai_generator.generate(home, away, user_insight)

    iteration = 0
    max_iterations = 5

    while iteration < max_iterations:
        # 2. 시뮬레이션 (100회)
        results = engine.simulate(params, num_runs=100)

        # 3. 편향 감지
        bias = bias_detector.analyze(results)

        # 4. 서사 일치율
        narrative = narrative_analyzer.analyze(results, params['expected_scenario'])

        # 5. 수렴 체크
        converged = convergence_judge.check(bias, narrative, iteration)

        if converged:
            break

        # 6. 파라미터 조정
        params = adjuster.adjust(params, bias, narrative)

        iteration += 1

    # 7. 최종 시뮬레이션 (3000회)
    final_results = engine.simulate(params, num_runs=3000)

    return {
        'prediction': final_results,
        'convergence_report': {...},
        'iterations': iteration,
        'final_bias_score': bias.score,
        'narrative_alignment': narrative.alignment
    }
```

---

## 3. 구현 계획

### 3.1 Phase 1: 기존 코드 정리 및 기반 마련

**작업**:
1. ✅ 기존 `simulation/statistical_engine.py` 분석
2. ✅ EPL Baseline 클래스 추출 및 재사용 준비
3. ✅ AI 클라이언트 인프라 확인 (이미 완료)
4. 새 디렉토리 구조 생성

**디렉토리 구조**:
```
simulation/
├── v2/                              # 새 v2.0 구현
│   ├── __init__.py
│   ├── ai_parameter_generator.py
│   ├── iterative_engine.py
│   ├── bias_detector.py
│   ├── narrative_analyzer.py
│   ├── convergence_judge.py
│   ├── parameter_adjuster.py
│   └── match_simulator_v2.py
├── legacy/                          # Phase 1 코드 보관 (삭제 대기)
│   ├── statistical_engine.py
│   ├── qwen_analyzer.py
│   └── match_simulator.py
└── shared/                          # 공통 유틸
    ├── epl_baseline.py             # EPL 통계 (재사용)
    └── types.py                    # 공통 타입 정의
```

### 3.2 Phase 2: 핵심 컴포넌트 구현

**우선순위 순서**:

1. **EPL Baseline 분리** (30분)
   - `shared/epl_baseline.py` 생성
   - 기존 코드에서 추출

2. **Iterative Simulation Engine** (2시간)
   - Phase 1 엔진을 확장
   - 파라미터 동적 적용 기능 추가
   - 100회/3000회 모드 지원

3. **AI Parameter Generator** (3시간)
   - Qwen AI를 이용한 파라미터 생성
   - 사용자 인사이트 파싱
   - 전술 분석 → 파라미터 변환

4. **Bias Detector** (2시간)
   - 통계적 이상 탐지
   - EPL 기준 대비 편향 계산
   - 문제 유형 분류

5. **Narrative Analyzer** (2시간)
   - 예상 시나리오 정의
   - 시뮬 결과와 비교
   - 일치율 계산

6. **Convergence Judge** (1시간)
   - 수렴 조건 구현
   - 간단한 threshold 체크

7. **Parameter Adjuster** (2시간)
   - 편향 기반 조정 로직
   - AI 추천 적용

8. **Match Simulator v2** (2시간)
   - 전체 워크플로우 조율
   - 반복 루프 구현

**총 예상 시간**: 14-16시간 (개발 + 테스트)

### 3.3 Phase 3: 테스트 및 검증

**테스트 계획**:
```
tests/v2/
├── test_ai_parameter_generator.py
├── test_iterative_engine.py
├── test_bias_detector.py
├── test_narrative_analyzer.py
├── test_convergence_judge.py
├── test_parameter_adjuster.py
└── test_match_simulator_v2.py
```

**검증 시나리오**:
1. **강팀 vs 약팀**: Man City (90) vs Luton (68)
   - 수렴: 2-3회 반복
   - 최종 홈승률: 70-80%

2. **동등한 팀**: Team A (75) vs Team B (75)
   - 수렴: 3-4회 반복
   - 최종 홈승률: 45-50%

3. **사용자 인사이트 포함**: Liverpool vs United
   - 인사이트: "Liverpool 공격수 부상"
   - 파라미터 변환 확인
   - 결과에 반영 확인

4. **EPL Baseline 검증**:
   - 평균 득점: 2.5-3.0
   - 홈승률: 40-50%
   - Draw: 25-30%

### 3.4 Phase 4: API 통합 및 문서화

**API 수정**:
- `/api/v1/simulation/predict` 엔드포인트 v2.0 전환
- 응답 포맷 확장:
```python
{
    "prediction": {...},
    "convergence_report": {
        "iterations": 3,
        "converged": True,
        "final_bias_score": 3.2,
        "narrative_alignment": 88.5
    },
    "ai_analysis": {...}
}
```

**문서 작성**:
- `V2_COMPLETE_REPORT.md` - 완료 리포트
- `V2_API_GUIDE.md` - API 사용 가이드
- `V2_ARCHITECTURE.md` - 상세 아키텍처

---

## 4. 품질 기준 (MVP)

### 4.1 결과 품질 (최우선)

**필수 달성 항목**:
- ✅ EPL 평균 득점: 2.5-3.0 (실제 2.8)
- ✅ 홈승률: 40-50% (실제 45%)
- ✅ 편향 점수: < 5.0
- ✅ 서사 일치율: > 85%
- ✅ 수렴 성공률: > 90% (5회 내)

### 4.2 AI 분석 깊이

**필수 기능**:
- ✅ 파라미터 생성 (전술 + 인사이트 기반)
- ✅ 편향 감지 (통계적 이상 탐지)
- ✅ 서사 일치율 분석
- ✅ 파라미터 조정 제안
- ✅ 수렴 판정

### 4.3 성능 (우선순위 낮음, 하지만 추적)

**참고용 목표**:
- 전체 예측 시간: < 3분 (Qwen AI 포함)
- 반복당 시간: 30-40초
- 최종 시뮬 시간: 40-50초

---

## 5. 위험 요소 및 대응

### 5.1 수렴 실패

**위험**: 5회 반복 내 수렴 실패

**대응**:
- 반복 6회째부터 수렴 기준 완화 (bias < 10%, narrative > 75%)
- 최대 8회까지 허용
- 8회 초과 시 경고와 함께 최종 결과 반환

### 5.2 AI 응답 품질

**위험**: Qwen AI가 부정확한 파라미터 생성

**대응**:
- 파라미터 범위 검증 (0.5-1.5 등)
- 극단적 값 필터링
- Fallback: 통계 기반 기본 파라미터

### 5.3 성능 저하

**위험**: 반복 시뮬로 인한 응답 시간 증가

**대응**:
- 초기/반복: 100회 (빠른 피드백)
- 최종: 3000회 (고품질)
- 추후 최적화: 병렬화, 캐싱

---

## 6. 마일스톤

**Day 1** (6-8시간):
- [x] 기존 코드 분석 완료
- [ ] 디렉토리 구조 생성
- [ ] EPL Baseline 분리
- [ ] Iterative Engine 구현
- [ ] AI Parameter Generator 구현

**Day 2** (6-8시간):
- [ ] Bias Detector 구현
- [ ] Narrative Analyzer 구현
- [ ] Convergence Judge 구현
- [ ] Parameter Adjuster 구현

**Day 3** (4-6시간):
- [ ] Match Simulator v2 통합
- [ ] 전체 워크플로우 테스트
- [ ] EPL Baseline 검증

**Day 4** (2-3시간):
- [ ] API 통합
- [ ] 사용자 인사이트 테스트
- [ ] 문서 작성

---

## 7. 성공 기준

### Phase 1 대비 개선

| 항목 | Phase 1 | v2.0 목표 |
|------|---------|-----------|
| 아키텍처 | 단일 패스 | 반복 개선 루프 ✅ |
| AI 기능 | 단순 가중치 | 파라미터 생성, 편향 감지, 수렴 판정 ✅ |
| 사용자 인사이트 | 텍스트만 전달 | 파라미터로 변환하여 직접 적용 ✅ |
| 득점 평균 | 2.47 (허용) | 2.5-3.0 유지 ✅ |
| 편향 점수 | 측정 안 함 | < 5.0 ✅ |
| 서사 일치율 | 없음 | > 85% ✅ |

### 최종 검증

**테스트 케이스**:
1. ✅ Man City vs Luton: 홈승률 70-80%, 수렴 2-3회
2. ✅ Even teams: 홈승률 45-50%, 수렴 3-4회
3. ✅ User insight: 파라미터 변환 및 반영 확인
4. ✅ EPL baseline: 전체 통계 일치율 > 85%

**모든 테스트 통과 시 v2.0 MVP 완료**

---

## 8. 다음 단계 (Post-MVP)

### Phase 3 (Future):
- 데이터베이스 통합 (Player/Team 모델)
- 최근 폼 데이터 반영
- H2H 전적 활용
- 부상자/출전 정지 추적
- 프론트엔드 UI 연동

### Phase 4 (Advanced):
- 서사 라이브러리 (500+ 시나리오)
- 고급 전술 분석
- 실시간 경기 예측
- 상용 AI 전환 (Claude/GPT)

---

**문서 버전**: 2.0
**작성자**: Claude Code
**날짜**: 2025-10-15
