"""
AI Integration Layer
Prompt 템플릿과 AI Client를 연결하는 통합 레이어

주요 기능:
- Phase 1: 시나리오 생성 (MatchInput → Scenario)
- Phase 3: 결과 분석 (Scenario + Result → AnalysisResult)
- Phase 7: 최종 리포트 (MatchInput + Result → Markdown)
"""

from typing import Dict, Any, Optional
import json
import sys
import os

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from ai.data_models import (
    MatchInput,
    Scenario,
    ScenarioEvent,
    SimulationResult,
    AnalysisResult,
    AnalysisStatus,
)


class AIClientError(Exception):
    """AI Client 에러"""
    pass


class AIIntegrationLayer:
    """
    AI Integration Layer

    Prompt → AI Client → 파싱 → 데이터 모델 변환
    """

    def __init__(self, ai_client, provider: str = 'claude'):
        """
        Args:
            ai_client: AI Client (ClaudeClient, QwenClient, 또는 MockAIClient)
            provider: 'claude', 'qwen', 또는 'mock'
        """
        self.ai_client = ai_client
        self.provider = provider

    # ==========================================================================
    # Phase 1: 시나리오 생성
    # ==========================================================================

    def generate_scenario(self, match_input: MatchInput) -> Scenario:
        """
        Phase 1: 시나리오 생성

        Args:
            match_input: 경기 입력 정보

        Returns:
            생성된 Scenario

        Raises:
            AIClientError: AI 호출 실패 또는 파싱 실패
        """
        # 1. Prompt 생성
        from ai.prompts.phase1_scenario import generate_phase1_prompt
        system_prompt, user_prompt = generate_phase1_prompt(match_input)

        # 2. AI 호출
        success, response, usage, error = self._call_ai(
            user_prompt, system_prompt
        )

        if not success:
            raise AIClientError(f"Phase 1 AI 호출 실패: {error}")

        # 3. JSON 파싱
        try:
            scenario_dict = self._parse_json(response)
        except Exception as e:
            raise AIClientError(f"Phase 1 JSON 파싱 실패: {e}\n\n응답:\n{response[:500]}")

        # 4. Scenario 객체 생성
        try:
            scenario = self._dict_to_scenario(scenario_dict)
        except Exception as e:
            raise AIClientError(f"Phase 1 Scenario 생성 실패: {e}")

        return scenario

    # ==========================================================================
    # Phase 3: 결과 분석
    # ==========================================================================

    def analyze_result(self,
                      original_scenario: Scenario,
                      simulation_result: SimulationResult,
                      iteration: int,
                      max_iterations: int = 5) -> AnalysisResult:
        """
        Phase 3: 결과 분석 및 조정

        Args:
            original_scenario: 원래 시나리오
            simulation_result: 시뮬레이션 결과
            iteration: 현재 반복 횟수
            max_iterations: 최대 반복 횟수

        Returns:
            분석 결과 (조정된 시나리오 포함 가능)

        Raises:
            AIClientError: AI 호출 실패 또는 파싱 실패
        """
        # 1. Prompt 생성
        from ai.prompts.phase3_analysis import generate_phase3_prompt
        system_prompt, user_prompt = generate_phase3_prompt(
            original_scenario,
            simulation_result,
            iteration,
            max_iterations
        )

        # 2. AI 호출
        success, response, usage, error = self._call_ai(
            user_prompt, system_prompt
        )

        if not success:
            raise AIClientError(f"Phase 3 AI 호출 실패: {error}")

        # 3. JSON 파싱
        try:
            analysis_dict = self._parse_json(response)
        except Exception as e:
            raise AIClientError(f"Phase 3 JSON 파싱 실패: {e}\n\n응답:\n{response[:500]}")

        # 4. AnalysisResult 객체 생성
        try:
            result = self._dict_to_analysis_result(analysis_dict)
        except Exception as e:
            raise AIClientError(f"Phase 3 AnalysisResult 생성 실패: {e}")

        return result

    # ==========================================================================
    # Phase 7: 최종 리포트
    # ==========================================================================

    def generate_report(self,
                       match_input: MatchInput,
                       final_result: SimulationResult) -> str:
        """
        Phase 7: 최종 리포트 생성

        Args:
            match_input: 경기 입력 정보
            final_result: 최종 시뮬레이션 결과

        Returns:
            마크다운 리포트 (텍스트)

        Raises:
            AIClientError: AI 호출 실패
        """
        # 1. Prompt 생성
        from ai.prompts.phase7_report import generate_phase7_prompt
        system_prompt, user_prompt = generate_phase7_prompt(
            match_input,
            final_result
        )

        # 2. AI 호출
        success, response, usage, error = self._call_ai(
            user_prompt, system_prompt
        )

        if not success:
            raise AIClientError(f"Phase 7 AI 호출 실패: {error}")

        # 3. 마크다운 반환 (파싱 불필요)
        return response

    # ==========================================================================
    # 헬퍼 메서드
    # ==========================================================================

    def _call_ai(self, user_prompt: str, system_prompt: str) -> tuple:
        """
        AI Client 호출 (Provider에 따라 다른 방식)

        Args:
            user_prompt: User prompt
            system_prompt: System prompt

        Returns:
            (success, response, usage, error) 튜플
        """
        if self.provider == 'mock':
            # Mock AI는 직접 호출
            return self.ai_client.generate(user_prompt, system_prompt)

        elif self.provider == 'qwen':
            # Qwen (Ollama) - tier 파라미터 없음
            return self.ai_client.generate(
                prompt=user_prompt,
                system_prompt=system_prompt
            )

        elif self.provider == 'claude':
            # Claude - tier 파라미터 필요
            return self.ai_client.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                tier='BASIC'
            )

        else:
            return False, None, None, f"Unknown provider: {self.provider}"

    def _parse_json(self, response: str) -> Dict[str, Any]:
        """
        LLM 응답에서 JSON 추출 및 파싱

        Args:
            response: LLM 응답 텍스트

        Returns:
            파싱된 JSON 딕셔너리

        Raises:
            json.JSONDecodeError: JSON 파싱 실패
        """
        response = response.strip()

        # ```json ... ``` 형태면 추출
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            json_str = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            json_str = response[start:end].strip()
        else:
            # { } 찾기
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end != 0:
                json_str = response[start:end]
            else:
                json_str = response

        return json.loads(json_str)

    def _dict_to_scenario(self, data: Dict[str, Any]) -> Scenario:
        """
        딕셔너리 → Scenario 변환

        Args:
            data: AI 응답 딕셔너리

        Returns:
            Scenario 객체
        """
        events = [
            ScenarioEvent(
                minute_range=e['minute_range'],
                type=e['type'],
                team=e['team'],
                probability_boost=e.get('probability_boost', 2.0),
                actor=e.get('actor'),
                reason=e.get('reason'),
            )
            for e in data['events']
        ]

        return Scenario(
            scenario_id=data.get('scenario_id', data.get('id', 'UNKNOWN')),
            description=data.get('description', ''),
            events=events,
        )

    def _dict_to_analysis_result(self, data: Dict[str, Any]) -> AnalysisResult:
        """
        딕셔너리 → AnalysisResult 변환

        Args:
            data: AI 응답 딕셔너리

        Returns:
            AnalysisResult 객체
        """
        status_str = data.get('status', 'needs_adjustment')

        if status_str == 'converged':
            status = AnalysisStatus.CONVERGED
        elif status_str == 'needs_adjustment':
            status = AnalysisStatus.NEEDS_ADJUSTMENT
        elif status_str == 'max_iterations':
            status = AnalysisStatus.MAX_ITERATIONS
        else:
            status = AnalysisStatus.NEEDS_ADJUSTMENT

        # 조정된 시나리오가 있으면 파싱
        adjusted_scenario = None
        if status == AnalysisStatus.NEEDS_ADJUSTMENT and 'adjusted_scenario' in data:
            adjusted_scenario = self._dict_to_scenario(data['adjusted_scenario'])

        return AnalysisResult(
            status=status,
            adjusted_scenario=adjusted_scenario,
            analysis=data.get('analysis', ''),
            suggestions=data.get('suggestions', []),
        )


# ==========================================================================
# Mock AI Client (테스트용)
# ==========================================================================

class MockAIClient:
    """
    테스트용 Mock AI Client

    실제 API 호출 없이 미리 정의된 응답 반환
    """

    def generate(self, prompt: str, system_prompt: Optional[str] = None, tier: str = 'BASIC'):
        """
        Mock AI 응답 생성

        Args:
            prompt: User prompt
            system_prompt: System prompt (사용 안 함)
            tier: Tier (사용 안 함)

        Returns:
            (success, response, usage, error) 튜플
        """
        # Phase 감지 (프롬프트 내용으로 판단)
        # 중요: Phase 3, 7을 먼저 체크 (더 구체적인 키워드)
        prompt_lower = prompt.lower()

        # Phase 3: 분석/조정 (먼저 체크 - 더 구체적)
        if '시뮬레이션 결과 분석' in prompt or ('분석' in prompt and '시뮬레이션 결과' in prompt):
            # 수렴 조건 확인: "converged'로 반환하세요" 문구 또는 ">= 60%" 체크
            if "converged'로 반환하세요" in prompt or '>= 60%' in prompt or '최대 반복' in prompt:
                # 수렴 조건 (높은 일치율 또는 최대 반복 도달)
                return True, self._get_mock_analysis_converged(), {}, None
            else:
                # 낮은 일치율 (< 60%) → 조정 필요
                return True, self._get_mock_analysis_adjustment(), {}, None

        # Phase 7: 리포트
        elif '리포트' in prompt or 'report' in prompt_lower:
            return True, self._get_mock_report(), {}, None

        # Phase 1: 시나리오 생성 (마지막에 체크 - 일반적인 키워드)
        elif '시나리오' in prompt or 'scenario' in prompt_lower:
            return True, self._get_mock_scenario(), {}, None

        # 알 수 없는 Phase
        return False, None, None, "Unknown prompt type"

    def _get_mock_scenario(self) -> str:
        """Mock 시나리오 JSON"""
        return """```json
{
  "scenario_id": "MOCK_001",
  "description": "Mock 시나리오 for testing",
  "events": [
    {
      "minute_range": [10, 25],
      "type": "wing_breakthrough",
      "team": "home",
      "probability_boost": 2.5,
      "actor": "Mock Player 1",
      "reason": "Testing reason 1"
    },
    {
      "minute_range": [15, 30],
      "type": "goal",
      "team": "home",
      "probability_boost": 2.0,
      "reason": "Testing reason 2"
    },
    {
      "minute_range": [60, 75],
      "type": "counter_attack",
      "team": "away",
      "probability_boost": 2.2,
      "reason": "Testing reason 3"
    }
  ]
}
```"""

    def _get_mock_analysis_converged(self) -> str:
        """Mock 분석 (수렴)"""
        return """```json
{
  "status": "converged",
  "analysis": "서사 일치율 67% 달성. 목표 충족.",
  "suggestions": []
}
```"""

    def _get_mock_analysis_adjustment(self) -> str:
        """Mock 분석 (조정 필요)"""
        return """```json
{
  "status": "needs_adjustment",
  "analysis": "서사 일치율 33%. 조정 필요.",
  "suggestions": [
    "wing_breakthrough boost 2.5→2.8",
    "goal boost 2.0→2.5"
  ],
  "adjusted_scenario": {
    "scenario_id": "MOCK_001_ADJ_1",
    "description": "조정된 Mock 시나리오",
    "events": [
      {
        "minute_range": [8, 30],
        "type": "wing_breakthrough",
        "team": "home",
        "probability_boost": 2.8,
        "actor": "Mock Player 1",
        "reason": "조정: boost 증가"
      },
      {
        "minute_range": [15, 32],
        "type": "goal",
        "team": "home",
        "probability_boost": 2.5,
        "reason": "조정: boost 증가"
      },
      {
        "minute_range": [60, 75],
        "type": "counter_attack",
        "team": "away",
        "probability_boost": 2.2,
        "reason": "유지"
      }
    ]
  }
}
```"""

    def _get_mock_report(self) -> str:
        """Mock 리포트 (마크다운)"""
        return """# Mock 경기 리포트

## 경기 요약
Mock 홈팀이 Mock 원정팀을 2-1로 꺾었습니다.

## 주요 순간
- **18분**: 홈팀 득점 ⚽
- **34분**: 홈팀 득점 ⚽
- **72분**: 원정팀 득점 ⚽

## 팀별 통계
| 항목 | 홈팀 | 원정팀 |
|------|------|--------|
| 슛 | 15 | 12 |

## 결론
홈팀의 승리!
"""


# ==========================================================================
# Testing
# ==========================================================================

def test_ai_integration():
    """AI Integration Layer 테스트"""
    print("=== AI Integration Layer 테스트 ===\n")

    # Mock AI Client 생성
    mock_ai = MockAIClient()
    ai_integration = AIIntegrationLayer(mock_ai, provider='mock')

    # 테스트 데이터
    from ai.data_models import TeamInput

    home_team = TeamInput(
        name="Arsenal",
        formation="4-3-3",
        recent_form="WWDWL",
        injuries=["Partey"],
        key_players=["Saka", "Odegaard", "Martinelli"],
    )

    away_team = TeamInput(
        name="Tottenham",
        formation="4-2-3-1",
        recent_form="LWWDW",
        injuries=["Romero"],
        key_players=["Son", "Maddison", "Kulusevski"],
    )

    match_input = MatchInput(
        match_id="TEST_001",
        home_team=home_team,
        away_team=away_team,
    )

    # Test 1: Phase 1 - 시나리오 생성
    print("Test 1: Phase 1 - 시나리오 생성")
    scenario = ai_integration.generate_scenario(match_input)
    print(f"  시나리오 ID: {scenario.scenario_id}")
    print(f"  이벤트 수: {len(scenario.events)}")
    assert len(scenario.events) >= 3
    print(f"  ✅ Test 1 통과\n")

    # Test 2: Phase 3 - 분석 (수렴)
    print("Test 2: Phase 3 - 분석 (수렴)")
    result_converged = SimulationResult(
        final_score={'home': 2, 'away': 1},
        events=[],
        narrative_adherence=0.67,
        stats={}
    )

    analysis = ai_integration.analyze_result(scenario, result_converged, iteration=2)
    print(f"  상태: {analysis.status.value}")
    print(f"  분석: {analysis.analysis}")
    assert analysis.status == AnalysisStatus.CONVERGED
    print(f"  ✅ Test 2 통과\n")

    # Test 3: Phase 3 - 분석 (조정 필요)
    print("Test 3: Phase 3 - 분석 (조정 필요)")
    result_needs_adj = SimulationResult(
        final_score={'home': 1, 'away': 1},
        events=[],
        narrative_adherence=0.33,
        stats={}
    )

    analysis2 = ai_integration.analyze_result(scenario, result_needs_adj, iteration=1)
    print(f"  상태: {analysis2.status.value}")
    print(f"  조정된 시나리오: {analysis2.adjusted_scenario is not None}")
    assert analysis2.status == AnalysisStatus.NEEDS_ADJUSTMENT
    assert analysis2.adjusted_scenario is not None
    print(f"  ✅ Test 3 통과\n")

    # Test 4: Phase 7 - 리포트 생성
    print("Test 4: Phase 7 - 리포트 생성")
    report = ai_integration.generate_report(match_input, result_converged)
    print(f"  리포트 길이: {len(report)} 문자")
    print(f"  리포트 샘플:\n{report[:200]}...")
    assert len(report) > 0
    assert "Mock" in report
    print(f"  ✅ Test 4 통과\n")

    print("=" * 60)
    print("✅ AI Integration Layer 모든 테스트 통과!")
    print("=" * 60)


if __name__ == "__main__":
    test_ai_integration()
