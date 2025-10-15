"""
실전 데이터 테스트

실제 EPL 팀 데이터를 사용한 전술 프레임워크 검증
"""

import sys
from pathlib import Path

# tactics 모듈 경로 추가
tactics_dir = Path(__file__).parent.parent
if str(tactics_dir) not in sys.path:
    sys.path.insert(0, str(tactics_dir))

# 프로젝트 루트 경로 추가 (squad_data 접근)
project_root = tactics_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.formations import FormationSystem
from analyzer.effectiveness_calculator import EffectivenessCalculator
from integration import TacticsIntegration

# 실제 팀 데이터 로드 시도
try:
    from data.squad_data import SQUAD_DATA
    print("✓ 실제 EPL 스쿼드 데이터 로드 성공")
    REAL_DATA_AVAILABLE = True
except ImportError:
    print("⚠ squad_data를 로드할 수 없습니다. 샘플 데이터를 사용합니다.")
    SQUAD_DATA = {}
    REAL_DATA_AVAILABLE = False


def print_section(title):
    """섹션 구분선 출력"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def get_team_info(team_name):
    """팀 정보 추출"""
    if team_name not in SQUAD_DATA:
        return None

    squad = SQUAD_DATA[team_name]

    # 팀 능력치 계산 (평균 overall rating 기반)
    # 실제로는 squad_data에 더 많은 정보가 있지만, 간단히 선수 수로 추정
    num_players = len(squad)

    # 주요 리그 팀들의 대략적인 능력 계수
    team_ability_map = {
        "Man City": 1.18,
        "Arsenal": 1.15,
        "Liverpool": 1.16,
        "Chelsea": 1.10,
        "Tottenham": 1.08,
        "Man Utd": 1.05,
        "Newcastle": 1.05,
        "Aston Villa": 1.03,
        "Brighton": 1.02,
    }

    team_ability = team_ability_map.get(team_name, 1.00)

    return {
        'name': team_name,
        'squad': squad,
        'squad_size': num_players,
        'team_ability': team_ability
    }


def analyze_formation_effectiveness():
    """포메이션별 효과성 분석"""
    print_section("TEST 1: 포메이션별 효과성 분석")

    fs = FormationSystem()
    calculator = EffectivenessCalculator()

    # 주요 공격 패턴
    attack_patterns = [
        'central_penetration',
        'wide_penetration',
        'cutback',
        'counter_fast'
    ]

    # 주요 포메이션
    formations = ['4-3-3', '4-2-3-1', '4-4-2', '3-5-2']

    print("공격 패턴별 최적 포메이션:\n")

    for pattern in attack_patterns:
        pattern_info = fs.get_goal_category_info(pattern)
        print(f"📊 {pattern_info['name']} (EPL 빈도: {pattern_info['epl_frequency']*100:.1f}%)")

        # 각 포메이션의 차단률
        blocking_rates = []
        for formation in formations:
            rate = fs.get_blocking_rate(formation, pattern)
            formation_data = fs.get_formation(formation)
            blocking_rates.append({
                'formation': formation_data['name_kr'],
                'rate': rate
            })

        # 차단률 높은 순으로 정렬
        blocking_rates.sort(key=lambda x: x['rate'], reverse=True)

        for i, data in enumerate(blocking_rates):
            icon = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "  "
            print(f"  {icon} {data['formation']}: {data['rate']}%")

        print()


def analyze_real_match():
    """실제 경기 매칭 분석"""
    print_section("TEST 2: 실제 경기 매칭 분석")

    # 실제 데이터가 없으면 스킵
    if not REAL_DATA_AVAILABLE:
        print("⚠ 실제 데이터가 없어 테스트를 건너뜁니다.\n")
        return

    # 빅매치 선정: Arsenal vs Man City
    home_team_name = "Arsenal"
    away_team_name = "Man City"

    home_info = get_team_info(home_team_name)
    away_info = get_team_info(away_team_name)

    if not home_info or not away_info:
        print(f"⚠ {home_team_name} 또는 {away_team_name} 데이터를 찾을 수 없습니다.\n")
        available_teams = list(SQUAD_DATA.keys())[:10]
        print(f"사용 가능한 팀: {', '.join(available_teams)}\n")
        return

    print(f"🏟️  경기: {home_team_name} (홈) vs {away_team_name} (원정)\n")
    print(f"홈팀 스쿼드: {home_info['squad_size']}명 (능력 계수: {home_info['team_ability']})")
    print(f"원정팀 스쿼드: {away_info['squad_size']}명 (능력 계수: {away_info['team_ability']})\n")

    # 전술 설정
    home_formation = "4-3-3"  # Arsenal의 일반적인 포메이션
    away_formation = "4-3-3"  # Man City의 하이 프레싱

    print(f"📋 홈팀 포메이션: {home_formation}")
    print(f"📋 원정팀 포메이션: {away_formation}\n")

    # 전술 분석
    calculator = EffectivenessCalculator()

    print("--- 수비력 분석 ---\n")

    # 홈팀 수비력
    home_defense = calculator.calculate_team_defensive_score(
        formation=home_formation,
        team_ability_coef=home_info['team_ability']
    )

    print(f"🛡️  {home_team_name} 종합 수비력: {home_defense['overall_defensive_score']:.1f}/100")
    print(f"   등급: {home_defense['rating']}")

    # 원정팀 수비력
    away_defense = calculator.calculate_team_defensive_score(
        formation=away_formation,
        team_ability_coef=away_info['team_ability']
    )

    print(f"\n🛡️  {away_team_name} 종합 수비력: {away_defense['overall_defensive_score']:.1f}/100")
    print(f"   등급: {away_defense['rating']}")

    # 매칭 우위 분석
    print("\n--- 전술 매칭 분석 ---\n")

    matchup = calculator.calculate_matchup_advantage(
        home_formation=home_formation,
        away_formation=away_formation,
        home_ability=home_info['team_ability'],
        away_ability=away_info['team_ability']
    )

    print(f"전술적 우위: {matchup['advantage'].upper()}")
    print(f"수비력 차이: {abs(matchup['difference']):.1f}점\n")

    # 세부 분석 (10% 이상 차이나는 부분만)
    significant_differences = [
        (cat, analysis)
        for cat, analysis in matchup['analysis_by_category'].items()
        if abs(analysis['difference']) > 10
    ]

    if significant_differences:
        print("📌 주요 전술적 차이점:\n")
        for cat, analysis in significant_differences:
            advantage = "홈팀 우위" if analysis['difference'] > 0 else "원정팀 우위"
            print(f"  • {analysis['name']}")
            print(f"    - {home_team_name}: {analysis['home_blocking']:.1f}% 차단")
            print(f"    - {away_team_name}: {analysis['away_blocking']:.1f}% 차단")
            print(f"    - {advantage} (+{abs(analysis['difference']):.1f}%)\n")
    else:
        print("두 팀의 전술적 차이가 크지 않습니다. 균형잡힌 경기가 예상됩니다.\n")


def analyze_formation_comparison():
    """포메이션 비교 분석"""
    print_section("TEST 3: 포메이션 비교 분석")

    calculator = EffectivenessCalculator()

    # 상대 팀의 공격 스타일 정의 (맨시티 스타일)
    opponent_style = {
        'central_penetration': 0.35,  # 중앙 침투 35%
        'wide_penetration': 0.25,     # 측면 침투 25%
        'cutback': 0.20,              # 컷백 20%
        'counter_fast': 0.10,         # 역습 10%
        'corner': 0.10                # 세트피스 10%
    }

    print("🎯 상대팀 공격 스타일 (Man City 기준):")
    for category, percentage in opponent_style.items():
        fs = FormationSystem()
        cat_info = fs.get_goal_category_info(category)
        if cat_info:
            print(f"  • {cat_info['name']}: {percentage*100:.0f}%")

    print("\n최적 수비 포메이션 추천:\n")

    # 포메이션 비교
    recommendations = calculator.compare_formations_for_opponent(
        opponent_style,
        team_ability_coef=1.10  # 강팀 기준
    )

    # Top 3 추천
    for i, rec in enumerate(recommendations[:3], 1):
        icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
        print(f"{icon} {rec['formation_name']}")
        print(f"   종합 차단률: {rec['overall_score']:.1f}%")
        print(f"   핵심 강점:")

        # 가장 효과적인 카테고리 3개
        categories = list(rec['by_category'].items())
        categories.sort(key=lambda x: x[1], reverse=True)

        for cat, rate in categories[:3]:
            fs = FormationSystem()
            cat_info = fs.get_goal_category_info(cat)
            if cat_info:
                print(f"     - {cat_info['name']}: {rate:.1f}%")
        print()


def test_tactical_advantage():
    """전술 우위 계산 테스트"""
    print_section("TEST 4: 다양한 포메이션 매칭")

    calculator = EffectivenessCalculator()

    matchups = [
        ("4-3-3", "4-2-3-1", "하이 프레싱 vs 컴팩트 수비"),
        ("3-5-2", "4-4-2", "윙백 시스템 vs 전통적 4백"),
        ("4-1-4-1", "4-3-3", "수비형 vs 공격형")
    ]

    for home_form, away_form, description in matchups:
        print(f"📊 {description}")
        print(f"   {home_form} vs {away_form}\n")

        matchup = calculator.calculate_matchup_advantage(
            home_formation=home_form,
            away_formation=away_form,
            home_ability=1.10,
            away_ability=1.10
        )

        print(f"   결과: {matchup['advantage'].upper()}")

        if matchup['advantage'] == 'balanced':
            print(f"   양팀 수비력이 비슷합니다 (차이: {abs(matchup['difference']):.1f}점)\n")
        else:
            winner = "홈팀" if matchup['advantage'] == 'home' else "원정팀"
            winner_form = home_form if matchup['advantage'] == 'home' else away_form
            print(f"   {winner} ({winner_form})이 {abs(matchup['difference']):.1f}점 우위\n")


def run_all_tests():
    """전체 실전 테스트 실행"""
    print("\n" + "=" * 80)
    print("  전술 프레임워크 실전 데이터 테스트")
    print("=" * 80)

    if REAL_DATA_AVAILABLE:
        print(f"\n✓ 실제 EPL 데이터 사용")
        available_teams = list(SQUAD_DATA.keys())
        print(f"✓ 로드된 팀: {len(available_teams)}개")
        print(f"  예: {', '.join(available_teams[:5])}...\n")
    else:
        print("\n⚠ 실제 데이터 미사용 (프레임워크 기능만 테스트)\n")

    try:
        # 테스트 실행
        analyze_formation_effectiveness()
        analyze_real_match()
        analyze_formation_comparison()
        test_tactical_advantage()

        print("=" * 80)
        print("  🎉 모든 실전 테스트 완료!")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
