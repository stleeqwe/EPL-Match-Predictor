"""
Test AI Analyzer
Phase 1-2-3-4 통합 테스트
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from simulation.v2.ai_scenario_generator import get_scenario_generator
from simulation.v2.multi_scenario_validator import get_validator
from simulation.v2.ai_analyzer import get_analyzer, apply_adjustments
from simulation.v2.event_simulation_engine import create_match_parameters


def test_ai_analyzer():
    """AI Analyzer 테스트 (Phase 1-2-3-4)"""
    print("=" * 70)
    print("AI Analyzer 테스트 (Phase 1-2-3-4)")
    print("=" * 70)

    # Phase 1: AI 시나리오 생성
    print("\n" + "=" * 70)
    print("Phase 1: AI 시나리오 생성")
    print("=" * 70)

    generator = get_scenario_generator()

    match_context = {
        "home_team": "Tottenham",
        "away_team": "Arsenal"
    }

    domain_knowledge = """
    손흥민은 빅매치에서 강하다. 스피드를 활용한 역습이 위협적이다.
    아스날 좌측 수비가 약하다 (티에르니 부상).
    """

    print("AI 호출 중...")
    success, scenarios, error = generator.generate_scenarios(
        match_context=match_context,
        domain_knowledge=domain_knowledge
    )

    if not success:
        print(f"❌ 시나리오 생성 실패: {error}")
        return

    print(f"✓ {len(scenarios)}개 시나리오 생성됨")
    for s in scenarios:
        print(f"  - {s.id}: {s.name}")

    # Phase 2: 각 시나리오 × 100회 시뮬레이션
    print("\n" + "=" * 70)
    print("Phase 2: 각 시나리오 × 100회 시뮬레이션")
    print("=" * 70)

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
        away_team=away_team
    )

    validator = get_validator()

    print(f"시뮬레이션 시작 ({len(scenarios)} × 100 = {len(scenarios) * 100}회)...")
    validation_results = validator.validate_scenarios(
        scenarios=scenarios,
        base_params=base_params,
        n=100
    )

    print("\n✓ 시뮬레이션 완료!")
    print(f"\n주요 통계:")
    avg_goals = sum(r['avg_score']['home'] + r['avg_score']['away'] for r in validation_results) / len(validation_results)
    avg_adherence = sum(r['narrative_adherence']['mean'] for r in validation_results) / len(validation_results)
    avg_bias = sum(r['bias_metrics']['score_bias'] for r in validation_results) / len(validation_results)

    print(f"  - 평균 득점: {avg_goals:.2f}골 (EPL: 2.8골)")
    print(f"  - 평균 서사 일치율: {avg_adherence:.1%} (목표: 75%)")
    print(f"  - 평균 득점 편향: {avg_bias:.1%} (목표: <10%)")

    # Phase 3: AI 분석 및 조정 제안
    print("\n" + "=" * 70)
    print("Phase 3: AI 분석 및 조정 제안")
    print("=" * 70)

    analyzer = get_analyzer()

    print("AI 분석 호출 중...")
    success, ai_analysis, error = analyzer.analyze_and_adjust(
        scenarios=scenarios,
        validation_results=validation_results,
        iteration=1
    )

    if not success:
        print(f"❌ AI 분석 실패: {error}")
        return

    print("\n✓ AI 분석 완료!")

    # 분석 결과 출력
    print("\n" + "-" * 70)
    print("분석 결과")
    print("-" * 70)

    issues = ai_analysis['analysis']['issues']
    print(f"\n발견된 이슈: {len(issues)}개")

    for i, issue in enumerate(issues, 1):
        print(f"\n{i}. [{issue['severity'].upper()}] {issue['issue_type']}")
        print(f"   시나리오: {issue.get('scenario_id', 'GLOBAL')}")
        print(f"   설명: {issue['description']}")
        print(f"   원인: {issue['root_cause']}")

        if 'adjustment' in issue:
            adj = issue['adjustment']
            print(f"   조정: {adj['parameter']}")
            print(f"     현재: {adj.get('current_value', 'N/A')}")
            print(f"     제안: {adj['proposed_value']}")
            print(f"     효과: {adj['expected_impact']}")

    # Global adjustments
    global_adjs = ai_analysis['analysis'].get('global_adjustments', {})
    if global_adjs:
        print(f"\n전역 조정: {len(global_adjs)}개")
        for param, adj in global_adjs.items():
            print(f"  - {param}: {adj['current']} → {adj['proposed']}")
            print(f"    이유: {adj['reason']}")

    # Convergence
    conv = ai_analysis['convergence']
    print(f"\n" + "-" * 70)
    print("수렴 판정")
    print("-" * 70)
    print(f"수렴 여부: {'✅ YES' if conv['converged'] else '❌ NO'}")
    print(f"신뢰도: {conv['confidence']:.1%}")
    print(f"\n충족된 기준:")
    for criterion in conv.get('criteria_met', []):
        print(f"  ✅ {criterion}")
    print(f"\n실패한 기준:")
    for criterion in conv.get('criteria_failed', []):
        print(f"  ❌ {criterion}")
    print(f"\n권장사항: {conv.get('recommendation', 'N/A')}")

    # Phase 4: 조정 적용
    print("\n" + "=" * 70)
    print("Phase 4: 조정 적용")
    print("=" * 70)

    print("조정 적용 중...")
    adjusted_scenarios = apply_adjustments(scenarios, ai_analysis)

    print(f"\n✓ 조정 완료!")
    print(f"  - 원본 시나리오: {len(scenarios)}개")
    print(f"  - 조정된 시나리오: {len(adjusted_scenarios)}개")

    # 변경 사항 출력
    print(f"\n변경 사항:")
    for orig, adj in zip(scenarios, adjusted_scenarios):
        if orig.id != adj.id:
            continue

        changes = []

        # Check event changes
        for i, (orig_event, adj_event) in enumerate(zip(orig.events, adj.events)):
            if orig_event.probability_boost != adj_event.probability_boost:
                changes.append(f"Event {i}: boost {orig_event.probability_boost:.2f} → {adj_event.probability_boost:.2f}")

        # Check parameter changes
        for param in orig.parameter_adjustments:
            if param in adj.parameter_adjustments:
                if orig.parameter_adjustments[param] != adj.parameter_adjustments[param]:
                    changes.append(f"{param}: {orig.parameter_adjustments[param]:.2f} → {adj.parameter_adjustments[param]:.2f}")

        if changes:
            print(f"\n  {orig.id}: {orig.name}")
            for change in changes:
                print(f"    - {change}")
        else:
            print(f"\n  {orig.id}: (변경 없음)")

    # Next steps
    print("\n" + "=" * 70)
    print("다음 단계")
    print("=" * 70)

    if conv['converged']:
        print("\n✅ 수렴 완료!")
        print("→ Phase 6: 최종 시뮬레이션 (3000회)")
        print("→ Phase 7: AI 최종 리포트")
    else:
        print(f"\n⏳ 수렴 미달 (신뢰도: {conv['confidence']:.1%})")
        print(f"→ 조정된 시나리오로 Phase 2 재실행")
        print(f"→ 예상 반복 횟수: {conv.get('estimated_iterations_needed', '?')}회")
        print(f"→ 최대 5회까지 반복")

    print("\n" + "=" * 70)
    print("테스트 완료!")
    print("=" * 70)

    return adjusted_scenarios, ai_analysis


if __name__ == "__main__":
    test_ai_analyzer()
