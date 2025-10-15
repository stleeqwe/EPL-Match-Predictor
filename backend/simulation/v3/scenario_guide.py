"""
Scenario Guide v3
AI 생성 시나리오를 분 단위 확률 부스트로 변환

핵심 기능:
1. 시나리오 이벤트 시퀀스를 분별 부스트 맵으로 파싱
2. 특정 분의 부스트 반환
3. 서사 일치율 계산용 예상 이벤트 추적
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import sys
import os

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from v3.data_classes import NarrativeBoost


@dataclass
class ExpectedEvent:
    """예상 이벤트 (서사 일치율 계산용)"""
    minute_range: tuple  # (start, end)
    type: str
    team: str
    occurred: bool = False  # 실제 발생 여부


class ScenarioGuide:
    """
    AI 생성 시나리오 → 확률 부스트 변환

    시나리오 예시:
    {
        'id': 'SYNTH_001',
        'events': [
            {
                'minute_range': [10, 25],
                'type': 'wing_breakthrough',
                'actor': 'Son',
                'team': 'home',
                'probability_boost': 2.5
            },
            {
                'minute_range': [15, 30],
                'type': 'goal',
                'team': 'home',
                'probability_boost': 1.8
            }
        ]
    }
    """

    def __init__(self, scenario: Dict):
        """
        Args:
            scenario: AI가 생성한 시나리오 딕셔너리
        """
        self.scenario = scenario
        self.boosts_by_minute = self._parse_events()
        self.expected_events = self._create_expected_events()

    def _parse_events(self) -> Dict[int, NarrativeBoost]:
        """
        이벤트 시퀀스 → 분별 부스트 맵

        Returns:
            {
                10: NarrativeBoost(...),
                11: NarrativeBoost(...),
                ...
            }
        """
        boosts = {}

        for event in self.scenario.get('events', []):
            minute_range = event['minute_range']
            start_minute = minute_range[0]
            end_minute = minute_range[1]

            for minute in range(start_minute, end_minute + 1):
                boost = NarrativeBoost(
                    type=event['type'],
                    multiplier=event.get('probability_boost', 1.0),
                    team=event.get('team', 'home'),
                    actor=event.get('actor'),
                    reason=event.get('reason')
                )

                # 같은 분에 여러 부스트가 있으면 마지막 것 사용
                # (또는 평균/최대값 등 다른 전략 가능)
                boosts[minute] = boost

        return boosts

    def _create_expected_events(self) -> List[ExpectedEvent]:
        """
        예상 이벤트 목록 생성 (서사 일치율 계산용)

        Returns:
            ExpectedEvent 리스트
        """
        expected = []

        for event in self.scenario.get('events', []):
            expected_event = ExpectedEvent(
                minute_range=(event['minute_range'][0], event['minute_range'][1]),
                type=event['type'],
                team=event.get('team', 'home')
            )
            expected.append(expected_event)

        return expected

    def get_boost_at(self, minute: int) -> Optional[NarrativeBoost]:
        """
        특정 분의 부스트 반환

        Args:
            minute: 분 (0-90)

        Returns:
            NarrativeBoost 또는 None
        """
        return self.boosts_by_minute.get(minute)

    def mark_event_occurred(self, minute: int, event_type: str, team: str):
        """
        실제 발생한 이벤트 기록 (서사 일치율 계산용)

        Args:
            minute: 발생 분
            event_type: 이벤트 타입
            team: 팀
        """
        for expected in self.expected_events:
            if expected.occurred:
                continue  # 이미 발생 처리됨

            # 매칭 조건: 분 범위 + 타입 + 팀
            if (expected.minute_range[0] <= minute <= expected.minute_range[1]
                and expected.type == event_type
                and expected.team == team):
                expected.occurred = True
                break

    def calculate_adherence(self) -> float:
        """
        서사 일치율 계산

        Returns:
            일치율 (0.0-1.0)
        """
        if len(self.expected_events) == 0:
            return 1.0  # 예상 이벤트 없으면 100%

        occurred_count = sum(1 for e in self.expected_events if e.occurred)
        return occurred_count / len(self.expected_events)


# ==========================================================================
# Testing
# ==========================================================================

def test_scenario_guide():
    """ScenarioGuide 테스트"""
    print("=== ScenarioGuide 테스트 ===\n")

    # 테스트 시나리오
    scenario = {
        'id': 'TEST_001',
        'name': '측면 돌파 → 득점',
        'events': [
            {
                'minute_range': [10, 20],
                'type': 'wing_breakthrough',
                'team': 'home',
                'actor': 'Son',
                'probability_boost': 2.0
            },
            {
                'minute_range': [15, 25],
                'type': 'goal',
                'team': 'home',
                'probability_boost': 1.5
            }
        ]
    }

    guide = ScenarioGuide(scenario)

    # Test 1: 부스트 맵 파싱
    print("Test 1: 부스트 맵 파싱")
    boost_15 = guide.get_boost_at(15)
    print(f"  15분 부스트: {boost_15}")
    print(f"  type={boost_15.type}, multiplier={boost_15.multiplier}")
    assert boost_15 is not None
    assert boost_15.type == 'goal'  # 15분은 goal 부스트 (마지막 것)
    print(f"  ✅ 부스트 맵 파싱 성공\n")

    # Test 2: 예상 이벤트 생성
    print("Test 2: 예상 이벤트 생성")
    print(f"  예상 이벤트 수: {len(guide.expected_events)}")
    for i, event in enumerate(guide.expected_events):
        print(f"    {i+1}. {event.type} ({event.minute_range[0]}-{event.minute_range[1]}분)")
    assert len(guide.expected_events) == 2
    print(f"  ✅ 예상 이벤트 생성 성공\n")

    # Test 3: 서사 일치율 계산
    print("Test 3: 서사 일치율 계산")

    # 초기 상태
    adherence_before = guide.calculate_adherence()
    print(f"  초기 일치율: {adherence_before:.0%}")
    assert adherence_before == 0.0

    # 이벤트 발생 기록
    guide.mark_event_occurred(minute=12, event_type='wing_breakthrough', team='home')
    adherence_mid = guide.calculate_adherence()
    print(f"  wing_breakthrough 발생 후: {adherence_mid:.0%}")
    assert adherence_mid == 0.5

    guide.mark_event_occurred(minute=18, event_type='goal', team='home')
    adherence_after = guide.calculate_adherence()
    print(f"  goal 발생 후: {adherence_after:.0%}")
    assert adherence_after == 1.0

    print(f"  ✅ 서사 일치율 계산 성공\n")

    # Test 4: 범위 밖 이벤트
    print("Test 4: 범위 밖 이벤트 (영향 없음)")
    guide2 = ScenarioGuide(scenario)
    guide2.mark_event_occurred(minute=5, event_type='wing_breakthrough', team='home')
    adherence = guide2.calculate_adherence()
    print(f"  5분 이벤트 (범위 밖): 일치율 {adherence:.0%}")
    assert adherence == 0.0  # 범위 밖이라 카운트 안됨
    print(f"  ✅ 범위 검증 성공\n")

    print("=" * 50)
    print("✅ ScenarioGuide 모든 테스트 통과!")
    print("=" * 50)


if __name__ == "__main__":
    test_scenario_guide()
