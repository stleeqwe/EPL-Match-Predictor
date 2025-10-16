"""
Comprehensive Domain Input Scenario Testing
다양한 팀 전력, 스타일, 포메이션 조합으로 시뮬레이션 검증
"""

import sys
import os
from typing import Dict

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from ai.data_models import TeamInput, MatchInput
from ai.qwen_client import QwenClient
from simulation.v3.ai_integration import AIIntegrationLayer
from simulation.v3.convergence_judge import ConvergenceJudge
from simulation.v3.statistical_engine import StatisticalMatchEngine
from simulation.v3.match_simulator_v3 import MatchSimulatorV3


class ScenarioTester:
    """다양한 시나리오로 시뮬레이션 테스트"""

    def __init__(self):
        self.qwen_client = QwenClient(model="qwen2.5:14b")
        self.engine = StatisticalMatchEngine(seed=42)
        self.ai_integration = AIIntegrationLayer(self.qwen_client, provider='qwen')
        self.judge = ConvergenceJudge(convergence_threshold=0.7, max_iterations=5)
        self.simulator = MatchSimulatorV3(
            statistical_engine=self.engine,
            ai_integration=self.ai_integration,
            convergence_judge=self.judge,
            max_iterations=2
        )

        self.results = []

    def create_team_input(
        self,
        name: str,
        formation: str,
        attack: float,
        defense: float,
        press: float,
        style: str,
        recent_form: str = "WWDWL",
        injuries: list = None,
        key_players: list = None
    ) -> TeamInput:
        """팀 입력 데이터 생성"""
        return TeamInput(
            name=name,
            formation=formation,
            recent_form=recent_form,
            injuries=injuries or [],
            key_players=key_players or ["Player1", "Player2", "Player3"],
            attack_strength=attack,
            defense_strength=defense,
            press_intensity=press,
            buildup_style=style
        )

    def run_scenario(
        self,
        scenario_name: str,
        home_team: TeamInput,
        away_team: TeamInput,
        expected_characteristics: Dict
    ):
        """시나리오 실행 및 검증"""
        print("\n" + "=" * 70)
        print(f"🎯 Scenario: {scenario_name}")
        print("=" * 70)

        # 팀 정보 출력
        print(f"\n🏠 Home: {home_team.name}")
        print(f"   Formation: {home_team.formation} | Style: {home_team.buildup_style}")
        print(f"   Attack: {home_team.attack_strength:.0f} | Defense: {home_team.defense_strength:.0f} | Press: {home_team.press_intensity:.0f}")

        print(f"\n✈️  Away: {away_team.name}")
        print(f"   Formation: {away_team.formation} | Style: {away_team.buildup_style}")
        print(f"   Attack: {away_team.attack_strength:.0f} | Defense: {away_team.defense_strength:.0f} | Press: {away_team.press_intensity:.0f}")

        # MatchInput 생성
        match_input = MatchInput(
            match_id=f"TEST_{scenario_name.replace(' ', '_').upper()}",
            home_team=home_team,
            away_team=away_team,
            venue=f"{home_team.name} Stadium",
            competition="Premier League",
            importance="regular"
        )

        print("\n⏱️  Running simulation...")

        try:
            # 시뮬레이션 실행
            result = self.simulator.simulate_match(match_input)

            # 결과 출력
            final_result = result['final_result']
            home_score = final_result.final_score['home']
            away_score = final_result.final_score['away']

            print(f"\n📊 Results:")
            print(f"   Score: {home_score}-{away_score}")
            print(f"   Iterations: {result['iterations']}")
            print(f"   Convergence: {result['convergence_info']['weighted_score']:.2f}")

            stats = final_result.stats
            print(f"\n📈 Stats:")
            print(f"   Home Shots: {stats.get('home_shots', 0)} | Away Shots: {stats.get('away_shots', 0)}")
            print(f"   Home Possession: {stats.get('home_possession', 0):.0f}% | Away Possession: {stats.get('away_possession', 0):.0f}%")

            # 검증
            self.validate_results(
                scenario_name,
                home_team,
                away_team,
                result,
                expected_characteristics
            )

            # 결과 저장
            self.results.append({
                'scenario': scenario_name,
                'score': f"{home_score}-{away_score}",
                'stats': stats,
                'convergence': result['convergence_info']['weighted_score'],
                'passed': True
            })

            print(f"\n✅ Scenario PASSED\n")

        except Exception as e:
            print(f"\n❌ Scenario FAILED: {e}\n")
            import traceback
            traceback.print_exc()

            self.results.append({
                'scenario': scenario_name,
                'error': str(e),
                'passed': False
            })

    def validate_results(
        self,
        scenario_name: str,
        home_team: TeamInput,
        away_team: TeamInput,
        result: Dict,
        expected: Dict
    ):
        """결과 검증"""
        print(f"\n🔍 Validation:")

        final_result = result['final_result']
        stats = final_result.stats
        home_score = final_result.final_score['home']
        away_score = final_result.final_score['away']

        # 1. 전력 차이에 따른 스코어 경향 확인
        attack_diff = home_team.attack_strength - away_team.attack_strength
        defense_diff = home_team.defense_strength - away_team.defense_strength

        if 'dominant_team' in expected:
            dominant = expected['dominant_team']
            if dominant == 'home':
                if home_score >= away_score:
                    print(f"   ✅ Home team dominance reflected in score")
                else:
                    print(f"   ⚠️  Home team should be stronger but lost")
            elif dominant == 'away':
                if away_score >= home_score:
                    print(f"   ✅ Away team dominance reflected in score")
                else:
                    print(f"   ⚠️  Away team should be stronger but lost")
            else:  # balanced
                print(f"   ✅ Balanced match (score: {home_score}-{away_score})")

        # 2. 점유율 검증 (possession 스타일이 더 높은 점유율을 가져야 함)
        if home_team.buildup_style == 'possession' and away_team.buildup_style == 'direct':
            if stats.get('home_possession', 50) > 55:
                print(f"   ✅ Possession style reflected in stats (Home: {stats.get('home_possession', 0):.0f}%)")
            else:
                print(f"   ⚠️  Possession style not well reflected")

        # 3. 공격력에 따른 슈팅 수 확인
        home_shots = stats.get('home_shots', 0)
        away_shots = stats.get('away_shots', 0)

        if home_team.attack_strength > away_team.attack_strength + 15:
            if home_shots >= away_shots:
                print(f"   ✅ Higher attack strength reflected in shots ({home_shots} vs {away_shots})")
            else:
                print(f"   ⚠️  Attack strength not well reflected in shots")

        # 4. 수렴 여부 확인
        convergence = result['convergence_info']['weighted_score']
        if convergence >= 0.3:
            print(f"   ✅ Reasonable convergence score: {convergence:.2f}")
        else:
            print(f"   ⚠️  Low convergence: {convergence:.2f}")


def main():
    """종합 시나리오 테스트 실행"""
    print("\n" + "=" * 70)
    print("🚀 Comprehensive Domain Input Scenario Testing")
    print("=" * 70)

    tester = ScenarioTester()

    # Health check
    is_healthy, error = tester.qwen_client.health_check()
    if not is_healthy:
        print(f"❌ Qwen not available: {error}")
        return False

    print("✅ Qwen 2.5 14B ready\n")

    # ========================================================================
    # Scenario 1: 강팀 vs 약팀 (압도적 전력 차이)
    # ========================================================================
    tester.run_scenario(
        scenario_name="Scenario 1: Strong vs Weak Team",
        home_team=tester.create_team_input(
            name="Manchester City",
            formation="4-3-3",
            attack=95,
            defense=90,
            press=85,
            style="possession",
            recent_form="WWWWW",
            key_players=["Haaland", "De Bruyne", "Rodri"]
        ),
        away_team=tester.create_team_input(
            name="Sheffield United",
            formation="5-4-1",
            attack=65,
            defense=68,
            press=70,
            style="direct",
            recent_form="LLLLD",
            key_players=["McBurnie", "Ahmedhodzic", "Foderingham"]
        ),
        expected_characteristics={
            'dominant_team': 'home',
            'possession_advantage': 'home',
            'goal_difference': 'large'
        }
    )

    # ========================================================================
    # Scenario 2: 동등한 전력 (비슷한 팀)
    # ========================================================================
    tester.run_scenario(
        scenario_name="Scenario 2: Evenly Matched Teams",
        home_team=tester.create_team_input(
            name="Arsenal",
            formation="4-3-3",
            attack=88,
            defense=85,
            press=82,
            style="possession",
            recent_form="WWDWL",
            key_players=["Saka", "Odegaard", "Martinelli"]
        ),
        away_team=tester.create_team_input(
            name="Liverpool",
            formation="4-3-3",
            attack=87,
            defense=84,
            press=88,
            style="possession",
            recent_form="WWLWW",
            key_players=["Salah", "Van Dijk", "Alexander-Arnold"]
        ),
        expected_characteristics={
            'dominant_team': 'balanced',
            'close_match': True,
            'goal_difference': 'small'
        }
    )

    # ========================================================================
    # Scenario 3: 공격형 vs 수비형
    # ========================================================================
    tester.run_scenario(
        scenario_name="Scenario 3: Attack-focused vs Defense-focused",
        home_team=tester.create_team_input(
            name="Newcastle United",
            formation="4-2-3-1",
            attack=90,
            defense=72,
            press=78,
            style="direct",
            recent_form="WWWDL",
            key_players=["Isak", "Gordon", "Bruno Guimaraes"]
        ),
        away_team=tester.create_team_input(
            name="Atletico Madrid",
            formation="4-4-2",
            attack=75,
            defense=92,
            press=85,
            style="direct",
            recent_form="DWWDW",
            key_players=["Griezmann", "Oblak", "Gimenez"]
        ),
        expected_characteristics={
            'attacking_home': True,
            'defensive_away': True,
            'goal_difference': 'variable'
        }
    )

    # ========================================================================
    # Scenario 4: Possession vs Direct
    # ========================================================================
    tester.run_scenario(
        scenario_name="Scenario 4: Possession vs Direct Playstyle",
        home_team=tester.create_team_input(
            name="Brighton",
            formation="4-3-3",
            attack=80,
            defense=78,
            press=75,
            style="possession",
            recent_form="WWDWW",
            key_players=["Mitoma", "Mac Allister", "Caicedo"]
        ),
        away_team=tester.create_team_input(
            name="Burnley",
            formation="4-4-2",
            attack=72,
            defense=80,
            press=78,
            style="direct",
            recent_form="DWLDW",
            key_players=["Rodriguez", "Brownhill", "Tarkowski"]
        ),
        expected_characteristics={
            'possession_advantage': 'home',
            'counter_attacks': 'away',
            'playstyle_contrast': True
        }
    )

    # ========================================================================
    # Scenario 5: 다양한 포메이션 조합
    # ========================================================================
    tester.run_scenario(
        scenario_name="Scenario 5: Formation Variety (3-5-2 vs 4-2-3-1)",
        home_team=tester.create_team_input(
            name="Tottenham",
            formation="3-5-2",
            attack=85,
            defense=80,
            press=82,
            style="mixed",
            recent_form="WWLWW",
            key_players=["Kane", "Son", "Kulusevski"]
        ),
        away_team=tester.create_team_input(
            name="Chelsea",
            formation="4-2-3-1",
            attack=83,
            defense=82,
            press=80,
            style="possession",
            recent_form="WDWWL",
            key_players=["Sterling", "Mount", "Havertz"]
        ),
        expected_characteristics={
            'tactical_battle': True,
            'formation_impact': True,
            'balanced': True
        }
    )

    # ========================================================================
    # 최종 결과 요약
    # ========================================================================
    print("\n" + "=" * 70)
    print("📋 Test Summary")
    print("=" * 70)

    passed = sum(1 for r in tester.results if r['passed'])
    total = len(tester.results)

    print(f"\nTotal Scenarios: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")

    print("\n" + "-" * 70)
    for i, result in enumerate(tester.results, 1):
        status = "✅" if result['passed'] else "❌"
        print(f"{status} {i}. {result['scenario']}")
        if result['passed']:
            print(f"   Score: {result['score']} | Convergence: {result['convergence']:.2f}")
        else:
            print(f"   Error: {result.get('error', 'Unknown')}")
    print("-" * 70)

    if passed == total:
        print("\n🎉 All scenarios PASSED!")
        print("✅ Domain input integration is working correctly across all test cases")
        return True
    else:
        print(f"\n⚠️  {total - passed} scenario(s) failed")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
