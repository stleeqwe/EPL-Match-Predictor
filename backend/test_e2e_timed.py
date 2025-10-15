"""
E2E Test with Detailed Timing Information
"""

import sys
import os
import time
from datetime import datetime

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


def format_time(seconds):
    """초를 읽기 쉬운 형식으로 변환"""
    if seconds < 60:
        return f"{seconds:.2f}초"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}분 {secs:.2f}초"


def main():
    """시간 측정이 포함된 E2E 테스트"""

    total_start = time.time()

    print("\n" + "=" * 60)
    print("🚀 E2E Test with Timing: Domain Data + Qwen AI")
    print("=" * 60 + "\n")
    print(f"⏱️  시작 시간: {datetime.now().strftime('%H:%M:%S')}\n")

    # Step 1: Domain 데이터 로드
    step_start = time.time()
    print("Step 1: Loading Domain Data from Backend...")
    loader = get_domain_data_loader()

    home_team_name = "Arsenal"
    away_team_name = "Liverpool"

    home_domain = loader.load_all(home_team_name)
    away_domain = loader.load_all(away_team_name)

    step_time = time.time() - step_start
    print(f"  ✅ 완료 (소요 시간: {format_time(step_time)})\n")

    # Step 2: TeamInput 변환
    step_start = time.time()
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

    step_time = time.time() - step_start
    print(f"  ✅ 완료 (소요 시간: {format_time(step_time)})\n")

    # Step 3: MatchInput 생성
    step_start = time.time()
    print("Step 3: Creating MatchInput...")
    match_input = MatchInput(
        match_id="E2E_TIMED_TEST",
        home_team=home_team,
        away_team=away_team,
        venue="Emirates Stadium",
        competition="Premier League",
        weather="Clear",
        importance="top_clash"
    )
    step_time = time.time() - step_start
    print(f"  ✅ 완료 (소요 시간: {format_time(step_time)})\n")

    # Step 4: Qwen Health Check
    step_start = time.time()
    print("Step 4: Checking Qwen AI...")
    qwen_client = QwenClient()
    is_healthy, error = qwen_client.health_check()

    if not is_healthy:
        print(f"  ❌ Qwen is not available: {error}")
        return False

    step_time = time.time() - step_start
    print(f"  ✅ 완료 (소요 시간: {format_time(step_time)})\n")

    # Step 5: 시뮬레이션 컴포넌트 생성
    step_start = time.time()
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
        max_iterations=2
    )

    step_time = time.time() - step_start
    print(f"  ✅ 완료 (소요 시간: {format_time(step_time)})\n")

    # Step 6: 시뮬레이션 실행
    step_start = time.time()
    print("Step 6: Running simulation with Qwen AI...")
    print("  ⏱️  시뮬레이션 시작...\n")

    try:
        simulation_start = time.time()
        result = simulator.simulate_match(match_input)
        simulation_time = time.time() - simulation_start

        print(f"\n  ✅ 시뮬레이션 완료!")
        print(f"  ⏱️  시뮬레이션 소요 시간: {format_time(simulation_time)}\n")

        # 결과 출력
        print("=" * 60)
        print("📊 Simulation Results")
        print("=" * 60 + "\n")

        print(f"⚽ Final Score: {result['final_result'].final_score['home']}-"
              f"{result['final_result'].final_score['away']}")
        print(f"🔄 Iterations: {result['iterations']}")
        print(f"📈 Convergence Score: {result['convergence_info']['weighted_score']:.2f}")
        print(f"✅ Converged: {result['convergence_info']['is_converged']}")

        total_time = time.time() - total_start

        # 시간 요약
        print("\n" + "=" * 60)
        print("⏱️  Time Summary")
        print("=" * 60)
        print(f"  Total E2E Test Time: {format_time(total_time)}")
        print(f"  Simulation Time: {format_time(simulation_time)}")
        print(f"  Overhead Time: {format_time(total_time - simulation_time)}")
        print("=" * 60)

        print(f"\n🎉 E2E Test PASSED!")
        print(f"⏱️  종료 시간: {datetime.now().strftime('%H:%M:%S')}")

        return True

    except Exception as e:
        print(f"\n❌ Simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
