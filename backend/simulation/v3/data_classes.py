"""
Data Classes for v3 Simulation Engine
서사 기반 시뮬레이션용 데이터 클래스
"""

from dataclasses import dataclass
from typing import Optional, Dict, List
from enum import Enum


# ==========================================================================
# Enums
# ==========================================================================

class TeamSide(Enum):
    """팀 사이드"""
    HOME = "home"
    AWAY = "away"


class EventType(Enum):
    """이벤트 타입"""
    SHOT = "shot"
    SHOT_ON_TARGET = "shot_on_target"
    SHOT_OFF_TARGET = "shot_off_target"
    GOAL = "goal"
    CORNER = "corner"
    FOUL = "foul"
    YELLOW_CARD = "yellow_card"
    RED_CARD = "red_card"
    PENALTY = "penalty"
    WING_BREAKTHROUGH = "wing_breakthrough"
    CENTRAL_PENETRATION = "central_penetration"
    COUNTER_ATTACK = "counter_attack"
    SET_PIECE = "set_piece"
    FORMATION_CHANGE = "formation_change"


class MatchState(Enum):
    """경기 상태"""
    LEADING = "leading"
    TRAILING = "trailing"
    DRAWING = "drawing"


# ==========================================================================
# Narrative Boost
# ==========================================================================

@dataclass
class NarrativeBoost:
    """
    서사 부스트 데이터 클래스

    서사 가이드에서 특정 분에 적용되는 확률 부스트

    Attributes:
        type: 이벤트 타입 (wing_breakthrough, goal, corner 등)
        multiplier: 확률 배수 (1.0-3.0)
        team: 대상 팀 (home or away)
        actor: 선수 이름 (선택사항)
        reason: 부스트 이유 (디버깅용)
    """
    type: str
    multiplier: float
    team: str
    actor: Optional[str] = None
    reason: Optional[str] = None

    def __post_init__(self):
        """검증"""
        assert 1.0 <= self.multiplier <= 3.0, \
            f"multiplier는 1.0-3.0 범위여야 함: {self.multiplier}"
        assert self.team in ["home", "away"], \
            f"team은 'home' 또는 'away'여야 함: {self.team}"


# ==========================================================================
# Team Info
# ==========================================================================

@dataclass
class TeamInfo:
    """
    팀 정보

    Attributes:
        name: 팀 이름
        formation: 포메이션 (4-3-3, 4-4-2 등)
        attack_strength: 공격력 (0-100)
        defense_strength: 수비력 (0-100)
        press_intensity: 압박 강도 (0-100)
        buildup_style: 빌드업 스타일 (direct, possession, mixed)
    """
    name: str
    formation: str
    attack_strength: float
    defense_strength: float
    press_intensity: float
    buildup_style: str

    def __post_init__(self):
        """검증"""
        assert 0 <= self.attack_strength <= 100
        assert 0 <= self.defense_strength <= 100
        assert 0 <= self.press_intensity <= 100
        assert self.buildup_style in ["direct", "possession", "mixed"]


# ==========================================================================
# Match Context
# ==========================================================================

@dataclass
class MatchContext:
    """
    경기 컨텍스트 (현재 상태)

    EventProbabilityCalculator에 전달되는 경기 상황 정보

    Attributes:
        minute: 현재 분 (0-90)
        score_home: 홈팀 득점
        score_away: 원정팀 득점
        possession_team: 현재 점유 팀
        home_team: 홈팀 정보
        away_team: 원정팀 정보
        stamina_home: 홈팀 체력 (0-100)
        stamina_away: 원정팀 체력 (0-100)
        formation_home: 현재 홈팀 포메이션
        formation_away: 현재 원정팀 포메이션
    """
    minute: int
    score_home: int
    score_away: int
    possession_team: str  # 'home' or 'away'
    home_team: TeamInfo
    away_team: TeamInfo
    stamina_home: float = 100.0
    stamina_away: float = 100.0
    formation_home: Optional[str] = None
    formation_away: Optional[str] = None

    def __post_init__(self):
        """검증 및 초기화"""
        assert 0 <= self.minute <= 90
        assert self.score_home >= 0
        assert self.score_away >= 0
        assert self.possession_team in ["home", "away"]
        assert 0 <= self.stamina_home <= 100
        assert 0 <= self.stamina_away <= 100

        # 포메이션 기본값 설정
        if self.formation_home is None:
            self.formation_home = self.home_team.formation
        if self.formation_away is None:
            self.formation_away = self.away_team.formation

    @property
    def attacking_team(self) -> TeamInfo:
        """현재 공격 팀"""
        return self.home_team if self.possession_team == "home" else self.away_team

    @property
    def defending_team(self) -> TeamInfo:
        """현재 수비 팀"""
        return self.away_team if self.possession_team == "home" else self.home_team

    @property
    def attacking_stamina(self) -> float:
        """공격 팀 체력"""
        return self.stamina_home if self.possession_team == "home" else self.stamina_away

    @property
    def defending_stamina(self) -> float:
        """수비 팀 체력"""
        return self.stamina_away if self.possession_team == "home" else self.stamina_home

    @property
    def score_diff_attacking(self) -> int:
        """공격 팀 관점 스코어 차이 (내 득점 - 상대 득점)"""
        if self.possession_team == "home":
            return self.score_home - self.score_away
        else:
            return self.score_away - self.score_home

    @property
    def match_state_attacking(self) -> MatchState:
        """공격 팀의 경기 상태"""
        diff = self.score_diff_attacking
        if diff > 0:
            return MatchState.LEADING
        elif diff < 0:
            return MatchState.TRAILING
        else:
            return MatchState.DRAWING


# ==========================================================================
# Match Result
# ==========================================================================

@dataclass
class MatchResult:
    """
    경기 결과

    Attributes:
        final_score: 최종 스코어 {'home': 2, 'away': 1}
        events: 이벤트 목록
        narrative_adherence: 서사 일치율 (0.0-1.0)
        stats: 추가 통계
    """
    final_score: Dict[str, int]
    events: List[Dict]
    narrative_adherence: float
    stats: Optional[Dict] = None

    def __post_init__(self):
        """검증"""
        assert 0.0 <= self.narrative_adherence <= 1.0


# ==========================================================================
# Helper Functions
# ==========================================================================

def create_test_context(minute: int = 0, score_home: int = 0, score_away: int = 0) -> MatchContext:
    """
    테스트용 MatchContext 생성 헬퍼

    Args:
        minute: 분
        score_home: 홈 득점
        score_away: 원정 득점

    Returns:
        MatchContext 객체
    """
    home_team = TeamInfo(
        name="Test Home",
        formation="4-3-3",
        attack_strength=80.0,
        defense_strength=75.0,
        press_intensity=70.0,
        buildup_style="possession"
    )

    away_team = TeamInfo(
        name="Test Away",
        formation="4-4-2",
        attack_strength=75.0,
        defense_strength=80.0,
        press_intensity=65.0,
        buildup_style="direct"
    )

    return MatchContext(
        minute=minute,
        score_home=score_home,
        score_away=score_away,
        possession_team="home",
        home_team=home_team,
        away_team=away_team
    )


if __name__ == "__main__":
    # 테스트
    print("=== Data Classes 테스트 ===\n")

    # NarrativeBoost 테스트
    boost = NarrativeBoost(
        type="wing_breakthrough",
        multiplier=2.5,
        team="home",
        actor="Son",
        reason="빅매치 강세"
    )
    print(f"✅ NarrativeBoost: {boost}")

    # MatchContext 테스트
    context = create_test_context(minute=20, score_home=1, score_away=0)
    print(f"\n✅ MatchContext created")
    print(f"   - Minute: {context.minute}")
    print(f"   - Score: {context.score_home}-{context.score_away}")
    print(f"   - Attacking team: {context.attacking_team.name}")
    print(f"   - Match state: {context.match_state_attacking}")

    # MatchResult 테스트
    result = MatchResult(
        final_score={"home": 2, "away": 1},
        events=[],
        narrative_adherence=0.85
    )
    print(f"\n✅ MatchResult: {result.final_score}, adherence={result.narrative_adherence:.2f}")

    print("\n✅ 모든 데이터 클래스 테스트 통과")
