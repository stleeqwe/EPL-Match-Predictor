"""
Parameter Adjuster v2.0
Adjusts simulation parameters based on bias and narrative analysis

핵심 기능:
1. 편향 분석 기반 파라미터 조정
2. 서사 불일치 해결
3. AI 추천 적용
"""

import logging
from typing import Dict, Optional
import json

from ai.ai_factory import get_ai_client

logger = logging.getLogger(__name__)


class ParameterAdjuster:
    """
    Adjusts simulation parameters to reduce bias and improve narrative alignment.

    Adjustment strategies:
    - Goal distribution skew → adjust attack/defense modifiers
    - Outcome probability deviation → adjust morale
    - Tempo misalignment → adjust tempo modifier
    - Scoreline unrealism → adjust shot conversion
    """

    def __init__(self):
        """Initialize parameter adjuster."""
        self.ai_client = get_ai_client()
        logger.info("ParameterAdjuster initialized")

    def adjust_parameters(
        self,
        current_parameters: Dict,
        bias_analysis: Dict,
        narrative_analysis: Dict,
        use_ai: bool = True
    ) -> Dict:
        """
        Adjust parameters to reduce bias and improve narrative alignment.

        Args:
            current_parameters: Current simulation parameters
            bias_analysis: Bias detection report
            narrative_analysis: Narrative alignment report
            use_ai: Whether to use AI for adjustment (default True)

        Returns:
            Adjusted parameters dict (same format as input)
        """
        logger.info("Adjusting parameters based on bias and narrative analysis")

        if use_ai:
            # Use AI for intelligent adjustment
            adjusted = self._ai_adjust_parameters(
                current_parameters,
                bias_analysis,
                narrative_analysis
            )
        else:
            # Use rule-based adjustment
            adjusted = self._rule_based_adjust(
                current_parameters,
                bias_analysis,
                narrative_analysis
            )

        logger.info("Parameter adjustment complete")
        return adjusted

    def _ai_adjust_parameters(
        self,
        current_params: Dict,
        bias: Dict,
        narrative: Dict
    ) -> Dict:
        """
        Use AI to intelligently adjust parameters.

        Returns:
            Adjusted parameters
        """
        try:
            # Build adjustment prompt
            prompt = self._build_adjustment_prompt(current_params, bias, narrative)

            system_prompt = """당신은 시뮬레이션 파라미터 조정 전문가입니다.

**임무**: 편향 분석과 서사 불일치를 해결하기 위해 파라미터를 조정합니다.

**출력 형식** (반드시 유효한 JSON):
```json
{
  "simulation_parameters": {
    "home_attack_modifier": 1.0,
    "away_attack_modifier": 1.0,
    "home_defense_modifier": 1.0,
    "away_defense_modifier": 1.0,
    "home_morale": 1.0,
    "away_morale": 1.0,
    "tempo_modifier": 1.0,
    "shot_conversion_modifier": 1.0,
    "expected_scenario": "balanced_standard"
  },
  "adjustment_reasoning": "조정 근거...",
  "expected_improvement": "예상 개선 효과..."
}
```

**조정 원칙**:
1. **작은 조정**: 한 번에 5-15% 조정 (0.05-0.15 변화)
2. **목표 지향**: 편향 점수 감소 및 서사 일치율 증가에 초점
3. **균형 유지**: 극단적 값(0.5 미만, 1.5 초과) 피하기
4. **인과 관계**: 문제와 해결책의 논리적 연결

**조정 전략**:
- 득점 과다 → attack_modifier 또는 shot_conversion 하향
- 득점 과소 → attack_modifier 또는 shot_conversion 상향
- 홈 승률 과다 → home_morale 하향 또는 away_morale 상향
- 템포 불일치 → tempo_modifier 조정
"""

            response = self.ai_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.5,
                max_tokens=1500
            )

            if not response:
                logger.warning("AI adjustment failed, using rule-based fallback")
                return self._rule_based_adjust(current_params, bias, narrative)

            # Parse JSON
            response_text = response.strip()
            if '```json' in response_text:
                start = response_text.find('```json') + 7
                end = response_text.find('```', start)
                response_text = response_text[start:end].strip()
            elif '```' in response_text:
                start = response_text.find('```') + 3
                end = response_text.find('```', start)
                response_text = response_text[start:end].strip()

            adjusted_params = json.loads(response_text)

            # Validate and return
            self._validate_and_clamp(adjusted_params['simulation_parameters'])
            return adjusted_params

        except Exception as e:
            logger.error(f"AI adjustment error: {e}")
            return self._rule_based_adjust(current_params, bias, narrative)

    def _rule_based_adjust(
        self,
        current_params: Dict,
        bias: Dict,
        narrative: Dict
    ) -> Dict:
        """
        Rule-based parameter adjustment (fallback).

        Returns:
            Adjusted parameters
        """
        params = current_params.get('simulation_parameters', {}).copy()

        # Extract issues
        bias_issues = {issue['type']: issue for issue in bias.get('issues', [])}
        narrative_issues = {issue['type']: issue for issue in narrative.get('misalignments', [])}

        adjustments = []

        # Handle goal distribution skew
        if 'goal_distribution_skew' in bias_issues:
            issue = bias_issues['goal_distribution_skew']
            if '과소' in issue['description']:
                # Increase scoring
                params['home_attack_modifier'] = min(1.5, params.get('home_attack_modifier', 1.0) * 1.10)
                params['away_attack_modifier'] = min(1.5, params.get('away_attack_modifier', 1.0) * 1.10)
                adjustments.append("득점 과소 → 공격력 10% 증가")
            else:
                # Decrease scoring
                params['home_attack_modifier'] = max(0.5, params.get('home_attack_modifier', 1.0) * 0.90)
                params['away_attack_modifier'] = max(0.5, params.get('away_attack_modifier', 1.0) * 0.90)
                adjustments.append("득점 과다 → 공격력 10% 감소")

        # Handle outcome probability deviation
        if 'outcome_probability_deviation' in bias_issues:
            issue = bias_issues['outcome_probability_deviation']
            if '높음' in issue['description']:
                # Reduce home advantage
                params['home_morale'] = max(0.8, params.get('home_morale', 1.0) * 0.95)
                adjustments.append("홈 승률 높음 → 홈 morale 5% 감소")
            elif '낮음' in issue['description']:
                # Increase home advantage
                params['home_morale'] = min(1.2, params.get('home_morale', 1.0) * 1.05)
                adjustments.append("홈 승률 낮음 → 홈 morale 5% 증가")

        # Handle tempo misalignment
        if 'tempo_misalignment' in narrative_issues:
            issue = narrative_issues['tempo_misalignment']
            if '낮음' in issue['description']:
                params['tempo_modifier'] = min(1.2, params.get('tempo_modifier', 1.0) * 1.10)
                adjustments.append("템포 낮음 → tempo_modifier 10% 증가")
            elif '높음' in issue['description']:
                params['tempo_modifier'] = max(0.8, params.get('tempo_modifier', 1.0) * 0.90)
                adjustments.append("템포 높음 → tempo_modifier 10% 감소")

        # Handle goal misalignment (narrative)
        if 'goal_misalignment' in narrative_issues:
            issue = narrative_issues['goal_misalignment']
            if '과소' in issue['description']:
                params['shot_conversion_modifier'] = min(1.2, params.get('shot_conversion_modifier', 1.0) * 1.08)
                adjustments.append("득점 과소 (서사) → shot_conversion 8% 증가")
            elif '과다' in issue['description']:
                params['shot_conversion_modifier'] = max(0.8, params.get('shot_conversion_modifier', 1.0) * 0.92)
                adjustments.append("득점 과다 (서사) → shot_conversion 8% 감소")

        adjustment_reasoning = '; '.join(adjustments) if adjustments else "No significant adjustments needed"

        return {
            'simulation_parameters': params,
            'adjustment_reasoning': adjustment_reasoning,
            'expected_improvement': "파라미터 조정으로 편향 감소 및 서사 일치율 증가 기대"
        }

    def _build_adjustment_prompt(
        self,
        current_params: Dict,
        bias: Dict,
        narrative: Dict
    ) -> str:
        """Build prompt for AI parameter adjustment."""
        params = current_params.get('simulation_parameters', {})

        prompt = f"""시뮬레이션 파라미터 조정이 필요합니다.

**현재 파라미터**:
```json
{json.dumps(params, indent=2, ensure_ascii=False)}
```

**편향 분석 결과**:
- 편향 점수: {bias['bias_score']}
- 평가: {bias['overall_assessment']}
- 문제점:
"""
        for issue in bias.get('issues', []):
            prompt += f"  - [{issue['severity']}] {issue['type']}: {issue['description']}\n"

        prompt += f"""
**서사 분석 결과**:
- 예상 시나리오: {narrative['expected_scenario']}
- 일치율: {narrative['narrative_alignment']}%
- 평가: {narrative['assessment']}
- 불일치:
"""
        for issue in narrative.get('misalignments', []):
            prompt += f"  - {issue['type']}: {issue['description']}\n"

        prompt += """
위 분석을 바탕으로 파라미터를 조정하여 편향을 줄이고 서사 일치율을 높이세요.
JSON 형식으로 조정된 파라미터를 출력하세요.
"""

        return prompt

    def _validate_and_clamp(self, params: Dict) -> None:
        """
        Validate and clamp parameters to acceptable ranges.

        Args:
            params: Parameters to validate (modified in-place)
        """
        # Clamp all modifiers to 0.5-1.5 range
        modifier_keys = [
            'home_attack_modifier', 'away_attack_modifier',
            'home_defense_modifier', 'away_defense_modifier',
            'tempo_modifier', 'shot_conversion_modifier'
        ]
        for key in modifier_keys:
            if key in params:
                params[key] = max(0.5, min(1.5, params[key]))

        # Clamp morale to 0.8-1.2 range
        for key in ['home_morale', 'away_morale']:
            if key in params:
                params[key] = max(0.8, min(1.2, params[key]))


def get_parameter_adjuster() -> ParameterAdjuster:
    """
    Get parameter adjuster instance.

    Returns:
        ParameterAdjuster instance
    """
    return ParameterAdjuster()
