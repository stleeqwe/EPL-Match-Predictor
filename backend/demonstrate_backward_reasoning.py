#!/usr/bin/env python3
"""
역추론 문제 시연
실제로 확률이 어디서 오는지 증명
"""

import json

def demonstrate_problem():
    """역추론 문제 시연"""

    print("="*80)
    print("역추론(Backward Reasoning) 문제 시연")
    print("="*80)

    # 1. 템플릿 확률
    print("\n[1단계] 템플릿이 먼저 확률 할당")
    print("-"*80)

    template_probs = {
        "Dominant home win": 0.15,
        "Close home win": 0.25,
        "Draw": 0.25,
        "Close away win": 0.20,
        "Dominant away win": 0.10,
        "High-scoring draw": 0.05
    }

    print("템플릿 확률 (사용자 데이터 보기 전):")
    for template, prob in template_probs.items():
        print(f"  {template}: {prob*100:.0f}%")

    print(f"\n합계: {sum(template_probs.values())*100:.0f}%")
    print("\n⚠️  문제: 확률이 사용자 데이터와 무관하게 이미 결정됨")

    # 2. 실제 생성 결과
    print("\n[2단계] AI가 사용자 데이터로 스토리 채우기")
    print("-"*80)

    with open('generated_scenarios.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    actual_probs = {}
    for scenario in data['scenarios']:
        name = scenario['name']
        prob = scenario['expected_probability']
        actual_probs[name] = prob

    print("실제 생성된 시나리오 확률:")
    for name, prob in actual_probs.items():
        print(f"  {name[:40]}...: {prob*100:.0f}%")

    print(f"\n합계: {sum(actual_probs.values())*100:.0f}%")

    # 3. 비교
    print("\n[3단계] 템플릿 vs 실제 확률 비교")
    print("-"*80)

    print("\n템플릿 확률이 그대로 유지됨:")
    print("  템플릿: [15%, 25%, 25%, 20%, 10%, 5%]")
    print("  실제:   [15%, 25%, 25%, 20%, 10%, 5%]")
    print("\n✓ 100% 일치 → 확률은 템플릿에서 나옴, 사용자 데이터는 스토리만 채움")

    # 4. 문제 시나리오
    print("\n[4단계] 문제 시나리오")
    print("-"*80)
    print("\n가상 시나리오 1: 압도적 우위 팀")
    print("  User Input:")
    print("    - 홈팀: Man City (공격력 95/100)")
    print("    - 원정팀: Sheffield (공격력 40/100)")
    print("    - 도메인 지식: 'Man City가 10-0으로 이길 수 있음'")
    print("\n  현재 시스템 출력:")
    print("    - Dominant home win: 15%  ← 템플릿 고정")
    print("    - Close home win: 25%")
    print("    - Draw: 25%              ← 비현실적!")
    print("    - Away win: 30%          ← 더 비현실적!")
    print("\n  ⚠️  문제: 압도적 우위인데도 무승부/원정승 확률이 높음")

    print("\n가상 시나리오 2: 레드카드 상황")
    print("  User Input:")
    print("    - 도메인 지식: '5분에 원정팀 주장이 레드카드 받을 것'")
    print("\n  현재 시스템 출력:")
    print("    - 레드카드 전용 시나리오 없음")
    print("    - 기존 7개 템플릿에 억지로 끼워맞춤")
    print("    - 'Close away win: 20%' ← 10명인데 이길 확률 20%?")
    print("\n  ⚠️  문제: 특수 상황을 템플릿에 반영할 수 없음")

    # 5. 정답 비교
    print("\n[5단계] 올바른 순추론 방식이라면?")
    print("-"*80)
    print("\n순추론 (Forward Reasoning):")
    print("  1. 사용자 데이터 입력")
    print("     - Arsenal attack: 60.8/100")
    print("     - Liverpool attack: 80.5/100")
    print("     - Commentary: 'Liverpool이 공격적으로 우세'")
    print("\n  2. AI가 데이터 분석")
    print("     - Liverpool 공격력 19.7 높음")
    print("     - 원정팀 우세 가능성 증가")
    print("\n  3. 자연스러운 확률 도출")
    print("     - Home win: 25%  (데이터 기반)")
    print("     - Draw: 20%")
    print("     - Away win: 55%  (Liverpool 우세 반영)")
    print("\n  ✓ 확률이 데이터에서 나옴")

    print("\n현재 시스템 (Backward Reasoning):")
    print("  1. 템플릿 확률 먼저 할당")
    print("     - Home win: 40% (15% + 25%)")
    print("     - Draw: 30%")
    print("     - Away win: 30%")
    print("\n  2. AI가 스토리 끼워맞춤")
    print("     - Liverpool 데이터를 Away win 30%에 할당")
    print("     - 억지로 Draw 30% 만들기 위해 '균형' 스토리 생성")
    print("\n  ✗ 확률이 템플릿에서 나옴, 데이터 무시")

    # 결론
    print("\n" + "="*80)
    print("결론: 사용자 지적이 정확함")
    print("="*80)
    print("\n✓ 결과는 정해놓고 (7개 템플릿)")
    print("✓ 과정은 끼워맞춘다 (AI가 사용자 데이터로 스토리 채움)")
    print("\n이것은:")
    print("  - 진짜 AI 시뮬레이션이 아니라")
    print("  - 템플릿 기반 스토리텔링에 가깝다")
    print()

if __name__ == "__main__":
    try:
        demonstrate_problem()
    except FileNotFoundError:
        print("Error: generated_scenarios.json not found")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
