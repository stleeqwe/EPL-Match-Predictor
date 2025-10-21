"""
Simulation Pipeline
설계 문서 Phase 1-7 완전 통합

AI-Guided Iterative Refinement Pipeline
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .ai_scenario_generator import get_scenario_generator
from .ai_scenario_generator_enriched import get_enriched_scenario_generator
from .multi_scenario_validator import get_validator
from .ai_analyzer import get_analyzer, apply_adjustments
from .event_simulation_engine import create_match_parameters, MatchParameters
from .enriched_helpers import enriched_to_match_params
from .scenario import Scenario
from ai.enriched_data_models import EnrichedTeamInput
from ai.ai_factory import get_ai_client
import json
import re

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """파이프라인 설정"""
    max_iterations: int = 5
    initial_runs: int = 100
    final_runs: int = 3000
    convergence_threshold: float = 0.85


class SimulationPipeline:
    """
    Phase 1-7 완전 구현
    설계 문서 정확 준수
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        """
        Args:
            config: 파이프라인 설정 (기본값 사용 가능)
        """
        self.config = config or PipelineConfig()
        self.scenario_generator = get_scenario_generator()
        self.validator = get_validator()
        self.analyzer = get_analyzer()

        logger.info(f"SimulationPipeline initialized (max_iterations={self.config.max_iterations})")

    def run(
        self,
        match_context: Dict,
        base_params: MatchParameters,
        player_stats: Optional[Dict] = None,
        tactics: Optional[Dict] = None,
        domain_knowledge: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        전체 파이프라인 실행

        Args:
            match_context: {"home_team": "...", "away_team": "..."}
            base_params: 기본 경기 파라미터
            player_stats: 선수 능력치 (선택)
            tactics: 전술 정보 (선택)
            domain_knowledge: 사용자 도메인 지식 (핵심!)

        Returns:
            Tuple of (success, result_dict, error_message)
        """
        try:
            logger.info("="*70)
            logger.info("Simulation Pipeline Started")
            logger.info("="*70)

            # Phase 1: AI 시나리오 생성
            logger.info("\n[Phase 1] AI Scenario Generation")
            logger.info("-"*70)

            success, scenarios, error = self.scenario_generator.generate_scenarios(
                match_context=match_context,
                player_stats=player_stats,
                tactics=tactics,
                domain_knowledge=domain_knowledge
            )

            if not success:
                return False, None, f"Phase 1 failed: {error}"

            logger.info(f"✓ Generated {len(scenarios)} scenarios")

            # Phase 2-5: Iterative Refinement Loop
            logger.info("\n[Phase 2-5] Iterative Refinement Loop")
            logger.info("-"*70)

            iteration = 1
            converged = False
            history = []
            current_scenarios = scenarios

            while not converged and iteration <= self.config.max_iterations:
                logger.info(f"\n>>> Iteration {iteration}/{self.config.max_iterations}")

                # Phase 2: Simulate (100 runs per scenario)
                logger.info(f"  Phase 2: Simulating ({len(current_scenarios)} × {self.config.initial_runs})...")
                validation_results = self.validator.validate_scenarios(
                    scenarios=current_scenarios,
                    base_params=base_params,
                    n=self.config.initial_runs
                )

                # Phase 3: AI Analysis
                logger.info(f"  Phase 3: AI Analysis...")
                success, ai_analysis, error = self.analyzer.analyze_and_adjust(
                    scenarios=current_scenarios,
                    validation_results=validation_results,
                    iteration=iteration
                )

                if not success:
                    logger.warning(f"  ⚠ Analysis failed: {error}")
                    # Continue with current scenarios
                    break

                # Record history
                history.append({
                    "iteration": iteration,
                    "scenarios": current_scenarios,
                    "validation_results": validation_results,
                    "ai_analysis": ai_analysis
                })

                # Phase 5: Convergence Check
                convergence = ai_analysis['convergence']
                logger.info(f"  Phase 5: Convergence Check")
                logger.info(f"    Converged: {convergence['converged']}")
                logger.info(f"    Confidence: {convergence['confidence']:.1%}")

                if convergence['converged'] and convergence['confidence'] >= self.config.convergence_threshold:
                    converged = True
                    logger.info(f"  ✓ Convergence achieved!")
                    break

                # Phase 4: Apply Adjustments
                logger.info(f"  Phase 4: Applying adjustments...")
                current_scenarios = apply_adjustments(current_scenarios, ai_analysis)
                logger.info(f"    → {len(current_scenarios)} scenarios adjusted")

                iteration += 1

            if not converged:
                logger.warning(f"\n⚠ Max iterations reached without convergence")
                logger.info(f"  Proceeding with best available scenarios")

            # Phase 6: Final High-Resolution Simulation
            logger.info(f"\n[Phase 6] Final High-Resolution Simulation")
            logger.info("-"*70)
            logger.info(f"  Simulating ({len(current_scenarios)} × {self.config.final_runs})...")

            final_results = self.validator.validate_scenarios(
                scenarios=current_scenarios,
                base_params=base_params,
                n=self.config.final_runs
            )

            logger.info(f"✓ Completed {len(current_scenarios) * self.config.final_runs} simulations")

            # Phase 7: AI Final Report
            logger.info(f"\n[Phase 7] AI Final Report")
            logger.info("-"*70)

            # Try AI-powered report first, fallback to simplified if it fails
            success, final_report, error = self._build_ai_final_report(
                current_scenarios,
                final_results,
                history,
                match_context
            )

            if not success:
                logger.warning(f"  AI report generation failed: {error}")
                logger.info("  Falling back to simplified report")
                final_report = self._build_simplified_report(
                    current_scenarios,
                    final_results,
                    history,
                    match_context
                )
                final_report['report_type'] = 'simplified'

            # Compile final output
            output = {
                "scenarios": [s.to_dict() for s in current_scenarios],
                "final_results": final_results,
                "report": final_report,
                "history": history,
                "converged": converged,
                "iterations": iteration - 1 if converged else iteration,
                "metadata": {
                    "home_team": match_context.get("home_team"),
                    "away_team": match_context.get("away_team"),
                    "total_simulations": (iteration - 1) * len(scenarios) * self.config.initial_runs + len(current_scenarios) * self.config.final_runs
                }
            }

            logger.info("\n" + "="*70)
            logger.info("Simulation Pipeline Completed Successfully")
            logger.info("="*70)

            return True, output, None

        except Exception as e:
            error_msg = f"Pipeline error: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg

    def _build_simplified_report(
        self,
        scenarios: List[Scenario],
        final_results: List[Dict],
        history: List[Dict],
        match_context: Dict
    ) -> Dict:
        """
        간소화된 최종 리포트 생성
        (Phase 7의 완전한 AI 리포트는 추후 구현)
        """
        # Calculate weighted probabilities
        total_prob = sum(s.expected_probability for s in scenarios)
        if total_prob > 0:
            normalized_probs = [s.expected_probability / total_prob for s in scenarios]
        else:
            normalized_probs = [1.0 / len(scenarios)] * len(scenarios)

        # Weighted average predictions
        weighted_home_wins = sum(
            r['win_rate']['home'] * prob
            for r, prob in zip(final_results, normalized_probs)
        )
        weighted_draws = sum(
            r['win_rate']['draw'] * prob
            for r, prob in zip(final_results, normalized_probs)
        )
        weighted_away_wins = sum(
            r['win_rate']['away'] * prob
            for r, prob in zip(final_results, normalized_probs)
        )

        weighted_home_goals = sum(
            r['avg_score']['home'] * prob
            for r, prob in zip(final_results, normalized_probs)
        )
        weighted_away_goals = sum(
            r['avg_score']['away'] * prob
            for r, prob in zip(final_results, normalized_probs)
        )

        # Find most likely scenario
        most_likely_scenario = max(zip(scenarios, normalized_probs), key=lambda x: x[1])

        # Build report
        report = {
            "match": {
                "home_team": match_context.get("home_team"),
                "away_team": match_context.get("away_team")
            },
            "prediction": {
                "win_probabilities": {
                    "home": weighted_home_wins,
                    "draw": weighted_draws,
                    "away": weighted_away_wins
                },
                "expected_goals": {
                    "home": weighted_home_goals,
                    "away": weighted_away_goals
                },
                "most_likely_outcome": self._determine_outcome(
                    weighted_home_wins,
                    weighted_draws,
                    weighted_away_wins
                )
            },
            "dominant_scenario": {
                "id": most_likely_scenario[0].id,
                "name": most_likely_scenario[0].name,
                "probability": most_likely_scenario[1],
                "reasoning": most_likely_scenario[0].reasoning
            },
            "all_scenarios": [
                {
                    "id": s.id,
                    "name": s.name,
                    "probability": prob,
                    "win_rate": final_results[i]['win_rate'],
                    "avg_score": final_results[i]['avg_score']
                }
                for i, (s, prob) in enumerate(zip(scenarios, normalized_probs))
            ],
            "convergence_summary": {
                "iterations": len(history),
                "converged": len(history) > 0 and history[-1]['ai_analysis']['convergence']['converged'],
                "final_confidence": history[-1]['ai_analysis']['convergence']['confidence'] if history else 0.0
            }
        }

        return report

    def _determine_outcome(self, home: float, draw: float, away: float) -> str:
        """가장 가능성 높은 결과 판정"""
        if home > draw and home > away:
            return "home_win"
        elif away > draw and away > home:
            return "away_win"
        else:
            return "draw"

    def _build_ai_final_report(
        self,
        scenarios: List[Scenario],
        final_results: List[Dict],
        history: List[Dict],
        match_context: Dict
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        AI 기반 최종 리포트 생성 (Phase 7 완전 구현)

        Args:
            scenarios: 최종 시나리오 리스트
            final_results: Phase 6 결과
            history: 반복 history
            match_context: 매치 컨텍스트

        Returns:
            Tuple of (success, report_dict, error_message)
        """
        try:
            # 1. Build AI prompt
            system_prompt = self._build_ai_report_system_prompt()
            user_prompt = self._build_ai_report_user_prompt(
                scenarios,
                final_results,
                history,
                match_context
            )

            # 2. Call AI
            logger.info("  Generating AI-powered final report...")
            ai_client = get_ai_client()  # Uses AI_PROVIDER from .env

            success, response_text, usage_data, error = ai_client.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=2000
            )

            if not success:
                logger.warning(f"  AI report generation failed: {error}")
                return False, None, error

            logger.info(f"  AI report generated ({usage_data['total_tokens']:.0f} tokens)")

            # 3. Parse AI response
            ai_report = self._parse_ai_report(response_text)

            if not ai_report:
                return False, None, "Failed to parse AI report"

            # 4. Build complete report with AI analysis
            simplified_report = self._build_simplified_report(
                scenarios,
                final_results,
                history,
                match_context
            )

            # Merge AI analysis into simplified report
            simplified_report['ai_analysis'] = ai_report
            simplified_report['report_type'] = 'ai_enhanced'

            logger.info("  ✓ AI-enhanced report complete")
            return True, simplified_report, None

        except Exception as e:
            error_msg = f"AI report generation error: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg

    def _build_ai_report_system_prompt(self) -> str:
        """AI 리포트 생성용 시스템 프롬프트"""
        return """You are an expert EPL match analysis AI.

Your role is to generate a comprehensive match analysis report based on simulation results.

Output format (JSON only):
{
  "executive_summary": "1-2 sentence summary of the match prediction",
  "tactical_analysis": "5-7 sentences analyzing tactical dynamics, formations, key matchups, etc.",
  "key_moments": [
    "First critical moment description",
    "Second critical moment description",
    "Third critical moment description"
  ],
  "player_highlights": [
    "Key player 1 performance analysis",
    "Key player 2 performance analysis"
  ],
  "statistical_insights": "3-5 sentences on statistical patterns and trends observed",
  "confidence_analysis": "2-3 sentences explaining why the prediction has high/medium/low confidence"
}

ONLY return valid JSON. No additional text."""

    def _build_ai_report_user_prompt(
        self,
        scenarios: List[Scenario],
        final_results: List[Dict],
        history: List[Dict],
        match_context: Dict
    ) -> str:
        """AI 리포트 생성용 사용자 프롬프트"""

        home_team = match_context.get('home_team', 'Home')
        away_team = match_context.get('away_team', 'Away')

        # Calculate weighted stats
        total_prob = sum(s.expected_probability for s in scenarios)
        normalized_probs = [s.expected_probability / total_prob for s in scenarios] if total_prob > 0 else [1.0 / len(scenarios)] * len(scenarios)

        weighted_home_wins = sum(r['win_rate']['home'] * prob for r, prob in zip(final_results, normalized_probs))
        weighted_draws = sum(r['win_rate']['draw'] * prob for r, prob in zip(final_results, normalized_probs))
        weighted_away_wins = sum(r['win_rate']['away'] * prob for r, prob in zip(final_results, normalized_probs))
        weighted_home_goals = sum(r['avg_score']['home'] * prob for r, prob in zip(final_results, normalized_probs))
        weighted_away_goals = sum(r['avg_score']['away'] * prob for r, prob in zip(final_results, normalized_probs))

        most_likely_scenario = max(zip(scenarios, normalized_probs), key=lambda x: x[1])

        prompt_parts = [
            f"# Match Analysis: {home_team} vs {away_team}\n",
            "Generate a comprehensive match analysis report based on the simulation results below.\n",
            f"\n## Prediction Summary:",
            f"- Win Probabilities: Home {weighted_home_wins:.1%}, Draw {weighted_draws:.1%}, Away {weighted_away_wins:.1%}",
            f"- Expected Goals: {weighted_home_goals:.2f} - {weighted_away_goals:.2f}",
            f"\n## Scenarios Analyzed ({len(scenarios)} scenarios, {final_results[0]['total_runs'] if final_results else 0} simulations each):\n"
        ]

        for i, (scenario, prob, result) in enumerate(zip(scenarios, normalized_probs, final_results), 1):
            prompt_parts.append(f"\n**Scenario {i}: {scenario.name}** (probability: {prob:.1%})")
            prompt_parts.append(f"  - Reasoning: {scenario.reasoning}")
            prompt_parts.append(f"  - Win rates: H={result['win_rate']['home']:.1%}, D={result['win_rate']['draw']:.1%}, A={result['win_rate']['away']:.1%}")
            prompt_parts.append(f"  - Avg score: {result['avg_score']['home']:.2f}-{result['avg_score']['away']:.2f}")

        prompt_parts.append(f"\n## Most Likely Scenario:")
        prompt_parts.append(f"**{most_likely_scenario[0].name}** ({most_likely_scenario[1]:.1%} probability)")
        prompt_parts.append(f"{most_likely_scenario[0].reasoning}")

        if history:
            last_iteration = history[-1]
            convergence = last_iteration['ai_analysis']['convergence']
            prompt_parts.append(f"\n## Convergence Info:")
            prompt_parts.append(f"- Iterations: {len(history)}")
            prompt_parts.append(f"- Converged: {convergence['converged']}")
            prompt_parts.append(f"- Final confidence: {convergence['confidence']:.1%}")

        prompt_parts.append("\nGenerate the analysis report in JSON format. Focus on tactical insights, key matchups, and statistical patterns.")

        return "\n".join(prompt_parts)

    def _parse_ai_report(self, response_text: str) -> Optional[Dict]:
        """AI 리포트 응답 파싱"""
        try:
            # Extract JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response_text.strip()

            # Parse JSON
            report = json.loads(json_str)

            # Validate required keys
            required_keys = ['executive_summary', 'tactical_analysis']
            if not all(key in report for key in required_keys):
                logger.warning(f"AI report missing required keys: {required_keys}")
                return None

            return report

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI report: {e}")
            logger.error(f"Response: {response_text[:500]}")
            return None
        except Exception as e:
            logger.error(f"AI report parsing error: {e}")
            return None

    def run_enriched(
        self,
        home_team: EnrichedTeamInput,
        away_team: EnrichedTeamInput,
        match_context: Optional[Dict] = None,
        event_callback=None
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        전체 파이프라인 실행 (Enriched Domain Input)

        Args:
            home_team: 홈팀 Enriched Domain Data
            away_team: 원정팀 Enriched Domain Data
            match_context: 매치 컨텍스트 (optional)
            event_callback: SSE 이벤트 콜백 함수 (optional)
                           Signature: callback(event_type: str, data: dict)

        Returns:
            Tuple of (success, result_dict, error_message)
        """
        try:
            logger.info("="*70)
            logger.info("Enriched Simulation Pipeline Started")
            logger.info("="*70)
            logger.info(f"Match: {home_team.name} vs {away_team.name}")

            # Helper function to emit events
            def emit_event(event_type: str, data: dict):
                if event_callback:
                    event_callback(event_type, data)

            # Convert EnrichedTeamInput to MatchParameters
            base_params = enriched_to_match_params(home_team, away_team)

            # Build match context
            if match_context is None:
                match_context = {}
            match_context['home_team'] = home_team.name
            match_context['away_team'] = away_team.name

            # Phase 1: Enriched AI Scenario Generation
            logger.info("\n[Phase 1] Enriched AI Scenario Generation")
            logger.info("-"*70)

            emit_event('phase1_started', {
                'phase': 1,
                'title': 'Generate Scenarios',
                'message': 'Analyzing team data and generating tactical scenarios...',
                'progress': 0.0
            })

            enriched_generator = get_enriched_scenario_generator()
            success, scenarios, error = enriched_generator.generate_scenarios_enriched(
                home_team=home_team,
                away_team=away_team,
                match_context=match_context
            )

            if not success:
                emit_event('phase1_error', {'error': error})
                return False, None, f"Phase 1 failed: {error}"

            logger.info(f"✓ Generated {len(scenarios)} enriched scenarios")

            emit_event('phase1_complete', {
                'phase': 1,
                'scenarios_count': len(scenarios),
                'scenarios': [{'name': s.name, 'probability': s.expected_probability} for s in scenarios],
                'message': f'Generated {len(scenarios)} tactical scenarios',
                'progress': 0.15
            })

            # Phase 2-5: Iterative Refinement Loop
            logger.info("\n[Phase 2-5] Iterative Refinement Loop")
            logger.info("-"*70)

            emit_event('phase2_5_started', {
                'phase': '2-5',
                'title': 'Iterative Refinement',
                'message': 'Starting iterative scenario validation...',
                'max_iterations': self.config.max_iterations,
                'progress': 0.15
            })

            iteration = 1
            converged = False
            history = []
            current_scenarios = scenarios

            while not converged and iteration <= self.config.max_iterations:
                logger.info(f"\n>>> Iteration {iteration}/{self.config.max_iterations}")

                emit_event('iteration_started', {
                    'iteration': iteration,
                    'max_iterations': self.config.max_iterations,
                    'message': f'Iteration {iteration}/{self.config.max_iterations} started',
                    'progress': 0.15 + (iteration - 1) * (0.70 / self.config.max_iterations)
                })

                # Phase 2: Simulate (100 runs per scenario)
                logger.info(f"  Phase 2: Simulating ({len(current_scenarios)} × {self.config.initial_runs})...")

                emit_event('phase2_validating', {
                    'phase': 2,
                    'iteration': iteration,
                    'message': f'Running {self.config.initial_runs} simulations per scenario...',
                    'scenarios_count': len(current_scenarios),
                    'runs_per_scenario': self.config.initial_runs,
                    'total_runs': len(current_scenarios) * self.config.initial_runs
                })

                validation_results = self.validator.validate_scenarios(
                    scenarios=current_scenarios,
                    base_params=base_params,
                    n=self.config.initial_runs
                )

                emit_event('phase2_complete', {
                    'phase': 2,
                    'iteration': iteration,
                    'message': f'Validation complete for iteration {iteration}'
                })

                # Phase 3: AI Analysis
                logger.info(f"  Phase 3: AI Analysis...")

                emit_event('phase3_analyzing', {
                    'phase': 3,
                    'iteration': iteration,
                    'message': 'AI analyzing scenario performance...'
                })

                success, ai_analysis, error = self.analyzer.analyze_and_adjust(
                    scenarios=current_scenarios,
                    validation_results=validation_results,
                    iteration=iteration
                )

                if not success:
                    logger.warning(f"  ⚠ Analysis failed: {error}")
                    emit_event('phase3_warning', {
                        'phase': 3,
                        'iteration': iteration,
                        'message': f'Analysis failed: {error}. Continuing with current scenarios.'
                    })
                    break

                emit_event('phase3_complete', {
                    'phase': 3,
                    'iteration': iteration,
                    'message': 'AI analysis complete'
                })

                # Record history
                history.append({
                    "iteration": iteration,
                    "scenarios": current_scenarios,
                    "validation_results": validation_results,
                    "ai_analysis": ai_analysis
                })

                # Phase 5: Convergence Check
                convergence = ai_analysis['convergence']
                logger.info(f"  Phase 5: Convergence Check")
                logger.info(f"    Converged: {convergence['converged']}")
                logger.info(f"    Confidence: {convergence['confidence']:.1%}")

                emit_event('convergence_check', {
                    'phase': 5,
                    'iteration': iteration,
                    'converged': convergence['converged'],
                    'confidence': convergence['confidence'],
                    'threshold': self.config.convergence_threshold,
                    'message': f"Confidence: {convergence['confidence']:.1%} (threshold: {self.config.convergence_threshold:.1%})"
                })

                if convergence['converged'] and convergence['confidence'] >= self.config.convergence_threshold:
                    converged = True
                    logger.info(f"  ✓ Convergence achieved!")

                    emit_event('convergence_reached', {
                        'iteration': iteration,
                        'confidence': convergence['confidence'],
                        'message': f'Convergence achieved after {iteration} iterations!',
                        'progress': 0.85
                    })
                    break

                # Phase 4: Apply Adjustments
                logger.info(f"  Phase 4: Applying adjustments...")

                emit_event('phase4_adjusting', {
                    'phase': 4,
                    'iteration': iteration,
                    'message': 'Applying AI-recommended adjustments...'
                })

                current_scenarios = apply_adjustments(current_scenarios, ai_analysis)
                logger.info(f"    → {len(current_scenarios)} scenarios adjusted")

                emit_event('iteration_complete', {
                    'iteration': iteration,
                    'max_iterations': self.config.max_iterations,
                    'scenarios_adjusted': len(current_scenarios),
                    'message': f'Iteration {iteration} complete',
                    'progress': 0.15 + iteration * (0.70 / self.config.max_iterations)
                })

                iteration += 1

            if not converged:
                logger.warning(f"\n⚠ Max iterations reached without convergence")
                logger.info(f"  Proceeding with best available scenarios")

                emit_event('max_iterations_reached', {
                    'iterations': iteration - 1,
                    'max_iterations': self.config.max_iterations,
                    'message': f'Max iterations reached. Proceeding with best scenarios.',
                    'progress': 0.85
                })

            # Phase 6: Final High-Resolution Simulation
            logger.info(f"\n[Phase 6] Final High-Resolution Simulation")
            logger.info("-"*70)
            logger.info(f"  Simulating ({len(current_scenarios)} × {self.config.final_runs})...")

            emit_event('phase6_started', {
                'phase': 6,
                'title': 'Final Simulation',
                'message': f'Running {len(current_scenarios) * self.config.final_runs:,} high-resolution simulations...',
                'scenarios_count': len(current_scenarios),
                'runs_per_scenario': self.config.final_runs,
                'total_runs': len(current_scenarios) * self.config.final_runs,
                'progress': 0.85
            })

            final_results = self.validator.validate_scenarios(
                scenarios=current_scenarios,
                base_params=base_params,
                n=self.config.final_runs
            )

            logger.info(f"✓ Completed {len(current_scenarios) * self.config.final_runs} simulations")

            emit_event('phase6_complete', {
                'phase': 6,
                'message': f'Completed {len(current_scenarios) * self.config.final_runs:,} simulations',
                'progress': 0.95
            })

            # Phase 7: AI Final Report
            logger.info(f"\n[Phase 7] AI Final Report")
            logger.info("-"*70)

            emit_event('phase7_started', {
                'phase': 7,
                'title': 'AI Report Generation',
                'message': 'Generating AI-powered final report...',
                'progress': 0.95
            })

            # Try AI-powered report first, fallback to simplified if it fails
            success, final_report, error = self._build_ai_final_report(
                current_scenarios,
                final_results,
                history,
                match_context
            )

            if not success:
                logger.warning(f"  AI report generation failed: {error}")
                logger.info("  Falling back to simplified report")

                emit_event('ai_report_fallback', {
                    'phase': 7,
                    'message': f'AI report failed, using simplified report'
                })

                final_report = self._build_simplified_report(
                    current_scenarios,
                    final_results,
                    history,
                    match_context
                )
                final_report['report_type'] = 'simplified'

            emit_event('phase7_complete', {
                'phase': 7,
                'message': 'Final report generated',
                'progress': 0.98,
                'report_type': final_report.get('report_type', 'ai_enhanced')
            })

            # Compile final output
            output = {
                "scenarios": [s.to_dict() for s in current_scenarios],
                "final_results": final_results,
                "report": final_report,
                "history": history,
                "converged": converged,
                "iterations": iteration - 1 if converged else iteration,
                "metadata": {
                    "home_team": home_team.name,
                    "away_team": away_team.name,
                    "total_simulations": (iteration - 1) * len(scenarios) * self.config.initial_runs + len(current_scenarios) * self.config.final_runs,
                    "enriched_data_used": True
                }
            }

            logger.info("\n" + "="*70)
            logger.info("Enriched Simulation Pipeline Completed Successfully")
            logger.info("="*70)

            return True, output, None

        except Exception as e:
            error_msg = f"Enriched pipeline error: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg


# Global instance
_pipeline = None


def get_pipeline(config: Optional[PipelineConfig] = None) -> SimulationPipeline:
    """Get global pipeline instance (singleton)."""
    global _pipeline
    if _pipeline is None:
        _pipeline = SimulationPipeline(config=config)
    return _pipeline
