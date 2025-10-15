"""
Performance Test for Statistical Engine v3
Week 1-2 최종 검증용 성능 테스트

검증 기준:
- 1,000회 시뮬레이션 < 20초
- 평균 득점 2.5-3.0
- 홈 승률 40-50%
- 서사 부스트 적용 시 확률 변화 확인
"""

import time
import sys
import os
from typing import List

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from v3.statistical_engine import StatisticalMatchEngine
from v3.data_classes import TeamInfo, MatchResult
from v3.scenario_guide import ScenarioGuide


def create_test_teams():
    """표준 테스트 팀 생성"""
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

    return home_team, away_team


def run_performance_test(n_simulations: int = 1000) -> dict:
    """
    대규모 성능 테스트

    Args:
        n_simulations: 시뮬레이션 횟수

    Returns:
        성능 지표 딕셔너리
    """
    print(f"=== Performance Test: {n_simulations}회 시뮬레이션 ===\n")

    home_team, away_team = create_test_teams()
    results: List[MatchResult] = []

    # 시간 측정 시작
    start_time = time.time()

    for i in range(n_simulations):
        engine = StatisticalMatchEngine(seed=i)
        result = engine.simulate_match(home_team, away_team)
        results.append(result)

        # 진행 상황 표시
        if (i + 1) % 100 == 0:
            elapsed = time.time() - start_time
            print(f"  진행: {i+1}/{n_simulations} ({elapsed:.2f}초 경과)")

    # 시간 측정 종료
    total_time = time.time() - start_time
    avg_time_per_match = total_time / n_simulations

    # 통계 집계
    home_wins = sum(1 for r in results if r.final_score['home'] > r.final_score['away'])
    away_wins = sum(1 for r in results if r.final_score['away'] > r.final_score['home'])
    draws = sum(1 for r in results if r.final_score['home'] == r.final_score['away'])

    avg_goals = sum(r.final_score['home'] + r.final_score['away'] for r in results) / len(results)
    avg_home_goals = sum(r.final_score['home'] for r in results) / len(results)
    avg_away_goals = sum(r.final_score['away'] for r in results) / len(results)

    avg_home_shots = sum(r.stats['home_shots'] for r in results) / len(results)
    avg_away_shots = sum(r.stats['away_shots'] for r in results) / len(results)

    return {
        'total_time': total_time,
        'avg_time_per_match': avg_time_per_match,
        'home_win_rate': home_wins / n_simulations,
        'draw_rate': draws / n_simulations,
        'away_win_rate': away_wins / n_simulations,
        'avg_goals': avg_goals,
        'avg_home_goals': avg_home_goals,
        'avg_away_goals': avg_away_goals,
        'avg_home_shots': avg_home_shots,
        'avg_away_shots': avg_away_shots
    }


def test_narrative_boost_impact():
    """서사 부스트 적용 전후 비교"""
    print("\n=== Narrative Boost Impact Test ===\n")

    home_team, away_team = create_test_teams()

    # 서사 없이 100회
    results_no_boost = []
    for i in range(100):
        engine = StatisticalMatchEngine(seed=i)
        result = engine.simulate_match(home_team, away_team)
        results_no_boost.append(result)

    # 홈팀 유리한 서사로 100회
    scenario = {
        'id': 'HOME_BOOST',
        'events': [
            {
                'minute_range': [10, 40],
                'type': 'wing_breakthrough',
                'team': 'home',
                'probability_boost': 2.5
            },
            {
                'minute_range': [15, 45],
                'type': 'goal',
                'team': 'home',
                'probability_boost': 2.0
            }
        ]
    }

    results_with_boost = []
    for i in range(100):
        guide = ScenarioGuide(scenario)
        engine = StatisticalMatchEngine(seed=i)
        result = engine.simulate_match(home_team, away_team, guide)
        results_with_boost.append(result)

    # 통계 비교
    stats_no_boost = {
        'home_win_rate': sum(1 for r in results_no_boost if r.final_score['home'] > r.final_score['away']) / 100,
        'avg_home_goals': sum(r.final_score['home'] for r in results_no_boost) / 100,
        'avg_home_shots': sum(r.stats['home_shots'] for r in results_no_boost) / 100,
        'avg_adherence': sum(r.narrative_adherence for r in results_no_boost) / 100
    }

    stats_with_boost = {
        'home_win_rate': sum(1 for r in results_with_boost if r.final_score['home'] > r.final_score['away']) / 100,
        'avg_home_goals': sum(r.final_score['home'] for r in results_with_boost) / 100,
        'avg_home_shots': sum(r.stats['home_shots'] for r in results_with_boost) / 100,
        'avg_adherence': sum(r.narrative_adherence for r in results_with_boost) / 100
    }

    print("부스트 없음:")
    print(f"  홈 승률: {stats_no_boost['home_win_rate']:.1%}")
    print(f"  홈 득점: {stats_no_boost['avg_home_goals']:.2f}골")
    print(f"  홈 슛: {stats_no_boost['avg_home_shots']:.1f}개")
    print(f"  서사 일치율: {stats_no_boost['avg_adherence']:.0%}")

    print("\n부스트 적용 (홈팀 유리):")
    print(f"  홈 승률: {stats_with_boost['home_win_rate']:.1%} (+{(stats_with_boost['home_win_rate'] - stats_no_boost['home_win_rate']):.1%}p)")
    print(f"  홈 득점: {stats_with_boost['avg_home_goals']:.2f}골 (+{(stats_with_boost['avg_home_goals'] - stats_no_boost['avg_home_goals']):.2f})")
    print(f"  홈 슛: {stats_with_boost['avg_home_shots']:.1f}개 (+{(stats_with_boost['avg_home_shots'] - stats_no_boost['avg_home_shots']):.1f})")
    print(f"  서사 일치율: {stats_with_boost['avg_adherence']:.0%}")

    # 검증
    assert stats_with_boost['home_win_rate'] > stats_no_boost['home_win_rate'], "부스트가 승률을 높여야 함"
    assert stats_with_boost['avg_home_goals'] > stats_no_boost['avg_home_goals'], "부스트가 득점을 높여야 함"
    assert stats_with_boost['avg_home_shots'] > stats_no_boost['avg_home_shots'], "부스트가 슛을 높여야 함"

    print("\n✅ 서사 부스트 효과 검증 완료")

    return stats_no_boost, stats_with_boost


def verify_criteria(metrics: dict) -> bool:
    """
    Week 1-2 검증 기준 충족 여부 확인

    검증 기준:
    - [x] 1,000회 시뮬 < 20초
    - [x] 평균 득점 2.5-3.0
    - [x] 홈 승률 40-50%
    - [x] 서사 부스트 적용 시 확률 변화 확인
    """
    print("\n" + "="*60)
    print("Week 1-2 검증 기준 충족 여부")
    print("="*60 + "\n")

    all_passed = True

    # 1. 성능 기준
    time_pass = metrics['total_time'] < 20.0
    print(f"[{'✅' if time_pass else '❌'}] 1,000회 시뮬레이션 < 20초")
    print(f"    실제: {metrics['total_time']:.2f}초 (경기당 {metrics['avg_time_per_match']*1000:.2f}ms)")
    all_passed = all_passed and time_pass

    # 2. 득점 기준
    goals_pass = 2.5 <= metrics['avg_goals'] <= 3.0
    print(f"\n[{'✅' if goals_pass else '❌'}] 평균 득점 2.5-3.0골")
    print(f"    실제: {metrics['avg_goals']:.2f}골 (홈 {metrics['avg_home_goals']:.2f}, 원정 {metrics['avg_away_goals']:.2f})")
    all_passed = all_passed and goals_pass

    # 3. 홈 승률 기준
    home_win_pass = 0.40 <= metrics['home_win_rate'] <= 0.50
    print(f"\n[{'✅' if home_win_pass else '❌'}] 홈 승률 40-50%")
    print(f"    실제: {metrics['home_win_rate']:.1%}")
    print(f"    분포: 홈승 {metrics['home_win_rate']:.1%} / 무승부 {metrics['draw_rate']:.1%} / 원정승 {metrics['away_win_rate']:.1%}")
    all_passed = all_passed and home_win_pass

    # 4. 추가 통계
    print(f"\n[ℹ️] 추가 통계")
    print(f"    평균 슛: 홈 {metrics['avg_home_shots']:.1f}, 원정 {metrics['avg_away_shots']:.1f}")

    print("\n" + "="*60)
    if all_passed:
        print("✅ Week 1-2 모든 검증 기준 통과!")
    else:
        print("❌ 일부 기준 미달 - 재조정 필요")
    print("="*60)

    return all_passed


if __name__ == "__main__":
    print("="*60)
    print("Week 1-2 Statistical Engine v3 최종 검증")
    print("="*60 + "\n")

    # 1. 성능 테스트 (1,000회)
    metrics = run_performance_test(1000)

    # 2. 서사 부스트 효과 테스트
    boost_stats = test_narrative_boost_impact()

    # 3. 검증 기준 확인
    passed = verify_criteria(metrics)

    if not passed:
        print("\n⚠️ 기준 미달 - 캘리브레이션 재검토 필요")
        sys.exit(1)

    print("\n✅ Week 1-2 최종 검증 완료 - Week 3로 진행 가능")
