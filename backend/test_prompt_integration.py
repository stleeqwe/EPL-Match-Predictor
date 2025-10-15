"""
Prompt Integration Test
Domain 데이터가 AI Prompt에 제대로 통합되었는지 테스트
"""

import sys
import os

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from ai.data_models import MatchInput, TeamInput
from ai.prompts.phase1_scenario import generate_phase1_prompt


def main():
    """Prompt Integration 테스트"""
    print("\n" + "=" * 60)
    print("🚀 Prompt Integration Test")
    print("=" * 60 + "\n")

    # Domain 데이터를 포함한 TeamInput 생성
    home_team = TeamInput(
        name="Arsenal",
        formation="4-3-3",
        recent_form="WWDWL",
        injuries=["Partey"],
        key_players=["Saka", "Odegaard", "Martinelli"],
        attack_strength=85.0,  # Domain 지식
        defense_strength=82.0,  # Domain 지식
        press_intensity=80.0,   # Domain 지식
        buildup_style="possession"  # Domain 지식
    )

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
        match_id="PROMPT_TEST_001",
        home_team=home_team,
        away_team=away_team,
        venue="Emirates Stadium",
        competition="Premier League",
        weather="Clear",
        importance="derby"
    )

    # Phase 1 Prompt 생성
    print("📝 Generating Phase 1 Prompt...\n")
    system_prompt, user_prompt = generate_phase1_prompt(match_input, include_examples=False)

    print("=" * 60)
    print("Generated User Prompt:")
    print("=" * 60)
    print(user_prompt)
    print("=" * 60)

    # Domain 지식 포함 확인
    print("\n✅ Validation:")

    checks = [
        ("공격력 (home)", "공격력: 85.0/100" in user_prompt),
        ("수비력 (home)", "수비력: 82.0/100" in user_prompt),
        ("압박 강도 (home)", "압박 강도: 80.0/100" in user_prompt),
        ("빌드업 스타일 (home)", "빌드업 스타일: possession" in user_prompt),
        ("공격력 (away)", "공격력: 83.0/100" in user_prompt),
        ("수비력 (away)", "수비력: 78.0/100" in user_prompt),
        ("압박 강도 (away)", "압박 강도: 75.0/100" in user_prompt),
        ("빌드업 스타일 (away)", "빌드업 스타일: direct" in user_prompt),
    ]

    all_passed = True
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}: {'Included' if result else 'Missing'}")
        if not result:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All Domain Data Successfully Integrated into AI Prompt!")
    else:
        print("⚠️ Some domain data missing from prompt")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed!")
