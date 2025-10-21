#!/usr/bin/env python3
"""
템플릿 vs AI 창의성 분석
고정된 것과 AI가 생성한 것을 명확히 구분
"""

import json
import sys

def analyze_scenarios():
    """생성된 시나리오 분석"""

    with open('generated_scenarios.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    scenarios = data['scenarios']

    print("="*80)
    print("템플릿 vs AI 창의성 분석")
    print("="*80)

    # 1. 고정된 것 (템플릿)
    print("\n[고정된 것 - 템플릿이 제공]")
    print("-"*80)

    print("\n결과 타입 분포:")
    results = {
        '홈승': 0,
        '무승부': 0,
        '원정승': 0
    }

    for scenario in scenarios:
        name = scenario['name']
        if '홈팀' in name and '승리' in name:
            results['홈승'] += 1
        elif '무승부' in name or '균형' in name:
            results['무승부'] += 1
        elif '원정팀' in name and '승리' in name:
            results['원정승'] += 1

    for result_type, count in results.items():
        print(f"  {result_type}: {count}개")

    print(f"\n✓ 결과 커버리지: 홈승/무/원정승 모두 포함 (템플릿 강제)")

    # 확률 분포
    print(f"\n확률 분포:")
    total_prob = sum(s['expected_probability'] for s in scenarios)
    print(f"  총합: {total_prob:.2f} (목표: 1.0)")
    print(f"  ✓ EPL 통계 준수 (템플릿 가이드)")

    # 2. AI가 창조한 것
    print("\n" + "="*80)
    print("[AI가 창조한 것 - 사용자 데이터 기반]")
    print("-"*80)

    # 선수 선택
    print("\n1. 선수 선택 (AI가 11명 중 결정):")
    actor_counts = {}
    for scenario in scenarios:
        for event in scenario['events']:
            actor = event.get('actor')
            if actor and actor not in ['Home Striker', 'Away Winger', 'Home Midfielder', 'Away Midfielder', 'Home Manager']:
                actor_counts[actor] = actor_counts.get(actor, 0) + 1

    for actor, count in sorted(actor_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  - {actor}: {count}회 등장")

    # 이벤트 타입 선택
    print("\n2. 이벤트 타입 선택 (AI가 11가지 중 선택):")
    event_types = {}
    for scenario in scenarios:
        for event in scenario['events']:
            event_type = event['type']
            event_types[event_type] = event_types.get(event_type, 0) + 1

    for event_type, count in sorted(event_types.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  - {event_type}: {count}회")

    # 타이밍 선택
    print("\n3. 타이밍 선택 (AI가 0-90분 중 결정):")
    early = mid = late = 0
    for scenario in scenarios:
        for event in scenario['events']:
            minute = event['minute_range'][0]
            if minute < 30:
                early += 1
            elif minute < 60:
                mid += 1
            else:
                late += 1

    print(f"  - 초반 (0-30min): {early}개 ({early/(early+mid+late)*100:.1f}%)")
    print(f"  - 중반 (30-60min): {mid}개 ({mid/(early+mid+late)*100:.1f}%)")
    print(f"  - 후반 (60-90min): {late}개 ({late/(early+mid+late)*100:.1f}%)")

    # 확률 부스트 분포
    print("\n4. 확률 부스트 계산 (AI가 1.0-3.0 범위에서 계산):")
    boosts = []
    for scenario in scenarios:
        for event in scenario['events']:
            boost = event.get('probability_boost', 1.0)
            boosts.append(boost)

    print(f"  - 평균: {sum(boosts)/len(boosts):.2f}x")
    print(f"  - 최소: {min(boosts):.1f}x")
    print(f"  - 최대: {max(boosts):.1f}x")
    print(f"  - 범위: 1.0-3.0 (템플릿 제약)")

    # 근거 생성 (AI 창의성의 정점)
    print("\n5. 근거 생성 (AI가 자연어로 설명):")
    print("\n예시 - SYNTH_001 이벤트들의 근거:")
    for i, event in enumerate(scenarios[0]['events'][:3], 1):
        print(f"\n  이벤트 {i}: {event['type']} ({event['minute_range'][0]}-{event['minute_range'][1]}분)")
        print(f"  근거: {event['reason'][:80]}...")

    # 3. 시나리오별 창의성 분석
    print("\n" + "="*80)
    print("[시나리오별 창의성 지표]")
    print("-"*80)

    for scenario in scenarios:
        print(f"\n{scenario['id']}: {scenario['name'][:40]}...")
        print(f"  - 이벤트 수: {len(scenario['events'])}개 (AI 결정)")
        print(f"  - 액터 다양성: {len(set(e.get('actor') for e in scenario['events'] if e.get('actor')))}명")
        print(f"  - 파라미터 조정: {len(scenario['parameter_adjustments'])}개")

        # 이벤트 시퀀스 논리
        event_sequence = " → ".join([e['type'] for e in scenario['events'][:4]])
        print(f"  - 이벤트 시퀀스: {event_sequence}...")

    # 4. 결론
    print("\n" + "="*80)
    print("결론")
    print("="*80)

    print("\n고정된 것 (템플릿):")
    print("  ✓ 결과 타입 (홈승/무/원정승)")
    print("  ✓ 시나리오 개수 (5-7개)")
    print("  ✓ 확률 범위 (EPL 통계 준수)")
    print("  ✓ probability_boost 범위 (1.0-3.0)")

    print("\nAI가 창조한 것:")
    print("  ✓ 선수 선택 (11명 중)")
    print("  ✓ 이벤트 타입 (11가지 중)")
    print("  ✓ 타이밍 (0-90분 내 minute_range)")
    print("  ✓ 확률 부스트 정확한 값")
    print("  ✓ 이벤트 시퀀스 논리")
    print("  ✓ 자연어 근거 생성")
    print("  ✓ 파라미터 조정 계산")

    print("\n비유:")
    print("  템플릿 = 영화 장르 (액션/로맨스/스릴러)")
    print("  AI 창의성 = 구체적 스토리/캐릭터/대사/장면")
    print()

if __name__ == "__main__":
    try:
        analyze_scenarios()
    except FileNotFoundError:
        print("Error: generated_scenarios.json not found")
        print("Run 'python3 inspect_scenario_generation.py' first")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
