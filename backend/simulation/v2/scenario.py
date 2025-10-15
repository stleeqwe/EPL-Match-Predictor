"""
Scenario Data Structures
설계 문서 Section 7.1 정확히 구현

시나리오는 5-7개의 서로 다른 경기 전개 방식을 표현합니다.
각 시나리오는 이벤트 시퀀스를 포함합니다.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum


class EventType(Enum):
    """이벤트 타입 (설계서 기반)"""
    WING_BREAKTHROUGH = "wing_breakthrough"
    CENTRAL_PENETRATION = "central_penetration"
    GOAL = "goal"
    SHOT_ON_TARGET = "shot_on_target"
    SHOT_OFF_TARGET = "shot_off_target"
    CORNER = "corner"
    FORMATION_CHANGE = "formation_change"
    SUBSTITUTION = "substitution"
    FOUL = "foul"
    YELLOW_CARD = "yellow_card"
    RED_CARD = "red_card"


@dataclass
class ScenarioEvent:
    """
    시나리오의 단일 이벤트 정의
    설계 문서 Section 7.1
    """
    minute_range: Tuple[int, int]  # [10, 25] - 이 범위에서 발생
    type: EventType  # 이벤트 타입
    team: str  # "home" or "away"
    actor: Optional[str] = None  # 특정 선수 (예: "Son")
    method: Optional[str] = None  # 방법 (예: "wing_attack", "central_attack")
    probability_boost: float = 1.0  # 기본 확률 대비 배수 (1.0-3.0)
    reason: str = ""  # AI가 이 이벤트를 포함한 이유
    trigger: Optional[str] = None  # 조건부 이벤트 (예: "leading")
    to: Optional[str] = None  # formation_change의 경우 목표 포메이션

    def __post_init__(self):
        """검증"""
        if self.minute_range[0] < 0 or self.minute_range[1] > 90:
            raise ValueError(f"Invalid minute_range: {self.minute_range}")
        if self.minute_range[0] > self.minute_range[1]:
            raise ValueError(f"minute_range start > end: {self.minute_range}")
        if not (1.0 <= self.probability_boost <= 3.0):
            raise ValueError(f"probability_boost must be 1.0-3.0, got {self.probability_boost}")


@dataclass
class Scenario:
    """
    완전한 시나리오 정의
    설계 문서 Section 7.1

    각 시나리오는 하나의 경기 전개 방식을 나타냅니다.
    예: "손흥민 측면 우위 → 초반 선제 → 완승"
    """
    id: str  # SYNTH_001
    name: str  # 시나리오 이름
    reasoning: str  # AI가 이 시나리오를 생성한 이유
    events: List[ScenarioEvent] = field(default_factory=list)
    parameter_adjustments: Dict = field(default_factory=dict)
    expected_probability: float = 0.0  # AI가 예상한 발생 확률 (0-1)
    base_narrative: Optional[str] = None  # 기반 서사 템플릿 ID (나중에)

    def __post_init__(self):
        """검증"""
        if not (0.0 <= self.expected_probability <= 1.0):
            raise ValueError(f"expected_probability must be 0-1, got {self.expected_probability}")

    def to_dict(self) -> Dict:
        """JSON 직렬화"""
        return {
            "id": self.id,
            "name": self.name,
            "reasoning": self.reasoning,
            "events": [
                {
                    "minute_range": list(event.minute_range),
                    "type": event.type.value,
                    "team": event.team,
                    "actor": event.actor,
                    "method": event.method,
                    "probability_boost": event.probability_boost,
                    "reason": event.reason,
                    "trigger": event.trigger,
                    "to": event.to
                }
                for event in self.events
            ],
            "parameter_adjustments": self.parameter_adjustments,
            "expected_probability": self.expected_probability,
            "base_narrative": self.base_narrative
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Scenario':
        """JSON 역직렬화"""
        events = [
            ScenarioEvent(
                minute_range=tuple(e["minute_range"]),
                type=EventType(e["type"]),
                team=e["team"],
                actor=e.get("actor"),
                method=e.get("method"),
                probability_boost=e.get("probability_boost", 1.0),
                reason=e.get("reason", ""),
                trigger=e.get("trigger"),
                to=e.get("to")
            )
            for e in data.get("events", [])
        ]

        return cls(
            id=data["id"],
            name=data["name"],
            reasoning=data["reasoning"],
            events=events,
            parameter_adjustments=data.get("parameter_adjustments", {}),
            expected_probability=data.get("expected_probability", 0.0),
            base_narrative=data.get("base_narrative")
        )


def create_example_scenario() -> Scenario:
    """
    예제 시나리오 (설계 문서 Section 3 예시)
    """
    return Scenario(
        id="SYNTH_001",
        name="손흥민 측면 우위 → 초반 선제 → 아스날 역전",
        reasoning="사용자 언급 '손흥민 빅매치 강세' + '아스날 좌측 약점' 반영",
        events=[
            ScenarioEvent(
                minute_range=(10, 25),
                type=EventType.WING_BREAKTHROUGH,
                team="home",
                actor="Son",
                probability_boost=2.5,
                reason="Son(92 스피드) vs 티에르니 부재"
            ),
            ScenarioEvent(
                minute_range=(15, 30),
                type=EventType.GOAL,
                team="home",
                method="wing_attack",
                probability_boost=1.8,
                reason="측면 돌파 후 득점"
            ),
            ScenarioEvent(
                minute_range=(65, 75),
                type=EventType.FORMATION_CHANGE,
                team="home",
                to="5-3-2",
                trigger="leading",
                reason="아르테타 수비 전환 패턴"
            ),
            ScenarioEvent(
                minute_range=(78, 88),
                type=EventType.GOAL,
                team="away",
                method="central_attack",
                probability_boost=1.6,
                reason="토트넘 수비 약화 + 아스날 중앙 강점"
            )
        ],
        parameter_adjustments={
            "Son_speed_modifier": 1.15,
            "Arsenal_left_defense_modifier": 0.75,
            "Tottenham_defensive_stability_after_60min": 0.85
        },
        expected_probability=0.16
    )
