"""
Full Flow Test with Real Qwen AI
실제 Qwen AI를 사용한 전체 Phase 1-7 플로우 테스트
"""

import sys
import os

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from ai.qwen_client import QwenClient
from ai.data_models import MatchInput, TeamInput
from simulation.v3.ai_integration import AIIntegrationLayer
from simulation.v3.convergence_judge import ConvergenceJudge
from simulation.v3.statistical_engine import StatisticalMatchEngine
from simulation.v3.match_simulator_v3 import MatchSimulatorV3


def create_test_match():
    """테스트용 경기 생성"""
    home_team = TeamInput(
        name="Arsenal",
        formation="4-3-3",
        recent_form="WWDWL",
        injuries=["Partey"],
        key_players=["Saka", "Odegaard", "Martinelli"],
        attack_strength=85.0,
        defense_strength=82.0,
    )

    away_team = TeamInput(
        name="Tottenham",
        formation="4-2-3-1",
        recent_form="LWWDW",
        injuries=["Romero"],
        key_players=["Son", "Maddison", "Kulusevski"],
        attack_strength=83.0,
        defense_strength=78.0,
    )

    return MatchInput(
        match_id="FULL_FLOW_TEST_001",
        home_team=home_team,
        away_team=away_team,
        venue="Emirates Stadium",
        competition="Premier League",
        weather="Clear",
        importance="derby"
    )


def main():
    """메인 테스트 실행"""
    print("\n" + "="*60)
    print("🚀 Full Flow Test with Real Qwen AI")
    print("="*60 + "\n")

    # 1. Qwen 건강 체크
    print("Step 1: Qwen Health Check...")
    qwen_client = QwenClient()
    is_healthy, error = qwen_client.health_check()

    if not is_healthy:
        print(f"❌ Qwen is not available: {error}")
        print("\n💡 Tip: Ollama 서버를 실행하세요: ollama serve")
        return

    print("✅ Qwen is ready!\n")

    # 2. 컴포넌트 생성
    print("Step 2: Creating components...")

    # Statistical Engine (실제 엔진)
    engine = StatisticalMatchEngine(seed=42)
    print("  ✅ Statistical Engine created")

    # AI Integration Layer (실제 Qwen AI)
    ai_integration = AIIntegrationLayer(qwen_client, provider='qwen')
    print("  ✅ AI Integration Layer created (provider=qwen)")

    # Convergence Judge
    judge = ConvergenceJudge(
        convergence_threshold=0.7,
        max_iterations=5
    )
    print("  ✅ Convergence Judge created")

    # Match Simulator V3
    simulator = MatchSimulatorV3(
        statistical_engine=engine,
        ai_integration=ai_integration,
        convergence_judge=judge,
        max_iterations=3  # 테스트용 3회
    )
    print("  ✅ Match Simulator V3 created\n")

    # 3. 경기 입력
    print("Step 3: Creating match input...")
    match_input = create_test_match()
    print(f"  Match: {match_input.home_team.name} vs {match_input.away_team.name}")
    print(f"  Venue: {match_input.venue}")
    print(f"  Importance: {match_input.importance}\n")

    # 4. 전체 시뮬레이션 실행
    print("Step 4: Running full simulation with Qwen AI...")
    print("  (Phase 1-7, 최대 3회 반복)\n")

    try:
        result = simulator.simulate_match(match_input)

        # 5. 결과 출력
        print("\n" + "="*60)
        print("📊 Simulation Results")
        print("="*60 + "\n")

        print(f"✅ Final Score: {result['final_result'].final_score['home']}-{result['final_result'].final_score['away']}")
        print(f"✅ Iterations: {result['iterations']}")
        print(f"✅ Convergence Score: {result['convergence_info']['weighted_score']:.2f}")
        print(f"✅ Converged: {result['convergence_info']['is_converged']}")
        print(f"✅ Scenario Changes: {len(result['scenario_history'])}")
        print(f"✅ Narrative Adherence: {result['final_result'].narrative_adherence:.0%}")

        print(f"\n📈 Statistics:")
        print(f"  Home Shots: {result['final_result'].stats.get('home_shots', 0)}")
        print(f"  Away Shots: {result['final_result'].stats.get('away_shots', 0)}")
        print(f"  Home Possession: {result['final_result'].stats.get('home_possession', 0)}")
        print(f"  Away Possession: {result['final_result'].stats.get('away_possession', 0)}")

        # 6. 최종 리포트 샘플
        print(f"\n📝 Final Report (first 500 chars):")
        print("-" * 60)
        print(result['final_report'][:500])
        print("...")
        print("-" * 60)

        # 7. 시나리오 히스토리
        print(f"\n📜 Scenario History:")
        for i, scenario in enumerate(result['scenario_history']):
            print(f"  {i+1}. {scenario.scenario_id} - {len(scenario.events)} events")
            if i < len(result['scenario_history']) - 1:
                print(f"     → 조정됨")

        # 8. 수렴 상세 정보
        print(f"\n🎯 Convergence Details:")
        details = result['convergence_info'].get('details', {})
        for key, value in details.items():
            print(f"  {key}: {value}")

        print(f"\n  Reason: {result['convergence_info']['reason']}")

        # 성공!
        print("\n" + "="*60)
        print("🎉 Full Flow Test PASSED!")
        print("="*60)
        print("\n✨ 실제 Qwen AI를 사용한 전체 시뮬레이션 성공!")
        print("\n주요 성과:")
        print("  ✅ Phase 1: AI 시나리오 생성 (Qwen)")
        print("  ✅ Phase 2: Statistical Engine 시뮬레이션")
        print("  ✅ Phase 3: AI 결과 분석 (Qwen)")
        print("  ✅ Phase 4: Convergence Judge 수렴 판단")
        print("  ✅ Phase 5: 시나리오 조정 (필요시)")
        print("  ✅ Phase 7: AI 최종 리포트 (Qwen)")
        print("\n🔥 Mock이 아닌 실제 AI로 전체 플로우 완성!")

        return result

    except Exception as e:
        print(f"\n❌ Simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = main()
    if result:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed!")
