"""
특징 엔지니어링
Pi-ratings, 폼 지표, 홈/원정 분리 계산
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple

class FeatureEngineer:
    def __init__(self):
        self.pi_ratings = {}  # {team_name: {'home': rating, 'away': rating}}
        self.lambda_learning_rate = 0.06  # λ (Dixon & Coles 권장값)
        self.gamma_learning_rate = 0.6    # γ (골 차이 영향)

    def calculate_pi_ratings(self, matches_df: pd.DataFrame, allowed_seasons: list = None) -> Dict[str, Dict[str, float]]:
        """
        Pi-ratings 계산 (Constantinou & Fenton, 2013)

        Args:
            matches_df: 경기 결과 DataFrame
            allowed_seasons: 계산에 사용할 시즌 리스트 (예: ['2024-2025', '2025-2026'])

        Returns:
            Dict: {team_name: {'home': rating, 'away': rating}}
        """
        # 시즌 필터링
        if allowed_seasons:
            matches_df = matches_df[matches_df['season'].isin(allowed_seasons)].copy()

        # 모든 팀 초기화 (rating = 0)
        teams = set(matches_df['home_team'].unique()) | set(matches_df['away_team'].unique())
        self.pi_ratings = {team: {'home': 0.0, 'away': 0.0} for team in teams}

        # 시간순 정렬
        matches_df = matches_df.sort_values('date').reset_index(drop=True)

        for _, match in matches_df.iterrows():
            home_team = match['home_team']
            away_team = match['away_team']
            home_goals = match['home_score']
            away_goals = match['away_score']

            # 결과가 없는 경기는 skip
            if pd.isna(home_goals) or pd.isna(away_goals):
                continue

            # 현재 레이팅
            r_home = self.pi_ratings[home_team]['home']
            r_away = self.pi_ratings[away_team]['away']

            # 예상 골 차이
            expected_diff = r_home - r_away

            # 실제 골 차이
            actual_diff = home_goals - away_goals

            # 레이팅 업데이트
            delta = actual_diff - expected_diff

            self.pi_ratings[home_team]['home'] += self.lambda_learning_rate * delta
            self.pi_ratings[away_team]['away'] -= self.lambda_learning_rate * delta

        return self.pi_ratings

    def get_recent_form(self, team: str, matches_df: pd.DataFrame, n_matches: int = 5) -> Dict[str, float]:
        """
        최근 n경기 폼 지표 계산

        Args:
            team: 팀명
            matches_df: 경기 결과 DataFrame
            n_matches: 최근 경기 수

        Returns:
            Dict: 폼 지표
        """
        # 해당 팀의 경기만 필터링
        team_matches = matches_df[
            (matches_df['home_team'] == team) | (matches_df['away_team'] == team)
        ].sort_values('date', ascending=False).head(n_matches)

        if len(team_matches) == 0:
            return {
                'points_per_game': 0.0,
                'goals_per_game': 0.0,
                'conceded_per_game': 0.0,
                'xg_per_game': 0.0,
                'xga_per_game': 0.0,
                'win_rate': 0.0
            }

        total_points = 0
        total_goals_for = 0
        total_goals_against = 0
        total_xg = 0
        total_xga = 0
        wins = 0

        for _, match in team_matches.iterrows():
            is_home = match['home_team'] == team

            if is_home:
                goals_for = match['home_score']
                goals_against = match['away_score']
                xg_for = match.get('home_xg', 0)
                xg_against = match.get('away_xg', 0)
            else:
                goals_for = match['away_score']
                goals_against = match['home_score']
                xg_for = match.get('away_xg', 0)
                xg_against = match.get('home_xg', 0)

            # 결과가 없는 경기 skip
            if pd.isna(goals_for) or pd.isna(goals_against):
                continue

            total_goals_for += goals_for
            total_goals_against += goals_against

            if not pd.isna(xg_for):
                total_xg += xg_for
            if not pd.isna(xg_against):
                total_xga += xg_against

            # 승점 계산
            if goals_for > goals_against:
                total_points += 3
                wins += 1
            elif goals_for == goals_against:
                total_points += 1

        n_completed = len(team_matches[team_matches['home_score'].notna()])

        if n_completed == 0:
            n_completed = 1  # Division by zero 방지

        return {
            'points_per_game': total_points / n_completed,
            'goals_per_game': total_goals_for / n_completed,
            'conceded_per_game': total_goals_against / n_completed,
            'xg_per_game': total_xg / n_completed if total_xg > 0 else 0.0,
            'xga_per_game': total_xga / n_completed if total_xga > 0 else 0.0,
            'win_rate': wins / n_completed
        }

    def get_home_away_stats(self, team: str, matches_df: pd.DataFrame, is_home: bool, allowed_seasons: list = None) -> Dict[str, float]:
        """
        홈/원정 별도 통계 계산

        Args:
            team: 팀명
            matches_df: 경기 결과 DataFrame
            is_home: 홈 여부
            allowed_seasons: 계산에 사용할 시즌 리스트

        Returns:
            Dict: 홈/원정 통계
        """
        # 시즌 필터링
        if allowed_seasons:
            matches_df = matches_df[matches_df['season'].isin(allowed_seasons)].copy()

        if is_home:
            team_matches = matches_df[matches_df['home_team'] == team]
            goals_for_col = 'home_score'
            goals_against_col = 'away_score'
            xg_for_col = 'home_xg'
            xg_against_col = 'away_xg'
        else:
            team_matches = matches_df[matches_df['away_team'] == team]
            goals_for_col = 'away_score'
            goals_against_col = 'home_score'
            xg_for_col = 'away_xg'
            xg_against_col = 'home_xg'

        # 완료된 경기만
        completed_matches = team_matches[team_matches[goals_for_col].notna()]

        if len(completed_matches) == 0:
            return {
                'avg_goals_for': 0.0,
                'avg_goals_against': 0.0,
                'avg_xg': 0.0,
                'avg_xga': 0.0,
                'win_rate': 0.0
            }

        wins = sum(completed_matches[goals_for_col] > completed_matches[goals_against_col])

        return {
            'avg_goals_for': completed_matches[goals_for_col].mean(),
            'avg_goals_against': completed_matches[goals_against_col].mean(),
            'avg_xg': completed_matches[xg_for_col].mean() if xg_for_col in completed_matches else 0.0,
            'avg_xga': completed_matches[xg_against_col].mean() if xg_against_col in completed_matches else 0.0,
            'win_rate': wins / len(completed_matches)
        }

    def create_match_features(self, home_team: str, away_team: str,
                             matches_df: pd.DataFrame,
                             recent_weight: float = 0.5,
                             season_weight: float = 0.35,
                             last_season_weight: float = 0.15,
                             allowed_seasons: list = None) -> Dict[str, float]:
        """
        경기 예측을 위한 특징 벡터 생성

        Args:
            home_team: 홈팀
            away_team: 원정팀
            matches_df: 경기 데이터
            recent_weight: 최근 5경기 가중치
            season_weight: 현재 시즌 가중치
            last_season_weight: 지난 시즌 가중치
            allowed_seasons: 계산에 사용할 시즌 리스트

        Returns:
            Dict: 특징 벡터
        """
        # Pi-ratings 계산
        if not self.pi_ratings:
            self.calculate_pi_ratings(matches_df, allowed_seasons=allowed_seasons)

        # Pi-ratings
        home_pi = self.pi_ratings.get(home_team, {}).get('home', 0.0)
        away_pi = self.pi_ratings.get(away_team, {}).get('away', 0.0)

        # 최근 폼
        home_recent = self.get_recent_form(home_team, matches_df, n_matches=5)
        away_recent = self.get_recent_form(away_team, matches_df, n_matches=5)

        # 홈/원정 통계
        home_stats = self.get_home_away_stats(home_team, matches_df, is_home=True, allowed_seasons=allowed_seasons)
        away_stats = self.get_home_away_stats(away_team, matches_df, is_home=False, allowed_seasons=allowed_seasons)

        # 특징 벡터 구성
        features = {
            # Pi-ratings
            'home_pi_rating': home_pi,
            'away_pi_rating': away_pi,
            'pi_rating_diff': home_pi - away_pi,

            # 최근 폼
            'home_recent_ppg': home_recent['points_per_game'],
            'away_recent_ppg': away_recent['points_per_game'],
            'home_recent_goals': home_recent['goals_per_game'],
            'away_recent_goals': away_recent['goals_per_game'],
            'home_recent_xg': home_recent['xg_per_game'],
            'away_recent_xg': away_recent['xg_per_game'],

            # 홈/원정 통계
            'home_avg_goals': home_stats['avg_goals_for'],
            'home_avg_conceded': home_stats['avg_goals_against'],
            'away_avg_goals': away_stats['avg_goals_for'],
            'away_avg_conceded': away_stats['avg_goals_against'],

            # 가중치
            'recent_weight': recent_weight,
            'season_weight': season_weight,
            'last_season_weight': last_season_weight
        }

        return features


if __name__ == "__main__":
    # 테스트
    engineer = FeatureEngineer()

    # 더미 데이터
    matches = pd.DataFrame({
        'date': pd.date_range(start='2024-08-17', periods=10, freq='W'),
        'home_team': ['Man City', 'Arsenal', 'Liverpool', 'Man City', 'Arsenal'] * 2,
        'away_team': ['Arsenal', 'Liverpool', 'Man City', 'Liverpool', 'Man City'] * 2,
        'home_score': [2, 1, 2, 3, 1, 2, 2, 1, 2, 1],
        'away_score': [1, 1, 1, 1, 2, 1, 0, 1, 2, 1],
        'home_xg': [2.3, 1.5, 2.1, 2.8, 1.2, 2.1, 2.3, 1.4, 2.0, 1.3],
        'away_xg': [1.1, 1.4, 1.2, 0.9, 2.0, 1.0, 0.8, 1.3, 1.8, 1.2]
    })

    print("=== Pi-ratings ===")
    ratings = engineer.calculate_pi_ratings(matches)
    for team, rating in ratings.items():
        print(f"{team}: Home={rating['home']:.2f}, Away={rating['away']:.2f}")

    print("\n=== Recent Form ===")
    form = engineer.get_recent_form('Man City', matches, n_matches=5)
    for key, value in form.items():
        print(f"{key}: {value:.2f}")

    print("\n=== Match Features ===")
    features = engineer.create_match_features('Man City', 'Arsenal', matches)
    for key, value in features.items():
        print(f"{key}: {value:.3f}")
