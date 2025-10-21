#!/usr/bin/env python3
"""
사용자 도메인 데이터 분석
세 가지 새로운 방법론 적용 가능성 검증
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from services.enriched_data_loader import EnrichedDomainDataLoader
import json

def analyze_data_availability():
    """사용자 도메인 데이터 분석"""

    print("="*80)
    print("사용자 도메인 데이터 구조 분석")
    print("세 가지 방법론 적용 가능성 검증")
    print("="*80)

    # Load sample data
    loader = EnrichedDomainDataLoader()
    arsenal = loader.load_team_data("Arsenal")
    liverpool = loader.load_team_data("Liverpool")

    print("\n[현재 사용 가능한 데이터]")
    print("-"*80)

    # 1. 팀 레벨 데이터
    print("\n1. 팀 레벨 데이터:")
    print(f"   - Formation: {arsenal.formation}")
    print(f"   - Formation Tactics:")
    if arsenal.formation_tactics:
        print(f"     • Name: {arsenal.formation_tactics.name}")
        print(f"     • Style: {arsenal.formation_tactics.style}")
        print(f"     • Buildup: {arsenal.formation_tactics.buildup[:50]}...")
        print(f"     • Pressing: {arsenal.formation_tactics.pressing[:50]}...")
        print(f"     • Strengths: {arsenal.formation_tactics.strengths}")
        print(f"     • Weaknesses: {arsenal.formation_tactics.weaknesses}")

    print(f"\n   - Derived Strengths (계산값):")
    ds = arsenal.derived_strengths
    print(f"     • Attack: {ds.attack_strength:.1f}/100")
    print(f"     • Defense: {ds.defense_strength:.1f}/100")
    print(f"     • Midfield: {ds.midfield_control:.1f}/100")
    print(f"     • Physical: {ds.physical_intensity:.1f}/100")

    print(f"\n   - Team Strategy Commentary:")
    print(f"     {arsenal.team_strategy_commentary[:100]}...")

    # 2. 선수 레벨 데이터
    print("\n2. 선수 레벨 데이터 (11명):")
    print(f"   총 {len(arsenal.lineup)}명")

    # Sample player
    sample_pos = list(arsenal.lineup.keys())[0]
    sample_player = arsenal.lineup[sample_pos]
    print(f"\n   예시: {sample_player.name} ({sample_pos})")
    print(f"   - Position: {sample_player.position}")
    print(f"   - Sub Position: {sample_player.sub_position}")
    print(f"   - Overall Rating: {sample_player.overall_rating:.2f}")
    print(f"   - Attributes ({len(sample_player.ratings)}개):")
    for attr, value in list(sample_player.ratings.items())[:5]:
        print(f"     • {attr}: {value:.2f}")
    print(f"   - User Commentary: {sample_player.user_commentary[:80]}...")

    # 3. 포지션 정보
    print("\n3. 포지션 정보:")
    print("   라인업 구조:")
    for pos, player in arsenal.lineup.items():
        print(f"   - {pos}: {player.name} ({player.sub_position})")

    # 데이터 요약
    print("\n" + "="*80)
    print("데이터 요약")
    print("="*80)

    print("\n✓ 있는 것:")
    print("  • 11명 선수별 10-12개 속성 (포지션 의존적)")
    print("  • 선수별 user commentary (정성적)")
    print("  • 포메이션 (4-3-3 등)")
    print("  • 포메이션 전술 (buildup, pressing, strengths, weaknesses)")
    print("  • 팀 전략 commentary (정성적)")
    print("  • Derived team strengths (attack, defense, midfield, physical)")
    print("  • 포지션 라벨 (GK, CB, LW, ST 등)")

    print("\n✗ 없는 것:")
    print("  • 역대 전적 데이터")
    print("  • Elo 레이팅")
    print("  • 선수 정확한 좌표 (x, y)")
    print("  • 히트맵 데이터")
    print("  • 실시간 폼 데이터")
    print("  • 부상 상태")
    print("  • 최근 5경기 성적")

    # 방법론별 분석
    print("\n" + "="*80)
    print("방법론별 데이터 요구사항 분석")
    print("="*80)

    analyze_poisson_rating_model(arsenal, liverpool)
    analyze_zone_dominance_model(arsenal, liverpool)
    analyze_key_player_model(arsenal, liverpool)

    # 통합 제안
    print("\n" + "="*80)
    print("통합 아키텍처 제안")
    print("="*80)

    propose_integrated_architecture()

def analyze_poisson_rating_model(arsenal, liverpool):
    """포아송-레이팅 하이브리드 모델 분석"""

    print("\n[1] 포아송-레이팅 하이브리드 모델")
    print("-"*80)

    print("\n요구사항:")
    print("  1. Elo 레이팅 (각 팀 공격력/수비력)")
    print("  2. 포메이션 궁합도")
    print("  3. 포아송 분포 파라미터")

    print("\n사용 가능한 데이터:")
    print("  ✓ Derived strengths → Elo 레이팅 대체 가능")
    print(f"    - Arsenal: Attack {arsenal.derived_strengths.attack_strength:.1f}, Defense {arsenal.derived_strengths.defense_strength:.1f}")
    print(f"    - Liverpool: Attack {liverpool.derived_strengths.attack_strength:.1f}, Defense {liverpool.derived_strengths.defense_strength:.1f}")

    print("\n  ✓ Formation tactics → 궁합도 계산 가능")
    print(f"    - Arsenal: {arsenal.formation_tactics.style if arsenal.formation_tactics else 'N/A'}")
    print(f"    - Liverpool: {liverpool.formation_tactics.style if liverpool.formation_tactics else 'N/A'}")
    print("    - 예: 공격적 vs 수비적 → 궁합 계수 조정")

    print("\n계산 예시:")
    # Simple calculation
    arsenal_attack = arsenal.derived_strengths.attack_strength
    liverpool_defense = liverpool.derived_strengths.defense_strength
    arsenal_lambda = (arsenal_attack / 100) * (1 - liverpool_defense / 100) * 2.8  # EPL avg

    liverpool_attack = liverpool.derived_strengths.attack_strength
    arsenal_defense = arsenal.derived_strengths.defense_strength
    liverpool_lambda = (liverpool_attack / 100) * (1 - arsenal_defense / 100) * 2.8

    print(f"  Arsenal λ (expected goals): {arsenal_lambda:.2f}")
    print(f"  Liverpool λ (expected goals): {liverpool_lambda:.2f}")

    print("\n결론:")
    print("  ✓ 충분히 구현 가능")
    print("  ⚠️  Elo 레이팅 대신 derived strengths 사용 (근사치)")

def analyze_zone_dominance_model(arsenal, liverpool):
    """Zone Dominance Matrix 분석"""

    print("\n[2] Zone Dominance Matrix")
    print("-"*80)

    print("\n요구사항:")
    print("  1. 경기장 9개 구역 분할")
    print("  2. 포메이션별 구역 점유율")
    print("  3. 선수 능력치로 구역 우세도")
    print("  4. xG 변환")

    print("\n사용 가능한 데이터:")
    print("  ✓ Lineup 포지션 정보 → 구역 매핑 가능")

    # Zone mapping example
    zones = {
        'left_defense': ['LB', 'CB-L'],
        'center_defense': ['CB', 'CB1', 'CB2'],
        'right_defense': ['RB', 'CB-R'],
        'left_midfield': ['LM', 'CM-L', 'LW'],
        'center_midfield': ['DM', 'CM', 'CM1', 'CM2', 'CAM'],
        'right_midfield': ['RM', 'CM-R', 'RW'],
        'left_attack': ['LW'],
        'center_attack': ['ST', 'CF', 'ST1', 'ST2'],
        'right_attack': ['RW']
    }

    print("\n  구역별 선수 배치 예시 (Arsenal):")
    for zone, positions in list(zones.items())[:3]:
        zone_players = [p for pos, p in arsenal.lineup.items() if pos in positions]
        if zone_players:
            avg_rating = sum(p.overall_rating for p in zone_players) / len(zone_players)
            print(f"    {zone}: {len(zone_players)}명, Avg {avg_rating:.2f}")

    print("\n  ✓ 선수 ratings → 구역 우세도 계산 가능")
    print("    - 예: center_midfield 평균 rating 4.1 → 우세도 82%")

    print("\n문제점:")
    print("  ⚠️  포지션 라벨이 정확하지 않을 수 있음")
    print("      (예: CB vs CB1 vs CB-L 표준화 필요)")
    print("  ⚠️  선수 움직임/이동 범위 데이터 없음")
    print("      (GK가 center_defense에만 있다고 가정)")

    print("\n결론:")
    print("  △ 근사치로 구현 가능하나 정확도 제한")
    print("  → 포지션 라벨 표준화 필요")

def analyze_key_player_model(arsenal, liverpool):
    """Key Player Weighted Model 분석"""

    print("\n[3] Key Player Weighted Model")
    print("-"*80)

    print("\n요구사항:")
    print("  1. 선수별 영향력 지수")
    print("  2. 포메이션 내 위치별 가중치")
    print("  3. 상대 취약 구역 분석")
    print("  4. 몬테카를로 시뮬레이션")

    print("\n사용 가능한 데이터:")
    print("  ✓ Overall rating → 영향력 지수")
    print("  ✓ Key strengths → 특화 능력 반영")

    # Calculate influence
    print("\n  영향력 지수 계산 예시:")
    top_players = sorted(arsenal.lineup.values(),
                        key=lambda p: p.overall_rating,
                        reverse=True)[:3]

    for i, player in enumerate(top_players, 1):
        strengths = player.get_key_strengths(3)
        strength_str = ", ".join([f"{s}: {player.ratings[s]:.2f}" for s in strengths[:2]])
        print(f"    {i}. {player.name} ({player.sub_position})")
        print(f"       Overall: {player.overall_rating:.2f}")
        print(f"       Top: {strength_str}")

    print("\n  ✓ Formation tactics weaknesses → 취약 구역")
    if arsenal.formation_tactics:
        print(f"    Arsenal weaknesses: {arsenal.formation_tactics.weaknesses}")

    print("\n  ✓ User commentary → 정성적 보정")
    print(f"    예: '{top_players[0].user_commentary[:60]}...'")

    print("\n결론:")
    print("  ✓ 충분히 구현 가능")
    print("  ✓ User commentary를 어떻게 정량화할지가 관건")

def propose_integrated_architecture():
    """통합 아키텍처 제안"""

    print("\n제안: 3단계 하이브리드 아키텍처")
    print("-"*80)

    print("""
Step 1: Mathematical Models (확률 기준 계산)
├─ Poisson-Rating Model
│  └─ Output: λ_home=1.03, λ_away=1.19
│      → P(2-1) = 12%, P(1-2) = 18%, P(1-1) = 22%
├─ Zone Dominance Matrix
│  └─ Output: Home center 65%, Away wing 72%
│      → xG_home = 1.2, xG_away = 1.5
└─ Key Player Weighted
   └─ Output: Isak influence 8.5/10, Trossard 7.2/10
       → Impact on scenarios

Step 2: AI Scenario Generation (템플릿 제거)
├─ Input: Step 1의 확률 분포 + User commentary
├─ Prompt:
│  "Based on mathematical analysis:
│   - Away team has 55% win probability (λ=1.19 > 1.03)
│   - Center dominance: Liverpool 65%
│   - Key player: Isak (influence 8.5)
│
│   Generate 3-7 realistic scenarios:
│   - Focus on LIKELY outcomes (away win scenarios)
│   - Include low-probability scenarios if interesting
│   - Use user commentary for narrative"
│
└─ Output: 자유 생성 시나리오 (3-10개)
   - Away win 2-1: 25% (Isak 중앙 돌파)
   - Away win 1-0: 20% (견고한 수비)
   - Draw 1-1: 18% (균형)
   - Home win 2-1: 15% (Trossard 측면 활용)
   - Away win 3-1: 12% (압도)
   - Draw 0-0: 10% (수비 대결)

Step 3: Monte Carlo Validation (Phase 2 재설계)
├─ 각 시나리오를 N회 시뮬레이션
├─ 시뮬레이션 엔진에 Step 1 모델 결과 반영
│  - Zone dominance → shot_per_minute 조정
│  - Key player influence → 개인별 확률 부스트
└─ Output: 검증된 확률 분포

NO MORE:
✗ EPL 평균 강제 맞추기
✗ 7개 고정 템플릿
✗ 편향 감지 (대신 데이터 기반 검증)
""")

    print("\n핵심 원칙:")
    print("  1. 확률은 수학적 모델에서 나온다 (템플릿 아님)")
    print("  2. AI는 확률을 바탕으로 시나리오 스토리 생성")
    print("  3. User commentary는 스토리와 개별 이벤트에 반영")
    print("  4. Phase 2는 검증용, 조정용 아님")

if __name__ == "__main__":
    try:
        analyze_data_availability()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
