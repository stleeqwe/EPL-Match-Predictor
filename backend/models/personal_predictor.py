"""
Personal Analysis Predictor
선수 능력치 기반 예측 모델
"""

import numpy as np
from scipy.stats import poisson
from typing import Dict, List


class PersonalPredictor:
    """선수 개인 능력치 기반 예측"""

    def __init__(self):
        self.home_advantage = 1.3  # 홈 어드밴티지

    def calculate_team_strength(self, player_ratings: List[Dict]) -> Dict[str, float]:
        """
        선수 능력치를 팀 전력으로 변환

        Args:
            player_ratings: [
                {'position': 'ST', 'ratings': {'슈팅': 85, '위치선정': 80, ...}},
                ...
            ]

        Returns:
            {'attack': 1.5, 'defense': 1.2}
        """
        if not player_ratings or len(player_ratings) == 0:
            return {'attack': 1.0, 'defense': 1.0}

        # 포지션별 선수 그룹핑
        positions = {
            'attack': ['ST', 'W'],      # 공격수, 윙어
            'midfield': ['AM', 'DM'],   # 공격/수비 미드필더
            'defense': ['CB', 'FB'],    # 센터백, 풀백
            'gk': ['GK']                # 골키퍼
        }

        position_ratings = {
            'attack': [],
            'midfield': [],
            'defense': [],
            'gk': []
        }

        # 선수별 평균 능력치 계산
        for player in player_ratings:
            pos = player.get('position', '')
            ratings = player.get('ratings', {})

            if not ratings:
                continue

            # 해당 선수의 평균 능력치
            avg_rating = np.mean(list(ratings.values()))

            # 포지션별로 분류
            for group, pos_list in positions.items():
                if pos in pos_list:
                    position_ratings[group].append(avg_rating)
                    break

        # 포지션별 평균 계산
        attack_avg = np.mean(position_ratings['attack']) if position_ratings['attack'] else 50
        midfield_avg = np.mean(position_ratings['midfield']) if position_ratings['midfield'] else 50
        defense_avg = np.mean(position_ratings['defense']) if position_ratings['defense'] else 50
        gk_avg = np.mean(position_ratings['gk']) if position_ratings['gk'] else 50

        # 팀 공격력: 공격수(40%) + 미드필더(40%) + 윙어(20%)
        team_attack = (attack_avg * 0.4 + midfield_avg * 0.4 + attack_avg * 0.2) / 100

        # 팀 수비력: 수비수(50%) + 미드필더(30%) + 골키퍼(20%)
        team_defense = (defense_avg * 0.5 + midfield_avg * 0.3 + gk_avg * 0.2) / 100

        # 최소값 보정 (0.3 ~ 2.0 범위)
        team_attack = max(0.3, min(2.0, team_attack))
        team_defense = max(0.3, min(2.0, team_defense))

        return {
            'attack': team_attack,
            'defense': team_defense
        }

    def predict_match(self,
                     home_ratings: List[Dict],
                     away_ratings: List[Dict],
                     home_advantage: float = 1.3) -> Dict:
        """
        경기 예측

        Args:
            home_ratings: 홈팀 선수 능력치
            away_ratings: 원정팀 선수 능력치
            home_advantage: 홈 어드밴티지 (기본 1.3)

        Returns:
            예측 결과
        """
        # 팀 전력 계산
        home_strength = self.calculate_team_strength(home_ratings)
        away_strength = self.calculate_team_strength(away_ratings)

        # Lambda 계산 (예상 득점)
        # 홈팀 득점 = 홈팀 공격력 × 원정팀 수비력의 역수 × 홈 어드밴티지
        lambda_home = home_strength['attack'] / away_strength['defense'] * home_advantage

        # 원정팀 득점 = 원정팀 공격력 × 홈팀 수비력의 역수
        lambda_away = away_strength['attack'] / home_strength['defense']

        # Poisson 분포로 확률 계산
        max_goals = 10
        score_matrix = np.zeros((max_goals + 1, max_goals + 1))

        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                prob = poisson.pmf(i, lambda_home) * poisson.pmf(j, lambda_away)
                score_matrix[i, j] = prob

        # 정규화
        score_matrix /= score_matrix.sum()

        # 결과 확률 계산
        home_win = np.sum(np.tril(score_matrix, -1))  # 하삼각 (홈 득점 > 원정 득점)
        draw = np.sum(np.diag(score_matrix))           # 대각선 (동점)
        away_win = np.sum(np.triu(score_matrix, 1))   # 상삼각 (원정 득점 > 홈 득점)

        # Top 5 스코어
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
            'team_strength': {
                'home': home_strength,
                'away': away_strength
            }
        }


if __name__ == "__main__":
    # 테스트
    predictor = PersonalPredictor()

    # 더미 선수 데이터
    man_city_ratings = [
        {'position': 'ST', 'ratings': {'슈팅': 95, '위치선정': 90, '퍼스트터치': 85, '스피드': 92, '피지컬': 88}},
        {'position': 'W', 'ratings': {'드리블': 88, '스피드': 90, '크로스': 82, '슈팅': 80, '민첩성': 92}},
        {'position': 'AM', 'ratings': {'패스': 95, '비전': 96, '드리블': 85, '슈팅': 82, '창조력': 94}},
        {'position': 'DM', 'ratings': {'태클': 85, '인터셉트': 88, '패스': 90, '체력': 86, '포지셔닝': 87}},
        {'position': 'CB', 'ratings': {'태클': 88, '마크': 90, '헤더': 87, '포지셔닝': 89, '피지컬': 85}},
        {'position': 'GK', 'ratings': {'반응속도': 88, '포지셔닝': 90, '핸들링': 87, '발재간': 85, '공중볼': 86}},
    ]

    liverpool_ratings = [
        {'position': 'ST', 'ratings': {'슈팅': 88, '위치선정': 90, '퍼스트터치': 86, '스피드': 89, '피지컬': 87}},
        {'position': 'W', 'ratings': {'드리블': 90, '스피드': 94, '크로스': 80, '슈팅': 83, '민첩성': 93}},
        {'position': 'AM', 'ratings': {'패스': 87, '비전': 88, '드리블': 89, '슈팅': 85, '창조력': 86}},
        {'position': 'DM', 'ratings': {'태클': 86, '인터셉트': 87, '패스': 85, '체력': 90, '포지셔닝': 88}},
        {'position': 'CB', 'ratings': {'태클': 90, '마크': 92, '헤더': 89, '포지셔닝': 91, '피지컬': 88}},
        {'position': 'GK', 'ratings': {'반응속도': 90, '포지셔닝': 89, '핸들링': 91, '발재간': 82, '공중볼': 87}},
    ]

    print("=== Personal Analysis Prediction ===")
    print("Manchester City vs Liverpool\n")

    prediction = predictor.predict_match(man_city_ratings, liverpool_ratings)

    print(f"Home Win: {prediction['home_win']:.1f}%")
    print(f"Draw: {prediction['draw']:.1f}%")
    print(f"Away Win: {prediction['away_win']:.1f}%")
    print(f"\nExpected Goals: {prediction['expected_home_goals']:.2f} - {prediction['expected_away_goals']:.2f}")
    print(f"\nTeam Strength:")
    print(f"  Man City - Attack: {prediction['team_strength']['home']['attack']:.2f}, Defense: {prediction['team_strength']['home']['defense']:.2f}")
    print(f"  Liverpool - Attack: {prediction['team_strength']['away']['attack']:.2f}, Defense: {prediction['team_strength']['away']['defense']:.2f}")
    print(f"\nTop 5 Scores:")
    for score in prediction['top_scores']:
        print(f"  {score['score']}: {score['probability']:.1f}%")
