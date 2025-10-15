"""
Phase 3 Prompt: Analysis & Adjustment
시뮬레이션 결과 분석 및 시나리오 조정

This prompt analyzes simulation results and adjusts the scenario
to improve narrative adherence through iterative refinement.
"""

from typing import Dict, Any
from ai.data_models import Scenario, SimulationResult


# ==========================================================================
# System Prompt
# ==========================================================================

SYSTEM_PROMPT = """당신은 EPL 경기 시뮬레이션 분석가입니다.

시뮬레이션 결과를 분석하고, **서사 일치율**을 높이기 위해 시나리오를 조정하세요.

## 목표
- **서사 일치율 >= 60%**: "converged" 상태로 반환 (조정 불필요)
- **서사 일치율 < 60%**: 시나리오 조정하여 재시뮬레이션

## 분석 방법

### 1. 서사 일치율 이해
- 서사 일치율 = (실제 발생한 이벤트 수) / (예상 이벤트 수)
- 예: 5개 이벤트 중 3개 발생 → 60%

### 2. 미발생 이벤트 분석
각 미발생 이벤트에 대해:
- **왜 발생하지 않았는가?**
  - minute_range가 너무 좁은가? (5-10분 vs 15-20분)
  - probability_boost가 너무 약한가? (1.5 vs 2.5)
  - 이벤트 타입이 상황에 맞지 않는가?
- **어떻게 조정할 것인가?**
  - minute_range 확대
  - probability_boost 증가
  - 이벤트 타입 변경
  - 또는 이벤트 제거

### 3. 조정 전략
- **Conservative (보수적)**: boost +0.2-0.5, range +5-10분
- **Moderate (중간)**: boost +0.5-1.0, range +10-15분
- **Aggressive (공격적)**: boost +1.0-1.5, range +15-20분

## 출력 형식

### A. 수렴 완료 (adherence >= 60%)
```json
{
  "status": "converged",
  "analysis": "서사 일치율 67% 달성. 5개 이벤트 중 4개 발생으로 목표 충족.",
  "suggestions": []
}
```

### B. 조정 필요 (adherence < 60%)
```json
{
  "status": "needs_adjustment",
  "analysis": "서사 일치율 40%. 5개 이벤트 중 2개만 발생. 조정 필요.",
  "suggestions": [
    "wing_breakthrough (10-25분)이 발생 안 함: boost 2.5→2.8, range [10,25]→[8,30]",
    "goal (15-30분)이 발생 안 함: boost 2.0→2.5로 증가"
  ],
  "adjusted_scenario": {
    "scenario_id": "EPL_2024_MATCH_XXX_ADJ_1",
    "description": "조정된 시나리오 (부스트 및 범위 확대)",
    "events": [
      {
        "minute_range": [8, 30],
        "type": "wing_breakthrough",
        "team": "home",
        "probability_boost": 2.8,
        "actor": "Saka",
        "reason": "조정: 범위 확대 + 부스트 증가"
      },
      {
        "minute_range": [15, 32],
        "type": "goal",
        "team": "home",
        "probability_boost": 2.5,
        "reason": "조정: 부스트 증가"
      }
    ]
  }
}
```

## 중요 규칙
1. **probability_boost는 3.0을 초과할 수 없음**
2. **minute_range는 0-90 범위 내**
3. **시나리오 ID에 _ADJ_N 추가** (N = 조정 횟수)
4. **발생한 이벤트는 유지**, 미발생 이벤트만 조정
5. **최대 5회 반복** 후에는 "converged" 반환
"""


# ==========================================================================
# User Prompt Template
# ==========================================================================

USER_PROMPT_TEMPLATE = """# 시뮬레이션 결과 분석

## 원래 시나리오
```json
{original_scenario}
```

## 시뮬레이션 결과
- **최종 스코어**: {final_score}
- **서사 일치율**: {adherence_percent}
- **반복 횟수**: {iteration}/{max_iterations}

## 이벤트 발생 여부

{event_analysis}

# 요구사항

{requirement}

**출력**: JSON 형식 분석 결과 (다른 텍스트 없이)
"""


# ==========================================================================
# Helper Functions
# ==========================================================================

def generate_phase3_prompt(
    original_scenario: Scenario,
    simulation_result: SimulationResult,
    iteration: int,
    max_iterations: int = 5
) -> tuple[str, str]:
    """
    Phase 3 프롬프트 생성

    Args:
        original_scenario: 원래 시나리오
        simulation_result: 시뮬레이션 결과
        iteration: 현재 반복 횟수
        max_iterations: 최대 반복 횟수

    Returns:
        (system_prompt, user_prompt) 튜플
    """
    import json

    # 이벤트 분석 생성
    event_analysis = _generate_event_analysis(
        original_scenario,
        simulation_result
    )

    # 요구사항 생성
    if iteration >= max_iterations:
        requirement = f"**최대 반복 {max_iterations}회 도달**. 'status': 'converged'로 반환하세요."
    elif simulation_result.narrative_adherence >= 0.6:
        requirement = "**서사 일치율 >= 60%**. 'status': 'converged'로 반환하세요."
    else:
        requirement = f"""**서사 일치율 < 60%**. 시나리오를 조정하세요:
- 미발생 이벤트의 boost와 range를 확대
- 조정된 시나리오를 'adjusted_scenario'에 포함
- 'status': 'needs_adjustment'로 설정"""

    # User prompt 생성
    user_prompt = USER_PROMPT_TEMPLATE.format(
        original_scenario=json.dumps(original_scenario.to_dict(), indent=2, ensure_ascii=False),
        final_score=f"{simulation_result.final_score['home']}-{simulation_result.final_score['away']}",
        adherence_percent=f"{simulation_result.narrative_adherence:.0%}",
        iteration=iteration,
        max_iterations=max_iterations,
        event_analysis=event_analysis,
        requirement=requirement,
    )

    return SYSTEM_PROMPT, user_prompt


def _generate_event_analysis(
    scenario: Scenario,
    result: SimulationResult
) -> str:
    """
    이벤트 발생 여부 분석 텍스트 생성

    Args:
        scenario: 원래 시나리오
        result: 시뮬레이션 결과

    Returns:
        분석 텍스트
    """
    lines = []

    # 예상 이벤트 추출 (result.expected_events 또는 scenario.events 사용)
    expected_events = result.expected_events if result.expected_events else []

    if not expected_events:
        # Fallback: scenario의 이벤트를 expected로 가정
        for i, event in enumerate(scenario.events):
            lines.append(
                f"{i+1}. **{event.type}** ({event.minute_range[0]}-{event.minute_range[1]}분, "
                f"team={event.team}, boost={event.probability_boost}) → 발생 여부 미확인"
            )
    else:
        # expected_events와 occurred_events 비교
        occurred_events = result.occurred_events if result.occurred_events else []

        for i, expected in enumerate(expected_events):
            # 발생 여부 확인
            occurred = expected.get('occurred', False)

            status = "✅ 발생" if occurred else "❌ 미발생"
            event_type = expected.get('type', '?')
            minute_range = expected.get('minute_range', [0, 0])
            team = expected.get('team', '?')

            lines.append(
                f"{i+1}. **{event_type}** ({minute_range[0]}-{minute_range[1]}분, team={team}) → {status}"
            )

    return "\n".join(lines) if lines else "이벤트 분석 정보 없음"


def estimate_token_count(text: str) -> int:
    """
    토큰 수 추정

    Args:
        text: 텍스트

    Returns:
        예상 토큰 수
    """
    words = text.split()
    return int(len(words) * 1.3)


# ==========================================================================
# Testing
# ==========================================================================

def test_phase3_prompt():
    """Phase 3 프롬프트 테스트"""
    print("=== Phase 3 Prompt 테스트 ===\n")

    from ai.data_models import ScenarioEvent

    # 테스트 시나리오
    events = [
        ScenarioEvent(
            minute_range=[10, 25],
            type="wing_breakthrough",
            team="home",
            probability_boost=2.5,
            actor="Saka",
            reason="측면 돌파 우위"
        ),
        ScenarioEvent(
            minute_range=[15, 30],
            type="goal",
            team="home",
            probability_boost=2.0,
            reason="초반 득점 가능성"
        ),
        ScenarioEvent(
            minute_range=[60, 75],
            type="counter_attack",
            team="away",
            probability_boost=2.2,
            reason="후반 역습"
        )
    ]

    scenario = Scenario(
        scenario_id="TEST_001",
        description="테스트 시나리오",
        events=events
    )

    # 테스트 시뮬레이션 결과 (낮은 일치율)
    result = SimulationResult(
        final_score={'home': 2, 'away': 1},
        events=[],
        narrative_adherence=0.33,  # 33% (3개 중 1개 발생)
        stats={'home_shots': 15, 'away_shots': 12},
        expected_events=[
            {'type': 'wing_breakthrough', 'minute_range': [10, 25], 'team': 'home', 'occurred': False},
            {'type': 'goal', 'minute_range': [15, 30], 'team': 'home', 'occurred': True},
            {'type': 'counter_attack', 'minute_range': [60, 75], 'team': 'away', 'occurred': False},
        ]
    )

    # Test 1: 조정 필요 (일치율 낮음)
    print("Test 1: 조정 필요 시나리오 (33% 일치율)")
    system_prompt, user_prompt = generate_phase3_prompt(scenario, result, iteration=1, max_iterations=5)

    print(f"  System Prompt 길이: {len(system_prompt)} 문자")
    print(f"  User Prompt 길이: {len(user_prompt)} 문자")
    print(f"  예상 토큰 수: {estimate_token_count(system_prompt + user_prompt)}")
    print(f"  ✅ 조정 필요 프롬프트 생성 성공\n")

    # Test 2: 수렴 완료 (일치율 높음)
    print("Test 2: 수렴 완료 시나리오 (67% 일치율)")
    result_converged = SimulationResult(
        final_score={'home': 2, 'away': 1},
        events=[],
        narrative_adherence=0.67,
        stats={'home_shots': 15, 'away_shots': 12}
    )

    system_prompt2, user_prompt2 = generate_phase3_prompt(scenario, result_converged, iteration=2, max_iterations=5)
    print(f"  예상 토큰 수: {estimate_token_count(system_prompt2 + user_prompt2)}")
    print(f"  ✅ 수렴 완료 프롬프트 생성 성공\n")

    # Test 3: 최대 반복 도달
    print("Test 3: 최대 반복 도달 (5회)")
    system_prompt3, user_prompt3 = generate_phase3_prompt(scenario, result, iteration=5, max_iterations=5)
    print(f"  예상 토큰 수: {estimate_token_count(system_prompt3 + user_prompt3)}")
    print(f"  ✅ 최대 반복 프롬프트 생성 성공\n")

    # User Prompt 샘플 출력
    print("Test 4: User Prompt 샘플")
    print("-" * 60)
    print(user_prompt[:600] + "...")
    print("-" * 60)
    print(f"  ✅ User Prompt 형식 확인\n")

    # 검증 기준
    total_tokens = estimate_token_count(system_prompt + user_prompt)
    print("=" * 60)
    print("검증 결과:")
    if total_tokens < 1500:
        print(f"  ✅ 토큰 수 목표 달성: {total_tokens} < 1,500")
    else:
        print(f"  ⚠️ 토큰 수 초과: {total_tokens} >= 1,500 (조정 필요)")

    print("=" * 60)
    print("✅ Phase 3 Prompt 테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    test_phase3_prompt()
