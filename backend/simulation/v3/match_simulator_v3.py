"""
Match Simulator V3 Orchestrator
Phase 1-7 통합 오케스트레이터

전체 플로우:
1. Phase 1: AI 시나리오 생성
2-6. 반복 루프 (최대 5회):
   - Phase 2: Statistical Engine 시뮬레이션
   - Phase 3: AI 결과 분석
   - Phase 4: 수렴 판단
   - Phase 5: 시나리오 조정
   - Phase 6: 다음 반복
7. Phase 7: 최종 리포트 생성
"""

from typing import Dict, Any, Optional
import sys
import os

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from ai.data_models import MatchInput, Scenario, SimulationResult, TeamInput
from simulation.v3.convergence_judge import ConvergenceJudge
from simulation.v3.ai_integration import AIIntegrationLayer
from simulation.v3.statistical_engine import StatisticalMatchEngine, TeamInfo, ScenarioGuide


class MatchSimulatorV3:
    """
    Match Simulator V3

    Phase 1-7 통합 오케스트레이터
    """

    def __init__(self,
                statistical_engine: StatisticalMatchEngine,
                ai_integration: AIIntegrationLayer,
                convergence_judge: ConvergenceJudge,
                max_iterations: int = 5):
        """
        Args:
            statistical_engine: Statistical Match Engine V3
            ai_integration: AI Integration Layer
            convergence_judge: Convergence Judge
            max_iterations: 최대 반복 횟수 (기본 5회)
        """
        self.engine = statistical_engine
        self.ai = ai_integration
        self.judge = convergence_judge
        self.max_iterations = max_iterations

    def simulate_match(self, match_input: MatchInput) -> Dict[str, Any]:
        """
        전체 시뮬레이션 실행

        Args:
            match_input: 경기 입력 정보

        Returns:
            {
                'final_result': SimulationResult,
                'final_report': str (markdown),
                'convergence_info': Dict,
                'iterations': int,
                'scenario_history': List[Scenario]
            }
        """
        print(f"\n{'='*60}")
        print(f"Match Simulator V3: {match_input.home_team.name} vs {match_input.away_team.name}")
        print(f"{'='*60}\n")

        # Phase 1: AI 시나리오 생성
        print("Phase 1: AI 시나리오 생성...")
        scenario = self.ai.generate_scenario(match_input)
        print(f"  ✅ 시나리오 생성 완료: {len(scenario.events)}개 이벤트")

        scenario_history = [scenario]
        previous_result = None
        final_result = None
        conv_info = {}
        iteration = 0

        # Phase 2-6: 반복 루프
        for iteration in range(1, self.max_iterations + 1):
            print(f"\n--- Iteration {iteration}/{self.max_iterations} ---")

            # Phase 2: Statistical Engine 시뮬레이션
            print("Phase 2: Statistical Engine 시뮬레이션...")
            guide = ScenarioGuide(scenario.to_dict())
            match_result = self.engine.simulate_match(
                self._to_team_info(match_input.home_team),
                self._to_team_info(match_input.away_team),
                guide
            )
            # MatchResult → SimulationResult 변환
            result = self._to_simulation_result(match_result)
            print(f"  최종 스코어: {result.final_score['home']}-{result.final_score['away']}")
            print(f"  서사 일치율: {result.narrative_adherence:.0%}")

            # Phase 3: AI 분석
            print("Phase 3: AI 분석/조정...")
            analysis = self.ai.analyze_result(scenario, result, iteration, self.max_iterations)
            print(f"  AI 상태: {analysis.status.value}")

            # Phase 4: 수렴 판단
            print("Phase 4: 수렴 판단...")
            is_converged, conv_info = self.judge.is_converged(
                analysis, result, previous_result, iteration
            )
            print(f"  수렴 점수: {conv_info['weighted_score']:.2f}")
            print(f"  수렴 여부: {'✅ Yes' if is_converged else '❌ No'}")

            if is_converged:
                # 수렴 완료 → Phase 7로
                print(f"\n✅ 수렴 완료! (Iteration {iteration})")
                final_result = result
                break

            # Phase 5: 시나리오 조정
            if analysis.adjusted_scenario:
                print("Phase 5: 시나리오 조정...")
                scenario = analysis.adjusted_scenario
                scenario_history.append(scenario)
                print(f"  ✅ 시나리오 조정 완료")
            else:
                print("  ℹ️  조정된 시나리오 없음, 현재 시나리오 유지")

            previous_result = result

            # Phase 6: 다음 반복으로
            if iteration == self.max_iterations:
                print(f"\n⚠️  최대 반복 {self.max_iterations}회 도달")
                final_result = result

        # Phase 7: 최종 리포트
        print("\nPhase 7: 최종 리포트 생성...")
        final_report = self.ai.generate_report(match_input, final_result)
        print(f"  ✅ 리포트 생성 완료 ({len(final_report)} 문자)")

        print(f"\n{'='*60}")
        print(f"✅ 시뮬레이션 완료!")
        print(f"{'='*60}\n")

        return {
            'final_result': final_result,
            'final_report': final_report,
            'convergence_info': conv_info,
            'iterations': iteration,
            'scenario_history': scenario_history,
        }

    def _to_team_info(self, team_input: TeamInput) -> TeamInfo:
        """
        TeamInput → TeamInfo 변환

        Args:
            team_input: TeamInput 객체

        Returns:
            TeamInfo 객체
        """
        return TeamInfo(
            name=team_input.name,
            formation=team_input.formation,
            attack_strength=team_input.attack_strength,
            defense_strength=team_input.defense_strength,
            press_intensity=70.0,  # 기본값
            buildup_style="mixed"  # 기본값 (direct, possession, mixed 중 선택)
        )

    def _to_simulation_result(self, match_result) -> SimulationResult:
        """
        MatchResult → SimulationResult 변환

        Args:
            match_result: MatchResult 객체 (from Statistical Engine)

        Returns:
            SimulationResult 객체 (for AI Integration Layer)
        """
        return SimulationResult(
            final_score=match_result.final_score,
            events=match_result.events,
            narrative_adherence=match_result.narrative_adherence,
            stats=match_result.stats if match_result.stats else {},
            expected_events=[],  # Statistical Engine는 expected_events를 제공하지 않음
            occurred_events=[]   # 필요시 events에서 추출 가능
        )


# ==========================================================================
# Testing
# ==========================================================================

def test_match_simulator_v3():
    """Match Simulator V3 테스트"""
    print("=== Match Simulator V3 테스트 ===\n")

    # Mock Components
    from simulation.v3.ai_integration import MockAIClient, AIIntegrationLayer
    from simulation.v3.convergence_judge import ConvergenceJudge

    # AI Integration Layer (Mock)
    mock_ai = MockAIClient()
    ai_integration = AIIntegrationLayer(mock_ai, provider='mock')

    # Convergence Judge
    convergence_judge = ConvergenceJudge(
        convergence_threshold=0.7,
        max_iterations=5
    )

    # Statistical Engine V3
    # 간단한 Mock Engine (실제로는 StatisticalMatchEngine 사용)
    class MockStatisticalEngine:
        def simulate_match(self, home_team, away_team, guide):
            """Mock 시뮬레이션"""
            return SimulationResult(
                final_score={'home': 2, 'away': 1},
                events=[],
                narrative_adherence=0.67,  # 67% (수렴 조건 충족)
                stats={
                    'home_shots': 15,
                    'away_shots': 12,
                    'home_possession': 58,
                    'away_possession': 42,
                }
            )

    mock_engine = MockStatisticalEngine()

    # Match Simulator V3
    simulator = MatchSimulatorV3(
        statistical_engine=mock_engine,
        ai_integration=ai_integration,
        convergence_judge=convergence_judge,
        max_iterations=3  # 테스트용 3회
    )

    # 테스트 경기 입력
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

    match_input = MatchInput(
        match_id="TEST_NLD_001",
        home_team=home_team,
        away_team=away_team,
        venue="Emirates Stadium",
        competition="Premier League",
        weather="Clear",
        importance="derby"
    )

    # Test 1: 전체 플로우 실행
    print("Test 1: 전체 플로우 실행\n")
    result = simulator.simulate_match(match_input)

    print("\n결과 검증:")
    print(f"  최종 스코어: {result['final_result'].final_score}")
    print(f"  반복 횟수: {result['iterations']}")
    print(f"  수렴 점수: {result['convergence_info']['weighted_score']:.2f}")
    print(f"  시나리오 변경 횟수: {len(result['scenario_history'])}")
    print(f"  리포트 길이: {len(result['final_report'])} 문자")

    # 검증
    assert result['final_result'] is not None
    assert result['final_report'] is not None
    assert result['iterations'] >= 1
    assert result['iterations'] <= 3
    assert len(result['scenario_history']) >= 1

    print(f"\n  ✅ Test 1 통과\n")

    print("=" * 60)
    print("✅ Match Simulator V3 테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    test_match_simulator_v3()
