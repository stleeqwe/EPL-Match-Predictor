"""
Expected Threat (xT) 계산 모듈
축구 경기에서 각 행동의 공격 기여도를 공간적으로 평가

참고:
- Karun Singh의 xT 프레임워크
- 12x8 그리드 기반 위협도 매트릭스
"""

import numpy as np
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExpectedThreatCalculator:
    """
    Expected Threat (xT) 계산 클래스

    경기장을 12x8 그리드로 나누고, 각 위치에서의 슈팅/이동 위협도를 계산
    """

    def __init__(self):
        """
        기본 xT 매트릭스 초기화 (12x8 그리드)

        - 12 columns (x축): 세로 방향 (자기 진영 → 상대 진영)
        - 8 rows (y축): 가로 방향 (사이드라인)
        - 값: 0~1 사이 (득점 위협도)
        """
        # Karun Singh의 연구 기반 기본 xT 매트릭스
        self.xt_matrix = np.array([
            [0.00616, 0.00946, 0.01280, 0.01642, 0.02113, 0.02682, 0.03380, 0.04213, 0.05249, 0.06582, 0.08367, 0.11197],
            [0.00745, 0.01077, 0.01449, 0.01868, 0.02401, 0.03044, 0.03828, 0.04771, 0.05937, 0.07428, 0.09413, 0.12561],
            [0.00885, 0.01223, 0.01633, 0.02112, 0.02710, 0.03429, 0.04304, 0.05362, 0.06664, 0.08323, 0.10520, 0.14014],
            [0.01025, 0.01369, 0.01817, 0.02356, 0.03019, 0.03814, 0.04780, 0.05954, 0.07390, 0.09218, 0.11628, 0.15467],
            [0.01025, 0.01369, 0.01817, 0.02356, 0.03019, 0.03814, 0.04780, 0.05954, 0.07390, 0.09218, 0.11628, 0.15467],
            [0.00885, 0.01223, 0.01633, 0.02112, 0.02710, 0.03429, 0.04304, 0.05362, 0.06664, 0.08323, 0.10520, 0.14014],
            [0.00745, 0.01077, 0.01449, 0.01868, 0.02401, 0.03044, 0.03828, 0.04771, 0.05937, 0.07428, 0.09413, 0.12561],
            [0.00616, 0.00946, 0.01280, 0.01642, 0.02113, 0.02682, 0.03380, 0.04213, 0.05249, 0.06582, 0.08367, 0.11197]
        ])

    def get_xt_value(self, x: float, y: float) -> float:
        """
        특정 위치의 xT 값 반환

        Args:
            x: X 좌표 (0~100, 0=자기 진영, 100=상대 진영)
            y: Y 좌표 (0~100, 0=왼쪽 사이드, 100=오른쪽 사이드)

        Returns:
            float: xT 값 (0~1)
        """
        # 좌표를 그리드 인덱스로 변환
        col = min(int(x / 100 * 12), 11)
        row = min(int(y / 100 * 8), 7)

        return self.xt_matrix[row, col]

    def calculate_move_xt(self, start_x: float, start_y: float, end_x: float, end_y: float) -> float:
        """
        이동(패스, 드리블)의 xT 증가량 계산

        Args:
            start_x, start_y: 시작 위치
            end_x, end_y: 종료 위치

        Returns:
            float: xT 증가량 (음수면 위협도 감소)
        """
        start_xt = self.get_xt_value(start_x, start_y)
        end_xt = self.get_xt_value(end_x, end_y)

        return end_xt - start_xt

    def calculate_team_xt_from_actions(self, actions_df: pd.DataFrame) -> dict:
        """
        팀의 행동 데이터로부터 xT 메트릭 계산

        Args:
            actions_df: 행동 데이터 DataFrame
                필수 컬럼: action_type, start_x, start_y, end_x, end_y, player_name

        Returns:
            dict: xT 메트릭
        """
        total_xt = 0
        action_xt = []

        for _, action in actions_df.iterrows():
            if action['action_type'] in ['pass', 'dribble', 'carry']:
                xt_gain = self.calculate_move_xt(
                    action['start_x'],
                    action['start_y'],
                    action['end_x'],
                    action['end_y']
                )
                total_xt += xt_gain
                action_xt.append({
                    'player': action['player_name'],
                    'action': action['action_type'],
                    'xt_gain': xt_gain
                })

        # 선수별 xT 집계
        player_xt = pd.DataFrame(action_xt).groupby('player')['xt_gain'].sum().to_dict()

        return {
            'total_xt': total_xt,
            'player_xt': player_xt,
            'avg_xt_per_action': total_xt / len(actions_df) if len(actions_df) > 0 else 0
        }

    def calculate_team_xt_from_stats(self, team_stats: dict) -> float:
        """
        팀 통계 데이터로부터 xT 추정

        Args:
            team_stats: 팀 통계 딕셔너리
                - passes: 패스 수
                - successful_passes: 성공한 패스 수
                - progressive_passes: 전진 패스 수
                - dribbles: 드리블 수
                - shots: 슈팅 수
                - possession: 점유율

        Returns:
            float: 추정 xT 값
        """
        # 간단한 휴리스틱 기반 xT 추정
        estimated_xt = 0

        # 성공한 패스 기여도 (평균 xT 증가 = 0.01)
        if 'successful_passes' in team_stats:
            estimated_xt += team_stats['successful_passes'] * 0.01

        # 전진 패스 추가 기여도
        if 'progressive_passes' in team_stats:
            estimated_xt += team_stats['progressive_passes'] * 0.03

        # 드리블 기여도
        if 'dribbles' in team_stats:
            estimated_xt += team_stats['dribbles'] * 0.04

        # 슈팅 기여도 (페널티 박스 내 위치 가정)
        if 'shots' in team_stats:
            estimated_xt += team_stats['shots'] * 0.08

        # 점유율 보정
        if 'possession' in team_stats:
            possession_factor = team_stats['possession'] / 50  # 50% 기준 정규화
            estimated_xt *= possession_factor

        return estimated_xt

    def calculate_match_xt_score(self, home_stats: dict, away_stats: dict) -> dict:
        """
        경기의 xT 스코어 계산

        Args:
            home_stats: 홈팀 통계
            away_stats: 원정팀 통계

        Returns:
            dict: xT 스코어 및 분석
        """
        home_xt = self.calculate_team_xt_from_stats(home_stats)
        away_xt = self.calculate_team_xt_from_stats(away_stats)

        xt_diff = home_xt - away_xt
        xt_ratio = home_xt / away_xt if away_xt > 0 else float('inf')

        # xT 기반 예상 득점 (간단한 선형 변환)
        home_expected_goals = home_xt * 0.015
        away_expected_goals = away_xt * 0.015

        return {
            'home_xt': home_xt,
            'away_xt': away_xt,
            'xt_difference': xt_diff,
            'xt_ratio': xt_ratio,
            'home_expected_goals_from_xt': home_expected_goals,
            'away_expected_goals_from_xt': away_expected_goals,
            'dominant_team': 'home' if xt_diff > 0 else 'away'
        }

    def visualize_xt_matrix(self):
        """
        xT 매트릭스 시각화 (텍스트)
        """
        logger.info("\n" + "=" * 60)
        logger.info("Expected Threat (xT) Matrix (12x8 Grid)")
        logger.info("=" * 60)
        logger.info("Direction: Left (Own Goal) → Right (Opponent Goal)")
        logger.info("-" * 60)

        for i, row in enumerate(self.xt_matrix):
            row_str = " | ".join([f"{val:.5f}" for val in row])
            logger.info(f"Row {i+1}: {row_str}")

        logger.info("=" * 60)

    def get_zone_name(self, x: float, y: float) -> str:
        """
        좌표에 해당하는 구역 이름 반환

        Args:
            x, y: 좌표 (0~100)

        Returns:
            str: 구역 이름 (예: "Defensive Third - Center")
        """
        # X축 구역
        if x < 33:
            x_zone = "Defensive Third"
        elif x < 67:
            x_zone = "Middle Third"
        else:
            x_zone = "Attacking Third"

        # Y축 구역
        if y < 25:
            y_zone = "Left Wing"
        elif y < 50:
            y_zone = "Left Center"
        elif y < 75:
            y_zone = "Right Center"
        else:
            y_zone = "Right Wing"

        return f"{x_zone} - {y_zone}"


if __name__ == "__main__":
    # 테스트
    logger.info("=" * 60)
    logger.info("Expected Threat (xT) Calculator Test")
    logger.info("=" * 60)

    calc = ExpectedThreatCalculator()

    # xT 매트릭스 시각화
    calc.visualize_xt_matrix()

    # 위치별 xT 값 테스트
    logger.info("\n" + "=" * 60)
    logger.info("Position xT Values")
    logger.info("=" * 60)

    test_positions = [
        (10, 50, "Own Penalty Area - Center"),
        (50, 50, "Midfield - Center"),
        (85, 50, "Opponent Penalty Area - Center"),
        (90, 25, "Opponent Penalty Area - Left"),
        (90, 75, "Opponent Penalty Area - Right")
    ]

    for x, y, desc in test_positions:
        xt_value = calc.get_xt_value(x, y)
        zone = calc.get_zone_name(x, y)
        logger.info(f"{desc}: xT = {xt_value:.5f} ({zone})")

    # 이동 xT 테스트
    logger.info("\n" + "=" * 60)
    logger.info("Move xT Calculation")
    logger.info("=" * 60)

    test_moves = [
        (20, 50, 60, 50, "Long pass from defense to midfield"),
        (50, 50, 80, 50, "Progressive pass to attacking third"),
        (75, 30, 85, 50, "Dribble towards center"),
        (85, 50, 90, 50, "Pass into penalty area")
    ]

    for start_x, start_y, end_x, end_y, desc in test_moves:
        xt_gain = calc.calculate_move_xt(start_x, start_y, end_x, end_y)
        logger.info(f"{desc}: xT gain = {xt_gain:+.5f}")

    # 팀 통계 기반 xT 계산
    logger.info("\n" + "=" * 60)
    logger.info("Match xT Analysis: Man City vs Arsenal")
    logger.info("=" * 60)

    home_stats = {
        'passes': 650,
        'successful_passes': 580,
        'progressive_passes': 45,
        'dribbles': 18,
        'shots': 15,
        'possession': 62
    }

    away_stats = {
        'passes': 450,
        'successful_passes': 380,
        'progressive_passes': 28,
        'dribbles': 12,
        'shots': 8,
        'possession': 38
    }

    match_xt = calc.calculate_match_xt_score(home_stats, away_stats)

    logger.info(f"Home xT: {match_xt['home_xt']:.2f}")
    logger.info(f"Away xT: {match_xt['away_xt']:.2f}")
    logger.info(f"xT Difference: {match_xt['xt_difference']:+.2f}")
    logger.info(f"xT Ratio: {match_xt['xt_ratio']:.2f}")
    logger.info(f"Dominant Team: {match_xt['dominant_team']}")
    logger.info(f"Expected Goals (Home): {match_xt['home_expected_goals_from_xt']:.2f}")
    logger.info(f"Expected Goals (Away): {match_xt['away_expected_goals_from_xt']:.2f}")

    logger.info("\n" + "=" * 60)
    logger.info("✅ xT Calculator Test Complete")
    logger.info("=" * 60)
