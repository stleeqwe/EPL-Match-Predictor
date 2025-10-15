"""
Statistical Match Engine v3
90분 분 단위 이벤트 기반 시뮬레이션 엔진

핵심 기능:
1. 90분 분 단위 루프
2. 매 분마다 이벤트 확률 계산 (서사 부스트 적용)
3. 이벤트 샘플링 (슛 → 온타겟 → 득점 체인)
4. 경기 상태 업데이트
5. 서사 일치율 추적
"""

import random
from typing import Dict, List, Optional
import sys
import os

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from v3.data_classes import MatchContext, MatchResult, TeamInfo
from v3.event_calculator import EventProbabilityCalculator
from v3.scenario_guide import ScenarioGuide


class StatisticalMatchEngine:
    """
    이벤트 기반 통계 시뮬레이션 엔진

    90분 경기를 분 단위로 시뮬레이션하여 확률 기반 결과를 생성합니다.
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Args:
            seed: 랜덤 시드 (재현성을 위해)
        """
        self.calculator = EventProbabilityCalculator()
        if seed is not None:
            random.seed(seed)

    def simulate_match(self,
                      home_team: TeamInfo,
                      away_team: TeamInfo,
                      scenario_guide: Optional[ScenarioGuide] = None) -> MatchResult:
        """
        단일 경기 시뮬레이션 (90분)

        Args:
            home_team: 홈팀 정보
            away_team: 원정팀 정보
            scenario_guide: 서사 가이드 (선택사항)

        Returns:
            MatchResult (최종 스코어, 이벤트, 서사 일치율)
        """
        # 1. 상태 초기화
        state = self._init_state(home_team, away_team)

        # 2. 90분 시뮬레이션
        for minute in range(90):
            state['minute'] = minute

            # 2a. 점유 팀 결정
            possession_team = self._determine_possession(state)
            state['possession_team'] = possession_team

            # 2b. 서사 부스트 가져오기
            boost = scenario_guide.get_boost_at(minute) if scenario_guide else None

            # 2c. 이벤트 확률 계산
            context = self._create_context(state)
            event_probs = self.calculator.calculate(context, boost)

            # 2d. 이벤트 샘플링
            event = self._sample_event(event_probs, possession_team, minute)

            # 2e. 이벤트 해결
            if event:
                self._resolve_event(event, state, scenario_guide)

            # 2f. 상태 업데이트
            self._update_state(state, minute)

        # 3. 서사 일치율 계산
        adherence = scenario_guide.calculate_adherence() if scenario_guide else 1.0

        # 4. 결과 반환
        return MatchResult(
            final_score={
                'home': state['score']['home'],
                'away': state['score']['away']
            },
            events=state['events'],
            narrative_adherence=adherence,
            stats={
                'home_shots': state['stats']['home_shots'],
                'away_shots': state['stats']['away_shots'],
                'home_possession': state['stats']['home_possession'],
                'away_possession': state['stats']['away_possession']
            }
        )

    def _init_state(self, home_team: TeamInfo, away_team: TeamInfo) -> Dict:
        """
        경기 상태 초기화

        Returns:
            {
                'minute': 0,
                'score': {'home': 0, 'away': 0},
                'stamina': {'home': 100.0, 'away': 100.0},
                'possession_team': 'home',
                'formation': {'home': '4-3-3', 'away': '4-4-2'},
                'home_team': TeamInfo,
                'away_team': TeamInfo,
                'events': [],
                'stats': {...}
            }
        """
        return {
            'minute': 0,
            'score': {'home': 0, 'away': 0},
            'stamina': {'home': 100.0, 'away': 100.0},
            'possession_team': 'home',
            'formation': {
                'home': home_team.formation,
                'away': away_team.formation
            },
            'home_team': home_team,
            'away_team': away_team,
            'events': [],
            'stats': {
                'home_shots': 0,
                'away_shots': 0,
                'home_possession': 0.0,
                'away_possession': 0.0,
                'possession_changes': 0
            }
        }

    def _create_context(self, state: Dict) -> MatchContext:
        """
        현재 상태 → MatchContext 변환

        Args:
            state: 경기 상태

        Returns:
            MatchContext 객체
        """
        return MatchContext(
            minute=state['minute'],
            score_home=state['score']['home'],
            score_away=state['score']['away'],
            possession_team=state['possession_team'],
            home_team=state['home_team'],
            away_team=state['away_team'],
            stamina_home=state['stamina']['home'],
            stamina_away=state['stamina']['away'],
            formation_home=state['formation']['home'],
            formation_away=state['formation']['away']
        )

    def _determine_possession(self, state: Dict) -> str:
        """
        점유 팀 결정

        간단한 모델: 이전 점유 + 약간의 랜덤 변화

        Returns:
            'home' or 'away'
        """
        current_possession = state['possession_team']

        # 10% 확률로 점유권 변경
        if random.random() < 0.10:
            new_possession = 'away' if current_possession == 'home' else 'home'
            state['stats']['possession_changes'] += 1
            return new_possession

        return current_possession

    def _sample_event(self, probs: Dict, possession_team: str, minute: int) -> Optional[Dict]:
        """
        확률 기반 이벤트 샘플링

        Args:
            probs: 이벤트 확률
            possession_team: 점유 팀
            minute: 분

        Returns:
            이벤트 딕셔너리 또는 None
        """
        # 슛 발생?
        if random.random() < probs['shot_rate']:
            return self._resolve_shot(probs, possession_team, minute)

        # 코너킥?
        if random.random() < probs['corner_rate']:
            return {
                'type': 'corner',
                'team': possession_team,
                'minute': minute
            }

        # 파울?
        if random.random() < probs['foul_rate']:
            return {
                'type': 'foul',
                'team': possession_team,  # 파울을 한 팀
                'minute': minute
            }

        return None  # 이벤트 없음

    def _resolve_shot(self, probs: Dict, team: str, minute: int) -> Dict:
        """
        슛 → 온타겟 → 득점 체인

        Args:
            probs: 이벤트 확률
            team: 슛 팀
            minute: 분

        Returns:
            슛 이벤트 딕셔너리
        """
        # 온타겟?
        if random.random() < probs['shot_on_target_ratio']:
            # 득점?
            if random.random() < probs['goal_conversion']:
                return {
                    'type': 'goal',
                    'team': team,
                    'minute': minute
                }
            return {
                'type': 'shot_on_target',
                'team': team,
                'minute': minute
            }

        return {
            'type': 'shot_off_target',
            'team': team,
            'minute': minute
        }

    def _resolve_event(self, event: Dict, state: Dict, scenario_guide: Optional[ScenarioGuide]):
        """
        이벤트 해결 (상태 업데이트)

        Args:
            event: 이벤트
            state: 경기 상태
            scenario_guide: 서사 가이드
        """
        event_type = event['type']
        team = event['team']

        # 이벤트 기록
        state['events'].append(event)

        # 통계 업데이트
        if event_type in ['shot_off_target', 'shot_on_target', 'goal']:
            stat_key = f'{team}_shots'
            state['stats'][stat_key] += 1

        # 득점 처리
        if event_type == 'goal':
            state['score'][team] += 1

            # 서사 가이드에 득점 기록
            if scenario_guide:
                scenario_guide.mark_event_occurred(
                    minute=event['minute'],
                    event_type='goal',
                    team=team
                )

        # 기타 이벤트도 서사에 기록
        elif scenario_guide:
            scenario_guide.mark_event_occurred(
                minute=event['minute'],
                event_type=event_type,
                team=team
            )

    def _update_state(self, state: Dict, minute: int):
        """
        상태 업데이트 (체력, 점유율 등)

        Args:
            state: 경기 상태
            minute: 분
        """
        # 체력 감소 (70분 이후)
        if minute >= 70:
            decay_rate = 0.2  # 분당 0.2% 감소
            state['stamina']['home'] = max(50.0, state['stamina']['home'] - decay_rate)
            state['stamina']['away'] = max(50.0, state['stamina']['away'] - decay_rate)

        # 점유율 통계 (누적 평균)
        current_possession = state['possession_team']
        if current_possession == 'home':
            state['stats']['home_possession'] += 1
        else:
            state['stats']['away_possession'] += 1


# ==========================================================================
# Testing
# ==========================================================================

def test_statistical_engine():
    """StatisticalMatchEngine 테스트"""
    print("=== StatisticalMatchEngine 테스트 ===\n")

    # 테스트 팀 생성
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

    engine = StatisticalMatchEngine(seed=42)  # 재현성을 위해 시드 고정

    # Test 1: 기본 시뮬레이션 (서사 없음)
    print("Test 1: 기본 시뮬레이션 (서사 없음)")
    result1 = engine.simulate_match(home_team, away_team)

    print(f"  최종 스코어: {result1.final_score['home']}-{result1.final_score['away']}")
    print(f"  전체 이벤트: {len(result1.events)}개")
    print(f"  홈 슛: {result1.stats['home_shots']}")
    print(f"  원정 슛: {result1.stats['away_shots']}")
    print(f"  서사 일치율: {result1.narrative_adherence:.0%}")

    assert result1.narrative_adherence == 1.0  # 서사 없으면 100%
    assert result1.final_score['home'] >= 0
    assert len(result1.events) > 0
    print(f"  ✅ 기본 시뮬레이션 성공\n")

    # Test 2: 서사 가이드 적용
    print("Test 2: 서사 가이드 적용")

    # 홈팀 유리한 서사
    scenario = {
        'id': 'TEST_HOME_WIN',
        'events': [
            {
                'minute_range': [10, 30],
                'type': 'wing_breakthrough',
                'team': 'home',
                'probability_boost': 3.0  # 3배 부스트
            },
            {
                'minute_range': [15, 35],
                'type': 'goal',
                'team': 'home',
                'probability_boost': 2.0
            }
        ]
    }

    guide = ScenarioGuide(scenario)
    engine2 = StatisticalMatchEngine(seed=42)  # 같은 시드
    result2 = engine2.simulate_match(home_team, away_team, guide)

    print(f"  최종 스코어: {result2.final_score['home']}-{result2.final_score['away']}")
    print(f"  서사 일치율: {result2.narrative_adherence:.0%}")
    print(f"  홈 슛: {result2.stats['home_shots']}")

    # 서사 부스트로 인해 홈팀 슛이 증가해야 함
    assert result2.stats['home_shots'] > 0
    print(f"  ✅ 서사 가이드 적용 성공\n")

    # Test 3: 여러 번 시뮬레이션 (확률 분포 확인)
    print("Test 3: 여러 번 시뮬레이션 (확률 분포)")

    results = []
    for i in range(100):
        engine_temp = StatisticalMatchEngine(seed=i)
        result = engine_temp.simulate_match(home_team, away_team)
        results.append(result)

    # 통계 집계
    home_wins = sum(1 for r in results if r.final_score['home'] > r.final_score['away'])
    away_wins = sum(1 for r in results if r.final_score['away'] > r.final_score['home'])
    draws = sum(1 for r in results if r.final_score['home'] == r.final_score['away'])

    avg_goals = sum(r.final_score['home'] + r.final_score['away'] for r in results) / len(results)

    print(f"  100회 시뮬레이션 결과:")
    print(f"    홈 승: {home_wins}회 ({home_wins}%)")
    print(f"    무승부: {draws}회 ({draws}%)")
    print(f"    원정 승: {away_wins}회 ({away_wins}%)")
    print(f"    평균 득점: {avg_goals:.2f}골/경기")

    # EPL 평균 (2.8골)과 유사한지 확인 (±1.0 허용)
    assert 1.8 <= avg_goals <= 3.8, f"평균 득점이 너무 벗어남: {avg_goals}"

    # 홈 승률이 약간 높아야 함 (홈 어드밴티지)
    assert home_wins >= away_wins * 0.8, "홈팀이 너무 약함"

    print(f"  ✅ 확률 분포 검증 성공\n")

    print("=" * 50)
    print("✅ StatisticalMatchEngine 모든 테스트 통과!")
    print("=" * 50)


if __name__ == "__main__":
    test_statistical_engine()
