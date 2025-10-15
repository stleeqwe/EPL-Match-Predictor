"""
AI Parameter Generator v2.0
Qwen AI-powered tactical analysis and parameter generation

핵심 기능:
1. 전술 프로파일 분석
2. 사용자 인사이트 → 시뮬레이션 파라미터 변환
3. 예상 시나리오 정의
"""

import json
import logging
from typing import Dict, Optional, Tuple

from ai.ai_factory import get_ai_client

logger = logging.getLogger(__name__)


class AIParameterGenerator:
    """
    AI-powered parameter generator for match simulation.

    Uses Qwen 2.5 32B to:
    - Analyze team tactical profiles
    - Convert user insights to quantitative parameters
    - Define expected match scenario
    """

    def __init__(self):
        """Initialize AI parameter generator."""
        self.ai_client = get_ai_client()
        logger.info("AIParameterGenerator initialized with Qwen AI")

    def generate_parameters(
        self,
        home_team_data: Dict,
        away_team_data: Dict,
        user_insight: Optional[str] = None
    ) -> Tuple[bool, Dict, Optional[str]]:
        """
        Generate simulation parameters from team data and user insight.

        Args:
            home_team_data: Home team tactical data
            away_team_data: Away team tactical data
            user_insight: Optional user analysis
                Example: "Liverpool 공격수 부상, United 새 감독 효과"

        Returns:
            Tuple of (success, parameters_dict, error_message)
            parameters_dict format:
            {
                'simulation_parameters': {
                    'home_attack_modifier': float (0.5-1.5),
                    'away_attack_modifier': float (0.5-1.5),
                    'home_defense_modifier': float (0.5-1.5),
                    'away_defense_modifier': float (0.5-1.5),
                    'home_morale': float (0.8-1.2),
                    'away_morale': float (0.8-1.2),
                    'tempo_modifier': float (0.8-1.2),
                    'shot_conversion_modifier': float (0.8-1.2),
                    'expected_scenario': str
                },
                'ai_reasoning': str,
                'confidence': str
            }
        """
        logger.info(f"Generating parameters: {home_team_data['name']} vs {away_team_data['name']}")

        try:
            # Build prompt
            prompt = self._build_parameter_generation_prompt(
                home_team_data,
                away_team_data,
                user_insight
            )

            system_prompt = """당신은 EPL 경기 시뮬레이션 전문가입니다.

**임무**: 팀 전술 프로파일과 사용자 인사이트를 분석하여 시뮬레이션 파라미터를 생성합니다.

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
  "ai_reasoning": "상세한 분석 및 근거...",
  "confidence": "high"
}
```

**파라미터 범위**:
- attack/defense_modifier: 0.5-1.5 (1.0 = 정상, 0.75 = 주요 선수 부상, 1.25 = 컨디션 최상)
- morale: 0.8-1.2 (1.0 = 보통, 0.85 = 연패 중, 1.15 = 새 감독 효과)
- tempo_modifier: 0.8-1.2 (1.0 = 보통, 0.85 = 수비적, 1.15 = 공격적)
- shot_conversion_modifier: 0.8-1.2 (1.0 = 보통, 0.9 = 결정력 부족, 1.1 = 핫스트라이크)

**expected_scenario 옵션**:
- "balanced_standard": 균형잡힌 일반적 경기
- "high_tempo_low_scoring": 치열하지만 저득점
- "high_scoring": 양팀 다득점 예상
- "defensive_low_scoring": 수비적 저득점
- "one_sided_domination": 일방적 우세

**사용자 인사이트 반영**:
사용자가 제공한 정보(부상, 새 감독, 컨디션 등)를 **반드시 정량적 파라미터로 변환**하세요.

예: "Liverpool 공격수 부상" → home_attack_modifier: 0.75
예: "United 새 감독 효과" → away_morale: 1.15
"""

            # Call AI
            response = self.ai_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.6,
                max_tokens=1500
            )

            if not response:
                return False, {}, "AI response empty"

            # Parse JSON
            try:
                # Extract JSON from markdown code blocks if present
                response_text = response.strip()
                if '```json' in response_text:
                    start = response_text.find('```json') + 7
                    end = response_text.find('```', start)
                    response_text = response_text[start:end].strip()
                elif '```' in response_text:
                    start = response_text.find('```') + 3
                    end = response_text.find('```', start)
                    response_text = response_text[start:end].strip()

                parameters = json.loads(response_text)

                # Validate parameters
                valid, error_msg = self._validate_parameters(parameters)
                if not valid:
                    logger.warning(f"Invalid parameters: {error_msg}")
                    # Return default parameters
                    parameters = self._get_default_parameters()

                logger.info(f"Parameters generated successfully: {parameters['expected_scenario']}")
                return True, parameters, None

            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {e}, Response: {response}")
                # Fallback to default parameters
                parameters = self._get_default_parameters()
                return True, parameters, None

        except Exception as e:
            logger.error(f"Parameter generation error: {e}")
            # Return default parameters on error
            parameters = self._get_default_parameters()
            return True, parameters, None

    def _build_parameter_generation_prompt(
        self,
        home_team_data: Dict,
        away_team_data: Dict,
        user_insight: Optional[str]
    ) -> str:
        """Build prompt for AI parameter generation."""
        home_name = home_team_data.get('name', 'Home Team')
        away_name = away_team_data.get('name', 'Away Team')

        # Extract tactical profiles
        home_profile = home_team_data.get('tactical_profile', {})
        away_profile = away_team_data.get('tactical_profile', {})

        prompt = f"""EPL 경기 시뮬레이션 파라미터를 생성합니다.

**경기**: {home_name} (홈) vs {away_name} (원정)

**{home_name} 전술 프로파일**:
- 공격 효율: {home_profile.get('attacking_efficiency', 75)}/100
- 수비 안정성: {home_profile.get('defensive_stability', 75)}/100
- 전술 조직력: {home_profile.get('tactical_organization', 75)}/100
- 체력/스태미나: {home_profile.get('physicality_stamina', 75)}/100
- 심리적 요소: {home_profile.get('psychological_factors', 75)}/100

**{away_name} 전술 프로파일**:
- 공격 효율: {away_profile.get('attacking_efficiency', 75)}/100
- 수비 안정성: {away_profile.get('defensive_stability', 75)}/100
- 전술 조직력: {away_profile.get('tactical_organization', 75)}/100
- 체력/스태미나: {away_profile.get('physicality_stamina', 75)}/100
- 심리적 요소: {away_profile.get('psychological_factors', 75)}/100
"""

        if user_insight:
            prompt += f"""
**사용자 인사이트**:
{user_insight}

→ 이 정보를 반드시 파라미터에 반영하세요 (정량적으로!)
"""
        else:
            prompt += """
**사용자 인사이트**: 없음 (기본 전술 분석만 수행)
"""

        prompt += """

위 정보를 바탕으로 시뮬레이션 파라미터를 JSON 형식으로 생성하세요.
"""

        return prompt

    def _validate_parameters(self, parameters: Dict) -> Tuple[bool, Optional[str]]:
        """
        Validate generated parameters.

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            sim_params = parameters.get('simulation_parameters', {})

            # Check required keys
            required_keys = [
                'home_attack_modifier', 'away_attack_modifier',
                'home_defense_modifier', 'away_defense_modifier',
                'home_morale', 'away_morale',
                'tempo_modifier', 'shot_conversion_modifier',
                'expected_scenario'
            ]

            for key in required_keys:
                if key not in sim_params:
                    return False, f"Missing key: {key}"

            # Validate ranges
            for key in required_keys[:-1]:  # Exclude expected_scenario
                value = sim_params[key]
                if not isinstance(value, (int, float)):
                    return False, f"{key} must be numeric"
                if not (0.5 <= value <= 1.5):
                    # Auto-correct out of range values
                    sim_params[key] = max(0.5, min(1.5, value))
                    logger.warning(f"Auto-corrected {key}: {value} → {sim_params[key]}")

            # Validate scenario
            valid_scenarios = [
                'balanced_standard', 'high_tempo_low_scoring', 'high_scoring',
                'defensive_low_scoring', 'one_sided_domination'
            ]
            if sim_params['expected_scenario'] not in valid_scenarios:
                sim_params['expected_scenario'] = 'balanced_standard'
                logger.warning("Invalid scenario, using balanced_standard")

            return True, None

        except Exception as e:
            return False, str(e)

    def _get_default_parameters(self) -> Dict:
        """
        Get default parameters (fallback).

        Returns:
            Default parameter dictionary
        """
        return {
            'simulation_parameters': {
                'home_attack_modifier': 1.0,
                'away_attack_modifier': 1.0,
                'home_defense_modifier': 1.0,
                'away_defense_modifier': 1.0,
                'home_morale': 1.0,
                'away_morale': 1.0,
                'tempo_modifier': 1.0,
                'shot_conversion_modifier': 1.0,
                'expected_scenario': 'balanced_standard'
            },
            'ai_reasoning': 'Using default parameters (AI generation failed or invalid)',
            'confidence': 'low'
        }


def get_parameter_generator() -> AIParameterGenerator:
    """
    Get AI parameter generator instance.

    Returns:
        AIParameterGenerator instance
    """
    return AIParameterGenerator()
