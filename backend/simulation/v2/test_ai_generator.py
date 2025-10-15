"""
Test AI Multi-Scenario Generator
Qwen AI를 사용한 시나리오 생성 테스트
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from simulation.v2.ai_scenario_generator import get_scenario_generator


def test_scenario_generation():
    """AI 시나리오 생성 테스트"""
    print("=" * 60)
    print("AI Multi-Scenario Generator 테스트")
    print("=" * 60)

    # 1. 초기화
    print("\n[1] AI Scenario Generator 초기화...")
    generator = get_scenario_generator()
    print("✓ 초기화 완료")

    # 2. 경기 컨텍스트
    print("\n[2] 경기 컨텍스트 준비...")
    match_context = {
        "home_team": "Tottenham",
        "away_team": "Arsenal",
        "venue": "Tottenham Hotspur Stadium"
    }
    print(f"✓ 경기: {match_context['home_team']} vs {match_context['away_team']}")

    # 3. 선수 능력치
    player_stats = {
        "Son": {
            "position": "LW",
            "speed": 92,
            "shooting": 88,
            "dribbling": 87
        },
        "Kane": {
            "position": "ST",
            "shooting": 91,
            "passing": 83,
            "heading": 89
        },
        "Saka": {
            "position": "RW",
            "speed": 87,
            "dribbling": 86,
            "shooting": 82
        }
    }
    print(f"✓ 주요 선수: {len(player_stats)}명")

    # 4. 전술
    tactics = {
        "Tottenham": {
            "formation": "4-3-3",
            "press_intensity": 78,
            "buildup_style": "direct"
        },
        "Arsenal": {
            "formation": "4-3-3",
            "press_intensity": 85,
            "buildup_style": "possession"
        }
    }
    print(f"✓ 전술: {tactics['Tottenham']['formation']} vs {tactics['Arsenal']['formation']}")

    # 5. 사용자 도메인 지식 (핵심!)
    domain_knowledge = """
    손흥민은 빅매치에서 특히 강하다. 스피드를 활용한 역습이 위협적이다.
    아스날은 티에르니 부상으로 좌측 수비가 약하다.
    아르테타 감독은 리드하면 5백으로 전환하는 패턴이 있다.
    토트넘은 중앙 수비가 불안하고 후반에 체력이 떨어진다.
    """
    print("\n[3] 사용자 도메인 지식:")
    print(domain_knowledge.strip())

    # 6. AI 시나리오 생성
    print("\n[4] AI 시나리오 생성 중...")
    print("   (Qwen AI 호출 - 약 10-30초 소요)")

    success, scenarios, error = generator.generate_scenarios(
        match_context=match_context,
        player_stats=player_stats,
        tactics=tactics,
        domain_knowledge=domain_knowledge
    )

    if not success:
        print(f"\n❌ 시나리오 생성 실패: {error}")
        return

    print(f"\n✓ 시나리오 생성 성공!")
    print(f"✓ 생성된 시나리오 수: {len(scenarios)}")

    # 7. 시나리오 상세 출력
    print("\n[5] 생성된 시나리오:")
    print("=" * 60)

    total_probability = 0.0
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n### Scenario {i}: {scenario.name}")
        print(f"ID: {scenario.id}")
        print(f"예상 확률: {scenario.expected_probability:.1%}")
        print(f"이유: {scenario.reasoning}")
        print(f"\n이벤트 시퀀스 ({len(scenario.events)}개):")

        for j, event in enumerate(scenario.events, 1):
            minute_start, minute_end = event.minute_range
            print(f"  {j}. [{minute_start:02d}-{minute_end:02d}분] {event.type.value}")
            print(f"     팀: {event.team}, 부스트: x{event.probability_boost}")
            if event.actor:
                print(f"     선수: {event.actor}")
            if event.reason:
                print(f"     근거: {event.reason}")

        if scenario.parameter_adjustments:
            print(f"\n파라미터 조정:")
            for param, value in list(scenario.parameter_adjustments.items())[:3]:
                print(f"  - {param}: {value}")

        total_probability += scenario.expected_probability
        print("-" * 60)

    # 8. 검증
    print(f"\n[6] 검증:")
    print(f"✓ 시나리오 수: {len(scenarios)} (목표: 5-7)")
    print(f"✓ 총 확률: {total_probability:.2f} (목표: 0.9-1.1)")

    if 5 <= len(scenarios) <= 7:
        print("✓ 시나리오 수 OK")
    else:
        print("⚠ 시나리오 수 범위 벗어남")

    if 0.9 <= total_probability <= 1.1:
        print("✓ 확률 합 OK")
    else:
        print("⚠ 확률 합 범위 벗어남")

    # 9. 이벤트 타입 통계
    print(f"\n[7] 이벤트 타입 통계:")
    event_types = {}
    for scenario in scenarios:
        for event in scenario.events:
            event_type = event.type.value
            event_types[event_type] = event_types.get(event_type, 0) + 1

    for event_type, count in sorted(event_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {event_type}: {count}회")

    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)

    return scenarios


if __name__ == "__main__":
    test_scenario_generation()
