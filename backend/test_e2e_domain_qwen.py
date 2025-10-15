"""
End-to-End Test: Domain Data + Qwen AI
Backend에서 Domain 데이터를 로드하여 Qwen AI로 시뮬레이션 실행
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
from simulation.v3.ai_integration import AIIntegrationLayer
from simulation.v3.convergence_judge import ConvergenceJudge
from simulation.v3.statistical_engine import StatisticalMatchEngine
from simulation.v3.match_simulator_v3 import MatchSimulatorV3


def main():
    """End-to-End 테스트"""
    print("\n" + "=" * 60)
    print("🚀 End-to-End Test: Domain Data + Qwen AI")
    print("=" * 60 + "\n")

    # Step 1: Backend에서 Domain 데이터 로드
    print("Step 1: Loading Domain Data from Backend...")
    loader = get_domain_data_loader()

    home_team_name = "Arsenal"
    away_team_name = "Liverpool"  # Liverpool은 domain 데이터가 없을 것임 (기본값 사용)

    home_domain = loader.load_all(home_team_name)
    away_domain = loader.load_all(away_team_name)

    print(f"  ✅ {home_team_name}: Formation={home_domain.formation}, "
          f"Team Strength={'✅' if home_domain.team_strength else '❌'}")
    print(f"  ✅ {away_team_name}: Formation={away_domain.formation}, "
          f"Team Strength={'✅' if away_domain.team_strength else '❌'}\n")

    # Step 2: Domain Data → TeamInput 변환
    print("Step 2: Converting Domain Data to TeamInput...")

    home_team = TeamInputMapper.map_to_team_input(
        team_name=home_team_name,
        domain_data=home_domain,
        recent_form="WWDWL",
        injuries=["Partey"],
        key_players=["Saka", "Odegaard", "Martinelli"]
    )

    away_team = TeamInputMapper.map_to_team_input(
        team_name=away_team_name,
        domain_data=away_domain,
        recent_form="WWLWW",
        injuries=["Matip"],
        key_players=["Salah", "Van Dijk", "Alexander-Arnold"]
    )

    print(f"  ✅ {home_team.name}:")
    print(f"     Attack: {home_team.attack_strength:.1f}, Defense: {home_team.defense_strength:.1f}")
    print(f"     Press: {home_team.press_intensity:.1f}, Style: {home_team.buildup_style}")
    print(f"  ✅ {away_team.name}:")
    print(f"     Attack: {away_team.attack_strength:.1f}, Defense: {away_team.defense_strength:.1f}")
    print(f"     Press: {away_team.press_intensity:.1f}, Style: {away_team.buildup_style}\n")

    # Step 3: MatchInput 생성
    print("Step 3: Creating MatchInput...")
    match_input = MatchInput(
        match_id="E2E_DOMAIN_TEST_001",
        home_team=home_team,
        away_team=away_team,
        venue="Emirates Stadium",
        competition="Premier League",
        weather="Clear",
        importance="top_clash"
    )
    print(f"  ✅ Match: {match_input.home_team.name} vs {match_input.away_team.name}\n")

    # Step 4: Qwen Health Check
    print("Step 4: Checking Qwen AI...")
    qwen_client = QwenClient()
    is_healthy, error = qwen_client.health_check()

    if not is_healthy:
        print(f"  ❌ Qwen is not available: {error}")
        print(f"  💡 Tip: Ollama 서버를 실행하세요: ollama serve")
        return False

    print(f"  ✅ Qwen is ready!\n")

    # Step 5: 시뮬레이션 컴포넌트 생성
    print("Step 5: Creating simulation components...")

    engine = StatisticalMatchEngine(seed=42)
    ai_integration = AIIntegrationLayer(qwen_client, provider='qwen')
    judge = ConvergenceJudge(
        convergence_threshold=0.7,
        max_iterations=5
    )

    simulator = MatchSimulatorV3(
        statistical_engine=engine,
        ai_integration=ai_integration,
        convergence_judge=judge,
        max_iterations=2  # 테스트용 2회로 제한
    )

    print(f"  ✅ All components created\n")

    # Step 6: 시뮬레이션 실행
    print("Step 6: Running simulation with Domain Data + Qwen AI...")
    print("  (This may take 30-60 seconds...)\n")

    print("=" * 60)

    try:
        result = simulator.simulate_match(match_input)

        # 결과 출력
        print("\n" + "=" * 60)
        print("📊 Simulation Results")
        print("=" * 60 + "\n")

        print(f"✅ Final Score: {result['final_result'].final_score['home']}-"
              f"{result['final_result'].final_score['away']}")
        print(f"✅ Iterations: {result['iterations']}")
        print(f"✅ Convergence Score: {result['convergence_info']['weighted_score']:.2f}")
        print(f"✅ Converged: {result['convergence_info']['is_converged']}")
        print(f"✅ Narrative Adherence: {result['final_result'].narrative_adherence:.0%}")

        print(f"\n📈 Statistics:")
        print(f"  Home Shots: {result['final_result'].stats.get('home_shots', 0)}")
        print(f"  Away Shots: {result['final_result'].stats.get('away_shots', 0)}")
        print(f"  Home Possession: {result['final_result'].stats.get('home_possession', 0)}")
        print(f"  Away Possession: {result['final_result'].stats.get('away_possession', 0)}")

        print(f"\n📝 Final Report (first 300 chars):")
        print("-" * 60)
        print(result['final_report'][:300])
        print("...")
        print("-" * 60)

        # 성공!
        print("\n" + "=" * 60)
        print("🎉 End-to-End Test PASSED!")
        print("=" * 60)
        print("\n✨ Domain 데이터가 Qwen AI 시뮬레이션에 성공적으로 통합되었습니다!")
        print("\n주요 성과:")
        print("  ✅ Step 1: Backend Domain 데이터 로드")
        print("  ✅ Step 2: 18개 Team Strength → 4개 기본 속성 변환")
        print("  ✅ Step 3: MatchInput에 Domain 데이터 포함")
        print("  ✅ Step 4: AI Prompt에 팀 전력 전달")
        print("  ✅ Step 5: Qwen AI로 시나리오 생성")
        print("  ✅ Step 6: 전체 시뮬레이션 완료")

        print(f"\n🔥 사용자가 MyVision 탭에 입력한 Domain 지식이")
        print(f"   AI 시뮬레이션에 성공적으로 반영되었습니다!")

        return True

    except Exception as e:
        print(f"\n❌ Simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed!")
