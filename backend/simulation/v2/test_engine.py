"""
Test Event-Based Simulation Engine
간단한 검증 테스트
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from simulation.v2.scenario import create_example_scenario
from simulation.v2.scenario_guide import ScenarioGuide
from simulation.v2.event_simulation_engine import (
    EventBasedSimulationEngine,
    create_match_parameters
)


def test_basic_simulation():
    """기본 시뮬레이션 테스트"""
    print("=" * 60)
    print("Event-Based Simulation Engine 테스트")
    print("=" * 60)

    # 1. 예제 시나리오 생성
    print("\n[1] 시나리오 생성...")
    scenario = create_example_scenario()
    print(f"✓ 시나리오 ID: {scenario.id}")
    print(f"✓ 시나리오 이름: {scenario.name}")
    print(f"✓ 이벤트 수: {len(scenario.events)}")

    # 2. ScenarioGuide 생성
    print("\n[2] ScenarioGuide 생성...")
    guide = ScenarioGuide(scenario)
    print(f"✓ 부스트가 적용되는 분: {len(guide.boosts_by_minute)}개")

    # 예시 부스트 확인
    boost_at_15 = guide.get_boost_at(15)
    if boost_at_15:
        print(f"✓ 15분 부스트: {boost_at_15['event_type']} (x{boost_at_15['multiplier']})")

    # 3. 경기 파라미터 생성
    print("\n[3] 경기 파라미터 생성...")
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

    params = create_match_parameters(
        home_team=home_team,
        away_team=away_team,
        home_formation="4-3-3",
        away_formation="4-3-3"
    )
    print(f"✓ Home: {params.home_formation}, Attack={home_team['attack_strength']}")
    print(f"✓ Away: {params.away_formation}, Attack={away_team['attack_strength']}")

    # 4. 시뮬레이션 엔진 생성
    print("\n[4] 시뮬레이션 엔진 초기화...")
    engine = EventBasedSimulationEngine()
    print("✓ 엔진 준비 완료")

    # 5. 단일 경기 시뮬레이션
    print("\n[5] 90분 시뮬레이션 실행...")
    result = engine.simulate_match(params, guide)

    print(f"✓ 최종 스코어: {result['final_score']['home']} - {result['final_score']['away']}")
    print(f"✓ 총 이벤트: {len(result['events'])}개")
    print(f"✓ 서사 일치율: {result['narrative_adherence']:.2%}")

    # 6. 이벤트 통계
    print("\n[6] 이벤트 통계:")
    stats = result['event_statistics']
    print(f"   - 총 슛: {stats['total_shots']}")
    print(f"   - 온타겟: {stats['shots_on_target']}")
    print(f"   - 골: {stats['goals']}")
    print(f"   - 코너킥: {stats['corners']}")
    print(f"   - 파울: {stats['fouls']}")

    # 7. 득점 타이밍
    print("\n[7] 득점 타이밍:")
    timing = stats['goal_timing']
    print(f"   - 0-30분: {timing['0-30min']}골")
    print(f"   - 30-60분: {timing['30-60min']}골")
    print(f"   - 60-90분: {timing['60-90min']}골")

    # 8. 10회 반복 테스트
    print("\n[8] 10회 반복 테스트...")
    results = []
    for i in range(10):
        r = engine.simulate_match(params, guide)
        results.append(r)

    # 통계
    avg_home_goals = sum(r['final_score']['home'] for r in results) / 10
    avg_away_goals = sum(r['final_score']['away'] for r in results) / 10
    avg_adherence = sum(r['narrative_adherence'] for r in results) / 10

    print(f"✓ 평균 홈 득점: {avg_home_goals:.2f}")
    print(f"✓ 평균 원정 득점: {avg_away_goals:.2f}")
    print(f"✓ 평균 총 득점: {avg_home_goals + avg_away_goals:.2f}")
    print(f"✓ 평균 서사 일치율: {avg_adherence:.2%}")

    # EPL 기준과 비교
    print("\n[9] EPL 기준 비교:")
    print(f"   - EPL 평균 득점: 2.8골")
    print(f"   - 시뮬레이션 평균: {avg_home_goals + avg_away_goals:.2f}골")

    total_goals = avg_home_goals + avg_away_goals
    deviation = abs(total_goals - 2.8) / 2.8 * 100
    print(f"   - 편차: {deviation:.1f}%")

    if deviation < 20:
        print("   ✓ 캘리브레이션 양호")
    else:
        print("   ⚠ 캘리브레이션 조정 필요")

    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)

    return results


if __name__ == "__main__":
    test_basic_simulation()
