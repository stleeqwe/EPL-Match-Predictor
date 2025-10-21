"""
AI Analyzer (Enhanced)
설계 문서 Section 3 (Phase 3) 정확 구현

시뮬레이션 결과 분석 및 조정 제안
"""

import json
import logging
import re
from typing import Dict, List, Optional, Tuple

from ai.ai_factory import get_ai_client
from .scenario import Scenario
from .event_simulation_engine import EPL_BASELINE

logger = logging.getLogger(__name__)


class AIAnalyzer:
    """
    AI 기반 시뮬레이션 분석기
    설계 문서 Phase 3 구현

    역할:
    1. 편향 감지 (득점, 승률, 이벤트)
    2. 서사 일치율 분석
    3. 파라미터 조정 제안
    4. 시나리오 품질 평가
    5. 수렴 판정
    """

    def __init__(self, model: str = None):
        """
        Args:
            model: AI model name (optional, uses AI_PROVIDER from .env if not specified)
        """
        self.ai_client = get_ai_client()  # Uses AI_PROVIDER from .env
        model_info = self.ai_client.get_model_info()
        logger.info(f"AIAnalyzer initialized with {model_info['provider']}: {model_info['model']}")

    def analyze_and_adjust(
        self,
        scenarios: List[Scenario],
        validation_results: List[Dict],
        iteration: int
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        시뮬레이션 결과 분석 및 조정 제안

        Args:
            scenarios: 현재 시나리오 리스트
            validation_results: Phase 2 검증 결과
            iteration: 현재 반복 횟수

        Returns:
            Tuple of (success, analysis_dict, error_message)
        """
        try:
            # 1. Build prompt
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_analysis_prompt(
                scenarios,
                validation_results,
                iteration
            )

            # 2. Call AI
            logger.info(f"Calling AI for analysis (iteration {iteration})...")
            success, response_text, usage_data, error = self.ai_client.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.7,  # Lower for analytical tasks
                max_tokens=4000
            )

            if not success:
                logger.error(f"AI analysis failed: {error}")
                return False, None, error

            logger.info(f"AI analysis received ({usage_data['total_tokens']:.0f} tokens)")

            # 3. Parse JSON response
            analysis = self._parse_analysis(response_text)

            if not analysis:
                return False, None, "Failed to parse analysis from AI response"

            # Extract issues from nested structure
            issues = analysis.get('analysis', {}).get('issues', [])
            logger.info(f"✓ Analysis complete: {len(issues)} issues detected")
            logger.info(f"✓ Convergence: {analysis.get('convergence', {}).get('converged', False)}")

            return True, analysis, None

        except Exception as e:
            error_msg = f"Analysis error: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg

    def _build_system_prompt(self) -> str:
        """
        시스템 프롬프트 (설계 문서 기반)
        """
        return """You are an expert simulation quality control AI.

Your role is to analyze simulation results and provide actionable adjustments.

IMPORTANT RULES:
1. You MUST respond with ONLY a valid JSON object
2. Identify ALL issues (bias, narrative adherence, etc.)
3. Provide specific adjustment values (not vague suggestions)
4. Judge convergence based on the criteria provided
5. Be conservative with convergence (only converge when truly ready)

Output format:
{
  "iteration": 1,
  "analysis": {
    "issues": [
      {
        "scenario_id": "SYNTH_001",
        "issue_type": "score_bias",
        "severity": "high",
        "description": "Average goals 2.46, EPL baseline 2.8 (-12%)",
        "root_cause": "shot_per_minute or goal_conversion too low",
        "adjustment": {
          "parameter": "shot_per_minute",
          "current_value": 0.165,
          "proposed_value": 0.180,
          "expected_impact": "Goals 2.46 → 2.7"
        }
      },
      {
        "scenario_id": "SYNTH_002",
        "issue_type": "narrative_adherence_low",
        "severity": "high",
        "description": "Narrative adherence 22%, target 75%",
        "root_cause": "probability_boost insufficient for expected events",
        "adjustment": {
          "parameter": "events[0].probability_boost",
          "current_value": 2.3,
          "proposed_value": 2.8,
          "expected_impact": "Adherence 22% → 60%"
        }
      }
    ],
    "global_adjustments": {
      "goal_rate_global_multiplier": {
        "current": 1.0,
        "proposed": 1.15,
        "reason": "Overall goals 2.46, need to reach 2.8"
      }
    },
    "scenario_recommendations": {
      "merge": [],
      "remove": []
    }
  },
  "convergence": {
    "converged": false,
    "confidence": 0.65,
    "criteria_met": ["score_range_check"],
    "criteria_failed": ["narrative_adherence", "bias_threshold"],
    "estimated_iterations_needed": 2,
    "recommendation": "2 more iterations recommended"
  }
}

ONLY return the JSON. No explanations."""

    def _build_analysis_prompt(
        self,
        scenarios: List[Scenario],
        validation_results: List[Dict],
        iteration: int
    ) -> str:
        """
        분석 프롬프트 생성 (설계 문서 Section 3)
        """
        prompt_parts = [
            f"# Iteration {iteration} Analysis\n",
            "Analyze the simulation results and provide adjustments.\n"
        ]

        # EPL baseline
        prompt_parts.append(f"\n## EPL Baseline Statistics:")
        prompt_parts.append(f"- Average goals: {EPL_BASELINE['avg_goals_per_game']:.1f} per match")
        prompt_parts.append(f"- Home win rate: {EPL_BASELINE['home_win_rate']:.0%}")
        prompt_parts.append(f"- Draw rate: {EPL_BASELINE['draw_rate']:.0%}")
        prompt_parts.append(f"- Away win rate: {EPL_BASELINE['away_win_rate']:.0%}")
        prompt_parts.append(f"- Shots per game: {EPL_BASELINE['shots_per_game']:.1f}")
        prompt_parts.append(f"- Shot on target ratio: {EPL_BASELINE['shot_on_target_ratio']:.0%}")

        # Validation results
        prompt_parts.append(f"\n## Simulation Results ({len(validation_results)} scenarios):")

        for i, result in enumerate(validation_results, 1):
            prompt_parts.append(f"\n### Scenario {i}: {result['scenario_name']}")
            prompt_parts.append(f"ID: {result['scenario_id']}")
            prompt_parts.append(f"Runs: {result['total_runs']}")

            # Win rates
            wr = result['win_rate']
            prompt_parts.append(f"Win rates: H={wr['home']:.1%}, D={wr['draw']:.1%}, A={wr['away']:.1%}")

            # Average score
            avg = result['avg_score']
            total = avg['home'] + avg['away']
            prompt_parts.append(f"Avg score: {avg['home']:.2f}-{avg['away']:.2f} (total: {total:.2f})")

            # Narrative adherence
            na = result['narrative_adherence']
            prompt_parts.append(f"Narrative adherence: {na['mean']:.1%} (std: {na['std']:.3f})")

            # Bias metrics
            bias = result['bias_metrics']
            prompt_parts.append(f"Score bias: {bias['score_bias']:.1%}")
            prompt_parts.append(f"Home advantage bias: {bias['home_advantage_bias']:.1%}")

        # Overall statistics
        avg_goals = sum(r['avg_score']['home'] + r['avg_score']['away'] for r in validation_results) / len(validation_results)
        avg_adherence = sum(r['narrative_adherence']['mean'] for r in validation_results) / len(validation_results)
        avg_score_bias = sum(r['bias_metrics']['score_bias'] for r in validation_results) / len(validation_results)

        prompt_parts.append(f"\n## Overall Statistics:")
        prompt_parts.append(f"- Average total goals: {avg_goals:.2f} (EPL: {EPL_BASELINE['avg_goals_per_game']:.1f})")
        prompt_parts.append(f"- Average narrative adherence: {avg_adherence:.1%} (target: 75%)")
        prompt_parts.append(f"- Average score bias: {avg_score_bias:.1%} (target: <10%)")

        # Analysis tasks
        prompt_parts.append(f"\n## Analysis Tasks:")
        prompt_parts.append("1. **Bias Detection**:")
        prompt_parts.append("   - Is average goals within 2.2-3.4 range?")
        prompt_parts.append("   - Are win rates within EPL ±10%?")
        prompt_parts.append("   - Is score bias < 10%?")

        prompt_parts.append("\n2. **Narrative Adherence Analysis**:")
        prompt_parts.append("   - Which scenarios have adherence < 75%?")
        prompt_parts.append("   - Why is adherence low? (probability_boost insufficient?)")
        prompt_parts.append("   - Suggest specific boost increases")

        prompt_parts.append("\n3. **Parameter Adjustments**:")
        prompt_parts.append("   - For each issue, provide:")
        prompt_parts.append("     * Specific parameter name")
        prompt_parts.append("     * Current value")
        prompt_parts.append("     * Proposed value (not ratio)")
        prompt_parts.append("     * Expected impact")

        prompt_parts.append("\n4. **Convergence Judgment**:")
        prompt_parts.append("   Criteria for convergence:")
        prompt_parts.append("   - [ ] All scenarios avg goals 2.2-3.4")
        prompt_parts.append("   - [ ] All scenarios bias < 10%")
        prompt_parts.append("   - [ ] All scenarios narrative adherence > 75%")
        prompt_parts.append("   - [ ] Win rates within EPL ±10%")
        prompt_parts.append("   - [ ] Changes from previous iteration < 5%")
        prompt_parts.append("   Only converge if ALL criteria met.")

        prompt_parts.append("\nProvide analysis in JSON format. ONLY JSON, nothing else.")

        return "\n".join(prompt_parts)

    def _parse_analysis(self, response_text: str) -> Optional[Dict]:
        """
        AI 응답을 분석 딕셔너리로 파싱
        """
        try:
            # Extract JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response_text.strip()

            # Parse JSON
            analysis = json.loads(json_str)

            # Validate structure
            required_keys = ['analysis', 'convergence']
            if not all(key in analysis for key in required_keys):
                logger.error(f"Missing required keys in analysis: {required_keys}")
                return None

            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            logger.error(f"Response: {response_text[:500]}")
            return None
        except Exception as e:
            logger.error(f"Analysis parsing error: {e}")
            return None


def apply_adjustments(
    scenarios: List[Scenario],
    ai_analysis: Dict
) -> List[Scenario]:
    """
    AI 조정 제안을 시나리오에 적용

    Args:
        scenarios: 현재 시나리오 리스트
        ai_analysis: AI 분석 결과

    Returns:
        조정된 시나리오 리스트
    """
    logger.info("Applying AI adjustments...")

    # Safely extract issues
    analysis_section = ai_analysis.get('analysis', {})
    if not analysis_section:
        logger.warning("No 'analysis' section in AI response, returning scenarios unchanged")
        return scenarios

    issues = analysis_section.get('issues', [])
    if not issues:
        logger.info("No issues detected, returning scenarios unchanged")
        return scenarios

    adjusted_scenarios = []

    # Process each scenario
    for scenario in scenarios:
        # Find issues for this scenario
        scenario_issues = [
            issue for issue in issues
            if issue and issue.get('scenario_id') == scenario.id
        ]

        if not scenario_issues:
            # No issues for this scenario, keep as is
            adjusted_scenarios.append(scenario)
            continue

        # Clone scenario
        adjusted_scenario = Scenario(
            id=scenario.id,
            name=scenario.name,
            reasoning=scenario.reasoning,
            events=scenario.events.copy(),
            parameter_adjustments=scenario.parameter_adjustments.copy(),
            expected_probability=scenario.expected_probability,
            base_narrative=scenario.base_narrative
        )

        # Apply adjustments
        for issue in scenario_issues:
            adjustment = issue.get('adjustment', {})
            param_name = adjustment.get('parameter', '')
            proposed_value = adjustment.get('proposed_value')

            if not param_name or proposed_value is None:
                continue

            # Apply adjustment based on parameter type
            if 'probability_boost' in param_name and 'events[' in param_name:
                # Extract event index
                try:
                    idx_str = param_name.split('[')[1].split(']')[0]
                    event_idx = int(idx_str)

                    if 0 <= event_idx < len(adjusted_scenario.events):
                        # Update probability_boost
                        old_boost = adjusted_scenario.events[event_idx].probability_boost
                        adjusted_scenario.events[event_idx].probability_boost = proposed_value
                        logger.info(f"  ✓ {scenario.id}: events[{event_idx}].probability_boost "
                                   f"{old_boost:.2f} → {proposed_value:.2f}")
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse event index from {param_name}: {e}")

            elif param_name in adjusted_scenario.parameter_adjustments:
                # Update parameter adjustment
                old_value = adjusted_scenario.parameter_adjustments[param_name]
                adjusted_scenario.parameter_adjustments[param_name] = proposed_value
                logger.info(f"  ✓ {scenario.id}: {param_name} {old_value:.2f} → {proposed_value:.2f}")

        adjusted_scenarios.append(adjusted_scenario)

    # Apply global adjustments (if any)
    global_adjs = ai_analysis['analysis'].get('global_adjustments', {})
    if global_adjs:
        logger.info(f"Global adjustments: {len(global_adjs)} found")
        # Note: Global adjustments would modify EPL_BASELINE or engine parameters
        # For now, we log them but don't apply (would need engine refactoring)

    # Handle scenario merge/remove recommendations
    recommendations = ai_analysis['analysis'].get('scenario_recommendations', {})

    # Remove scenarios
    remove_ids = [r['scenario'] for r in recommendations.get('remove', [])]
    if remove_ids:
        adjusted_scenarios = [s for s in adjusted_scenarios if s.id not in remove_ids]
        logger.info(f"  ✓ Removed {len(remove_ids)} scenarios: {remove_ids}")

    # Merge scenarios (simplified: just remove duplicates for now)
    merge_groups = recommendations.get('merge', [])
    if merge_groups:
        logger.info(f"  ⚠ Merge recommendations found but not implemented yet: {len(merge_groups)}")

    logger.info(f"✓ Adjustments applied: {len(adjusted_scenarios)} scenarios")
    return adjusted_scenarios


# Global instance
_analyzer = None


def get_analyzer(model: str = None) -> AIAnalyzer:
    """Get global analyzer instance (singleton)."""
    global _analyzer
    if _analyzer is None:
        _analyzer = AIAnalyzer(model=model)
    return _analyzer
