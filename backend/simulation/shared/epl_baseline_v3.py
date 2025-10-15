"""
EPL Baseline Statistics v3
이벤트 기반 확률 엔진용 EPL 평균 통계

Data Source: EPL 2023-24 Season
Reference: Premier League Official Statistics
"""

EPL_BASELINE_V3 = {
    # ==========================================================================
    # 득점 관련 (Goals)
    # ==========================================================================
    "avg_goals_per_game": 2.8,        # 양팀 합계 평균 득점
    "home_goals": 1.53,               # 홈팀 평균 득점
    "away_goals": 1.27,               # 원정팀 평균 득점
    "goal_std": 1.6,                  # 득점 표준편차

    # ==========================================================================
    # 슛 관련 (Shots)
    # ==========================================================================
    "shots_per_game": 26.4,           # 양팀 합계 평균 슛 (경기당)
    "shot_per_minute": 0.26,          # 팀당 슛 확률 (분당) - 캘리브레이션됨 v3
    "shot_on_target_ratio": 0.33,     # 온타겟 비율 (전체 슛 중)
    "goal_conversion_on_target": 0.35, # 온타겟 슛 중 득점 확률 (캘리브레이션됨 v3)

    # ==========================================================================
    # 기타 이벤트 (Other Events)
    # ==========================================================================
    "corner_per_minute": 0.10,        # 코너킥 확률 (분당)
    "corners_per_game": 10.6,         # 양팀 합계 평균 코너킥
    "foul_per_minute": 0.08,          # 파울 확률 (분당)
    "fouls_per_game": 22.1,           # 양팀 합계 평균 파울
    "yellow_card_per_game": 3.8,      # 양팀 합계 평균 옐로카드
    "red_card_per_game": 0.28,        # 양팀 합계 평균 레드카드
    "penalty_per_game": 0.13,         # 양팀 합계 평균 페널티킥

    # ==========================================================================
    # 점유율 (Possession)
    # ==========================================================================
    "avg_possession": 50.0,           # 기본 점유율 (50-50)
    "possession_std": 12.0,           # 점유율 표준편차

    # ==========================================================================
    # 승률 분포 (Win Rate Distribution)
    # ==========================================================================
    "home_win_rate": 0.46,            # 홈팀 승률
    "draw_rate": 0.27,                # 무승부 비율
    "away_win_rate": 0.27,            # 원정팀 승률

    # ==========================================================================
    # 시간대별 득점 분포 (Goal Distribution by Time)
    # ==========================================================================
    "goals_by_period": {
        "0-15": 0.12,                 # 0-15분 득점 비율
        "15-30": 0.18,                # 15-30분 득점 비율
        "30-45": 0.20,                # 30-45분 득점 비율
        "45-60": 0.18,                # 45-60분 득점 비율
        "60-75": 0.17,                # 60-75분 득점 비율
        "75-90": 0.15                 # 75-90분 득점 비율
    },

    # ==========================================================================
    # 전술 매치업 계수 (Tactical Matchup Coefficients)
    # ==========================================================================
    "tactical_coefficients": {
        # 포메이션별 공격 보정
        "formation_attack_modifier": {
            "4-3-3": 1.12,            # 공격적 포메이션
            "4-2-3-1": 1.08,
            "4-4-2": 1.00,            # 기본
            "3-5-2": 0.95,
            "5-3-2": 0.88,            # 수비적 포메이션
            "3-4-3": 1.05
        },

        # 압박 강도별 계수
        "press_intensity_effect": {
            "high": {                 # 압박 > 80
                "pass_success": 0.88,
                "turnover": 1.35
            },
            "medium": {               # 압박 60-80
                "pass_success": 0.95,
                "turnover": 1.15
            },
            "low": {                  # 압박 < 60
                "pass_success": 1.0,
                "turnover": 1.0
            }
        }
    },

    # ==========================================================================
    # 경기 상황 계수 (Match State Coefficients)
    # ==========================================================================
    "match_state_modifiers": {
        "leading": {                  # 이기고 있을 때
            "shot_rate": 0.85,
            "defensive_positioning": 1.15
        },
        "trailing": {                 # 지고 있을 때
            "shot_rate": 1.18,
            "risk_taking": 1.25
        },
        "drawing": {                  # 동점일 때
            "shot_rate": 1.0,
            "balanced": 1.0
        }
    },

    # ==========================================================================
    # 체력 감소 계수 (Fatigue Coefficients)
    # ==========================================================================
    "fatigue_effect": {
        "70-80": 0.95,                # 70-80분 체력 95%
        "80-90": 0.88                 # 80-90분 체력 88%
    }
}


def validate_baseline(baseline: dict) -> bool:
    """
    EPL Baseline 검증

    검증 항목:
    1. 홈/원정 득점 합이 전체 평균과 일치
    2. 승률 합이 1.0
    3. 시간대별 득점 비율 합이 1.0

    Returns:
        검증 통과 여부
    """
    # 1. 득점 검증
    total_goals = baseline["home_goals"] + baseline["away_goals"]
    assert abs(total_goals - baseline["avg_goals_per_game"]) < 0.1, \
        f"득점 불일치: {total_goals} != {baseline['avg_goals_per_game']}"

    # 2. 승률 검증
    total_win_rate = (baseline["home_win_rate"] +
                      baseline["draw_rate"] +
                      baseline["away_win_rate"])
    assert abs(total_win_rate - 1.0) < 0.01, \
        f"승률 합 불일치: {total_win_rate} != 1.0"

    # 3. 시간대별 득점 비율 검증
    goal_period_sum = sum(baseline["goals_by_period"].values())
    assert abs(goal_period_sum - 1.0) < 0.01, \
        f"시간대별 득점 비율 합 불일치: {goal_period_sum} != 1.0"

    print("✅ EPL Baseline v3 검증 통과")
    return True


# 검증 실행
if __name__ == "__main__":
    validate_baseline(EPL_BASELINE_V3)

    # 주요 통계 출력
    print("\n=== EPL Baseline v3 주요 통계 ===")
    print(f"평균 득점: {EPL_BASELINE_V3['avg_goals_per_game']}골/경기")
    print(f"홈 승률: {EPL_BASELINE_V3['home_win_rate']:.1%}")
    print(f"분당 슛 확률: {EPL_BASELINE_V3['shot_per_minute']}")
    print(f"온타겟 비율: {EPL_BASELINE_V3['shot_on_target_ratio']:.1%}")
    print(f"온타겟 득점률: {EPL_BASELINE_V3['goal_conversion_on_target']:.1%}")
