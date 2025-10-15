"""
Match Simulator V3 통합 테스트
전체 플로우 및 엣지 케이스 검증
"""

import sys
import os

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from ai.data_models import MatchInput, TeamInput, SimulationResult
from simulation.v3.match_simulator_v3 import MatchSimulatorV3
from simulation.v3.ai_integration import MockAIClient, AIIntegrationLayer
from simulation.v3.convergence_judge import ConvergenceJudge
from simulation.v3.statistical_engine import StatisticalMatchEngine


def create_test_match_input() -> MatchInput:
    """테스트용 경기 입력 생성"""
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
        match_id="TEST_INTEGRATION_001",
        home_team=home_team,
        away_team=away_team,
        venue="Emirates Stadium",
        competition="Premier League",
        weather="Clear",
        importance="derby"
    )


def test_full_flow_mock():
    """Test 1: 전체 플로우 통합 테스트 (Mock AI)"""
    print("=== Test 1: 전체 플로우 통합 테스트 ===\n")

    # 1. 컴포넌트 생성
    engine = StatisticalMatchEngine(seed=42)
    mock_ai = MockAIClient()
    ai_integration = AIIntegrationLayer(mock_ai, provider='mock')
    judge = ConvergenceJudge(convergence_threshold=0.7, max_iterations=5)

    simulator = MatchSimulatorV3(
        statistical_engine=engine,
        ai_integration=ai_integration,
        convergence_judge=judge,
        max_iterations=3
    )

    # 2. 테스트 경기 입력
    match_input = create_test_match_input()

    # 3. 시뮬레이션 실행
    result = simulator.simulate_match(match_input)

    # 4. 검증
    assert result['final_result'] is not None, "final_result가 없음"
    assert result['final_report'] is not None, "final_report가 없음"
    assert result['iterations'] >= 1, "반복 횟수가 1 미만"
    assert result['iterations'] <= 3, "최대 반복 초과"
    assert len(result['scenario_history']) >= 1, "시나리오 히스토리 없음"
    assert isinstance(result['final_result'], SimulationResult), "final_result 타입 오류"
    assert isinstance(result['final_report'], str), "final_report 타입 오류"
    assert len(result['final_report']) > 0, "리포트 내용 없음"

    print("\n✅ Test 1 통과: 전체 플로우 정상 작동\n")
    return result


def test_single_iteration_convergence():
    """Test 2: 1회 반복으로 수렴"""
    print("=== Test 2: 1회 반복 수렴 테스트 ===\n")

    # Mock Engine - 항상 높은 일치율 반환
    class HighAdherenceEngine:
        def simulate_match(self, home_team, away_team, guide):
            return SimulationResult(
                final_score={'home': 2, 'away': 1},
                events=[],
                narrative_adherence=0.75,  # 75% - 수렴 조건 충족
                stats={'home_shots': 15, 'away_shots': 12}
            )

    engine = HighAdherenceEngine()
    mock_ai = MockAIClient()
    ai_integration = AIIntegrationLayer(mock_ai, provider='mock')
    judge = ConvergenceJudge(convergence_threshold=0.7, max_iterations=5)

    simulator = MatchSimulatorV3(
        statistical_engine=engine,
        ai_integration=ai_integration,
        convergence_judge=judge,
        max_iterations=5
    )

    match_input = create_test_match_input()
    result = simulator.simulate_match(match_input)

    # 검증: 1회만에 수렴해야 함
    assert result['iterations'] == 1, f"1회 수렴 실패: {result['iterations']}회"
    assert result['convergence_info']['is_converged'], "수렴 플래그 오류"

    print(f"\n✅ Test 2 통과: 1회 반복으로 수렴 (일치율 75%)\n")
    return result


def test_max_iterations_reached():
    """Test 3: 최대 반복 도달"""
    print("=== Test 3: 최대 반복 도달 테스트 ===\n")

    # Mock Engine - 항상 낮은 일치율 반환
    class LowAdherenceEngine:
        def simulate_match(self, home_team, away_team, guide):
            return SimulationResult(
                final_score={'home': 1, 'away': 1},
                events=[],
                narrative_adherence=0.30,  # 30% - 수렴 조건 미충족
                stats={'home_shots': 10, 'away_shots': 10}
            )

    engine = LowAdherenceEngine()
    mock_ai = MockAIClient()
    ai_integration = AIIntegrationLayer(mock_ai, provider='mock')
    judge = ConvergenceJudge(convergence_threshold=0.7, max_iterations=3)

    simulator = MatchSimulatorV3(
        statistical_engine=engine,
        ai_integration=ai_integration,
        convergence_judge=judge,
        max_iterations=3
    )

    match_input = create_test_match_input()
    result = simulator.simulate_match(match_input)

    # 검증: 3회 반복 후 종료
    assert result['iterations'] == 3, f"최대 반복 오류: {result['iterations']}회"
    assert len(result['scenario_history']) >= 1, "시나리오 히스토리 없음"

    print(f"\n✅ Test 3 통과: 최대 반복 3회 도달 후 종료\n")
    return result


def test_scenario_adjustment():
    """Test 4: 시나리오 조정 확인"""
    print("=== Test 4: 시나리오 조정 테스트 ===\n")

    # Mock Engine - 처음엔 낮은 일치율, 나중엔 높은 일치율
    class AdaptiveEngine:
        def __init__(self):
            self.call_count = 0

        def simulate_match(self, home_team, away_team, guide):
            self.call_count += 1
            if self.call_count == 1:
                # 첫 번째: 낮은 일치율
                return SimulationResult(
                    final_score={'home': 0, 'away': 0},
                    events=[],
                    narrative_adherence=0.20,
                    stats={'home_shots': 5, 'away_shots': 5}
                )
            else:
                # 두 번째 이후: 높은 일치율
                return SimulationResult(
                    final_score={'home': 2, 'away': 1},
                    events=[],
                    narrative_adherence=0.80,
                    stats={'home_shots': 18, 'away_shots': 10}
                )

    engine = AdaptiveEngine()
    mock_ai = MockAIClient()
    ai_integration = AIIntegrationLayer(mock_ai, provider='mock')
    judge = ConvergenceJudge(convergence_threshold=0.7, max_iterations=5)

    simulator = MatchSimulatorV3(
        statistical_engine=engine,
        ai_integration=ai_integration,
        convergence_judge=judge,
        max_iterations=5
    )

    match_input = create_test_match_input()
    result = simulator.simulate_match(match_input)

    # 검증: 2회 반복 (1회 조정 후 수렴)
    assert result['iterations'] == 2, f"반복 횟수 오류: {result['iterations']}회"
    assert len(result['scenario_history']) >= 2, "시나리오 조정 미발생"

    print(f"\n✅ Test 4 통과: 시나리오 조정 후 수렴 (2회 반복)\n")
    return result


def test_convergence_criteria():
    """Test 5: 수렴 기준 검증"""
    print("=== Test 5: 수렴 기준 검증 테스트 ===\n")

    engine = StatisticalMatchEngine(seed=42)
    mock_ai = MockAIClient()
    ai_integration = AIIntegrationLayer(mock_ai, provider='mock')

    # 다양한 threshold 테스트
    thresholds = [0.5, 0.7, 0.9]

    for threshold in thresholds:
        judge = ConvergenceJudge(convergence_threshold=threshold, max_iterations=5)
        simulator = MatchSimulatorV3(
            statistical_engine=engine,
            ai_integration=ai_integration,
            convergence_judge=judge,
            max_iterations=5
        )

        match_input = create_test_match_input()
        result = simulator.simulate_match(match_input)

        print(f"  Threshold {threshold}: {result['iterations']}회 반복, "
              f"수렴 점수 {result['convergence_info']['weighted_score']:.2f}")

        assert result['iterations'] >= 1, "반복 횟수 오류"
        assert result['iterations'] <= 5, "최대 반복 초과"

    print(f"\n✅ Test 5 통과: 다양한 수렴 기준 정상 작동\n")


def run_all_tests():
    """모든 통합 테스트 실행"""
    print("=" * 60)
    print("Match Simulator V3 통합 테스트 시작")
    print("=" * 60)
    print()

    try:
        # Test 1: 전체 플로우
        result1 = test_full_flow_mock()

        # Test 2: 1회 수렴
        result2 = test_single_iteration_convergence()

        # Test 3: 최대 반복
        result3 = test_max_iterations_reached()

        # Test 4: 시나리오 조정
        result4 = test_scenario_adjustment()

        # Test 5: 수렴 기준
        test_convergence_criteria()

        # 최종 요약
        print("=" * 60)
        print("✅ 모든 통합 테스트 통과!")
        print("=" * 60)
        print()
        print("테스트 요약:")
        print(f"  ✅ Test 1: 전체 플로우 - {result1['iterations']}회 반복")
        print(f"  ✅ Test 2: 1회 수렴 - {result2['iterations']}회 반복")
        print(f"  ✅ Test 3: 최대 반복 - {result3['iterations']}회 반복")
        print(f"  ✅ Test 4: 시나리오 조정 - {result4['iterations']}회 반복")
        print(f"  ✅ Test 5: 수렴 기준 - 다양한 threshold 테스트")
        print()
        print("=" * 60)
        print("Week 6: Iterative Loop Orchestrator 완성! 🎉")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}\n")
        raise
    except Exception as e:
        print(f"\n❌ 예외 발생: {e}\n")
        raise


if __name__ == "__main__":
    run_all_tests()
