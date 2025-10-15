"""
Scenario Guide
설계 문서 Section 4.2 구현

시나리오를 분별 부스트 맵으로 변환
"""

from typing import Dict, Optional
from .scenario import Scenario


class ScenarioGuide:
    """
    시나리오를 분 단위 부스트 맵으로 변환
    설계 문서 Section 4.2
    """

    def __init__(self, scenario: Scenario):
        """
        Args:
            scenario: Scenario 객체
        """
        self.scenario = scenario
        self.boosts_by_minute = self._parse_events()
        self.events = scenario.events  # For narrative adherence calculation

    def _parse_events(self) -> Dict[int, Dict]:
        """
        이벤트 시퀀스 → 분별 부스트 맵

        Returns:
            {
                15: {
                    "team": "home",
                    "event_type": "wing_breakthrough",
                    "multiplier": 2.5
                },
                ...
            }
        """
        boosts = {}

        for event in self.scenario.events:
            # minute_range is a tuple (start, end)
            start, end = event.minute_range

            for minute in range(start, end + 1):
                # Multiple events can overlap - use the highest boost
                if minute in boosts:
                    # If same event type, take higher boost
                    if boosts[minute]["event_type"] == event.type.value:
                        if event.probability_boost > boosts[minute]["multiplier"]:
                            boosts[minute] = {
                                "team": event.team,
                                "event_type": event.type.value,
                                "multiplier": event.probability_boost,
                                "actor": event.actor,
                                "method": event.method
                            }
                else:
                    boosts[minute] = {
                        "team": event.team,
                        "event_type": event.type.value,
                        "multiplier": event.probability_boost,
                        "actor": event.actor,
                        "method": event.method
                    }

        return boosts

    def get_boost_at(self, minute: int) -> Optional[Dict]:
        """
        특정 분의 부스트 반환

        Args:
            minute: 경기 시간 (0-89)

        Returns:
            부스트 정보 또는 None
        """
        return self.boosts_by_minute.get(minute, None)

    def get_events_in_range(self, start: int, end: int) -> list:
        """
        특정 시간 범위의 예상 이벤트 반환

        Args:
            start: 시작 분
            end: 종료 분

        Returns:
            해당 범위의 이벤트 리스트
        """
        events_in_range = []
        for event in self.scenario.events:
            event_start, event_end = event.minute_range
            # Check if ranges overlap
            if not (event_end < start or event_start > end):
                events_in_range.append(event)

        return events_in_range
