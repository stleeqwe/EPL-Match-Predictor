"""
Test Complete Pipeline (간단한 버전)
Phase 1-7 전체 테스트 (빠른 실행)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from simulation.v2.simulation_pipeline import get_pipeline, PipelineConfig
from simulation.v2.event_simulation_engine import create_match_parameters


def test_complete_pipeline():
    """전체 파이프라인 테스트 (간단한 버전)"""
    print("=" * 70)
    print("Complete Pipeline Test (Phase 1-7)")
    print("=" * 70)

    # Setup
    print("\n[Setup] 파이프라인 설정...")

    # Simplified config for faster testing
    config = PipelineConfig(
        max_iterations=2,  # 빠른 테스트를 위해 2회로 제한
        initial_runs=50,   # 50회로 감소 (원래 100회)
        final_runs=100,    # 100회로 감소 (원래 3000회)
        convergence_threshold=0.70  # 낮춤 (원래 0.85)
    )

    pipeline = get_pipeline(config)
    print("✓ 파이프라인 초기화 완료")

    # Match context
    match_context = {
        "home_team": "Tottenham",
        "away_team": "Arsenal"
    }

    # Base parameters
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

    # Domain knowledge
    domain_knowledge = """
    손흥민은 빅매치에서 특히 강하다. 스피드를 활용한 역습이 위협적이다.
    아스날은 티에르니 부상으로 좌측 수비가 약하다.
    """

    print("\n설정:")
    print(f"  - 경기: {match_context['home_team']} vs {match_context['away_team']}")
    print(f"  - 최대 반복: {config.max_iterations}회")
    print(f"  - 초기 시뮬레이션: 50회/시나리오")
    print(f"  - 최종 시뮬레이션: 100회/시나리오")

    # Run pipeline
    print("\n" + "=" * 70)
    print("파이프라인 실행 시작")
    print("=" * 70)
    print("\n⏳ 이 작업은 2-5분 소요될 수 있습니다...")
    print("   (AI 호출 + 수백 번의 시뮬레이션)\n")

    success, result, error = pipeline.run(
        match_context=match_context,
        base_params=base_params,
        domain_knowledge=domain_knowledge
    )

    if not success:
        print(f"\n❌ 파이프라인 실행 실패: {error}")
        return

    print("\n" + "=" * 70)
    print("✓ 파이프라인 실행 완료!")
    print("=" * 70)

    # Display results
    print("\n" + "-" * 70)
    print("최종 결과")
    print("-" * 70)

    report = result['report']
    pred = report['prediction']

    print(f"\n### 경기: {report['match']['home_team']} vs {report['match']['away_team']}")

    print(f"\n### 승부 예측:")
    print(f"  - 홈 승: {pred['win_probabilities']['home']:.1%}")
    print(f"  - 무승부: {pred['win_probabilities']['draw']:.1%}")
    print(f"  - 원정 승: {pred['win_probabilities']['away']:.1%}")

    print(f"\n### 예상 득점:")
    print(f"  - 홈: {pred['expected_goals']['home']:.2f}골")
    print(f"  - 원정: {pred['expected_goals']['away']:.2f}골")

    print(f"\n### 가장 가능성 높은 결과:")
    outcome = pred['most_likely_outcome']
    if outcome == 'home_win':
        print(f"  ✓ 홈 승리 ({report['match']['home_team']})")
    elif outcome == 'away_win':
        print(f"  ✓ 원정 승리 ({report['match']['away_team']})")
    else:
        print(f"  ✓ 무승부")

    print(f"\n### 지배적 시나리오:")
    dominant = report['dominant_scenario']
    print(f"  이름: {dominant['name']}")
    print(f"  확률: {dominant['probability']:.1%}")
    print(f"  이유: {dominant['reasoning']}")

    # All scenarios
    print(f"\n### 모든 시나리오 ({len(report['all_scenarios'])}개):")
    for i, scenario in enumerate(report['all_scenarios'], 1):
        print(f"\n  {i}. {scenario['name']}")
        print(f"     확률: {scenario['probability']:.1%}")
        print(f"     홈 승률: {scenario['win_rate']['home']:.1%}")
        print(f"     평균 득점: {scenario['avg_score']['home']:.2f}-{scenario['avg_score']['away']:.2f}")

    # Convergence
    conv = report['convergence_summary']
    print(f"\n### 수렴 정보:")
    print(f"  - 반복 횟수: {conv['iterations']}회")
    print(f"  - 수렴 여부: {'✅ YES' if conv['converged'] else '❌ NO'}")
    print(f"  - 최종 신뢰도: {conv['final_confidence']:.1%}")

    # Metadata
    meta = result['metadata']
    print(f"\n### 통계:")
    print(f"  - 총 시뮬레이션: {meta['total_simulations']:,}회")
    print(f"  - 생성된 시나리오: {len(result['scenarios'])}개")

    print("\n" + "=" * 70)
    print("테스트 완료!")
    print("=" * 70)

    return result


if __name__ == "__main__":
    test_complete_pipeline()
