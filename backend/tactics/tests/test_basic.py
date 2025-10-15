"""
전술 프레임워크 기본 테스트

독립적으로 작동하는지 검증
"""

import sys
from pathlib import Path

# tactics 모듈을 import할 수 있도록 경로 추가
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from core.formations import FormationSystem
from core.tactical_styles import TacticalStyle, DefensiveParameters, TacticalPresets
from analyzer.effectiveness_calculator import EffectivenessCalculator
from analyzer.goal_path_classifier import GoalPathClassifier, GoalData
from integration import TacticsIntegration


def test_formation_system():
    """포메이션 시스템 테스트"""
    print("=" * 60)
    print("TEST 1: 포메이션 시스템")
    print("=" * 60)

    fs = FormationSystem()

    # 포메이션 목록
    formations = fs.list_formations()
    print(f"✓ 포메이션 수: {len(formations)}")
    assert len(formations) == 6, "6개 포메이션이 있어야 함"

    # 포메이션 로드
    formation_433 = fs.get_formation("4-3-3")
    print(f"✓ 4-3-3 로드: {formation_433['name_kr']}")
    assert formation_433 is not None

    # 차단률 조회
    blocking_rate = fs.get_blocking_rate("4-3-3", "central_penetration")
    print(f"✓ 4-3-3 중앙 침투 차단률: {blocking_rate}%")
    assert 80 <= blocking_rate <= 90

    # 최적 포메이션
    best = fs.get_best_formation_for_category("central_penetration")
    print(f"✓ 중앙 침투 최적 포메이션: {best['name_kr']} ({best['blocking_rate']}%)")

    print("✅ 포메이션 시스템 테스트 통과\n")


def test_tactical_styles():
    """전술 스타일 테스트"""
    print("=" * 60)
    print("TEST 2: 전술 스타일")
    print("=" * 60)

    # 커스텀 전술
    tactics = TacticalStyle(
        name="Test Tactics",
        defensive=DefensiveParameters(
            pressing_intensity=8,
            defensive_line=7
        )
    )
    print(f"✓ 커스텀 전술 생성: {tactics.name}")
    assert tactics.defensive.pressing_intensity == 8

    # 프리셋
    tiki_taka = TacticalPresets.get_tiki_taka()
    print(f"✓ 티키타카 프리셋: 압박 강도 {tiki_taka.defensive.pressing_intensity}/10")
    assert tiki_taka.defensive.pressing_intensity == 9

    print("✅ 전술 스타일 테스트 통과\n")


def test_effectiveness_calculator():
    """효과성 계산기 테스트"""
    print("=" * 60)
    print("TEST 3: 효과성 계산기")
    print("=" * 60)

    calculator = EffectivenessCalculator()

    # 차단률 계산
    result = calculator.calculate_blocking_rate(
        formation="4-3-3",
        goal_category="central_penetration",
        team_ability_coef=1.12
    )
    print(f"✓ 차단률 계산: {result['predicted_blocking_rate']}%")
    assert result['predicted_blocking_rate'] > 0

    # 팀 수비 점수
    defense_score = calculator.calculate_team_defensive_score(
        formation="4-2-3-1",
        team_ability_coef=1.05
    )
    print(f"✓ 팀 수비 점수: {defense_score['overall_defensive_score']:.1f}/100")
    assert 80 <= defense_score['overall_defensive_score'] <= 100

    # 매칭 분석
    matchup = calculator.calculate_matchup_advantage(
        home_formation="4-3-3",
        away_formation="4-2-3-1",
        home_ability=1.10,
        away_ability=1.08
    )
    print(f"✓ 매칭 분석: {matchup['advantage']} 우위")
    assert matchup['advantage'] in ['home', 'away', 'balanced']

    print("✅ 효과성 계산기 테스트 통과\n")


def test_goal_path_classifier():
    """득점 경로 분류기 테스트"""
    print("=" * 60)
    print("TEST 4: 득점 경로 분류기")
    print("=" * 60)

    classifier = GoalPathClassifier()

    # 고속 역습 분류
    goal1 = GoalData(
        buildup_passes=2,
        buildup_duration=2.5,
        x_start=42,
        y_start=34,
        x_shot=94,
        y_shot=38
    )
    category1, conf1 = classifier.classify_goal(goal1)
    print(f"✓ 고속 역습 분류: {category1} (확신도: {conf1:.2f})")
    assert category1 == "counter_fast"

    # 컷백 분류
    goal2 = GoalData(
        buildup_passes=4,
        buildup_duration=8.0,
        x_start=50,
        y_start=12,
        x_shot=85,
        y_shot=34,
        assist_type='cutback'
    )
    category2, conf2 = classifier.classify_goal(goal2)
    print(f"✓ 컷백 분류: {category2} (확신도: {conf2:.2f})")
    assert category2 == "cutback"

    print("✅ 득점 경로 분류기 테스트 통과\n")


def test_integration():
    """통합 인터페이스 테스트"""
    print("=" * 60)
    print("TEST 5: 통합 인터페이스")
    print("=" * 60)

    integration = TacticsIntegration()

    # 선수 전술 적용
    player = {
        'id': 1,
        'name': 'Test Player',
        'position': 'DM',
        'stamina': 85,
        'technical_attributes': {'tackling': 88}
    }
    tactics = {'pressing_intensity': 9}
    adjusted = integration.apply_tactics_to_player(player, tactics, 'DM')
    print(f"✓ 선수 전술 적합도: {adjusted['tactical_fit_score']:.1f}/100")
    assert 'tactical_fit_score' in adjusted

    # 전술 우위 분석
    home = {'formation': '4-3-3', 'team_ability': 1.10}
    away = {'formation': '4-2-3-1', 'team_ability': 1.08}
    advantage = integration.get_tactical_advantage(home, away)
    print(f"✓ 전술 우위: {advantage['advantage']}")
    assert 'advantage' in advantage

    print("✅ 통합 인터페이스 테스트 통과\n")


def run_all_tests():
    """전체 테스트 실행"""
    print("\n" + "=" * 60)
    print("전술 프레임워크 테스트 시작")
    print("=" * 60 + "\n")

    try:
        test_formation_system()
        test_tactical_styles()
        test_effectiveness_calculator()
        test_goal_path_classifier()
        test_integration()

        print("=" * 60)
        print("🎉 모든 테스트 통과!")
        print("=" * 60)
        return True

    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
