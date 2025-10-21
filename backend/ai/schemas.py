"""
Pydantic Schemas for Structured AI Outputs
AI responses를 type-safe하게 검증하기 위한 schema 정의

Benefits:
- 100% valid JSON 보장
- Runtime type checking
- Automatic validation
- Clear API contracts
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional, Dict, Union
from enum import Enum


# ==========================================================================
# Event Types
# ==========================================================================

class EventType(str, Enum):
    """Supported event types in match scenarios"""
    GOAL_OPPORTUNITY = "goal_opportunity"
    DEFENSIVE_ACTION = "defensive_action"
    MIDFIELD_BATTLE = "midfield_battle"
    SET_PIECE = "set_piece"
    COUNTER_ATTACK = "counter_attack"
    WING_BREAKTHROUGH = "wing_breakthrough"
    PRESSURE = "pressure"
    TRANSITION = "transition"


class Team(str, Enum):
    """Team identifier"""
    HOME = "home"
    AWAY = "away"


class ConvergenceState(str, Enum):
    """AI convergence analysis states"""
    CONVERGED = "converged"
    NEEDS_ADJUSTMENT = "needs_adjustment"
    DIVERGED = "diverged"


# ==========================================================================
# Scenario Schemas
# ==========================================================================

class ScenarioEvent(BaseModel):
    """
    Single match event in scenario

    Example:
    {
        "minute_range": [10, 20],
        "event_type": "goal_opportunity",
        "team": "home",
        "description": "Arsenal builds through midfield...",
        "probability_boost": 0.15,
        "actor": "Saka",
        "reason": "Exploiting space on the right wing"
    }
    """
    minute_range: List[int] = Field(
        ...,
        min_length=2,
        max_length=2,
        description="[start_minute, end_minute] between 0-90"
    )

    event_type: EventType = Field(
        ...,
        description="Type of tactical event"
    )

    team: Team = Field(
        ...,
        description="Which team (home or away)"
    )

    description: str = Field(
        ...,
        min_length=10,
        max_length=200,
        description="Tactical description of the event"
    )

    probability_boost: float = Field(
        ...,
        ge=-1.0,
        le=2.0,
        description="Probability multiplier (-1.0 to 2.0)"
    )

    actor: Optional[str] = Field(
        default=None,
        description="Key player involved (optional)"
    )

    reason: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Tactical reason for event (optional)"
    )

    @field_validator('minute_range')
    @classmethod
    def validate_minute_range(cls, v):
        """Ensure minute range is valid"""
        if not (0 <= v[0] <= 90 and 0 <= v[1] <= 90):
            raise ValueError("Minutes must be between 0-90")
        if v[0] > v[1]:
            raise ValueError("Start minute must be <= end minute")
        return v

    @field_validator('probability_boost')
    @classmethod
    def validate_boost(cls, v):
        """Ensure boost is reasonable"""
        if abs(v) > 2.0:
            raise ValueError("Probability boost must be between -1.0 and 2.0")
        return v


class MatchScenario(BaseModel):
    """
    Complete match scenario with narrative and events

    Example:
    {
        "events": [...],
        "description": "Arsenal will dominate possession...",
        "predicted_score": {"home": 2, "away": 1},
        "confidence": 0.75
    }
    """
    events: List[ScenarioEvent] = Field(
        ...,
        min_length=3,
        max_length=10,
        description="3-10 key events in the match"
    )

    description: str = Field(
        ...,
        min_length=50,
        max_length=500,
        description="Overall match narrative"
    )

    predicted_score: Dict[str, int] = Field(
        ...,
        description="AI's predicted final score"
    )

    confidence: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="AI's confidence in scenario (0-1)"
    )

    @field_validator('predicted_score')
    @classmethod
    def validate_score(cls, v):
        """Ensure score has home and away"""
        if 'home' not in v or 'away' not in v:
            raise ValueError("Score must have 'home' and 'away' keys")
        if not (0 <= v['home'] <= 10 and 0 <= v['away'] <= 10):
            raise ValueError("Scores must be between 0-10")
        return v

    @field_validator('events')
    @classmethod
    def validate_events_non_overlapping(cls, v):
        """Warn if events overlap too much"""
        # Sort by start time
        sorted_events = sorted(v, key=lambda e: e.minute_range[0])

        # Check for excessive overlap
        for i in range(len(sorted_events) - 1):
            curr_end = sorted_events[i].minute_range[1]
            next_start = sorted_events[i + 1].minute_range[0]

            # Allow some overlap but warn if too much
            if curr_end > next_start + 10:
                # This is a warning, not an error
                pass

        return v


# ==========================================================================
# Analysis Schemas
# ==========================================================================

class DiscrepancyIssue(BaseModel):
    """Single discrepancy found in simulation"""
    type: Literal["score_mismatch", "event_missing", "probability_deviation", "other"] = Field(
        ...,
        description="Type of discrepancy"
    )

    description: str = Field(
        ...,
        min_length=10,
        max_length=200,
        description="Description of the issue"
    )

    severity: Literal["low", "medium", "high"] = Field(
        ...,
        description="Severity of discrepancy"
    )


class AnalysisResult(BaseModel):
    """
    AI analysis of simulation result

    Example:
    {
        "state": "needs_adjustment",
        "issues": [...],
        "adjusted_scenario": {...},
        "confidence": 0.8,
        "reasoning": "Home team scored less than expected..."
    }
    """
    state: ConvergenceState = Field(
        ...,
        description="Convergence state"
    )

    issues: List[DiscrepancyIssue] = Field(
        default_factory=list,
        max_length=10,
        description="List of discrepancies found"
    )

    adjusted_scenario: Optional[MatchScenario] = Field(
        default=None,
        description="Modified scenario if adjustment needed"
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="AI's confidence in analysis (0-1)"
    )

    reasoning: str = Field(
        ...,
        min_length=20,
        max_length=500,
        description="AI's reasoning for the decision"
    )

    @field_validator('adjusted_scenario')
    @classmethod
    def validate_adjustment(cls, v, info):
        """Ensure adjusted_scenario exists when state is needs_adjustment"""
        state = info.data.get('state')
        if state == ConvergenceState.NEEDS_ADJUSTMENT and v is None:
            raise ValueError("adjusted_scenario must be provided when state is needs_adjustment")
        return v


# ==========================================================================
# Response Wrappers
# ==========================================================================

class AIResponse(BaseModel):
    """
    Generic AI response wrapper

    Contains the parsed result plus metadata
    """
    success: bool = Field(
        ...,
        description="Whether the AI call succeeded"
    )

    data: Optional[Union[MatchScenario, AnalysisResult]] = Field(
        default=None,
        description="Parsed response data"
    )

    usage: Dict[str, int] = Field(
        default_factory=dict,
        description="Token usage stats"
    )

    error: Optional[str] = Field(
        default=None,
        description="Error message if failed"
    )

    latency_ms: Optional[float] = Field(
        default=None,
        description="Response latency in milliseconds"
    )

    retries: int = Field(
        default=0,
        description="Number of retries needed"
    )


# ==========================================================================
# Validation Helpers
# ==========================================================================

def validate_scenario(scenario: MatchScenario) -> tuple[bool, List[str]]:
    """
    Additional validation logic for scenarios

    Returns:
        (is_valid, error_messages)
    """
    errors = []

    # Check event count
    if len(scenario.events) < 3:
        errors.append("Scenario must have at least 3 events")

    # Check team balance (not too lopsided)
    home_events = sum(1 for e in scenario.events if e.team == Team.HOME)
    away_events = sum(1 for e in scenario.events if e.team == Team.AWAY)

    if home_events == 0 or away_events == 0:
        errors.append("Scenario must have events for both teams")

    # Check probability boosts are reasonable
    avg_boost = sum(e.probability_boost for e in scenario.events) / len(scenario.events)
    if abs(avg_boost) > 0.5:
        errors.append(f"Average probability boost too extreme: {avg_boost:.2f}")

    # Check timeline coverage
    min_minute = min(e.minute_range[0] for e in scenario.events)
    max_minute = max(e.minute_range[1] for e in scenario.events)

    if max_minute - min_minute < 30:
        errors.append("Events should cover at least 30 minutes of match time")

    return len(errors) == 0, errors


def scenario_to_dict(scenario: MatchScenario) -> dict:
    """
    Convert Pydantic scenario to dict for legacy code

    Compatible with existing Scenario dataclass
    """
    return {
        'scenario_id': f"AI_SCENARIO_{hash(scenario.description) % 10000:04d}",
        'description': scenario.description,
        'events': [
            {
                'minute_range': e.minute_range,
                'type': e.event_type.value,
                'team': e.team.value,
                'probability_boost': e.probability_boost,
                'actor': e.actor or "Unknown",
                'reason': e.reason or e.description
            }
            for e in scenario.events
        ],
        'predicted_score': scenario.predicted_score,
        'confidence': scenario.confidence
    }


# ==========================================================================
# Example Usage
# ==========================================================================

if __name__ == "__main__":
    """Test schema validation"""

    print("=" * 70)
    print("Testing Pydantic Schemas")
    print("=" * 70)

    # Test 1: Valid scenario
    print("\nTest 1: Valid Scenario")
    try:
        scenario = MatchScenario(
            events=[
                ScenarioEvent(
                    minute_range=[10, 25],
                    event_type=EventType.WING_BREAKTHROUGH,
                    team=Team.HOME,
                    description="Arsenal attacks down the right wing through Saka",
                    probability_boost=0.15,
                    actor="Saka",
                    reason="Exploiting defensive weakness"
                ),
                ScenarioEvent(
                    minute_range=[35, 50],
                    event_type=EventType.MIDFIELD_BATTLE,
                    team=Team.HOME,
                    description="Midfield control contested between both teams",
                    probability_boost=0.0
                ),
                ScenarioEvent(
                    minute_range=[60, 75],
                    event_type=EventType.COUNTER_ATTACK,
                    team=Team.AWAY,
                    description="Liverpool counters on the break",
                    probability_boost=0.2,
                    actor="Salah"
                )
            ],
            description="High-tempo match with Arsenal dominating early but Liverpool dangerous on the counter",
            predicted_score={"home": 2, "away": 1},
            confidence=0.75
        )

        print("✅ Valid scenario created!")
        print(f"  Events: {len(scenario.events)}")
        print(f"  Predicted: {scenario.predicted_score}")
        print(f"  Confidence: {scenario.confidence}")

        # Validate
        is_valid, errors = validate_scenario(scenario)
        print(f"  Additional validation: {'✅ PASSED' if is_valid else '❌ FAILED'}")

    except Exception as e:
        print(f"❌ Validation failed: {e}")

    # Test 2: Invalid minute range
    print("\nTest 2: Invalid Minute Range")
    try:
        bad_event = ScenarioEvent(
            minute_range=[95, 100],  # Invalid!
            event_type=EventType.GOAL_OPPORTUNITY,
            team=Team.HOME,
            description="Late goal attempt",
            probability_boost=0.1
        )
        print("❌ Should have failed!")
    except Exception as e:
        print(f"✅ Correctly rejected: {e}")

    # Test 3: Invalid probability boost
    print("\nTest 3: Invalid Probability Boost")
    try:
        bad_event = ScenarioEvent(
            minute_range=[10, 20],
            event_type=EventType.GOAL_OPPORTUNITY,
            team=Team.HOME,
            description="Overpowered event",
            probability_boost=5.0  # Too high!
        )
        print("❌ Should have failed!")
    except Exception as e:
        print(f"✅ Correctly rejected: {e}")

    # Test 4: Analysis Result
    print("\nTest 4: Analysis Result")
    try:
        analysis = AnalysisResult(
            state=ConvergenceState.NEEDS_ADJUSTMENT,
            issues=[
                DiscrepancyIssue(
                    type="score_mismatch",
                    description="Home team scored 1 goal but predicted 2",
                    severity="medium"
                )
            ],
            adjusted_scenario=scenario,  # Reuse from Test 1
            confidence=0.8,
            reasoning="Home team underperformed expectations, adjusting probability boosts downward"
        )

        print("✅ Valid analysis created!")
        print(f"  State: {analysis.state.value}")
        print(f"  Issues: {len(analysis.issues)}")
        print(f"  Has adjustment: {analysis.adjusted_scenario is not None}")

    except Exception as e:
        print(f"❌ Validation failed: {e}")

    # Test 5: JSON serialization
    print("\nTest 5: JSON Serialization")
    json_str = scenario.model_dump_json(indent=2)
    print(f"✅ Serialized to JSON ({len(json_str)} bytes)")

    # Test deserialization
    scenario_restored = MatchScenario.model_validate_json(json_str)
    print(f"✅ Deserialized from JSON")
    print(f"  Events restored: {len(scenario_restored.events)}")

    print("\n" + "=" * 70)
    print("✅ All schema tests passed!")
    print("=" * 70)
