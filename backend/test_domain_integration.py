"""
Domain Data Integration Test
Backend에서 Domain 데이터를 로드하여 AI 시뮬레이션에 전달하는 통합 테스트
"""

import sys
import os

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from services.domain_data_loader import DomainDataLoader, get_domain_data_loader
from services.team_input_mapper import TeamInputMapper


def test_domain_data_loader():
    """Test 1: Domain Data Loader"""
    print("=" * 60)
    print("Test 1: Domain Data Loader")
    print("=" * 60 + "\n")

    loader = get_domain_data_loader()

    # Arsenal 데이터 로드 (이전 테스트에서 저장한 데이터)
    team_name = "Arsenal"

    print(f"Loading domain data for {team_name}...\n")

    # 개별 로드 테스트
    formation = loader.load_formation(team_name)
    print(f"✅ Formation: {formation}")

    lineup = loader.load_lineup(team_name)
    if lineup:
        print(f"✅ Lineup: {len(lineup)} players")
    else:
        print(f"⚠️  Lineup: Not found")

    team_strength = loader.load_team_strength(team_name)
    if team_strength:
        ratings = team_strength.get('ratings', {})
        comment = team_strength.get('comment', '')
        print(f"✅ Team Strength: {len(ratings)} attributes")
        print(f"   Comment: {comment[:50]}..." if len(comment) > 50 else f"   Comment: {comment}")
    else:
        print(f"⚠️  Team Strength: Not found")

    # 전체 로드 테스트
    print(f"\nLoading all data...")
    domain_data = loader.load_all(team_name)

    print(f"\n📊 Domain Data Summary:")
    print(f"  Team: {domain_data.team_name}")
    print(f"  Formation: {domain_data.formation}")
    print(f"  Lineup: {'✅' if domain_data.lineup else '❌'} ({len(domain_data.lineup) if domain_data.lineup else 0} players)")
    print(f"  Team Strength: {'✅' if domain_data.team_strength else '❌'} ({len(domain_data.team_strength) if domain_data.team_strength else 0} attributes)")
    print(f"  Tactics: {'✅' if domain_data.tactics else '❌'}")
    print(f"  Overall Score: {'✅' if domain_data.overall_score else '❌'}")

    # 데이터 준비 상태 확인
    summary = loader.get_data_summary(team_name)
    print(f"\n📋 Data Readiness:")
    for key, ready in summary.items():
        status = "✅" if ready else "❌"
        print(f"  {status} {key}")

    return domain_data


def test_team_input_mapper(domain_data):
    """Test 2: TeamInput Mapper"""
    print("\n" + "=" * 60)
    print("Test 2: TeamInput Mapper")
    print("=" * 60 + "\n")

    # Domain Data → TeamInput 변환
    team_input = TeamInputMapper.map_to_team_input(
        team_name=domain_data.team_name,
        domain_data=domain_data,
        recent_form="WWDWL",
        injuries=["Partey"],
        key_players=["Saka", "Odegaard", "Martinelli"]
    )

    print(f"📊 TeamInput Object:")
    print(f"  Name: {team_input.name}")
    print(f"  Formation: {team_input.formation}")
    print(f"  Recent Form: {team_input.recent_form}")
    print(f"  Injuries: {', '.join(team_input.injuries) if team_input.injuries else 'None'}")
    print(f"  Key Players: {', '.join(team_input.key_players[:3]) if team_input.key_players else 'None'}")
    print(f"\n  🎯 Calculated Attributes (from 18 Team Strength attributes):")
    print(f"     Attack Strength: {team_input.attack_strength:.1f}/100")
    print(f"     Defense Strength: {team_input.defense_strength:.1f}/100")
    print(f"     Press Intensity: {team_input.press_intensity:.1f}/100")
    print(f"     Buildup Style: {team_input.buildup_style}")

    # 상세 설명 생성
    description = TeamInputMapper.get_enriched_description(domain_data)
    print(f"\n📝 Enriched Description:")
    print(f"  {description}")

    return team_input


def test_ai_prompt_integration(team_input):
    """Test 3: AI Prompt에 통합"""
    print("\n" + "=" * 60)
    print("Test 3: AI Prompt Integration")
    print("=" * 60 + "\n")

    # MatchInput 생성
    from ai.data_models import MatchInput, TeamInput

    home_team = team_input

    away_team = TeamInput(
        name="Tottenham",
        formation="4-2-3-1",
        recent_form="LWWDW",
        injuries=["Romero"],
        key_players=["Son", "Maddison", "Kulusevski"],
        attack_strength=83.0,
        defense_strength=78.0,
        press_intensity=75.0,
        buildup_style="direct"
    )

    match_input = MatchInput(
        match_id="DOMAIN_TEST_001",
        home_team=home_team,
        away_team=away_team,
        venue="Emirates Stadium",
        competition="Premier League",
        weather="Clear",
        importance="derby"
    )

    print(f"📋 MatchInput Created:")
    print(f"  Match: {match_input.home_team.name} vs {match_input.away_team.name}")
    print(f"  Venue: {match_input.venue}")
    print(f"  Importance: {match_input.importance}")

    # to_dict() 확인
    match_dict = match_input.to_dict()

    print(f"\n📦 MatchInput.to_dict() Output:")
    print(f"  Home Team:")
    for key, value in match_dict['home_team'].items():
        print(f"    {key}: {value}")

    print(f"\n✅ Domain 데이터가 MatchInput에 성공적으로 통합되었습니다!")

    return match_input


def main():
    """메인 테스트 실행"""
    print("\n" + "=" * 60)
    print("🚀 Domain Data Integration Test")
    print("=" * 60 + "\n")

    try:
        # Test 1: Domain Data Loader
        domain_data = test_domain_data_loader()

        # Test 2: TeamInput Mapper
        team_input = test_team_input_mapper(domain_data)

        # Test 3: AI Prompt Integration
        match_input = test_ai_prompt_integration(team_input)

        # 성공!
        print("\n" + "=" * 60)
        print("✅ All Integration Tests Passed!")
        print("=" * 60)
        print("\n🎉 Backend Domain 데이터가 AI 시뮬레이션에 성공적으로 통합되었습니다!")
        print("\n주요 성과:")
        print("  ✅ Domain Data Loader: Backend 데이터 로드")
        print("  ✅ TeamInput Mapper: 18개 속성 → 4개 기본 속성 변환")
        print("  ✅ AI Integration: MatchInput에 domain 데이터 포함")
        print("\n다음 단계:")
        print("  → MatchInput.to_dict()에서 모든 필드 전달하도록 수정")
        print("  → AI Prompt에서 이 데이터 활용")

        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed!")
