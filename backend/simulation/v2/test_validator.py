"""
Test Multi-Scenario Validator
각 시나리오 × 100회 시뮬레이션 테스트
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from simulation.v2.ai_scenario_generator import get_scenario_generator
from simulation.v2.multi_scenario_validator import get_validator
from simulation.v2.event_simulation_engine import create_match_parameters


def test_multi_scenario_validation():
    """Multi-Scenario Validator 테스트"""
    print("=" * 70)
    print("Multi-Scenario Validator 테스트")
    print("=" * 70)

    # 1. AI 시나리오 생성 (간단한 버전)
    print("\n[1] AI 시나리오 생성...")

    generator = get_scenario_generator()

    match_context = {
        "home_team": "Tottenham",
        "away_team": "Arsenal"
    }

    domain_knowledge = """
    손흥민은 빅매치에서 강하다.
    아스날 좌측 수비가 약하다.
    """

    print("   (AI 호출 중...)")
    success, scenarios, error = generator.generate_scenarios(
        match_context=match_context,
        domain_knowledge=domain_knowledge
    )

    if not success:
        print(f"❌ 시나리오 생성 실패: {error}")
        return

    print(f"✓ {len(scenarios)}개 시나리오 생성됨")

    # 2. 기본 경기 파라미터 설정
    print("\n[2] 경기 파라미터 설정...")

    home_team = {
        "attack_strength": 85,
        "defense_strength": 78,
        "midfield_strength": 82,
        "press_intensity": 75
    }

    away_team = {
        "attack_strength": 88,
        "defense_strength": 85,
        "midfield_strength": 86,
        "press_intensity": 82
    }

    base_params = create_match_parameters(
        home_team=home_team,
        away_team=away_team,
        home_formation="4-3-3",
        away_formation="4-3-3"
    )

    print("✓ 파라미터 준비 완료")

    # 3. Multi-Scenario Validation
    print(f"\n[3] 각 시나리오 × 100회 시뮬레이션...")
    print(f"   총 {len(scenarios)} × 100 = {len(scenarios) * 100}회 시뮬레이션")
    print(f"   (약 30-60초 소요)\n")

    validator = get_validator()

    validation_results = validator.validate_scenarios(
        scenarios=scenarios,
        base_params=base_params,
        n=100
    )

    print("\n✓ 모든 시나리오 검증 완료!")

    # 4. 결과 출력
    print("\n" + "=" * 70)
    print("[4] 검증 결과")
    print("=" * 70)

    for result in validation_results:
        print(f"\n### {result['scenario_name']}")
        print(f"ID: {result['scenario_id']}")
        print(f"\n승률:")
        print(f"  - 홈 승: {result['win_rate']['home']:.1%}")
        print(f"  - 무승부: {result['win_rate']['draw']:.1%}")
        print(f"  - 원정 승: {result['win_rate']['away']:.1%}")

        print(f"\n평균 득점:")
        print(f"  - 홈: {result['avg_score']['home']:.2f}골")
        print(f"  - 원정: {result['avg_score']['away']:.2f}골")
        print(f"  - 총: {result['avg_score']['home'] + result['avg_score']['away']:.2f}골")

        print(f"\n서사 일치율:")
        print(f"  - 평균: {result['narrative_adherence']['mean']:.1%}")
        print(f"  - 표준편차: {result['narrative_adherence']['std']:.3f}")
        print(f"  - 범위: {result['narrative_adherence']['min']:.1%} - {result['narrative_adherence']['max']:.1%}")

        print(f"\n편향도:")
        print(f"  - 득점 편향: {result['bias_metrics']['score_bias']:.1%}")
        print(f"    (실제: {result['bias_metrics']['total_goals_avg']:.2f}골 vs EPL: {result['bias_metrics']['epl_reference']:.1f}골)")
        print(f"  - 홈 어드밴티지 편향: {result['bias_metrics']['home_advantage_bias']:.1%}")

        print(f"\n득점 타이밍:")
        timing = result['event_distribution']['goal_timing']
        print(f"  - 0-30분: {timing['0-30min']:.1%}")
        print(f"  - 30-60분: {timing['30-60min']:.1%}")
        print(f"  - 60-90분: {timing['60-90min']:.1%}")

        print(f"\n가장 가능성 높은 스코어:")
        for score, prob in list(result['score_distribution'].items())[:3]:
            print(f"  - {score}: {prob:.1%}")

        print("-" * 70)

    # 5. 전체 통계
    print("\n" + "=" * 70)
    print("[5] 전체 통계")
    print("=" * 70)

    avg_home_goals = sum(r['avg_score']['home'] for r in validation_results) / len(validation_results)
    avg_away_goals = sum(r['avg_score']['away'] for r in validation_results) / len(validation_results)
    avg_total_goals = avg_home_goals + avg_away_goals

    print(f"\n평균 득점 (모든 시나리오):")
    print(f"  - 홈: {avg_home_goals:.2f}골")
    print(f"  - 원정: {avg_away_goals:.2f}골")
    print(f"  - 총: {avg_total_goals:.2f}골")
    print(f"  - EPL 기준: 2.8골")
    print(f"  - 편차: {abs(avg_total_goals - 2.8) / 2.8 * 100:.1f}%")

    avg_adherence = sum(r['narrative_adherence']['mean'] for r in validation_results) / len(validation_results)
    print(f"\n평균 서사 일치율:")
    print(f"  - {avg_adherence:.1%}")
    print(f"  - 목표: 75% 이상")
    if avg_adherence >= 0.75:
        print("  ✓ 목표 달성")
    else:
        print("  ⚠ 목표 미달 (Phase 3에서 조정 필요)")

    avg_score_bias = sum(r['bias_metrics']['score_bias'] for r in validation_results) / len(validation_results)
    print(f"\n평균 득점 편향:")
    print(f"  - {avg_score_bias:.1%}")
    print(f"  - 목표: 10% 이하")
    if avg_score_bias <= 0.10:
        print("  ✓ 목표 달성")
    else:
        print("  ⚠ 목표 초과 (Phase 3에서 조정 필요)")

    # 6. Phase 3 입력 데이터 확인
    print("\n" + "=" * 70)
    print("[6] Phase 3 (AI Analyzer) 입력 데이터 준비 완료")
    print("=" * 70)
    print("\n✓ validation_results 객체 생성됨")
    print(f"✓ {len(validation_results)}개 시나리오의 통계 포함")
    print("\n다음 단계: AI Analyzer가 이 데이터를 분석하여")
    print("  - 편향 감지")
    print("  - 서사 일치율 분석")
    print("  - 파라미터 조정 제안")
    print("  - 수렴 판정")

    print("\n" + "=" * 70)
    print("테스트 완료!")
    print("=" * 70)

    return validation_results


if __name__ == "__main__":
    test_multi_scenario_validation()
