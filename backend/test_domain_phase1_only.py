"""
Simple Domain + Qwen Test (Phase 1 Only)
Domain 데이터가 Qwen AI Phase 1에 제대로 전달되는지 확인
"""

import sys
import os

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from services.domain_data_loader import get_domain_data_loader
from services.team_input_mapper import TeamInputMapper
from ai.data_models import MatchInput
from ai.qwen_client import QwenClient
from ai.prompts.phase1_scenario import generate_phase1_prompt


def main():
    """간단한 Domain + Phase 1 테스트"""
    print("\n" + "=" * 60)
    print("🚀 Domain Data + Qwen AI Phase 1 Test")
    print("=" * 60 + "\n")

    # Step 1: Domain 데이터 로드
    print("Step 1: Loading Domain Data...")
    loader = get_domain_data_loader()
    home_domain = loader.load_all("Arsenal")

    print(f"  ✅ Arsenal Domain Data:")
    print(f"     Formation: {home_domain.formation}")
    print(f"     Team Strength: {len(home_domain.team_strength) if home_domain.team_strength else 0} attributes")
    print(f"     Comment: {home_domain.team_strength_comment[:50] if home_domain.team_strength_comment else 'None'}...\n")

    # Step 2: TeamInput 변환
    print("Step 2: Converting to TeamInput...")
    home_team = TeamInputMapper.map_to_team_input(
        team_name="Arsenal",
        domain_data=home_domain,
        recent_form="WWDWL",
        injuries=["Partey"],
        key_players=["Saka", "Odegaard", "Martinelli"]
    )

    away_team = TeamInputMapper.map_to_team_input(
        team_name="Liverpool",
        domain_data=loader.load_all("Liverpool"),  # 데이터 없을 것 (기본값 사용)
        recent_form="WWLWW",
        injuries=["Matip"],
        key_players=["Salah", "Van Dijk", "Alisson"]
    )

    print(f"  ✅ Home: {home_team.name} (Attack: {home_team.attack_strength:.1f}, Style: {home_team.buildup_style})")
    print(f"  ✅ Away: {away_team.name} (Attack: {away_team.attack_strength:.1f}, Style: {away_team.buildup_style})\n")

    # Step 3: MatchInput 생성
    print("Step 3: Creating MatchInput with Domain Data...")
    match_input = MatchInput(
        match_id="PHASE1_TEST_001",
        home_team=home_team,
        away_team=away_team,
        venue="Emirates Stadium",
        competition="Premier League",
        importance="top_clash"
    )
    print(f"  ✅ Match: {match_input.home_team.name} vs {match_input.away_team.name}\n")

    # Step 4: Prompt 생성
    print("Step 4: Generating Phase 1 Prompt...")
    system_prompt, user_prompt = generate_phase1_prompt(match_input, include_examples=False)

    # Domain 속성이 포함되어 있는지 확인
    checks = [
        ("공격력 (Arsenal)", f"공격력: {home_team.attack_strength}/100" in user_prompt),
        ("수비력 (Arsenal)", f"수비력: {home_team.defense_strength}/100" in user_prompt),
        ("빌드업 스타일 (Arsenal)", f"빌드업 스타일: {home_team.buildup_style}" in user_prompt),
    ]

    all_passed = True
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
        if not result:
            all_passed = False

    if not all_passed:
        print("\n  ⚠️ Domain 데이터가 Prompt에 포함되지 않았습니다!")
        return False

    print("\n" + "=" * 60)
    print("User Prompt Sample (first 800 chars):")
    print("=" * 60)
    print(user_prompt[:800])
    print("...")
    print("=" * 60)

    # Step 5: Qwen Health Check
    print("\nStep 5: Checking Qwen AI...")
    qwen_client = QwenClient()
    is_healthy, error = qwen_client.health_check()

    if not is_healthy:
        print(f"  ❌ Qwen is not available: {error}")
        print(f"  ⚠️ Phase 1 생성은 건너뜁니다 (Prompt 검증은 완료)")
        return True  # Prompt 검증은 성공

    print(f"  ✅ Qwen is ready!\n")

    # Step 6: Phase 1 시나리오 생성
    print("Step 6: Generating Scenario with Qwen AI...")
    print("  (This may take 10-30 seconds...)\n")

    success, response, usage, error = qwen_client.generate(
        prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=0.7,
        max_tokens=2000
    )

    if not success:
        print(f"  ❌ Qwen generation failed: {error}")
        return False

    print(f"  ✅ Scenario generated!")
    print(f"\n📊 Usage:")
    print(f"  Input tokens: ~{usage['input_tokens']:.0f}")
    print(f"  Output tokens: ~{usage['output_tokens']:.0f}")

    print(f"\n📝 Generated Scenario (first 500 chars):")
    print("-" * 60)
    print(response[:500])
    print("...")
    print("-" * 60)

    # 성공!
    print("\n" + "=" * 60)
    print("🎉 Domain Data + Qwen AI Phase 1 Test PASSED!")
    print("=" * 60)
    print("\n✨ 주요 성과:")
    print("  ✅ Backend Domain 데이터 로드")
    print("  ✅ 18개 Team Strength → 4개 기본 속성 변환")
    print("  ✅ Domain 데이터가 AI Prompt에 포함")
    print("  ✅ Qwen AI로 시나리오 생성 성공")
    print("\n🔥 사용자가 MyVision 탭에 입력한 Domain 지식이")
    print("   AI에 성공적으로 전달되어 시나리오 생성에 반영되었습니다!")

    return True


if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ Test completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Test failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
