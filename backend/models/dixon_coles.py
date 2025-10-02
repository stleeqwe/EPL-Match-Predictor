"""
Dixon-Coles 모델 구현 (Time-Weighted)
Modelling Association Football Scores and Inefficiencies in the Football Betting Market (1997)

시간 가중치 추가:
- calculate_exponential_decay_weights() 활용
- 최근 경기에 더 높은 가중치 부여
"""

import numpy as np
from scipy.stats import poisson
from scipy.optimize import minimize
from typing import Dict, Tuple
import pandas as pd
import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.time_weighting import calculate_exponential_decay_weights

class DixonColesModel:
    def __init__(self, xi=0.005):
        self.home_advantage = 1.3  # γ (홈 어드밴티지)
        self.rho = -0.15  # ρ (저점수 경기 보정 파라미터)
        self.xi = xi  # ξ (시간 감쇠 파라미터) - 기본값 0.005
        self.team_attack = {}  # α (공격력)
        self.team_defense = {}  # β (수비력)

    def tau(self, home_goals: int, away_goals: int, lambda_home: float, lambda_away: float) -> float:
        """
        Dixon-Coles tau 함수 (저점수 경기 보정)

        Args:
            home_goals: 홈팀 득점
            away_goals: 원정팀 득점
            lambda_home: 홈팀 예상 득점
            lambda_away: 원정팀 예상 득점

        Returns:
            float: 보정 계수
        """
        if home_goals == 0 and away_goals == 0:
            return 1 - lambda_home * lambda_away * self.rho
        elif home_goals == 0 and away_goals == 1:
            return 1 + lambda_home * self.rho
        elif home_goals == 1 and away_goals == 0:
            return 1 + lambda_away * self.rho
        elif home_goals == 1 and away_goals == 1:
            return 1 - self.rho
        else:
            return 1.0

    def time_weight(self, days_ago: float) -> float:
        """
        시간 가중치 함수

        Args:
            days_ago: 며칠 전 경기인지

        Returns:
            float: 가중치 (최근 경기일수록 높음)
        """
        return np.exp(-self.xi * days_ago)

    def fit(self, matches_df: pd.DataFrame, allowed_seasons: list = None):
        """
        모델 학습

        Args:
            matches_df: 경기 데이터 (home_team, away_team, home_score, away_score, date, season)
            allowed_seasons: 학습에 사용할 시즌 리스트 (예: ['2024-2025', '2025-2026'])
        """
        # 시즌 필터링
        if allowed_seasons:
            matches_df = matches_df[matches_df['season'].isin(allowed_seasons)].copy()

        # 팀 목록 추출
        teams = sorted(set(matches_df['home_team'].unique()) | set(matches_df['away_team'].unique()))
        n_teams = len(teams)

        # 팀 인덱스 매핑
        team_to_idx = {team: idx for idx, team in enumerate(teams)}

        # 초기 파라미터 설정
        # [attack_1, ..., attack_n, defense_1, ..., defense_n, home_adv, rho]
        initial_params = np.concatenate([
            np.ones(n_teams) * 0.1,  # 공격력
            np.ones(n_teams) * 0.1,  # 수비력
            [self.home_advantage],    # 홈 어드밴티지
            [self.rho]                # rho
        ])

        # 경기 데이터 준비
        completed_matches = matches_df[matches_df['home_score'].notna()].copy()

        # 시간 가중치 계산 (calculate_exponential_decay_weights 사용)
        match_weights = calculate_exponential_decay_weights(
            completed_matches['date'],
            xi=self.xi
        )
        completed_matches['weight'] = match_weights

        def negative_log_likelihood(params):
            """음의 로그 가능도 (시간 가중치 적용)"""
            attack = params[:n_teams]
            defense = params[n_teams:2*n_teams]
            home_adv = params[2*n_teams]
            rho = params[2*n_teams + 1]

            log_likelihood = 0

            for idx, match in completed_matches.iterrows():
                home_idx = team_to_idx[match['home_team']]
                away_idx = team_to_idx[match['away_team']]

                # Lambda 계산
                lambda_home = attack[home_idx] * defense[away_idx] * home_adv
                lambda_away = attack[away_idx] * defense[home_idx]

                # 시간 가중치 (이미 계산된 값 사용)
                weight = match['weight']

                # Poisson 확률
                home_goals = int(match['home_score'])
                away_goals = int(match['away_score'])

                prob = (poisson.pmf(home_goals, lambda_home) *
                       poisson.pmf(away_goals, lambda_away) *
                       self.tau_modified(home_goals, away_goals, lambda_home, lambda_away, rho))

                if prob > 0:
                    log_likelihood += weight * np.log(prob)

            return -log_likelihood

        # 최적화
        result = minimize(
            negative_log_likelihood,
            initial_params,
            method='L-BFGS-B',
            bounds=[(0.01, 5.0)] * (2 * n_teams) + [(1.0, 2.0), (-0.5, 0.0)]
        )

        # 학습된 파라미터 저장
        attack = result.x[:n_teams]
        defense = result.x[n_teams:2*n_teams]
        self.home_advantage = result.x[2*n_teams]
        self.rho = result.x[2*n_teams + 1]

        self.team_attack = {teams[i]: attack[i] for i in range(n_teams)}
        self.team_defense = {teams[i]: defense[i] for i in range(n_teams)}

    def tau_modified(self, home_goals, away_goals, lambda_home, lambda_away, rho):
        """Modified tau for optimization"""
        if home_goals == 0 and away_goals == 0:
            return 1 - lambda_home * lambda_away * rho
        elif home_goals == 0 and away_goals == 1:
            return 1 + lambda_home * rho
        elif home_goals == 1 and away_goals == 0:
            return 1 + lambda_away * rho
        elif home_goals == 1 and away_goals == 1:
            return 1 - rho
        else:
            return 1.0

    def predict_match(self, home_team: str, away_team: str, max_goals: int = 10) -> Dict[str, float]:
        """
        경기 결과 예측

        Args:
            home_team: 홈팀
            away_team: 원정팀
            max_goals: 최대 득점 (계산 범위)

        Returns:
            Dict: 예측 결과
        """
        # Lambda 계산
        lambda_home = (self.team_attack.get(home_team, 1.0) *
                      self.team_defense.get(away_team, 1.0) *
                      self.home_advantage)

        lambda_away = (self.team_attack.get(away_team, 1.0) *
                      self.team_defense.get(home_team, 1.0))

        # 스코어 확률 행렬 계산
        score_matrix = np.zeros((max_goals + 1, max_goals + 1))

        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                prob = (poisson.pmf(i, lambda_home) *
                       poisson.pmf(j, lambda_away) *
                       self.tau(i, j, lambda_home, lambda_away))
                score_matrix[i, j] = prob

        # 정규화
        score_matrix /= score_matrix.sum()

        # 결과 확률 계산
        home_win = np.sum(np.tril(score_matrix, -1))  # 홈팀 득점 > 원정팀 득점
        draw = np.sum(np.diag(score_matrix))           # 동점
        away_win = np.sum(np.triu(score_matrix, 1))   # 원정팀 득점 > 홈팀 득점

        # 가장 가능성 높은 스코어 Top 5
        top_scores = []
        flat_indices = np.argsort(score_matrix.ravel())[::-1][:5]

        for idx in flat_indices:
            home_goals = idx // (max_goals + 1)
            away_goals = idx % (max_goals + 1)
            prob = score_matrix[home_goals, away_goals]
            top_scores.append({
                'score': f"{home_goals}-{away_goals}",
                'probability': prob * 100
            })

        return {
            'home_win': home_win * 100,
            'draw': draw * 100,
            'away_win': away_win * 100,
            'expected_home_goals': lambda_home,
            'expected_away_goals': lambda_away,
            'top_scores': top_scores,
            'lambda_home': lambda_home,
            'lambda_away': lambda_away
        }


if __name__ == "__main__":
    # 테스트
    model = DixonColesModel()

    # 더미 데이터
    matches = pd.DataFrame({
        'date': pd.date_range(start='2024-01-01', periods=20, freq='W'),
        'home_team': ['Man City', 'Arsenal', 'Liverpool', 'Chelsea', 'Tottenham'] * 4,
        'away_team': ['Arsenal', 'Liverpool', 'Man City', 'Tottenham', 'Chelsea'] * 4,
        'home_score': [2, 1, 2, 1, 2, 3, 2, 1, 2, 1, 2, 1, 3, 2, 1, 2, 1, 2, 1, 2],
        'away_score': [1, 1, 1, 0, 1, 1, 2, 1, 0, 1, 1, 1, 2, 1, 0, 1, 1, 1, 0, 1]
    })

    print("=== Training Dixon-Coles Model ===")
    model.fit(matches)

    print("\n=== Team Parameters ===")
    print("Attack:")
    for team, value in model.team_attack.items():
        print(f"  {team}: {value:.3f}")

    print("\nDefense:")
    for team, value in model.team_defense.items():
        print(f"  {team}: {value:.3f}")

    print(f"\nHome Advantage: {model.home_advantage:.3f}")
    print(f"Rho: {model.rho:.3f}")

    print("\n=== Match Prediction: Man City vs Arsenal ===")
    prediction = model.predict_match('Man City', 'Arsenal')

    print(f"Home Win: {prediction['home_win']:.1f}%")
    print(f"Draw: {prediction['draw']:.1f}%")
    print(f"Away Win: {prediction['away_win']:.1f}%")
    print(f"Expected Score: {prediction['expected_home_goals']:.2f} - {prediction['expected_away_goals']:.2f}")

    print("\nTop 5 Most Likely Scores:")
    for score in prediction['top_scores']:
        print(f"  {score['score']}: {score['probability']:.1f}%")
