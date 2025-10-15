"""
Event Probability Calculator v3
서사 부스트를 적용할 수 있는 이벤트 확률 계산기

핵심 기능:
1. EPL Baseline 기반 기본 확률 계산
2. 팀 능력치 보정
3. 홈 어드밴티지 적용 (홈 승률 46% 반영)
4. 전술 매치업 반영
5. 경기 상황 (스코어, 시간) 반영
6. 체력 감소 반영
7. 서사 부스트 적용 ⭐
"""

from typing import Dict, Optional
import sys
import os

# 상대 import를 위한 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# 직접 파일 import (순환 import 방지)
import importlib.util
spec = importlib.util.spec_from_file_location("epl_baseline_v3", os.path.join(parent_dir, "shared", "epl_baseline_v3.py"))
epl_baseline_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(epl_baseline_module)
EPL_BASELINE_V3 = epl_baseline_module.EPL_BASELINE_V3

from v3.data_classes import MatchContext, NarrativeBoost, MatchState


class EventProbabilityCalculator:
    """
    이벤트 확률 계산기

    현재 경기 상황과 서사 부스트를 고려하여
    각 이벤트의 발생 확률을 계산합니다.
    """

    def __init__(self, baseline: Dict = None):
        """
        Args:
            baseline: EPL 기준 통계 (기본값: EPL_BASELINE_V3)
        """
        self.baseline = baseline or EPL_BASELINE_V3

    def calculate(self, context: MatchContext, boost: Optional[NarrativeBoost] = None) -> Dict[str, float]:
        """
        이벤트 확률 계산 (메인 메서드)

        Args:
            context: 경기 컨텍스트 (현재 상태)
            boost: 서사 부스트 (선택사항)

        Returns:
            {
                'shot_rate': 0.15,          # 분당 슛 확률
                'shot_on_target_ratio': 0.40, # 온타겟 비율
                'goal_conversion': 0.11,     # 온타겟 중 득점 확률
                'corner_rate': 0.10,         # 분당 코너킥 확률
                'foul_rate': 0.08           # 분당 파울 확률
            }
        """
        # 1. 기본 확률 (EPL Baseline)
        probs = {
            'shot_rate': self.baseline['shot_per_minute'],
            'shot_on_target_ratio': self.baseline['shot_on_target_ratio'],
            'goal_conversion': self.baseline['goal_conversion_on_target'],
            'corner_rate': self.baseline['corner_per_minute'],
            'foul_rate': self.baseline['foul_per_minute']
        }

        # 2. 팀 능력치 보정
        probs = self._adjust_for_team_strength(probs, context)

        # 3. 홈 어드밴티지 ⭐
        probs = self._adjust_for_home_advantage(probs, context)

        # 4. 전술 보정
        probs = self._adjust_for_tactics(probs, context)

        # 5. 경기 상황 보정 (스코어, 시간)
        probs = self._adjust_for_match_state(probs, context)

        # 6. 체력 보정
        probs = self._adjust_for_fatigue(probs, context)

        # 7. 서사 부스트 적용 ⭐
        if boost:
            probs = self._apply_narrative_boost(probs, boost, context)

        return probs

    def _adjust_for_team_strength(self, probs: Dict, context: MatchContext) -> Dict:
        """
        팀 능력치 보정

        공격력 vs 수비력 비율로 슛 확률 조정
        """
        attack_rating = context.attacking_team.attack_strength / 80.0  # 80 = 기준값
        defense_rating = context.defending_team.defense_strength / 80.0

        strength_ratio = attack_rating / defense_rating

        # 슛 확률 조정
        probs['shot_rate'] *= strength_ratio

        # 드리블 성공률 (향후 확장용)
        # probs['dribble_success'] *= strength_ratio

        return probs

    def _adjust_for_home_advantage(self, probs: Dict, context: MatchContext) -> Dict:
        """
        홈 어드밴티지 보정

        홈팀이 점유권을 가질 때 슛 확률과 득점 확률 약간 증가
        EPL 홈 승률 46% vs 원정 27% 반영
        """
        # 홈팀이 공격 중일 때만 보너스
        if context.possession_team == "home":
            probs['shot_rate'] *= 1.08      # 8% 증가
            probs['goal_conversion'] *= 1.05 # 5% 증가

        return probs

    def _adjust_for_tactics(self, probs: Dict, context: MatchContext) -> Dict:
        """
        전술 보정

        1. 포메이션별 공격 성향
        2. 압박 강도에 따른 패스 성공률
        """
        # 1. 포메이션 보정
        attacking_formation = (context.formation_home if context.possession_team == "home"
                              else context.formation_away)

        formation_modifier = self.baseline['tactical_coefficients']['formation_attack_modifier'].get(
            attacking_formation, 1.0
        )
        probs['shot_rate'] *= formation_modifier

        # 2. 압박 강도 보정
        defending_press = context.defending_team.press_intensity

        if defending_press > 80:
            # 고강도 압박 → 패스 어려움, 턴오버 증가
            press_effect = self.baseline['tactical_coefficients']['press_intensity_effect']['high']
        elif defending_press > 60:
            press_effect = self.baseline['tactical_coefficients']['press_intensity_effect']['medium']
        else:
            press_effect = self.baseline['tactical_coefficients']['press_intensity_effect']['low']

        # 압박이 강하면 슛 기회 감소
        probs['shot_rate'] *= press_effect['pass_success']

        return probs

    def _adjust_for_match_state(self, probs: Dict, context: MatchContext) -> Dict:
        """
        경기 상황 보정

        1. 스코어 차이에 따른 공격 성향
        2. 시간대별 득점 확률
        """
        # 1. 스코어 상황 보정
        match_state = context.match_state_attacking

        if match_state == MatchState.LEADING:
            # 이기고 있을 때 → 공격 감소, 수비 강화
            state_mod = self.baseline['match_state_modifiers']['leading']
            probs['shot_rate'] *= state_mod['shot_rate']
        elif match_state == MatchState.TRAILING:
            # 지고 있을 때 → 공격 증가, 리스크 감수
            state_mod = self.baseline['match_state_modifiers']['trailing']
            probs['shot_rate'] *= state_mod['shot_rate']
        # else: DRAWING → 변화 없음

        # 2. 시간대별 득점 확률 (향후 확장)
        # 현재는 단순화: 후반 75분 이후 득점 약간 증가
        if context.minute >= 75:
            probs['goal_conversion'] *= 1.08  # 8% 증가 (피로 + 시간 압박)

        return probs

    def _adjust_for_fatigue(self, probs: Dict, context: MatchContext) -> Dict:
        """
        체력 감소 보정

        70분 이후 체력 감소에 따른 슛 확률 증가 (정확도는 감소하지만 시도는 증가)
        """
        if context.minute >= 80:
            fatigue_factor = self.baseline['fatigue_effect']['80-90']
        elif context.minute >= 70:
            fatigue_factor = self.baseline['fatigue_effect']['70-80']
        else:
            fatigue_factor = 1.0

        # 체력이 떨어지면 슛 시도는 증가 (다급함)
        probs['shot_rate'] *= (1.0 + (1.0 - fatigue_factor) * 0.5)

        # 온타겟 비율은 감소 (정확도 떨어짐)
        probs['shot_on_target_ratio'] *= fatigue_factor

        return probs

    def _apply_narrative_boost(self, probs: Dict, boost: NarrativeBoost, context: MatchContext) -> Dict:
        """
        서사 부스트 적용 ⭐

        특정 이벤트 타입의 확률을 배수로 증가

        Args:
            probs: 현재 확률
            boost: 서사 부스트
            context: 경기 컨텍스트 (팀 확인용)

        Returns:
            조정된 확률
        """
        # 부스트가 현재 공격 팀에 적용되는지 확인
        if boost.team != context.possession_team:
            return probs  # 다른 팀 부스트는 적용 안함

        # 이벤트 타입별 부스트 적용
        if boost.type == 'wing_breakthrough':
            # 측면 돌파 → 슛 증가
            probs['shot_rate'] *= boost.multiplier

        elif boost.type == 'goal':
            # 득점 → 득점 전환율 증가
            probs['goal_conversion'] *= boost.multiplier

        elif boost.type == 'corner':
            # 코너킥 → 코너킥 확률 증가
            probs['corner_rate'] *= boost.multiplier

        elif boost.type == 'set_piece':
            # 세트피스 → 코너킥 + 프리킥 증가
            probs['corner_rate'] *= boost.multiplier
            probs['foul_rate'] *= boost.multiplier * 0.5  # 파울도 약간 증가

        elif boost.type == 'counter_attack':
            # 역습 → 슛 + 온타겟 비율 증가
            probs['shot_rate'] *= boost.multiplier
            probs['shot_on_target_ratio'] *= min(boost.multiplier, 1.5)  # 온타겟은 최대 1.5배

        elif boost.type == 'central_penetration':
            # 중앙 돌파 → 슛 증가 (wing보다 약간 낮음)
            probs['shot_rate'] *= boost.multiplier * 0.9

        else:
            # 알 수 없는 타입 → 슛 확률 기본 증가
            probs['shot_rate'] *= boost.multiplier

        return probs


# ==========================================================================
# Testing
# ==========================================================================

def test_event_calculator():
    """EventProbabilityCalculator 테스트"""
    from v3.data_classes import create_test_context

    print("=== EventProbabilityCalculator 테스트 ===\n")

    calculator = EventProbabilityCalculator()

    # Test 1: 기본 확률 계산 (부스트 없음)
    print("Test 1: 기본 확률 계산")
    context = create_test_context(minute=20, score_home=0, score_away=0)
    probs = calculator.calculate(context)

    print(f"  shot_rate: {probs['shot_rate']:.4f}")
    print(f"  shot_on_target_ratio: {probs['shot_on_target_ratio']:.2f}")
    print(f"  goal_conversion: {probs['goal_conversion']:.2f}")
    print(f"  ✅ 기본 계산 성공\n")

    # Test 2: 서사 부스트 적용
    print("Test 2: 서사 부스트 (wing_breakthrough, 2.5배)")
    boost = NarrativeBoost(
        type="wing_breakthrough",
        multiplier=2.5,
        team="home",
        actor="Son"
    )
    probs_boosted = calculator.calculate(context, boost)

    print(f"  shot_rate (부스트 전): {probs['shot_rate']:.4f}")
    print(f"  shot_rate (부스트 후): {probs_boosted['shot_rate']:.4f}")
    print(f"  증가율: {(probs_boosted['shot_rate'] / probs['shot_rate']):.2f}x")

    assert probs_boosted['shot_rate'] > probs['shot_rate'] * 2.4, "부스트 적용 안됨!"
    print(f"  ✅ 부스트 적용 성공\n")

    # Test 3: 경기 상황별 확률 변화
    print("Test 3: 경기 상황별 확률 변화")

    # 3a. 동점 (기준)
    context_draw = create_test_context(minute=30, score_home=0, score_away=0)
    probs_draw = calculator.calculate(context_draw)

    # 3b. 리드 중
    context_leading = create_test_context(minute=30, score_home=2, score_away=0)
    probs_leading = calculator.calculate(context_leading)

    # 3c. 지고 있음
    context_trailing = create_test_context(minute=30, score_home=0, score_away=2)
    probs_trailing = calculator.calculate(context_trailing)

    print(f"  동점: shot_rate={probs_draw['shot_rate']:.4f}")
    print(f"  리드 중: shot_rate={probs_leading['shot_rate']:.4f} (기준 대비 {probs_leading['shot_rate']/probs_draw['shot_rate']:.2f}x)")
    print(f"  지는 중: shot_rate={probs_trailing['shot_rate']:.4f} (기준 대비 {probs_trailing['shot_rate']/probs_draw['shot_rate']:.2f}x)")

    assert probs_trailing['shot_rate'] > probs_leading['shot_rate'], "지는 팀이 더 공격적이어야 함!"
    print(f"  ✅ 경기 상황 반영 성공\n")

    # Test 4: 체력 감소
    print("Test 4: 체력 감소 (후반 80분)")
    context_early = create_test_context(minute=20)
    context_late = create_test_context(minute=85)

    probs_early = calculator.calculate(context_early)
    probs_late = calculator.calculate(context_late)

    print(f"  20분: shot_rate={probs_early['shot_rate']:.4f}, on_target={probs_early['shot_on_target_ratio']:.2f}")
    print(f"  85분: shot_rate={probs_late['shot_rate']:.4f}, on_target={probs_late['shot_on_target_ratio']:.2f}")
    print(f"  슛 증가: {(probs_late['shot_rate'] / probs_early['shot_rate']):.2f}x")
    print(f"  정확도 감소: {(probs_late['shot_on_target_ratio'] / probs_early['shot_on_target_ratio']):.2f}x")

    assert probs_late['shot_rate'] > probs_early['shot_rate'], "후반에 슛 시도 증가해야 함!"
    assert probs_late['shot_on_target_ratio'] < probs_early['shot_on_target_ratio'], "후반에 정확도 감소해야 함!"
    print(f"  ✅ 체력 감소 반영 성공\n")

    print("=" * 50)
    print("✅ EventProbabilityCalculator 모든 테스트 통과!")
    print("=" * 50)


if __name__ == "__main__":
    test_event_calculator()
