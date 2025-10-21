"""
Event-Based Simulation Engine
설계 문서 Section 4 정확히 구현

90분 분 단위 이벤트 기반 시뮬레이션
"""

import random
import numpy as np
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from .scenario_guide import ScenarioGuide


# EPL 기준 통계 (재캘리브레이션)
# EPL 평균: 2.8골/경기 = 1.4골/팀
# 역산: 1.4골 달성을 위한 파라미터
EPL_BASELINE = {
    # 득점 관련
    "avg_goals_per_game": 2.8,
    "home_goals": 1.53,
    "away_goals": 1.27,

    # 슛 관련 (최종 캘리브레이션)
    # 목표: 2.8골/경기 = 1.4골/팀
    # 보정 계수를 고려한 역산
    "shots_per_game": 26.4,  # 양팀 합
    "shot_per_minute": 0.165,  # 조정: 0.145 → 0.165
    "shot_on_target_ratio": 0.35,  # 조정: 0.33 → 0.35
    "goal_conversion_on_target": 0.33,  # 조정: 0.325 → 0.33

    # 기타 이벤트
    "corners_per_game": 10.6,
    "corner_per_minute": 0.059,  # 10.6 / (90*2)
    "fouls_per_game": 22.1,
    "foul_per_minute": 0.123,
    "yellow_cards_per_game": 3.8,
    "red_cards_per_game": 0.28,
    "penalties_per_game": 0.13,

    # 점유율
    "avg_possession": 50,  # 50-50

    # 승률 분포
    "home_win_rate": 0.46,
    "draw_rate": 0.27,
    "away_win_rate": 0.27
}


@dataclass
class MatchParameters:
    """경기 파라미터"""
    home_team: Dict
    away_team: Dict
    home_formation: str = "4-3-3"
    away_formation: str = "4-3-3"


@dataclass
class MatchContext:
    """현재 경기 상황"""
    minute: int
    score: Dict[str, int]
    possession: Dict[str, float]
    stamina: Dict[str, float]
    formation: Dict[str, str]
    attacking_team: str
    defending_team: str


class EventProbabilityCalculator:
    """
    현재 경기 상황에서 이벤트 확률 계산
    설계 문서 Section 4.2
    """

    def __init__(self, baseline: Dict = None):
        """
        Args:
            baseline: EPL 기준 통계 (기본: EPL_BASELINE)
        """
        self.baseline = baseline or EPL_BASELINE.copy()

    def calculate(
        self,
        context: MatchContext,
        params: MatchParameters,
        boost: Optional[Dict] = None
    ) -> Dict[str, float]:
        """
        현재 상황에서 이벤트 확률 계산

        Args:
            context: 경기 상황
            params: 경기 파라미터
            boost: 서사 가이드의 확률 부스트

        Returns:
            이벤트별 확률
        """
        # 1. 기본 확률
        probs = self.baseline.copy()

        # 2. 팀 능력치 보정
        probs = self._adjust_for_team_strength(probs, context, params)

        # 3. 전술 보정
        probs = self._adjust_for_tactics(probs, context, params)

        # 4. 경기 상황 보정
        probs = self._adjust_for_match_state(probs, context)

        # 5. 체력/시간 보정
        probs = self._adjust_for_fatigue(probs, context)

        # 6. 서사 부스트
        if boost:
            probs = self._apply_boost(probs, boost, context)

        return probs

    def _adjust_for_team_strength(
        self,
        probs: Dict,
        context: MatchContext,
        params: MatchParameters
    ) -> Dict:
        """
        팀 능력치 기반 보정
        공격력 vs 수비력
        """
        # Get team stats
        attacking_team = params.home_team if context.attacking_team == "home" else params.away_team
        defending_team = params.away_team if context.attacking_team == "home" else params.home_team

        # Attack and defense ratings (0-100)
        attack_rating = attacking_team.get("attack_strength", 75) / 100.0
        defense_rating = defending_team.get("defense_strength", 75) / 100.0

        # Strength ratio
        strength_ratio = attack_rating / max(defense_rating, 0.5)

        # Adjust shot rate
        probs["shot_per_minute"] *= strength_ratio

        return probs

    def _adjust_for_tactics(
        self,
        probs: Dict,
        context: MatchContext,
        params: MatchParameters
    ) -> Dict:
        """
        전술적 매치업 보정
        """
        attacking_team = params.home_team if context.attacking_team == "home" else params.away_team
        defending_team = params.away_team if context.attacking_team == "home" else params.home_team

        att_formation = context.formation[context.attacking_team]
        def_formation = context.formation[context.defending_team]

        # Formation matchup adjustments
        # 4-3-3 attacks well
        if att_formation in ["4-3-3", "4-2-3-1"]:
            probs["shot_per_minute"] *= 1.12

        # 5-3-2 defends well
        if def_formation in ["5-3-2", "5-4-1"]:
            probs["shot_per_minute"] *= 0.88

        # Press intensity
        press = defending_team.get("press_intensity", 70)
        if press > 80:
            probs["shot_per_minute"] *= 0.92
            probs["foul_per_minute"] *= 1.25

        return probs

    def _adjust_for_match_state(self, probs: Dict, context: MatchContext) -> Dict:
        """
        스코어 상황 보정
        """
        score_diff = context.score[context.attacking_team] - context.score[context.defending_team]

        if score_diff < 0:  # Losing - attack more
            probs["shot_per_minute"] *= 1.18
        elif score_diff > 0:  # Winning - defend more
            probs["shot_per_minute"] *= 0.85

        # Possession influence
        possession_share = context.possession[context.attacking_team]
        probs["shot_per_minute"] *= (possession_share / 50.0)

        return probs

    def _adjust_for_fatigue(self, probs: Dict, context: MatchContext) -> Dict:
        """
        체력/시간 보정
        """
        if context.minute > 70:
            # Fatigue increases shot attempts (desperation) but decreases quality
            fatigue_factor = (100 - context.stamina[context.attacking_team]) / 100.0
            probs["shot_per_minute"] *= (1 + fatigue_factor * 0.25)
            probs["shot_on_target_ratio"] *= (1 - fatigue_factor * 0.15)

        return probs

    def _apply_boost(self, probs: Dict, boost: Dict, context: MatchContext) -> Dict:
        """
        서사 부스트 적용
        """
        # Only apply boost if it's for the attacking team
        if boost["team"] != context.attacking_team:
            return probs

        event_type = boost["event_type"]
        multiplier = boost["multiplier"]

        # Apply boost based on event type
        if event_type == "wing_breakthrough":
            probs["shot_per_minute"] *= multiplier
        elif event_type == "goal":
            probs["goal_conversion_on_target"] *= multiplier
        elif event_type == "shot_on_target":
            probs["shot_on_target_ratio"] *= multiplier
        elif event_type == "corner":
            probs["corner_per_minute"] *= multiplier

        return probs


class EventSampler:
    """
    확률에 따라 이벤트 샘플링
    설계 문서 Section 4.2
    """

    def sample(self, event_probs: Dict, context: MatchContext) -> Optional[Dict]:
        """
        확률 기반 이벤트 생성

        Args:
            event_probs: 이벤트별 확률
            context: 경기 상황

        Returns:
            발생한 이벤트 또는 None
        """
        # Shot?
        if random.random() < event_probs["shot_per_minute"]:
            return self._resolve_shot(event_probs, context)

        # Corner?
        if random.random() < event_probs["corner_per_minute"]:
            return {
                "type": "corner",
                "team": context.attacking_team,
                "minute": context.minute
            }

        # Foul?
        if random.random() < event_probs["foul_per_minute"]:
            return self._resolve_foul(event_probs, context)

        return None

    def _resolve_shot(self, probs: Dict, context: MatchContext) -> Dict:
        """
        슛 → 온타겟 → 득점 체인
        """
        # On target?
        if random.random() < probs["shot_on_target_ratio"]:
            # Goal?
            if random.random() < probs["goal_conversion_on_target"]:
                return {
                    "type": "goal",
                    "team": context.attacking_team,
                    "minute": context.minute
                }
            return {
                "type": "shot_on_target",
                "team": context.attacking_team,
                "minute": context.minute
            }

        return {
            "type": "shot_off_target",
            "team": context.attacking_team,
            "minute": context.minute
        }

    def _resolve_foul(self, probs: Dict, context: MatchContext) -> Dict:
        """
        파울 해결
        """
        return {
            "type": "foul",
            "team": context.defending_team,  # Defending team commits foul
            "minute": context.minute
        }


class EventBasedSimulationEngine:
    """
    분 단위 이벤트 기반 시뮬레이션
    설계 문서 Section 4 구현
    """

    def __init__(self):
        """Initialize engine"""
        self.probability_calculator = EventProbabilityCalculator()
        self.event_sampler = EventSampler()

    def simulate_match(
        self,
        params: MatchParameters,
        scenario_guide: ScenarioGuide
    ) -> Dict:
        """
        90분 시뮬레이션 (1분 단위)

        Args:
            params: 경기 파라미터
            scenario_guide: 시나리오 가이드

        Returns:
            {
                "final_score": {"home": 2, "away": 1},
                "events": [...],
                "narrative_adherence": 0.82
            }
        """
        # Initialize state
        state = {
            "minute": 0,
            "score": {"home": 0, "away": 0},
            "events": [],
            "possession": {"home": 50, "away": 50},
            "stamina": {"home": 100, "away": 100},
            "formation": {
                "home": params.home_formation,
                "away": params.away_formation
            }
        }

        # 90-minute loop
        for minute in range(90):
            state["minute"] = minute

            # 1. Determine possession
            possession_team = self._determine_possession(params, state)

            # 2. Get scenario boost for this minute
            boost = scenario_guide.get_boost_at(minute)

            # 3. Create context
            context = MatchContext(
                minute=minute,
                score=state["score"].copy(),
                possession=state["possession"].copy(),
                stamina=state["stamina"].copy(),
                formation=state["formation"].copy(),
                attacking_team=possession_team,
                defending_team="away" if possession_team == "home" else "home"
            )

            # 4. Calculate event probabilities
            event_probs = self.probability_calculator.calculate(context, params, boost)

            # 5. Sample event
            event = self.event_sampler.sample(event_probs, context)

            # 6. Resolve event
            if event:
                self._resolve_event(event, state)

            # 7. Update state
            self._update_state(state, minute, params)

        # 8. Calculate narrative adherence
        narrative_adherence = self._calculate_adherence(state, scenario_guide)

        return {
            "final_score": state["score"],
            "events": state["events"],
            "narrative_adherence": narrative_adherence,
            "event_statistics": self._calculate_event_statistics(state)
        }

    def _determine_possession(self, params: MatchParameters, state: Dict) -> str:
        """
        점유 팀 결정
        """
        # Base possession on team strength
        home_midfield = params.home_team.get("midfield_strength", 75)
        away_midfield = params.away_team.get("midfield_strength", 75)

        total = home_midfield + away_midfield
        home_possession = home_midfield / total * 100

        # Add some randomness
        home_possession += random.gauss(0, 10)
        home_possession = max(30, min(70, home_possession))

        # Update state
        state["possession"]["home"] = home_possession
        state["possession"]["away"] = 100 - home_possession

        # Determine who has possession this minute
        return "home" if random.random() < (home_possession / 100) else "away"

    def _resolve_event(self, event: Dict, state: Dict):
        """
        이벤트 해결 및 상태 업데이트
        """
        # Add event to history
        state["events"].append(event)

        # If goal, update score
        if event["type"] == "goal":
            state["score"][event["team"]] += 1

    def _update_state(self, state: Dict, minute: int, params: MatchParameters):
        """
        상태 업데이트 (체력, 포메이션 등)
        """
        # Stamina decay
        if minute > 60:
            decay_rate = 0.5  # 0.5% per minute
            state["stamina"]["home"] = max(50, state["stamina"]["home"] - decay_rate)
            state["stamina"]["away"] = max(50, state["stamina"]["away"] - decay_rate)

    def _calculate_adherence(
        self,
        state: Dict,
        scenario_guide: ScenarioGuide
    ) -> float:
        """
        시나리오와 실제 결과의 일치율
        설계 문서 Section 4.2
        """
        adherence_score = 0.0
        expected_events = scenario_guide.events

        if not expected_events:
            return 1.0  # No expectations = perfect adherence

        for expected_event in expected_events:
            # Find matching events in actual results
            start, end = expected_event.minute_range
            event_type = expected_event.type.value

            matching_events = [
                e for e in state["events"]
                if e["type"] == event_type
                and start <= e["minute"] <= end
                and (expected_event.team is None or e.get("team") == expected_event.team)
            ]

            if matching_events:
                adherence_score += 1.0

        return adherence_score / len(expected_events)

    def _calculate_event_statistics(self, state: Dict) -> Dict:
        """
        이벤트 통계 계산
        """
        events = state["events"]

        return {
            "total_shots": len([e for e in events if "shot" in e["type"]]),
            "shots_on_target": len([e for e in events if e["type"] == "shot_on_target"]),
            "goals": len([e for e in events if e["type"] == "goal"]),
            "corners": len([e for e in events if e["type"] == "corner"]),
            "fouls": len([e for e in events if e["type"] == "foul"]),
            "goal_timing": {
                "0-30min": len([e for e in events if e["type"] == "goal" and e["minute"] < 30]),
                "30-60min": len([e for e in events if e["type"] == "goal" and 30 <= e["minute"] < 60]),
                "60-90min": len([e for e in events if e["type"] == "goal" and e["minute"] >= 60])
            }
        }


# Helper function to create match parameters
def create_match_parameters(
    home_team: Dict,
    away_team: Dict,
    home_formation: str = "4-3-3",
    away_formation: str = "4-3-3"
) -> MatchParameters:
    """
    경기 파라미터 생성

    Args:
        home_team: {"attack_strength": 80, "defense_strength": 75, ...}
        away_team: {"attack_strength": 82, "defense_strength": 78, ...}
        home_formation: "4-3-3"
        away_formation: "4-3-3"

    Returns:
        MatchParameters
    """
    return MatchParameters(
        home_team=home_team,
        away_team=away_team,
        home_formation=home_formation,
        away_formation=away_formation
    )
