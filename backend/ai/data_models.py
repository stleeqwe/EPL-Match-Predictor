"""
AI Data Models
AI 시스템에서 사용하는 데이터 클래스 정의

주요 클래스:
- MatchInput: 경기 입력 정보
- Scenario: AI 생성 시나리오
- SimulationResult: 시뮬레이션 결과
- AnalysisResult: 분석 결과
- AIConfig: AI Client 설정
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


# ==========================================================================
# Enums
# ==========================================================================

class AnalysisStatus(Enum):
    """분석 상태"""
    NEEDS_ADJUSTMENT = "needs_adjustment"  # 시나리오 조정 필요
    CONVERGED = "converged"                # 수렴 완료
    MAX_ITERATIONS = "max_iterations"      # 최대 반복 도달


class AIProvider(Enum):
    """AI 제공자"""
    CLAUDE = "claude"
    QWEN = "qwen"
    GPT4 = "gpt4"  # 향후 확장


# ==========================================================================
# Match Input
# ==========================================================================

@dataclass
class TeamInput:
    """팀 입력 정보"""
    name: str
    formation: str                    # '4-3-3', '4-4-2', etc.
    recent_form: str                  # 'WWDLL' (최근 5경기)
    injuries: List[str]               # 부상자 명단
    key_players: List[str]            # 주요 선수
    attack_strength: float = 80.0     # 공격력 (0-100)
    defense_strength: float = 80.0    # 수비력 (0-100)
    press_intensity: float = 70.0     # 압박 강도 (0-100)
    buildup_style: str = "mixed"      # 'direct', 'possession', 'mixed'

    def __post_init__(self):
        """검증"""
        assert 0 <= self.attack_strength <= 100
        assert 0 <= self.defense_strength <= 100
        assert 0 <= self.press_intensity <= 100
        assert self.buildup_style in ["direct", "possession", "mixed"]


@dataclass
class MatchInput:
    """경기 입력 정보 (Phase 1 프롬프트용)"""
    match_id: str
    home_team: TeamInput
    away_team: TeamInput
    venue: str = "Home Stadium"
    competition: str = "Premier League"
    weather: Optional[str] = None      # 'sunny', 'rainy', etc.
    importance: str = "normal"         # 'normal', 'derby', 'top_clash'

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환 (프롬프트 템플릿용)"""
        return {
            'match_id': self.match_id,
            'home_team': {
                'name': self.home_team.name,
                'formation': self.home_team.formation,
                'recent_form': self.home_team.recent_form,
                'injuries': ', '.join(self.home_team.injuries) if self.home_team.injuries else 'None',
                'key_players': ', '.join(self.home_team.key_players[:3]),  # 상위 3명
                # Domain 지식: 팀 전력 속성 (18개 Team Strength에서 계산된 값)
                'attack_strength': self.home_team.attack_strength,
                'defense_strength': self.home_team.defense_strength,
                'press_intensity': self.home_team.press_intensity,
                'buildup_style': self.home_team.buildup_style,
            },
            'away_team': {
                'name': self.away_team.name,
                'formation': self.away_team.formation,
                'recent_form': self.away_team.recent_form,
                'injuries': ', '.join(self.away_team.injuries) if self.away_team.injuries else 'None',
                'key_players': ', '.join(self.away_team.key_players[:3]),
                # Domain 지식: 팀 전력 속성 (18개 Team Strength에서 계산된 값)
                'attack_strength': self.away_team.attack_strength,
                'defense_strength': self.away_team.defense_strength,
                'press_intensity': self.away_team.press_intensity,
                'buildup_style': self.away_team.buildup_style,
            },
            'venue': self.venue,
            'competition': self.competition,
            'weather': self.weather or 'Clear',
            'importance': self.importance,
        }


# ==========================================================================
# Scenario
# ==========================================================================

@dataclass
class ScenarioEvent:
    """시나리오 이벤트 (단일 이벤트)"""
    minute_range: List[int]           # [start, end] (e.g., [10, 25])
    type: str                         # 'wing_breakthrough', 'goal', etc.
    team: str                         # 'home' or 'away'
    probability_boost: float          # 1.0-3.0
    actor: Optional[str] = None       # 선수 이름
    reason: Optional[str] = None      # 부스트 이유

    def __post_init__(self):
        """검증"""
        assert len(self.minute_range) == 2
        assert 0 <= self.minute_range[0] <= 90
        assert 0 <= self.minute_range[1] <= 90
        assert self.minute_range[0] <= self.minute_range[1]
        assert 1.0 <= self.probability_boost <= 3.0
        assert self.team in ["home", "away"]

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환 (ScenarioGuide 호환)"""
        return {
            'minute_range': self.minute_range,
            'type': self.type,
            'team': self.team,
            'probability_boost': self.probability_boost,
            'actor': self.actor,
            'reason': self.reason,
        }


@dataclass
class Scenario:
    """AI 생성 시나리오"""
    scenario_id: str
    description: str                  # 시나리오 설명 (1-2 문장)
    events: List[ScenarioEvent]

    def __post_init__(self):
        """검증"""
        assert 3 <= len(self.events) <= 10, \
            f"이벤트는 3-10개여야 함: {len(self.events)}개"

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환 (ScenarioGuide 호환)"""
        return {
            'id': self.scenario_id,
            'description': self.description,
            'events': [e.to_dict() for e in self.events],
        }


# ==========================================================================
# Simulation Result
# ==========================================================================

@dataclass
class SimulationResult:
    """시뮬레이션 결과 (Phase 3 분석용)"""
    final_score: Dict[str, int]       # {'home': 2, 'away': 1}
    events: List[Dict]                # 모든 이벤트
    narrative_adherence: float        # 서사 일치율 (0.0-1.0)
    stats: Dict[str, Any]             # 통계 (슛, 점유율 등)

    # 추가 정보
    expected_events: List[Dict] = field(default_factory=list)  # 예상 이벤트
    occurred_events: List[Dict] = field(default_factory=list)  # 발생 이벤트

    def __post_init__(self):
        """검증"""
        assert 0.0 <= self.narrative_adherence <= 1.0

    def get_summary(self) -> str:
        """요약 문자열"""
        return (
            f"Final Score: {self.final_score['home']}-{self.final_score['away']}\n"
            f"Narrative Adherence: {self.narrative_adherence:.0%}\n"
            f"Total Events: {len(self.events)}\n"
            f"Home Shots: {self.stats.get('home_shots', 0)}\n"
            f"Away Shots: {self.stats.get('away_shots', 0)}"
        )


# ==========================================================================
# Analysis Result
# ==========================================================================

@dataclass
class AnalysisResult:
    """분석 결과 (Phase 3 출력)"""
    status: AnalysisStatus
    adjusted_scenario: Optional[Scenario] = None  # 조정된 시나리오 (필요 시)
    analysis: str = ""                            # 분석 내용
    suggestions: List[str] = field(default_factory=list)  # 제안 사항

    def is_converged(self) -> bool:
        """수렴 여부"""
        return self.status in [AnalysisStatus.CONVERGED, AnalysisStatus.MAX_ITERATIONS]


# ==========================================================================
# AI Config
# ==========================================================================

@dataclass
class AIConfig:
    """AI Client 설정"""
    provider: AIProvider              # AI 제공자
    api_key: str                      # API 키
    model: Optional[str] = None       # 모델 이름 (None이면 기본값)
    timeout: int = 30                 # 타임아웃 (초)
    max_retries: int = 3              # 최대 재시도 횟수
    temperature: float = 0.7          # 창의성 (0.0-1.0)

    def __post_init__(self):
        """검증 및 기본값 설정"""
        assert self.timeout > 0
        assert self.max_retries >= 0
        assert 0.0 <= self.temperature <= 1.0

        # 기본 모델 설정
        if self.model is None:
            if self.provider == AIProvider.CLAUDE:
                self.model = "claude-3-5-sonnet-20241022"
            elif self.provider == AIProvider.QWEN:
                self.model = "qwen2.5:72b"
            elif self.provider == AIProvider.GPT4:
                self.model = "gpt-4-turbo-preview"


# ==========================================================================
# Testing
# ==========================================================================

def test_data_models():
    """데이터 모델 테스트"""
    print("=== AI Data Models 테스트 ===\n")

    # Test 1: TeamInput
    print("Test 1: TeamInput")
    home_team = TeamInput(
        name="Arsenal",
        formation="4-3-3",
        recent_form="WWDWL",
        injuries=["Partey"],
        key_players=["Saka", "Odegaard", "Martinelli"],
        attack_strength=85.0,
        defense_strength=82.0,
    )
    print(f"  {home_team.name}: {home_team.formation}")
    print(f"  Recent form: {home_team.recent_form}")
    print(f"  ✅ TeamInput 생성 성공\n")

    # Test 2: MatchInput
    print("Test 2: MatchInput")
    away_team = TeamInput(
        name="Tottenham",
        formation="4-2-3-1",
        recent_form="LWWDW",
        injuries=["Romero"],
        key_players=["Son", "Maddison", "Kane"],
    )

    match_input = MatchInput(
        match_id="EPL_2024_001",
        home_team=home_team,
        away_team=away_team,
        importance="derby"
    )
    print(f"  Match: {match_input.home_team.name} vs {match_input.away_team.name}")
    print(f"  Importance: {match_input.importance}")
    print(f"  ✅ MatchInput 생성 성공\n")

    # Test 3: ScenarioEvent
    print("Test 3: ScenarioEvent")
    event = ScenarioEvent(
        minute_range=[10, 25],
        type="wing_breakthrough",
        team="home",
        probability_boost=2.5,
        actor="Saka",
        reason="최근 5경기 3골 1어시스트"
    )
    print(f"  Event: {event.type} ({event.minute_range[0]}-{event.minute_range[1]}분)")
    print(f"  Boost: {event.probability_boost}x")
    print(f"  ✅ ScenarioEvent 생성 성공\n")

    # Test 4: Scenario
    print("Test 4: Scenario")
    events_list = [
        event,
        ScenarioEvent(
            minute_range=[15, 30],
            type="goal",
            team="home",
            probability_boost=2.0,
        ),
        ScenarioEvent(
            minute_range=[60, 75],
            type="counter_attack",
            team="away",
            probability_boost=2.2,
        )
    ]
    scenario = Scenario(
        scenario_id="DERBY_001",
        description="Arsenal이 측면 공격을 통해 초반 주도권을 잡는 시나리오",
        events=events_list
    )

    print(f"  Scenario: {scenario.scenario_id}")
    print(f"  Events: {len(scenario.events)}개")
    print(f"  ✅ Scenario 생성 성공\n")

    # Test 5: SimulationResult
    print("Test 5: SimulationResult")
    result = SimulationResult(
        final_score={'home': 2, 'away': 1},
        events=[],
        narrative_adherence=0.67,
        stats={'home_shots': 15, 'away_shots': 12}
    )
    print(result.get_summary())
    print(f"  ✅ SimulationResult 생성 성공\n")

    # Test 6: AnalysisResult
    print("Test 6: AnalysisResult")
    analysis = AnalysisResult(
        status=AnalysisStatus.CONVERGED,
        analysis="서사 일치율 67% 달성, 목표 충족"
    )
    print(f"  Status: {analysis.status.value}")
    print(f"  Converged: {analysis.is_converged()}")
    print(f"  ✅ AnalysisResult 생성 성공\n")

    # Test 7: AIConfig
    print("Test 7: AIConfig")
    config = AIConfig(
        provider=AIProvider.CLAUDE,
        api_key="sk-test-key-12345",
    )
    print(f"  Provider: {config.provider.value}")
    print(f"  Model: {config.model}")
    print(f"  ✅ AIConfig 생성 성공\n")

    print("=" * 50)
    print("✅ 모든 데이터 모델 테스트 통과!")
    print("=" * 50)


if __name__ == "__main__":
    test_data_models()
